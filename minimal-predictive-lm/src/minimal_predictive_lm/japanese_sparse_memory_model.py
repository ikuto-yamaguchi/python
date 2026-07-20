from __future__ import annotations

import math
import random
import time
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

PAD, BOS, EOS, UNK = 0, 1, 2, 3


class CharVocab:
    def __init__(self, chars: Sequence[str]):
        self.itos = ["<pad>", "<bos>", "<eos>", "<unk>"] + list(chars)
        self.stoi = {char: index for index, char in enumerate(self.itos)}

    @classmethod
    def build(cls, texts: Sequence[str], max_size: int = 4096):
        counts = Counter(char for text in texts for char in text)
        return cls([char for char, _ in counts.most_common(max_size - 4)])

    def encode(self, text: str, limit: int):
        return [self.stoi.get(char, UNK) for char in text[:limit]]

    def decode(self, ids: Sequence[int]):
        return "".join(self.itos[int(index)] for index in ids if int(index) >= 4)

    def __len__(self):
        return len(self.itos)

    def to_dict(self):
        return {"itos": self.itos}


@dataclass(frozen=True)
class Pair:
    prompt: str
    response: str


@dataclass(frozen=True)
class Config:
    embedding_dim: int = 128
    hidden_dim: int = 256
    slots: int = 16
    topk: int = 2
    max_prompt_chars: int = 160
    max_response_chars: int = 192
    batch_size: int = 24
    learning_rate: float = 0.002
    epochs: int = 2
    seed: int = 11


