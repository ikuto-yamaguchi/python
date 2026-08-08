"""バイトレベルの基本モジュール(トークナイザー不使用)。

語彙は 0-255 の生バイト + 特殊 3 記号のみ。どんな言語・記号・
バイナリでも前処理なしに扱え、語彙構築や OOV の問題が存在しない。
"""

from __future__ import annotations

import torch
import torch.nn as nn

PAD = 256
BOS = 257
EOS = 258
VOCAB = 259


def to_bytes(s: str) -> list[int]:
    return list(s.encode("utf-8"))


def pad_batch(seqs: list[list[int]], device: str = "cpu") -> tuple[torch.Tensor, torch.Tensor]:
    """バイト列のリストを (B, L) にパディングし、長さテンソルと共に返す。"""
    lengths = torch.tensor([len(s) for s in seqs], dtype=torch.long)
    L = int(lengths.max())
    out = torch.full((len(seqs), L), PAD, dtype=torch.long)
    for i, s in enumerate(seqs):
        out[i, : len(s)] = torch.tensor(s, dtype=torch.long)
    return out.to(device), lengths.to(device)


class ByteEncoder(nn.Module):
    """バイト列 → 単一の潜在ベクトル。"""

    def __init__(self, latent_dim: int = 64, emb_dim: int = 64, hidden: int = 192):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, emb_dim, padding_idx=PAD)
        self.gru = nn.GRU(emb_dim, hidden, batch_first=True)
        self.proj = nn.Linear(hidden, latent_dim)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        packed = nn.utils.rnn.pack_padded_sequence(
            self.emb(x), lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, h = self.gru(packed)  # (1, B, hidden)
        return self.proj(h.squeeze(0))


class ByteDecoder(nn.Module):
    """潜在ベクトル → バイト列(自己回帰生成)。

    潜在ベクトルは初期隠れ状態に加えて毎ステップの入力にも連結する
    (条件情報が長い系列でも減衰しないようにするための定石)。
    """

    def __init__(self, latent_dim: int = 64, emb_dim: int = 64, hidden: int = 192):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, emb_dim, padding_idx=PAD)
        self.init_h = nn.Linear(latent_dim, hidden)
        self.gru = nn.GRU(emb_dim + latent_dim, hidden, batch_first=True)
        self.out = nn.Linear(hidden, VOCAB)

    def _step_input(self, tokens: torch.Tensor, latent: torch.Tensor) -> torch.Tensor:
        L = tokens.shape[1]
        lat = latent.unsqueeze(1).expand(-1, L, -1)
        return torch.cat([self.emb(tokens), lat], dim=-1)

    def forward(self, latent: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """teacher forcing で各位置のロジット (B, L+1, VOCAB) を返す。

        入力系列は [BOS, t1..tL]、教師は [t1..tL, EOS] を想定する。
        """
        B = latent.shape[0]
        bos = torch.full((B, 1), BOS, dtype=torch.long, device=latent.device)
        inp = torch.cat([bos, targets], dim=1)
        h0 = torch.tanh(self.init_h(latent)).unsqueeze(0)
        out, _ = self.gru(self._step_input(inp, latent), h0)
        return self.out(out)

    @torch.no_grad()
    def generate(self, latent: torch.Tensor, max_len: int = 32) -> list[list[int]]:
        B = latent.shape[0]
        h = torch.tanh(self.init_h(latent)).unsqueeze(0)
        tok = torch.full((B, 1), BOS, dtype=torch.long, device=latent.device)
        done = torch.zeros(B, dtype=torch.bool, device=latent.device)
        seqs: list[list[int]] = [[] for _ in range(B)]
        for _ in range(max_len):
            out, h = self.gru(self._step_input(tok, latent), h)
            tok = self.out(out[:, -1]).argmax(dim=-1, keepdim=True)
            for i in range(B):
                t = int(tok[i, 0])
                if not done[i]:
                    if t == EOS:
                        done[i] = True
                    elif t < 256:
                        seqs[i].append(t)
            if bool(done.all()):
                break
        return seqs


def decoder_loss(logits: torch.Tensor, targets: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
    """[t1..tL, EOS] を教師とした交差エントロピー。PAD は無視する。"""
    B, L = targets.shape
    eos_col = torch.full((B, 1), PAD, dtype=torch.long, device=targets.device)
    shifted = torch.cat([targets, eos_col], dim=1)
    shifted[torch.arange(B), lengths] = EOS
    return nn.functional.cross_entropy(
        logits.reshape(-1, VOCAB), shifted.reshape(-1), ignore_index=PAD
    )
