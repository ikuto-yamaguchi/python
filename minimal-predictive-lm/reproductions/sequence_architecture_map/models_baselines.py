from __future__ import annotations

import math

import torch
from torch import Tensor, nn
import torch.nn.functional as F


class LanguageModel(nn.Module):
    def state_bytes(self, context_length: int) -> int:
        raise NotImplementedError

    def state_reads(self, context_length: int) -> int:
        return self.state_bytes(context_length) // 4


class GRULM(LanguageModel):
    def __init__(self, vocab_size: int, dim: int) -> None:
        super().__init__()
        self.dim = dim
        self.embedding = nn.Embedding(vocab_size, dim)
        self.gru = nn.GRU(dim, dim, batch_first=True)
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor, state: Tensor | None = None):
        output, state = self.gru(self.embedding(tokens), state)
        return self.head(self.norm(output)), state

    def state_bytes(self, context_length: int) -> int:
        return self.dim * 4


class DiagonalSSMLM(LanguageModel):
    """Selective diagonal SSM probe; not a full Mamba-2 reproduction."""

    def __init__(self, vocab_size: int, dim: int) -> None:
        super().__init__()
        self.dim = dim
        self.embedding = nn.Embedding(vocab_size, dim)
        self.in_norm = nn.LayerNorm(dim)
        self.decay, self.write, self.gate = nn.Linear(dim, dim), nn.Linear(dim, dim), nn.Linear(dim, dim)
        self.out = nn.Linear(dim, dim, bias=False)
        self.ffn = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, dim * 2), nn.GELU(), nn.Linear(dim * 2, dim))
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor, state: Tensor | None = None):
        batch, length = tokens.shape
        state = torch.zeros(batch, self.dim, device=tokens.device) if state is None else state
        outputs = []
        for index in range(length):
            x = self.in_norm(self.embedding(tokens[:, index]))
            decay, write = torch.sigmoid(self.decay(x) + 1.0), torch.tanh(self.write(x))
            state = decay * state + (1.0 - decay) * write
            y = x + self.out(state * torch.sigmoid(self.gate(x)))
            y = y + self.ffn(y)
            outputs.append(self.head(self.norm(y)))
        return torch.stack(outputs, dim=1), state

    def state_bytes(self, context_length: int) -> int:
        return self.dim * 4


class CausalSelfAttention(nn.Module):
    def __init__(self, dim: int, heads: int) -> None:
        super().__init__()
        if dim % heads:
            raise ValueError("dimension must be divisible by heads")
        self.dim, self.heads, self.head_dim = dim, heads, dim // heads
        self.qkv, self.out = nn.Linear(dim, dim * 3, bias=False), nn.Linear(dim, dim, bias=False)

    def forward(self, x: Tensor) -> Tensor:
        batch, length, dim = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        shape = (batch, length, self.heads, self.head_dim)
        q, k, v = (tensor.view(shape).transpose(1, 2) for tensor in (q, k, v))
        scores = (q @ k.transpose(-1, -2)) / math.sqrt(self.head_dim)
        scores = scores.masked_fill(torch.ones(length, length, device=x.device, dtype=torch.bool).triu(1), float("-inf"))
        value = F.softmax(scores, dim=-1) @ v
        return self.out(value.transpose(1, 2).contiguous().view(batch, length, dim))


class TransformerLM(LanguageModel):
    def __init__(self, vocab_size: int, dim: int, heads: int = 2, max_len: int = 256) -> None:
        super().__init__()
        self.dim = dim
        self.embedding, self.position = nn.Embedding(vocab_size, dim), nn.Embedding(max_len, dim)
        self.ln1, self.attn, self.ln2 = nn.LayerNorm(dim), CausalSelfAttention(dim, heads), nn.LayerNorm(dim)
        self.ffn = nn.Sequential(nn.Linear(dim, dim * 3), nn.GELU(), nn.Linear(dim * 3, dim))
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, vocab_size, bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor, state=None):
        positions = torch.arange(tokens.shape[1], device=tokens.device)
        x = self.embedding(tokens) + self.position(positions)
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return self.head(self.norm(x)), None

    def state_bytes(self, context_length: int) -> int:
        return 2 * context_length * self.dim * 4
