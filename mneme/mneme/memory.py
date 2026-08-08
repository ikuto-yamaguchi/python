"""外部エピソード記憶。

知識をモデルのパラメータ(勾配学習で焼き込む重み)ではなく、
外部の (key, value) ストアとして保持する。特徴:

- 書き込みは append のみで勾配計算不要 → 新知識の追加コストはゼロ学習ステップ
- 読み出しはコサイン類似度の top-k 検索 → 完全一致に近い正確な想起
- ストアを差し替えるだけで再学習なしにドメインを切り替えられる
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


class EpisodicMemory:
    """コサイン類似度 top-k 検索による外部 (key, value) 記憶。"""

    def __init__(self, dim: int, device: str = "cpu"):
        self.dim = dim
        self.device = device
        self.keys = torch.empty(0, dim, device=device)
        self.values = torch.empty(0, dim, device=device)

    def __len__(self) -> int:
        return self.keys.shape[0]

    def clear(self) -> None:
        self.keys = torch.empty(0, self.dim, device=self.device)
        self.values = torch.empty(0, self.dim, device=self.device)

    @torch.no_grad()
    def write(self, keys: torch.Tensor, values: torch.Tensor) -> None:
        """(B, dim) の key/value ペアを追記する。勾配は保持しない。"""
        assert keys.shape == values.shape and keys.shape[1] == self.dim
        self.keys = torch.cat([self.keys, keys.detach().to(self.device)], dim=0)
        self.values = torch.cat([self.values, values.detach().to(self.device)], dim=0)

    def read(
        self, queries: torch.Tensor, k: int = 1, temperature: float = 0.05
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """(B, dim) のクエリで top-k 検索し、類似度で重み付けした value を返す。

        Returns:
            values: (B, dim) 重み付き集約された value
            scores: (B, k) 上位 k 件のコサイン類似度
        """
        B = queries.shape[0]
        if len(self) == 0:
            zeros = torch.zeros(B, self.dim, device=queries.device)
            return zeros, torch.zeros(B, k, device=queries.device)
        k = min(k, len(self))
        q = F.normalize(queries, dim=-1)
        mk = F.normalize(self.keys, dim=-1)
        sims = q @ mk.T  # (B, N)
        scores, idx = sims.topk(k, dim=-1)  # (B, k)
        weights = F.softmax(scores / temperature, dim=-1)  # (B, k)
        gathered = self.values[idx]  # (B, k, dim)
        values = (weights.unsqueeze(-1) * gathered).sum(dim=1)
        return values, scores
