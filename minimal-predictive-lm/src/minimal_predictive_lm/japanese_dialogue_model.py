from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Sequence

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence

PAD, BOS, EOS, BYTE_OFFSET, VOCAB_SIZE = 0, 1, 2, 3, 259


class ByteCodec:
    @staticmethod
    def encode(text: str, limit: int) -> list[int]:
        raw = text.encode("utf-8")[:limit]
        while raw:
            try:
                raw.decode("utf-8")
                break
            except UnicodeDecodeError:
                raw = raw[:-1]
        return [value + BYTE_OFFSET for value in raw]

    @staticmethod
    def decode(tokens: Sequence[int]) -> tuple[str, bool]:
        raw = bytes(int(t) - BYTE_OFFSET for t in tokens if BYTE_OFFSET <= int(t) < VOCAB_SIZE)
        try:
            return raw.decode("utf-8"), True
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace"), False


@dataclass(frozen=True)
class Pair:
    prompt: str
    response: str


@dataclass(frozen=True)
class Config:
    embedding_dim: int = 128
    hidden_dim: int = 256
    layers: int = 1
    max_prompt_bytes: int = 256
    max_response_bytes: int = 256
    batch_size: int = 32
    learning_rate: float = 0.002
    epochs: int = 1
    seed: int = 7


class DialogueCycleModel(nn.Module):
    """Fixed-memory, non-Transformer UTF-8 generator.

    Direction 0 learns prompt->response. Direction 1 uses the same parameters to
    reconstruct prompt from response, forcing the response state to preserve the
    communicative obligation rather than only local continuation statistics.
    """

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.embedding = nn.Embedding(VOCAB_SIZE, cfg.embedding_dim, padding_idx=PAD)
        self.encoder = nn.GRU(cfg.embedding_dim, cfg.hidden_dim, cfg.layers, batch_first=True)
        self.direction = nn.Embedding(2, cfg.hidden_dim)
        self.bridge = nn.Sequential(
            nn.Linear(cfg.hidden_dim * 2, cfg.hidden_dim),
            nn.Tanh(),
            nn.LayerNorm(cfg.hidden_dim),
        )
        self.decoder = nn.GRU(
            cfg.embedding_dim + cfg.hidden_dim,
            cfg.hidden_dim,
            cfg.layers,
            batch_first=True,
        )
        self.output = nn.Linear(cfg.hidden_dim, VOCAB_SIZE)

    def encode(self, source: torch.Tensor, lengths: torch.Tensor, direction: torch.Tensor):
        packed = pack_padded_sequence(
            self.embedding(source), lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.encoder(packed)
        context = self.bridge(torch.cat([hidden[-1], self.direction(direction)], -1))
        return context, context.unsqueeze(0).repeat(self.cfg.layers, 1, 1)

    def forward(self, source, lengths, decoder_input, direction):
        context, hidden = self.encode(source, lengths, direction)
        embedded = self.embedding(decoder_input)
        repeated = context.unsqueeze(1).expand(-1, embedded.size(1), -1)
        decoded, _ = self.decoder(torch.cat([embedded, repeated], -1), hidden)
        return self.output(decoded)

    @torch.no_grad()
    def generate(self, prompt: str, *, device="cpu", max_bytes: int | None = None):
        self.eval()
        ids = ByteCodec.encode(prompt, self.cfg.max_prompt_bytes) or [EOS]
        source = torch.tensor([ids], dtype=torch.long, device=device)
        lengths = torch.tensor([len(ids)], device=device)
        direction = torch.zeros(1, dtype=torch.long, device=device)
        context, hidden = self.encode(source, lengths, direction)
        current = torch.tensor([[BOS]], dtype=torch.long, device=device)
        generated: list[int] = []
        for _ in range(max_bytes or self.cfg.max_response_bytes):
            step = torch.cat([self.embedding(current), context.unsqueeze(1)], -1)
            decoded, hidden = self.decoder(step, hidden)
            current = self.output(decoded[:, -1]).argmax(-1, keepdim=True)
            token = int(current.item())
            if token == EOS:
                break
            if token not in (PAD, BOS):
                generated.append(token)
        text, valid = ByteCodec.decode(generated)
        return text, valid, generated

    def persistent_bytes(self) -> int:
        return sum(p.numel() * p.element_size() for p in self.parameters())


def _pad(sequences: Sequence[Sequence[int]]):
    lengths = torch.tensor([max(1, len(item)) for item in sequences])
    output = torch.full((len(sequences), int(lengths.max())), PAD, dtype=torch.long)
    for index, item in enumerate(sequences):
        if item:
            output[index, : len(item)] = torch.tensor(item)
        else:
            output[index, 0] = EOS
    return output, lengths


def make_batch(pairs: Sequence[Pair], cfg: Config, reverse: bool):
    if reverse:
        sources = [ByteCodec.encode(x.response, cfg.max_response_bytes) for x in pairs]
        targets = [ByteCodec.encode(x.prompt, cfg.max_prompt_bytes) + [EOS] for x in pairs]
        direction_value = 1
    else:
        sources = [ByteCodec.encode(x.prompt, cfg.max_prompt_bytes) for x in pairs]
        targets = [ByteCodec.encode(x.response, cfg.max_response_bytes) + [EOS] for x in pairs]
        direction_value = 0
    source, lengths = _pad(sources)
    decoder_input, _ = _pad([[BOS] + target[:-1] for target in targets])
    target, _ = _pad(targets)
    direction = torch.full((len(pairs),), direction_value, dtype=torch.long)
    return source, lengths, decoder_input, target, direction


def batch_loss(model: DialogueCycleModel, batch, device):
    source, lengths, decoder_input, target, direction = (x.to(device) for x in batch)
    logits = model(source, lengths, decoder_input, direction)
    return nn.functional.cross_entropy(
        logits.reshape(-1, VOCAB_SIZE), target.reshape(-1), ignore_index=PAD
    )


def train_model(train_pairs, valid_pairs, cfg: Config, *, cycle: bool, device):
    random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    model = DialogueCycleModel(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=0.01)
    order = list(range(len(train_pairs)))
    started = time.perf_counter()
    history = []
    for epoch in range(cfg.epochs):
        random.Random(cfg.seed + epoch).shuffle(order)
        model.train()
        total = 0.0
        steps = 0
        for start in range(0, len(order), cfg.batch_size):
            pairs = [train_pairs[i] for i in order[start : start + cfg.batch_size]]
            optimizer.zero_grad(set_to_none=True)
            answer = batch_loss(model, make_batch(pairs, cfg, False), device)
            loss = answer
            if cycle:
                loss = answer + 0.35 * batch_loss(model, make_batch(pairs, cfg, True), device)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += float(loss)
            steps += 1
        history.append({"epoch": epoch + 1, "train_loss": total / max(steps, 1)})
    answer_nll, reverse_nll = [], []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(valid_pairs), cfg.batch_size):
            pairs = valid_pairs[start : start + cfg.batch_size]
            answer_nll.append(float(batch_loss(model, make_batch(pairs, cfg, False), device)))
            reverse_nll.append(float(batch_loss(model, make_batch(pairs, cfg, True), device)))
    return model, {
        "cycle": cycle,
        "history": history,
        "training_seconds": time.perf_counter() - started,
        "valid_answer_nll": sum(answer_nll) / max(len(answer_nll), 1),
        "valid_reverse_nll": sum(reverse_nll) / max(len(reverse_nll), 1),
        "model_bytes": model.persistent_bytes(),
    }