class SparseDialogueMemory(nn.Module):
    """Character generator with a fixed-size sparse source memory.

    The prompt is divided into a constant number of learned content slots. The
    decoder reads only its top-k slots at each output step. Memory does not grow
    with conversation length and no Transformer attention or KV cache is used.
    """

    def __init__(self, cfg: Config, vocab_size: int):
        super().__init__()
        self.cfg = cfg
        self.embedding = nn.Embedding(vocab_size, cfg.embedding_dim, padding_idx=PAD)
        self.encoder = nn.GRU(
            cfg.embedding_dim, cfg.hidden_dim, batch_first=True, bidirectional=True
        )
        self.slot_projection = nn.Linear(cfg.hidden_dim * 2, cfg.hidden_dim)
        self.direction = nn.Embedding(2, cfg.hidden_dim)
        self.decoder = nn.GRU(
            cfg.embedding_dim + cfg.hidden_dim, cfg.hidden_dim, batch_first=True
        )
        self.query = nn.Linear(cfg.hidden_dim, cfg.hidden_dim, bias=False)
        self.fuse = nn.Sequential(
            nn.Linear(cfg.hidden_dim * 2, cfg.hidden_dim),
            nn.Tanh(),
            nn.LayerNorm(cfg.hidden_dim),
        )
        self.output = nn.Linear(cfg.hidden_dim, vocab_size)

    def build_slots(self, source: torch.Tensor, lengths: torch.Tensor):
        packed = pack_padded_sequence(
            self.embedding(source),
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        packed_output, _ = self.encoder(packed)
        encoded, _ = pad_packed_sequence(packed_output, batch_first=True)
        rows = []
        for batch_index, length in enumerate(lengths.tolist()):
            sequence = encoded[batch_index, :length]
            pieces = []
            for slot in range(self.cfg.slots):
                lower = slot * length // self.cfg.slots
                upper = max(lower + 1, (slot + 1) * length // self.cfg.slots)
                pieces.append(sequence[lower : min(upper, length)].mean(0))
            rows.append(torch.stack(pieces))
        return self.slot_projection(torch.stack(rows))

    def retrieve(self, decoded: torch.Tensor, slots: torch.Tensor):
        scores = torch.einsum(
            "bth,bsh->bts", self.query(decoded), slots
        ) / math.sqrt(self.cfg.hidden_dim)
        values, indices = scores.topk(min(self.cfg.topk, self.cfg.slots), dim=-1)
        expanded = slots.unsqueeze(1).expand(-1, decoded.size(1), -1, -1)
        selected = torch.gather(
            expanded,
            2,
            indices.unsqueeze(-1).expand(-1, -1, -1, slots.size(-1)),
        )
        weights = torch.softmax(values, dim=-1).unsqueeze(-1)
        return (selected * weights).sum(2)

    def forward(self, source, lengths, decoder_input, direction):
        slots = self.build_slots(source, lengths)
        context = slots.mean(1) + self.direction(direction)
        embedded = self.embedding(decoder_input)
        repeated = context.unsqueeze(1).expand(-1, embedded.size(1), -1)
        decoded, _ = self.decoder(
            torch.cat([embedded, repeated], dim=-1), context.unsqueeze(0)
        )
        retrieved = self.retrieve(decoded, slots)
        return self.output(self.fuse(torch.cat([decoded, retrieved], dim=-1)))

    @torch.no_grad()
    def generate(self, prompt: str, vocab: CharVocab, *, device="cpu", max_chars=None):
        self.eval()
        ids = vocab.encode(prompt, self.cfg.max_prompt_chars) or [UNK]
        source = torch.tensor([ids], dtype=torch.long, device=device)
        lengths = torch.tensor([len(ids)], device=device)
        slots = self.build_slots(source, lengths)
        direction = torch.zeros(1, dtype=torch.long, device=device)
        context = slots.mean(1) + self.direction(direction)
        hidden = context.unsqueeze(0)
        current = torch.tensor([[BOS]], dtype=torch.long, device=device)
        generated: list[int] = []
        for _ in range(max_chars or self.cfg.max_response_chars):
            embedded = self.embedding(current)
            decoded, hidden = self.decoder(
                torch.cat([embedded, context.unsqueeze(1)], dim=-1), hidden
            )
            retrieved = self.retrieve(decoded, slots)
            logits = self.output(
                self.fuse(torch.cat([decoded, retrieved], dim=-1))
            )[:, -1]
            for token in set(generated[-8:]):
                logits[:, token] -= 1.2 * generated[-8:].count(token)
            token = int(logits.argmax(-1).item())
            if token == EOS:
                break
            if token not in (PAD, BOS):
                generated.append(token)
            current = torch.tensor([[token]], dtype=torch.long, device=device)
        return vocab.decode(generated), generated

    def persistent_bytes(self):
        return sum(parameter.numel() * parameter.element_size() for parameter in self.parameters())


def _pad(sequences):
    lengths = torch.tensor([max(1, len(sequence)) for sequence in sequences])
    output = torch.full((len(sequences), int(lengths.max())), PAD, dtype=torch.long)
    for index, sequence in enumerate(sequences):
        output[index, : len(sequence)] = torch.tensor(sequence or [UNK])
    return output, lengths


def make_batch(pairs, vocab: CharVocab, cfg: Config, reverse=False):
    if reverse:
        sources = [vocab.encode(pair.response, cfg.max_response_chars) for pair in pairs]
        targets = [vocab.encode(pair.prompt, cfg.max_prompt_chars) + [EOS] for pair in pairs]
        direction = 1
    else:
        sources = [vocab.encode(pair.prompt, cfg.max_prompt_chars) for pair in pairs]
        targets = [vocab.encode(pair.response, cfg.max_response_chars) + [EOS] for pair in pairs]
        direction = 0
    source, lengths = _pad(sources)
    decoder_input, _ = _pad([[BOS] + target[:-1] for target in targets])
    target, _ = _pad(targets)
    return source, lengths, decoder_input, target, torch.full((len(pairs),), direction)


def batch_loss(model, batch, device):
    source, lengths, decoder_input, target, direction = (item.to(device) for item in batch)
    logits = model(source, lengths, decoder_input, direction)
    return nn.functional.cross_entropy(
        logits.reshape(-1, logits.size(-1)), target.reshape(-1), ignore_index=PAD
    )


def train_model(train, valid, vocab, cfg: Config, *, cycle: bool, device):
    random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    model = SparseDialogueMemory(cfg, len(vocab)).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.learning_rate, weight_decay=0.01
    )
    order = list(range(len(train)))
    history = []
    started = time.perf_counter()
    for epoch in range(cfg.epochs):
        random.Random(cfg.seed + epoch).shuffle(order)
        model.train()
        total = 0.0
        steps = 0
        for start in range(0, len(order), cfg.batch_size):
            pairs = [train[index] for index in order[start : start + cfg.batch_size]]
            optimizer.zero_grad(set_to_none=True)
            answer = batch_loss(model, make_batch(pairs, vocab, cfg), device)
            loss = answer
            if cycle:
                loss = answer + 0.25 * batch_loss(
                    model, make_batch(pairs, vocab, cfg, reverse=True), device
                )
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += float(loss)
            steps += 1
        history.append({"epoch": epoch + 1, "train_loss": total / max(steps, 1)})
    validation = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(valid), cfg.batch_size):
            validation.append(
                float(
                    batch_loss(
                        model,
                        make_batch(valid[start : start + cfg.batch_size], vocab, cfg),
                        device,
                    )
                )
            )
    return model, {
        "cycle": cycle,
        "history": history,
        "training_seconds": time.perf_counter() - started,
        "valid_nll": sum(validation) / max(len(validation), 1),
        "model_bytes": model.persistent_bytes(),
    }
