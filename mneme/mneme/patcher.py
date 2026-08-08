"""エントロピー動的パッチング(トークナイザーの置き換え)。

固定語彙の BPE トークナイザーは、頻度統計だけで文字列を切るため
特化ドメインの分布とずれると急激に非効率になる(数字・コード・
専門用語・多言語で顕著)。ここでは語彙表を一切持たず、

  1. 極小のバイトレベル言語モデルで「次のバイトの予測エントロピー」を推定
  2. エントロピーが閾値を超えた位置=情報量が跳ねる位置でパッチを区切る

ことで、予測が容易な区間は長いパッチに圧縮し、情報密度が高い区間に
計算資源を集中させる。境界はデータ適応的で、ドメインが変われば
エントロピーモデルを差し替えるだけで再適応できる。
(Byte Latent Transformer, Pagnoni et al. 2024 のエントロピーパッチングに基づく)
"""

from __future__ import annotations

import math
import random

import torch
import torch.nn as nn
import torch.nn.functional as F


class ByteEntropyLM(nn.Module):
    """次バイト予測のための極小 GRU 言語モデル。"""

    def __init__(self, emb_dim: int = 32, hidden: int = 96):
        super().__init__()
        self.emb = nn.Embedding(257, emb_dim)  # 256 バイト + BOS(256)
        self.gru = nn.GRU(emb_dim, hidden, batch_first=True)
        self.out = nn.Linear(hidden, 256)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(self.emb(x))
        return self.out(out)


class EntropyPatcher:
    """バイト列をエントロピー境界で可変長パッチに分割する。"""

    BOS = 256

    def __init__(
        self,
        emb_dim: int = 32,
        hidden: int = 96,
        threshold: float | None = None,
        max_patch: int = 16,
        device: str = "cpu",
    ):
        self.lm = ByteEntropyLM(emb_dim, hidden).to(device)
        self.threshold = threshold
        self.max_patch = max_patch
        self.device = device

    def fit(
        self,
        corpus: bytes,
        steps: int = 300,
        batch: int = 32,
        seqlen: int = 128,
        lr: float = 3e-3,
        seed: int = 0,
        verbose: bool = False,
    ) -> list[float]:
        """コーパスで次バイト予測を学習する。"""
        rng = random.Random(seed)
        data = torch.tensor(list(corpus), dtype=torch.long)
        opt = torch.optim.Adam(self.lm.parameters(), lr=lr)
        losses = []
        self.lm.train()
        for step in range(steps):
            starts = [rng.randrange(0, len(data) - seqlen - 1) for _ in range(batch)]
            x = torch.stack([data[s : s + seqlen] for s in starts]).to(self.device)
            bos = torch.full((batch, 1), self.BOS, dtype=torch.long, device=self.device)
            logits = self.lm(torch.cat([bos, x[:, :-1]], dim=1))
            loss = F.cross_entropy(logits.reshape(-1, 256), x.reshape(-1))
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
            if verbose and (step + 1) % 100 == 0:
                print(f"  entropy-lm step {step + 1}/{steps} loss={losses[-1]:.3f}")
        self.lm.eval()
        return losses

    @torch.no_grad()
    def entropies(self, data: bytes) -> torch.Tensor:
        """各位置のバイトを予測する際のエントロピー(bits)を返す。"""
        x = torch.tensor(list(data), dtype=torch.long, device=self.device)
        bos = torch.tensor([self.BOS], dtype=torch.long, device=self.device)
        inp = torch.cat([bos, x[:-1]]).unsqueeze(0)
        logits = self.lm(inp).squeeze(0)  # (L, 256)
        logp = F.log_softmax(logits, dim=-1)
        ent_nats = -(logp.exp() * logp).sum(dim=-1)
        return ent_nats / math.log(2.0)

    def calibrate(self, corpus: bytes, target_avg_patch: float = 6.0) -> float:
        """平均パッチ長が目標値になるよう閾値をコーパスから決める。"""
        ents = self.entropies(corpus)
        q = 1.0 - 1.0 / target_avg_patch
        self.threshold = float(torch.quantile(ents, q))
        return self.threshold

    def segment(self, data: bytes) -> list[tuple[int, int]]:
        """[start, end) のパッチ境界リストを返す。全バイトを必ず被覆する。"""
        if self.threshold is None:
            raise RuntimeError("threshold 未設定です。calibrate() を先に呼んでください。")
        if len(data) == 0:
            return []
        ents = self.entropies(data)
        bounds = [0]
        for i in range(1, len(data)):
            if float(ents[i]) > self.threshold or i - bounds[-1] >= self.max_patch:
                bounds.append(i)
        bounds.append(len(data))
        return list(zip(bounds[:-1], bounds[1:]))

    def show(self, text: str, sep: str = "|") -> str:
        """パッチ境界を可視化した文字列を返す(デバッグ用)。"""
        data = text.encode("utf-8")
        parts = [data[a:b] for a, b in self.segment(data)]
        return sep.join(p.decode("utf-8", errors="replace") for p in parts)
