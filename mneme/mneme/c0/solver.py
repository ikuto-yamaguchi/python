"""条件充足ソルバ: 条件式の生バイト列 → 充足する整数値。

これがこの特化エージェントの「知能コア」で、約 0.7M パラメータしかない。
入力は `a >= -37` や `!(b == 42)` のようなテキスト(トークナイザーなし、
生バイト)。出力は 2 つのヘッドで構成する:

- 定数ヘッド: 条件式中の定数の数字列を復号(コピー系の read スキル)
- オフセットヘッド: 演算子と否定の意味論から {-1, 0, +1} を選ぶ
  (例: `a > 37` → 定数 37 + オフセット +1 → 38)

教師データは生成器が無限に作れる(条件と正解値のペア)。実タスクでは
ここが「教師 LLM の出力を実行検証でフィルタした軌跡」に置き換わる。
"""

from __future__ import annotations

import keyword
import random
import string

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..modules import ByteDecoder, ByteEncoder, decoder_loss, pad_batch, to_bytes
from .codegen import NEG, OPS, DOMAIN_CONSTS

# 実効演算子 → (定数に対するオフセット, クラス番号)
_OFFSET = {"==": 0, "!=": 1, ">": 1, ">=": 0, "<": -1, "<=": 0}
_OFFSET_CLASS = {-1: 0, 0: 1, 1: 2}
_CLASS_OFFSET = {v: k for k, v in _OFFSET_CLASS.items()}


def canonical_value(op: str, c: int, negated: bool) -> int:
    """条件の第一正準解(境界値)。"""
    if negated:
        op = NEG[op]
    return c + _OFFSET[op]


def _sample_condition(rng: random.Random) -> tuple[str, int, int]:
    """(条件テキスト, 定数, オフセットクラス) を 1 件サンプルする。"""
    while True:
        var = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 2)))
        if not keyword.iskeyword(var):
            break
    op = rng.choice(OPS)
    c = rng.choice(DOMAIN_CONSTS) if rng.random() < 0.3 else rng.randint(-999, 999)
    negated = rng.random() < 0.5
    text = f"{var} {op} {c}"
    if negated:
        text = f"!({text})"
    eff = NEG[op] if negated else op
    return text, c, _OFFSET_CLASS[_OFFSET[eff]]


class ConditionSolver(nn.Module):
    """条件式バイト列 → 充足整数値。"""

    def __init__(self, latent_dim: int = 96, emb_dim: int = 64, hidden: int = 256):
        super().__init__()
        self.encoder = ByteEncoder(latent_dim, emb_dim, hidden)
        self.const_decoder = ByteDecoder(latent_dim, emb_dim, hidden)
        self.offset_head = nn.Linear(latent_dim, 3)

    def fit(
        self,
        steps: int = 2500,
        batch: int = 128,
        lr: float = 2e-3,
        seed: int = 0,
        verbose: bool = False,
    ) -> list[float]:
        rng = random.Random(seed)
        opt = torch.optim.Adam(self.parameters(), lr=lr)
        losses = []
        self.train()
        for step in range(steps):
            samples = [_sample_condition(rng) for _ in range(batch)]
            x, xl = pad_batch([to_bytes(t) for t, _, _ in samples])
            y, yl = pad_batch([to_bytes(str(c)) for _, c, _ in samples])
            off = torch.tensor([o for _, _, o in samples], dtype=torch.long)
            latent = self.encoder(x, xl)
            logits = self.const_decoder(latent, y)
            loss = decoder_loss(logits, y, yl) + F.cross_entropy(
                self.offset_head(latent), off
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
            if verbose and (step + 1) % 250 == 0:
                print(f"  solver step {step + 1}/{steps} loss={losses[-1]:.4f}")
        self.eval()
        return losses

    @torch.no_grad()
    def encode(self, texts: list[str]) -> torch.Tensor:
        x, lengths = pad_batch([to_bytes(t) for t in texts])
        return self.encoder(x, lengths)

    @torch.no_grad()
    def predict(self, text: str) -> int | None:
        """条件テキストから充足値を推定する。解析不能なら None。"""
        x, lengths = pad_batch([to_bytes(text)])
        latent = self.encoder(x, lengths)
        digits = self.const_decoder.generate(latent, max_len=8)[0]
        try:
            c = int(bytes(digits).decode("ascii"))
        except ValueError:
            return None
        cls = int(self.offset_head(latent).argmax(dim=-1)[0])
        return c + _CLASS_OFFSET[cls]

    @torch.no_grad()
    def accuracy(self, n: int = 500, seed: int = 999) -> float:
        """ホールドアウト条件に対する充足率(実行で検証)。"""
        rng = random.Random(seed)
        ok = 0
        for _ in range(n):
            text, _, _ = _sample_condition(rng)
            v = self.predict(text)
            if v is None:
                continue
            expr = text.replace("!(", "not (") if text.startswith("!(") else text
            var = expr.split()[1 if expr.startswith("not") else 0].lstrip("(")
            if bool(eval(expr, {}, {var: v})):
                ok += 1
        return ok / n

    def param_count(self) -> int:
        return sum(p.numel() for p in self.parameters())
