"""MNEME 言語モデル: 全コンポーネントを結合した生成アーキテクチャ。

パイプライン:

  生バイト列
    → EntropyPatcher(可変長パッチに分割: トークナイザーの置き換え)
    → LocalEncoder(パッチ内バイト → パッチ潜在ベクトル)
    → LatentCore(パッチ潜在列上の因果 Transformer + 外部記憶読み出し)
    → LocalDecoder(次パッチのバイト列を自己回帰予測)

推論の系列長 O(パッチ数) は O(バイト数) より数倍短く、
Transformer の O(L^2) 計算はパッチ列上でのみ発生する。
外部記憶(EpisodicMemory)には過去のパッチ潜在を書き込めるため、
コンテキスト窓を超えた正確な長期想起が可能になる
(Memorizing Transformers, Wu et al. 2022 と同型のゲート付き読み出し)。
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .memory import EpisodicMemory
from .modules import BOS, PAD, VOCAB
from .patcher import EntropyPatcher


class MemoryAttention(nn.Module):
    """外部記憶からのゲート付き読み出し層。"""

    def __init__(self, dim: int, k: int = 4):
        super().__init__()
        self.k = k
        self.q_proj = nn.Linear(dim, dim)
        self.o_proj = nn.Linear(dim, dim)
        self.gate = nn.Linear(2 * dim, dim)

    def forward(self, h: torch.Tensor, memory: EpisodicMemory) -> torch.Tensor:
        if len(memory) == 0:
            return h
        shape = h.shape
        flat = h.reshape(-1, shape[-1])
        r, _ = memory.read(self.q_proj(flat), k=self.k)
        g = torch.sigmoid(self.gate(torch.cat([flat, r], dim=-1)))
        return (flat + g * self.o_proj(r)).reshape(shape)


class LocalEncoder(nn.Module):
    """パッチ内バイト列 → パッチ潜在ベクトル。"""

    def __init__(self, dim: int):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, dim, padding_idx=PAD)
        self.gru = nn.GRU(dim, dim, batch_first=True)

    def forward(self, patches: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        packed = nn.utils.rnn.pack_padded_sequence(
            self.emb(patches), lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, h = self.gru(packed)
        return h.squeeze(0)  # (num_patches, dim)


class LocalDecoder(nn.Module):
    """文脈潜在ベクトル → パッチ内バイト列の自己回帰予測。"""

    def __init__(self, dim: int):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, dim, padding_idx=PAD)
        self.gru = nn.GRU(dim, dim, batch_first=True)
        self.out = nn.Linear(dim, VOCAB)

    def forward(self, context: torch.Tensor, patches: torch.Tensor) -> torch.Tensor:
        B = patches.shape[0]
        bos = torch.full((B, 1), BOS, dtype=torch.long, device=patches.device)
        inp = torch.cat([bos, patches[:, :-1]], dim=1)
        h0 = torch.tanh(context).unsqueeze(0)
        out, _ = self.gru(self.emb(inp), h0)
        return self.out(out)


class MnemeLM(nn.Module):
    """トークナイザーフリー + 外部記憶の生成モデル本体。"""

    def __init__(
        self,
        dim: int = 128,
        core_layers: int = 2,
        core_heads: int = 4,
        max_patch: int = 16,
        memory_k: int = 4,
        patcher: EntropyPatcher | None = None,
    ):
        super().__init__()
        self.dim = dim
        self.max_patch = max_patch
        self.patcher = patcher  # 学習済みを注入(nn.Module ではないので別管理)
        self.local_encoder = LocalEncoder(dim)
        self.pos = nn.Embedding(2048, dim)
        layer = nn.TransformerEncoderLayer(
            d_model=dim,
            nhead=core_heads,
            dim_feedforward=dim * 4,
            batch_first=True,
            norm_first=True,
        )
        self.core = nn.TransformerEncoder(layer, num_layers=core_layers)
        self.memory_attn = MemoryAttention(dim, k=memory_k)
        self.memory = EpisodicMemory(dim)
        self.local_decoder = LocalDecoder(dim)

    def _patchify(self, data: bytes) -> tuple[torch.Tensor, torch.Tensor]:
        """バイト列を (S, max_patch) のパディング済みパッチ行列にする。"""
        spans = self.patcher.segment(data)
        S = len(spans)
        patches = torch.full((S, self.max_patch), PAD, dtype=torch.long)
        lengths = torch.zeros(S, dtype=torch.long)
        for i, (a, b) in enumerate(spans):
            chunk = list(data[a:b])[: self.max_patch]
            patches[i, : len(chunk)] = torch.tensor(chunk, dtype=torch.long)
            lengths[i] = len(chunk)
        return patches, lengths

    def forward(self, data: bytes, use_memory: bool = True) -> torch.Tensor:
        """バイト単位の平均 NLL(nats)を返す。

        パッチ i のバイト列は、パッチ 0..i-1 までの文脈潜在
        (+外部記憶からの読み出し)を条件に予測される。
        """
        patches, lengths = self._patchify(data)
        S = patches.shape[0]
        latents = self.local_encoder(patches, lengths)  # (S, dim)
        x = (latents + self.pos(torch.arange(S, device=patches.device))).unsqueeze(0)
        mask = nn.Transformer.generate_square_subsequent_mask(S)
        h = self.core(x, mask=mask, is_causal=True).squeeze(0)  # (S, dim)
        if use_memory:
            h = self.memory_attn(h, self.memory)
        # パッチ i の条件 = 直前までの文脈を集約した h[i-1](先頭はゼロ文脈)
        context = torch.cat([torch.zeros(1, self.dim, device=h.device), h[:-1]], dim=0)
        logits = self.local_decoder(context, patches)  # (S, max_patch, VOCAB)
        loss = nn.functional.cross_entropy(
            logits.reshape(-1, VOCAB), patches.reshape(-1), ignore_index=PAD
        )
        return loss

    @torch.no_grad()
    def memorize(self, data: bytes) -> None:
        """バイト列をパッチ潜在として外部記憶に書き込む(勾配不要)。"""
        patches, lengths = self._patchify(data)
        latents = self.local_encoder(patches, lengths)
        self.memory.write(latents, latents)

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())
