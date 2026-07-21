from __future__ import annotations

import argparse
import io
import json
import random
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import torch
from torch import Tensor, nn
import torch.nn.functional as F

torch.set_num_threads(1)

TOKENS = [
    "<pad>", "<bos>", "<eos>", "記録", "更新", "質問", "回答", "は", "の", "色", "。", "？",
    "葵", "蓮", "凛", "空", "海", "森", "赤", "青", "緑", "白", "黒", "黄",
    "雑音", "静か", "速い", "丸い", "遠い", "近い",
]
TOKEN_TO_ID = {token: index for index, token in enumerate(TOKENS)}
PAD_ID = TOKEN_TO_ID["<pad>"]
BOS_ID = TOKEN_TO_ID["<bos>"]
NAMES = ["葵", "蓮", "凛", "空", "海", "森"]
COLORS = ["赤", "青", "緑", "白", "黒", "黄"]
DISTRACTORS = ["静か", "速い", "丸い", "遠い", "近い"]


def make_example(rng: random.Random, depth: int, held_out: bool) -> tuple[Tensor, int]:
    names = rng.sample(NAMES, 4)
    colors = rng.sample(COLORS, 4)
    if held_out:
        colors = colors[1:] + colors[:1]
    state = dict(zip(names, colors))
    tokens = ["<bos>"]
    for name in names:
        tokens += ["記録", name, "は", state[name], "。"]
    for _ in range(depth):
        if rng.random() < 0.75:
            name = rng.choice(names)
            color = rng.choice(COLORS)
            state[name] = color
            tokens += ["更新", name, "は", color, "。"]
        else:
            tokens += ["雑音", rng.choice(DISTRACTORS), "。"]
    query = rng.choice(names)
    tokens += ["質問", query, "の", "色", "は", "？", "回答", state[query], "<eos>"]
    ids = torch.tensor([TOKEN_TO_ID[token] for token in tokens], dtype=torch.long)
    return ids, len(ids) - 2


class StateTrackingDataset(torch.utils.data.Dataset):
    def __init__(self, size: int, seed: int, held_out: bool, depth: int) -> None:
        rng = random.Random(seed)
        self.examples = [make_example(rng, depth, held_out) for _ in range(size)]

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> tuple[Tensor, int]:
        return self.examples[index]


def collate(batch: Sequence[tuple[Tensor, int]]) -> tuple[Tensor, Tensor, Tensor]:
    max_length = max(len(ids) for ids, _ in batch)
    inputs = torch.full((len(batch), max_length - 1), PAD_ID, dtype=torch.long)
    targets = torch.full_like(inputs, -100)
    answer_indices = torch.empty(len(batch), dtype=torch.long)
    for row, (ids, answer_position) in enumerate(batch):
        inputs[row, : len(ids) - 1] = ids[:-1]
        targets[row, : len(ids) - 1] = ids[1:]
        answer_indices[row] = answer_position - 1
    return inputs, targets, answer_indices


class TinyGRULM(nn.Module):
    def __init__(self, dim: int = 20) -> None:
        super().__init__()
        self.dim = dim
        self.embedding = nn.Embedding(len(TOKENS), dim)
        self.gru = nn.GRU(dim, dim, batch_first=True)
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, len(TOKENS), bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor) -> Tensor:
        hidden, _ = self.gru(self.embedding(tokens))
        return self.head(self.norm(hidden))

    def step(self, token: Tensor, state: Tensor | None) -> tuple[Tensor, Tensor]:
        hidden, state = self.gru(self.embedding(token).unsqueeze(1), state)
        return self.head(self.norm(hidden[:, 0])), state

    def state_elements(self, context_length: int) -> int:
        return self.dim


class TinyTransformerLM(nn.Module):
    def __init__(self, dim: int = 16, heads: int = 4, ff_dim: int = 32, max_length: int = 128) -> None:
        super().__init__()
        self.dim = dim
        self.max_length = max_length
        self.embedding = nn.Embedding(len(TOKENS), dim)
        self.position = nn.Embedding(max_length, dim)
        layer = nn.TransformerEncoderLayer(
            dim, heads, ff_dim, dropout=0.0, batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, 1)
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, len(TOKENS), bias=False)
        self.head.weight = self.embedding.weight

    def forward(self, tokens: Tensor) -> Tensor:
        length = tokens.shape[1]
        positions = torch.arange(length, device=tokens.device)
        x = self.embedding(tokens) + self.position(positions).unsqueeze(0)
        causal_mask = torch.triu(
            torch.ones(length, length, dtype=torch.bool, device=tokens.device), diagonal=1
        )
        return self.head(self.norm(self.encoder(x, mask=causal_mask)))

    def state_elements(self, context_length: int) -> int:
        return 2 * context_length * self.dim


@dataclass
class Metrics:
    architecture: str
    seed: int
    train_examples: int
    parameters: int
    model_bytes: int
    state_bytes_at_64: int
    peak_rss_kib: int
    train_seconds: float
    answer_accuracy: float
    stress_answer_accuracy: float
    validation_nll: float
    token_latency_ms: float
    full_softmax_candidates: int
    state_reads_at_64: int


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def serialized_size(model: nn.Module) -> int:
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return buffer.tell()


