from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn
import torch.nn.functional as F

from models_baselines import LanguageModel


class DeltaNetLM(LanguageModel):
    """Gated delta-rule linear-attention probe."""

    def __init__(self, vocab_size: int, dim: int, head_size: int = 8) -> None:
        super().__init__()
        if dim % head_size:
            raise ValueError("dimension must be divisible by head size")
        self.dim, self.head_size, self.heads = dim, head_size, dim // head_size
        self.embedding, self.norm_in = nn.Embedding(vocab_size, dim), nn.LayerNorm(dim)
        self.q, self.k, self.v = (nn.Linear(dim, dim, bias=False) for _ in range(3))
        self.beta, self.decay = nn.Linear(dim, self.heads), nn.Linear(dim, self.heads)
        self.out = nn.Linear(dim, dim, bias=False)
        self.ffn = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, dim * 2), nn.GELU(), nn.Linear(dim * 2, dim))
        self.norm, self.head = nn.LayerNorm(dim), nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor, state: Tensor | None = None):
        batch, length = tokens.shape
        shape = (batch, self.heads, self.head_size, self.head_size)
        state = torch.zeros(shape, device=tokens.device) if state is None else state
        outputs = []
        for index in range(length):
            x = self.norm_in(self.embedding(tokens[:, index]))
            q = F.normalize(self.q(x).view(batch, self.heads, self.head_size), dim=-1)
            k = F.normalize(self.k(x).view(batch, self.heads, self.head_size), dim=-1)
            v = self.v(x).view(batch, self.heads, self.head_size)
            beta = torch.sigmoid(self.beta(x)).view(batch, self.heads, 1, 1)
            state = state * torch.sigmoid(self.decay(x) + 2.0).view(batch, self.heads, 1, 1)
            error = v - (state @ k.unsqueeze(-1)).squeeze(-1)
            state = state + beta * (error.unsqueeze(-1) @ k.unsqueeze(-2))
            y = x + self.out((state @ q.unsqueeze(-1)).squeeze(-1).reshape(batch, self.dim))
            y = y + self.ffn(y)
            outputs.append(self.head(self.norm(y)))
        return torch.stack(outputs, dim=1), state

    def state_bytes(self, context_length: int) -> int:
        return self.heads * self.head_size * self.head_size * 4


@dataclass
class RWKVState:
    x_prev: Tensor
    matrix: Tensor
    ffn_prev: Tensor


class RWKV7ProbeLM(LanguageModel):
    """One-layer readable RWKV-7 x070 mechanism probe."""

    def __init__(self, vocab_size: int, dim: int, head_size: int = 8) -> None:
        super().__init__()
        if dim % head_size:
            raise ValueError("dimension must be divisible by head size")
        self.dim, self.head_size, self.heads = dim, head_size, dim // head_size
        self.embedding, self.ln1, self.ln2 = nn.Embedding(vocab_size, dim), nn.LayerNorm(dim), nn.LayerNorm(dim)
        base = torch.linspace(0.05, 0.95, dim)
        for name, offset in (("x_r", 0), ("x_w", .05), ("x_k", .10), ("x_v", .15), ("x_a", .20), ("x_g", .25)):
            setattr(self, name, nn.Parameter((base + offset).clamp(0, 1)))
        rank = max(4, dim // 4)
        self.w1, self.w2 = nn.Linear(dim, rank, bias=False), nn.Linear(rank, dim, bias=False)
        self.a1, self.a2 = nn.Linear(dim, rank, bias=False), nn.Linear(rank, dim, bias=False)
        self.g1, self.g2 = nn.Linear(dim, rank, bias=False), nn.Linear(rank, dim, bias=False)
        self.w0, self.a0 = nn.Parameter(torch.linspace(-1.5, .5, dim)), nn.Parameter(torch.zeros(dim))
        self.k_k, self.k_a = nn.Parameter(torch.ones(dim)), nn.Parameter(torch.ones(dim))
        self.r_k = nn.Parameter(torch.zeros(self.heads, head_size))
        self.r, self.k, self.v, self.o = (nn.Linear(dim, dim, bias=False) for _ in range(4))
        self.gn_w, self.gn_b = nn.Parameter(torch.ones(dim)), nn.Parameter(torch.zeros(dim))
        self.ffn_mix = nn.Parameter(torch.linspace(.1, .9, dim))
        self.ffn_k, self.ffn_v = nn.Linear(dim, dim * 3, bias=False), nn.Linear(dim * 3, dim, bias=False)
        self.norm, self.head = nn.LayerNorm(dim), nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def initial_state(self, batch: int, device) -> RWKVState:
        return RWKVState(
            torch.zeros(batch, self.dim, device=device),
            torch.zeros(batch, self.heads, self.head_size, self.head_size, device=device),
            torch.zeros(batch, self.dim, device=device),
        )

    def forward(self, tokens: Tensor, state: RWKVState | None = None):
        batch, length = tokens.shape
        state = self.initial_state(batch, tokens.device) if state is None else state
        outputs = []
        for index in range(length):
            raw, x = self.embedding(tokens[:, index]), self.ln1(self.embedding(tokens[:, index]))
            diff = state.x_prev - x
            xr, xw, xk, xv, xa, xg = [x + diff * getattr(self, name) for name in ("x_r", "x_w", "x_k", "x_v", "x_a", "x_g")]
            r, k, v = self.r(xr), self.k(xk), self.v(xv)
            w = torch.exp(-0.606531 * torch.sigmoid(self.w0 + self.w2(torch.tanh(self.w1(xw)))))
            a, g = torch.sigmoid(self.a0 + self.a2(self.a1(xa))), self.g2(torch.sigmoid(self.g1(xg)))
            kk = F.normalize((k * self.k_k).view(batch, self.heads, self.head_size), dim=-1).reshape(batch, self.dim)
            k = k * (1 + (a - 1) * self.k_a)
            kh, vh, rh = (tensor.view(batch, self.heads, self.head_size) for tensor in (k, v, r))
            kkh, ah = kk.view(batch, self.heads, self.head_size), a.view(batch, self.heads, self.head_size)
            matrix = state.matrix * w.view(batch, self.heads, 1, self.head_size)
            matrix = matrix + state.matrix @ ((-kkh).unsqueeze(-1) @ (kkh * ah).unsqueeze(-2))
            matrix = matrix + vh.unsqueeze(-1) @ kh.unsqueeze(-2)
            y = (matrix @ rh.unsqueeze(-1)).squeeze(-1).reshape(batch, self.dim)
            y = F.group_norm(y, self.heads, self.gn_w, self.gn_b, eps=64e-5)
            y = y + ((rh * kh * self.r_k).sum(-1, keepdim=True) * vh).reshape(batch, self.dim)
            hidden = raw + self.o(y * g)
            z = self.ln2(hidden)
            mixed = z + (state.ffn_prev - z) * self.ffn_mix
            hidden = hidden + self.ffn_v(F.relu(self.ffn_k(mixed)).square())
            state = RWKVState(x, matrix, z)
            outputs.append(self.head(self.norm(hidden)))
        return torch.stack(outputs, dim=1), state

    def state_bytes(self, context_length: int) -> int:
        return (2 * self.dim + self.heads * self.head_size * self.head_size) * 4
