"""知識想起ベンチマーク: 外部記憶 vs パラメータ記憶。

「賢い小さな知能 + 正確で大量の外部記憶」というアーキテクチャ仮説を
検証するための最小タスク。ランダムな key→value の事実集合を保持し、
key を与えられたら value を正確に想起できるかを測る。

- MemoryRecallModel: 汎用の符号化/復号能力(=知能)だけを一度学習し、
  事実そのものは外部記憶に書き込む。事実の追加に勾配学習は不要。
- ParametricRecallModel: 同規模のネットワークに事実を勾配学習で
  焼き込む(通常の LLM が知識を保持する方法の縮図)。
"""

from __future__ import annotations

import random
import string

import torch
import torch.nn as nn

from .memory import EpisodicMemory
from .modules import ByteDecoder, ByteEncoder, decoder_loss, pad_batch, to_bytes


def make_facts(
    n: int, key_len: int = 8, val_len: int = 8, seed: int = 0
) -> list[tuple[str, str]]:
    """ユニークな key を持つランダム事実 (key, value) を n 件生成する。"""
    rng = random.Random(seed)
    keys: set[str] = set()
    while len(keys) < n:
        keys.add("".join(rng.choices(string.ascii_lowercase, k=key_len)))
    return [
        (k, "".join(rng.choices(string.ascii_lowercase, k=val_len)))
        for k in sorted(keys)
    ]


def random_strings(n: int, length: int, rng: random.Random) -> list[str]:
    return [
        "".join(rng.choices(string.ascii_lowercase, k=length)) for _ in range(n)
    ]


class MemoryRecallModel(nn.Module):
    """符号化/復号のみ学習し、事実は外部記憶に置くモデル。"""

    def __init__(self, latent_dim: int = 64, emb_dim: int = 64, hidden: int = 256):
        super().__init__()
        self.encoder = ByteEncoder(latent_dim, emb_dim, hidden)
        self.decoder = ByteDecoder(latent_dim, emb_dim, hidden)
        self.memory = EpisodicMemory(latent_dim)

    def train_codec(
        self,
        steps: int = 1500,
        batch: int = 128,
        str_len: int = 6,
        lr: float = 2e-3,
        seed: int = 0,
        verbose: bool = False,
    ) -> list[float]:
        """ランダム文字列の自己符号化で汎用の符号化/復号能力を学習する。

        学習データに事実は一切含まれない。ここで得るのは「文字列を
        潜在ベクトルへ可逆に写す」という汎用スキルのみで、後から書き
        込まれるどの事実に対しても勾配更新なしで機能する。
        """
        rng = random.Random(seed)
        opt = torch.optim.Adam(self.parameters(), lr=lr)
        losses = []
        self.train()
        for step in range(steps):
            xs = [to_bytes(s) for s in random_strings(batch, str_len, rng)]
            x, lengths = pad_batch(xs)
            latent = self.encoder(x, lengths)
            logits = self.decoder(latent, x)
            loss = decoder_loss(logits, x, lengths)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
            if verbose and (step + 1) % 100 == 0:
                print(f"  codec step {step + 1}/{steps} loss={losses[-1]:.4f}")
        self.eval()
        return losses

    @torch.no_grad()
    def write_facts(self, facts: list[tuple[str, str]]) -> None:
        """事実を外部記憶へ書き込む。勾配学習ステップ数はゼロ。"""
        keys, lk = pad_batch([to_bytes(k) for k, _ in facts])
        vals, lv = pad_batch([to_bytes(v) for _, v in facts])
        self.memory.write(self.encoder(keys, lk), self.encoder(vals, lv))

    @torch.no_grad()
    def answer(self, queries: list[str], max_len: int = 32) -> list[str]:
        x, lengths = pad_batch([to_bytes(q) for q in queries])
        q_latent = self.encoder(x, lengths)
        v_latent, _ = self.memory.read(q_latent, k=1)
        decoded = self.decoder.generate(v_latent, max_len=max_len)
        return [bytes(d).decode("utf-8", errors="replace") for d in decoded]


class ParametricRecallModel(nn.Module):
    """事実を重みに焼き込む同規模のベースライン。"""

    def __init__(self, latent_dim: int = 64, emb_dim: int = 64, hidden: int = 256):
        super().__init__()
        self.encoder = ByteEncoder(latent_dim, emb_dim, hidden)
        self.core = nn.Sequential(
            nn.Linear(latent_dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, latent_dim),
        )
        self.decoder = ByteDecoder(latent_dim, emb_dim, hidden)

    def train_on_facts(
        self,
        facts: list[tuple[str, str]],
        steps: int = 2000,
        batch: int = 128,
        lr: float = 2e-3,
        seed: int = 0,
        verbose: bool = False,
    ) -> list[float]:
        """事実集合そのものを教師データとして end-to-end 学習する。"""
        rng = random.Random(seed)
        opt = torch.optim.Adam(self.parameters(), lr=lr)
        losses = []
        self.train()
        for step in range(steps):
            sample = [facts[rng.randrange(len(facts))] for _ in range(batch)]
            keys, lk = pad_batch([to_bytes(k) for k, _ in sample])
            vals, lv = pad_batch([to_bytes(v) for _, v in sample])
            latent = self.core(self.encoder(keys, lk))
            logits = self.decoder(latent, vals)
            loss = decoder_loss(logits, vals, lv)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
            if verbose and (step + 1) % 300 == 0:
                print(f"  baseline step {step + 1}/{steps} loss={losses[-1]:.4f}")
        self.eval()
        return losses

    @torch.no_grad()
    def answer(self, queries: list[str], max_len: int = 32) -> list[str]:
        x, lengths = pad_batch([to_bytes(q) for q in queries])
        latent = self.core(self.encoder(x, lengths))
        decoded = self.decoder.generate(latent, max_len=max_len)
        return [bytes(d).decode("utf-8", errors="replace") for d in decoded]


def exact_match(model, facts: list[tuple[str, str]], batch: int = 256) -> float:
    """全事実に対する完全一致率を返す。"""
    correct = 0
    for i in range(0, len(facts), batch):
        chunk = facts[i : i + batch]
        preds = model.answer([k for k, _ in chunk])
        correct += sum(p == v for p, (_, v) in zip(preds, chunk))
    return correct / len(facts)