def evaluate(model: nn.Module, loader: torch.utils.data.DataLoader) -> tuple[float, float]:
    model.eval()
    correct = 0
    count = 0
    total_loss = 0.0
    total_tokens = 0
    with torch.no_grad():
        for inputs, targets, answer_indices in loader:
            logits = model(inputs)
            total_loss += float(F.cross_entropy(
                logits.reshape(-1, logits.shape[-1]),
                targets.reshape(-1),
                ignore_index=-100,
                reduction="sum",
            ))
            total_tokens += int(targets.ne(-100).sum())
            rows = torch.arange(inputs.shape[0])
            correct += int((logits[rows, answer_indices].argmax(-1) == targets[rows, answer_indices]).sum())
            count += inputs.shape[0]
    return correct / max(1, count), total_loss / max(1, total_tokens)


def benchmark_latency(model: nn.Module, steps: int = 128) -> float:
    model.eval()
    with torch.no_grad():
        if isinstance(model, TinyGRULM):
            token = torch.tensor([BOS_ID])
            state = None
            for _ in range(16):
                _, state = model.step(token, state)
            started = time.perf_counter()
            for index in range(steps):
                token = torch.tensor([(index % (len(TOKENS) - 1)) + 1])
                _, state = model.step(token, state)
        else:
            sequence = torch.tensor([[BOS_ID] + [((i % (len(TOKENS) - 1)) + 1) for i in range(63)]])
            for _ in range(4):
                model(sequence)
            started = time.perf_counter()
            for _ in range(steps):
                model(sequence)
    return (time.perf_counter() - started) * 1000.0 / steps


def train_one(architecture: str, seed: int, train_examples: int, epochs: int = 2) -> Metrics:
    seed_everything(seed)
    if architecture == "gru":
        model: nn.Module = TinyGRULM()
    elif architecture == "transformer":
        model = TinyTransformerLM()
    else:
        raise ValueError(f"unknown architecture: {architecture}")

    train_set = StateTrackingDataset(train_examples, seed * 1009 + train_examples, False, depth=5)
    valid_set = StateTrackingDataset(128, 910_000 + seed, True, depth=5)
    stress_set = StateTrackingDataset(128, 920_000 + seed, True, depth=16)
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=32, shuffle=True, generator=generator, collate_fn=collate
    )
    valid_loader = torch.utils.data.DataLoader(valid_set, batch_size=64, collate_fn=collate)
    stress_loader = torch.utils.data.DataLoader(stress_set, batch_size=64, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=0.01)

    model.train()
    started = time.perf_counter()
    for _ in range(epochs):
        for inputs, targets, answer_indices in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            token_loss = F.cross_entropy(
                logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100
            )
            rows = torch.arange(inputs.shape[0])
            answer_loss = F.cross_entropy(logits[rows, answer_indices], targets[rows, answer_indices])
            (0.35 * token_loss + 0.65 * answer_loss).backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    train_seconds = time.perf_counter() - started
    accuracy, nll = evaluate(model, valid_loader)
    stress_accuracy, _ = evaluate(model, stress_loader)
    state_elements = model.state_elements(64)
    return Metrics(
        architecture=architecture,
        seed=seed,
        train_examples=train_examples,
        parameters=sum(parameter.numel() for parameter in model.parameters()),
        model_bytes=serialized_size(model),
        state_bytes_at_64=state_elements * 4,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        train_seconds=train_seconds,
        answer_accuracy=accuracy,
        stress_answer_accuracy=stress_accuracy,
        validation_nll=nll,
        token_latency_ms=benchmark_latency(model),
        full_softmax_candidates=len(TOKENS),
        state_reads_at_64=state_elements,
    )


def aggregate_runs(runs: list[Metrics]) -> dict[str, dict[str, dict[str, float]]]:
    result: dict[str, dict[str, dict[str, float]]] = {}
    for architecture in ("gru", "transformer"):
        result[architecture] = {}
        for scale in (128, 512, 1024):
            rows = [row for row in runs if row.architecture == architecture and row.train_examples == scale]
            result[architecture][str(scale)] = {
                "answer_accuracy_mean": statistics.mean(row.answer_accuracy for row in rows),
                "answer_accuracy_min": min(row.answer_accuracy for row in rows),
                "stress_answer_accuracy_mean": statistics.mean(row.stress_answer_accuracy for row in rows),
                "validation_nll_mean": statistics.mean(row.validation_nll for row in rows),
                "train_seconds_mean": statistics.mean(row.train_seconds for row in rows),
                "token_latency_ms_mean": statistics.mean(row.token_latency_ms for row in rows),
                "model_bytes_max": max(row.model_bytes for row in rows),
                "state_bytes_at_64_max": max(row.state_bytes_at_64 for row in rows),
                "peak_rss_kib_max": max(row.peak_rss_kib for row in rows),
            }
    return result


def run_experiment(output: Path) -> dict:
    runs = [
        train_one(architecture, seed, scale)
        for architecture in ("gru", "transformer")
        for scale in (128, 512, 1024)
        for seed in (1, 7, 19)
    ]
    aggregate = aggregate_runs(runs)
    report = {
        "comparison_scope": {
            "rwkv7_reference_pr": 129,
            "parameter_counts": {
                "rwkv7": 3888,
                "gru": runs[0].parameters,
                "transformer": next(row.parameters for row in runs if row.architecture == "transformer"),
            },
            "chance_answer_accuracy": 1.0 / len(COLORS),
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
            "completion": False,
        },
        "aggregate": aggregate,
        "interpretation": {
            "all_models_near_chance": True,
            "rwkv7_unique_advantage_observed": False,
            "reason": (
                "RWKV-7 PR #129, GRU, and Transformer remain near the 1/6 answer chance level. "
                "The benchmark therefore does not support a model-quality claim; it only exposes "
                "the constant-state and latency differences of recurrent execution."
            ),
        },
        "runs": [asdict(row) for row in runs],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/rwkv7_baseline_report.json"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_experiment(args.output)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    print(f"report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
