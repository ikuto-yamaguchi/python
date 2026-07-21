from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Iterable

import torch
from torch import nn
import torch.nn.functional as F

from architecture_map import evaluate, seed_everything
from model_registry import build_model
from suite import MixedSequenceDataset, WEIGHTED_CHANCE, collate


def train_control(architecture: str, seed: int, train_examples: int, epochs: int, target_parameters: int) -> dict:
    seed_everything(seed)
    model = build_model(architecture, target_parameters)
    train_set = MixedSequenceDataset(train_examples, seed * 1009 + train_examples, held_out=False, depth=6)
    valid_set = MixedSequenceDataset(256, 800_000 + seed, held_out=True, depth=6)
    stress_set = MixedSequenceDataset(256, 900_000 + seed, held_out=True, depth=18)
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(
        train_set, batch_size=128, shuffle=True, generator=generator, collate_fn=collate
    )
    valid_loader = torch.utils.data.DataLoader(valid_set, batch_size=256, shuffle=False, collate_fn=collate)
    stress_loader = torch.utils.data.DataLoader(stress_set, batch_size=256, shuffle=False, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.01)

    started = time.perf_counter()
    model.train()
    for _ in range(epochs):
        for inputs, targets, answer_mask, _ in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(inputs)
            token_loss = F.cross_entropy(
                logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100
            )
            answer_loss = F.cross_entropy(logits[answer_mask], targets[answer_mask])
            loss = 0.20 * token_loss + 0.80 * answer_loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

    answer_accuracy, validation_nll, per_task = evaluate(model, valid_loader)
    stress_accuracy, _, _ = evaluate(model, stress_loader)
    return {
        "architecture": architecture,
        "seed": seed,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "answer_accuracy": answer_accuracy,
        "stress_accuracy": stress_accuracy,
        "validation_nll": validation_nll,
        "per_task_accuracy": per_task,
        "train_seconds": time.perf_counter() - started,
    }


def aggregate(rows: list[dict]) -> dict:
    result: dict[str, dict] = {}
    for architecture in ("gru", "transformer"):
        subset = [row for row in rows if row["architecture"] == architecture]
        result[architecture] = {
            "parameters": subset[0]["parameters"],
            "answer_accuracy_mean": statistics.mean(row["answer_accuracy"] for row in subset),
            "answer_accuracy_pstdev": statistics.pstdev(row["answer_accuracy"] for row in subset),
            "stress_accuracy_mean": statistics.mean(row["stress_accuracy"] for row in subset),
            "stress_accuracy_pstdev": statistics.pstdev(row["stress_accuracy"] for row in subset),
            "validation_nll_mean": statistics.mean(row["validation_nll"] for row in subset),
            "train_seconds_mean": statistics.mean(row["train_seconds"] for row in subset),
            "per_task_accuracy_mean": {
                task: statistics.mean(row["per_task_accuracy"][task] for row in subset)
                for task in subset[0]["per_task_accuracy"]
            },
        }
    return result


def run(output: Path, quick: bool = False) -> dict:
    seeds = (1,) if quick else (1, 7, 19)
    train_examples = 256 if quick else 2048
    epochs = 2 if quick else 30
    target_parameters = 10_000 if quick else 20_000
    rows = [
        train_control(architecture, seed, train_examples, epochs, target_parameters)
        for architecture in ("gru", "transformer")
        for seed in seeds
    ]
    report = {
        "configuration": {
            "train_examples": train_examples,
            "epochs": epochs,
            "seeds": list(seeds),
            "target_parameters": target_parameters,
            "weighted_answer_chance": WEIGHTED_CHANCE,
        },
        "aggregate": aggregate(rows),
        "interpretation": {
            "purpose": "Verify that the mixed suite is learnable before ranking newer mechanisms.",
            "novelty_warning": (
                "A classical GRU remains a mandatory baseline; omitting it would create novelty bias."
            ),
        },
        "runs": rows,
        "highschool_level_passed": False,
        "native_japanese_communication_passed": False,
        "completion": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/capacity_control_report.json"))
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run(args.output, quick=args.quick)
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
