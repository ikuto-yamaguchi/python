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
from typing import Iterable

import torch
from torch import nn
import torch.nn.functional as F

torch.set_num_threads(1)

from model_registry import ARCH_CLASSES, build_model
from models_baselines import LanguageModel
from suite import MixedSequenceDataset, TASKS, TOKENS, WEIGHTED_CHANCE, collate


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def serialized_size(model: nn.Module) -> int:
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return buffer.tell()


@dataclass
class Metrics:
    architecture: str
    seed: int
    train_examples: int
    parameters: int
    model_bytes: int
    train_seconds: float
    validation_nll: float
    answer_accuracy: float
    stress_accuracy: float
    per_task_accuracy: dict[str, float]
    context_state_bytes: dict[str, int]
    token_latency_ms: dict[str, float]
    candidate_count: int
    state_reads_128: int
    peak_rss_kib: int


def evaluate(model: LanguageModel, loader: torch.utils.data.DataLoader) -> tuple[float, float, dict[str, float]]:
    model.eval()
    total_loss = total_tokens = correct = count = 0
    task_correct = {task: 0 for task in TASKS}
    task_count = {task: 0 for task in TASKS}
    with torch.no_grad():
        for inputs, targets, answer_mask, task_ids in loader:
            logits, _ = model(inputs)
            total_loss += float(F.cross_entropy(
                logits.reshape(-1, logits.shape[-1]), targets.reshape(-1),
                ignore_index=-100, reduction="sum"
            ))
            total_tokens += int(targets.ne(-100).sum())
            matches = (logits.argmax(-1) == targets) & answer_mask
            correct, count = correct + int(matches.sum()), count + int(answer_mask.sum())
            for index, task in enumerate(TASKS):
                rows = task_ids == index
                task_correct[task] += int(matches[rows].sum())
                task_count[task] += int(answer_mask[rows].sum())
    return correct / max(1, count), total_loss / max(1, total_tokens), {
        task: task_correct[task] / max(1, task_count[task]) for task in TASKS
    }


def benchmark_full_pass(model: LanguageModel, context: int, repeats: int) -> float:
    tokens = torch.tensor([[(index % (len(TOKENS) - 1)) + 1 for index in range(context)]])
    model.eval()
    with torch.no_grad():
        for _ in range(2):
            model(tokens)
        started = time.perf_counter()
        for _ in range(repeats):
            model(tokens)
    return (time.perf_counter() - started) * 1000 / repeats / context


def train_one(name: str, seed: int, train_examples: int, epochs: int = 3) -> Metrics:
    seed_everything(seed)
    model = build_model(name)
    train = MixedSequenceDataset(train_examples, seed * 1009 + train_examples, False, 6)
    valid = MixedSequenceDataset(128, 800_000 + seed, True, 6)
    stress = MixedSequenceDataset(128, 900_000 + seed, True, 18)
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(train, 128, True, generator=generator, collate_fn=collate)
    valid_loader = torch.utils.data.DataLoader(valid, 256, False, collate_fn=collate)
    stress_loader = torch.utils.data.DataLoader(stress, 256, False, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=.01)
    started = time.perf_counter()
    model.train()
    for _ in range(epochs):
        for inputs, targets, answer_mask, _ in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(inputs)
            token_loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100)
            answer_loss = F.cross_entropy(logits[answer_mask], targets[answer_mask])
            (.20 * token_loss + .80 * answer_loss).backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    train_seconds = time.perf_counter() - started
    accuracy, nll, per_task = evaluate(model, valid_loader)
    stress_accuracy, _, _ = evaluate(model, stress_loader)
    state_bytes = {str(length): model.state_bytes(length) for length in (32, 128, 512)}
    latency = {str(length): benchmark_full_pass(model, length, 2 if length == 128 else 3) for length in (32, 128)}
    return Metrics(
        name, seed, train_examples, sum(parameter.numel() for parameter in model.parameters()),
        serialized_size(model), train_seconds, nll, accuracy, stress_accuracy, per_task,
        state_bytes, latency, len(TOKENS), model.state_reads(128),
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )


def aggregate(rows: list[Metrics]) -> dict:
    result: dict[str, dict] = {}
    for architecture in ARCH_CLASSES:
        result[architecture] = {}
        for scale in sorted({row.train_examples for row in rows if row.architecture == architecture}):
            subset = [row for row in rows if row.architecture == architecture and row.train_examples == scale]
            result[architecture][str(scale)] = {
                "parameters_mean": statistics.mean(row.parameters for row in subset),
                "model_bytes_max": max(row.model_bytes for row in subset),
                "answer_accuracy_mean": statistics.mean(row.answer_accuracy for row in subset),
                "answer_accuracy_min": min(row.answer_accuracy for row in subset),
                "stress_accuracy_mean": statistics.mean(row.stress_accuracy for row in subset),
                "validation_nll_mean": statistics.mean(row.validation_nll for row in subset),
                "train_seconds_mean": statistics.mean(row.train_seconds for row in subset),
                "full_pass_ms_per_token_32_mean": statistics.mean(row.token_latency_ms["32"] for row in subset),
                "full_pass_ms_per_token_128_mean": statistics.mean(row.token_latency_ms["128"] for row in subset),
                "state_bytes_128": subset[0].context_state_bytes["128"],
                "per_task_accuracy_mean": {
                    task: statistics.mean(row.per_task_accuracy[task] for row in subset) for task in TASKS
                },
            }
    return result


def run_experiment(output: Path, quick: bool = False) -> dict:
    scales, seeds, epochs = ((128, 512), (1,), 1) if quick else ((256, 1024), (1, 7, 19), 3)
    checkpoint = output.with_suffix(".jsonl")
    rows = [Metrics(**json.loads(line)) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    completed = {(row.architecture, row.seed, row.train_examples) for row in rows}
    for scale in scales:
        for seed in seeds:
            for architecture in ARCH_CLASSES:
                key = architecture, seed, scale
                if key in completed:
                    continue
                print(f"running {architecture} scale={scale} seed={seed}", flush=True)
                metric = train_one(architecture, seed, scale, epochs)
                rows.append(metric)
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                with checkpoint.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(asdict(metric), ensure_ascii=False) + "\n")
                completed.add(key)
    report = {
        "research_map": {
            "families": list(ARCH_CLASSES) + ["test_time_training_separate_track", "native_mobile_runtime_separate_track"],
            "suite": list(TASKS),
        },
        "claim_scope": {
            "this_is": "matched-budget mechanism comparison",
            "this_is_not": ["paper-scale reproduction", "free Japanese dialogue", "smartphone proof", "general intelligence"],
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
            "completion": False,
        },
        "chance_levels": {"overwrite": 1/6, "multi_query": 1/6, "arithmetic": 1/6, "parity": 1/2, "weighted": WEIGHTED_CHANCE},
        "aggregate": aggregate(rows),
        "runs": [asdict(row) for row in rows],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/architecture_map_report.json"))
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    print(json.dumps(run_experiment(args.output, args.quick)["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
