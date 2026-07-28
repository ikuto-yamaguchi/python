#!/usr/bin/env python3
"""Matched offline comparison harness for the R0.2 typed SILG baseline.

This is not a new mechanism family. It evaluates the already implemented
Gaddy--Klein-style environment-first path against a topology-matched end-to-end
baseline and a state-only control on the same immutable typed trajectory file.

Online SILG task success is reported only when the input rows contain an
independently produced ``task_success`` field. The harness never substitutes
next-state reconstruction, action accuracy, representation quality or
compression for task success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import nn
from torch.utils.data import DataLoader

from gaddy_klein_typed_baseline import (
    CANONICAL_SEEDS,
    Config,
    LanguageMessageEncoder,
    TransitionMessageEncoder,
    TypedDecoder,
    TypedRows,
    collate,
    load_rows,
    parameter_bytes,
    seed_all,
    symmetric_message_kl,
    train_environment,
    typed_transition_loss,
    validate_rows,
)

METHOD_REFERENCE_COMMIT = "ac1e7cb62ae94c76f545bf942f0c8febce43891f"
CONDITIONS = ("all", "entity_holdout", "dynamics_holdout", "language_holdout")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_seed(row: dict[str, Any]) -> int | None:
    value = row.get("seed", row.get("episode_seed"))
    return None if value is None else int(value)


def validate_seed(rows: list[dict[str, Any]], seed: int) -> None:
    observed = {value for row in rows if (value := row_seed(row)) is not None}
    if observed and observed != {seed}:
        raise ValueError(f"dataset seed mismatch: requested={seed}, observed={sorted(observed)}")


class EndToEndModel(nn.Module):
    """Same inference topology as the environment-first language path."""

    def __init__(self, specs, config: Config):
        super().__init__()
        self.language = LanguageMessageEncoder(config)
        self.decoder = TypedDecoder(specs, config)

    def forward(self, before, text, hard: bool):
        logits, message = self.language(text, hard=hard)
        state, action = self.decoder(before, message)
        return logits, state, action


class StateOnlyModel(nn.Module):
    """Typed decoder with a learned instruction-independent message."""

    def __init__(self, specs, config: Config):
        super().__init__()
        self.variables = config.message_variables
        self.symbols = config.message_symbols
        self.message_logits = nn.Parameter(torch.zeros(self.variables, self.symbols))
        self.decoder = TypedDecoder(specs, config)

    def forward(self, before):
        message = torch.softmax(self.message_logits, dim=-1)
        message = message.unsqueeze(0).expand(next(iter(before.values())).shape[0], -1, -1)
        return self.decoder(before, message)


def make_loader(rows, specs, config: Config, *, shuffle: bool) -> DataLoader:
    return DataLoader(
        TypedRows(rows, specs, config.max_text_len),
        batch_size=config.batch_size,
        shuffle=shuffle,
        collate_fn=collate,
    )


def train_environment_first_language(
    transition: TransitionMessageEncoder,
    language: LanguageMessageEncoder,
    decoder: TypedDecoder,
    loader: DataLoader,
    specs,
    config: Config,
) -> float:
    transition.eval()
    for parameter in transition.parameters():
        parameter.requires_grad = False
    decoder.eval()
    for parameter in decoder.parameters():
        parameter.requires_grad = False
    optimizer = torch.optim.Adam(language.parameters(), lr=config.learning_rate)
    started = time.perf_counter()
    for _ in range(config.lang_epochs):
        language.train()
        for batch in loader:
            with torch.no_grad():
                env_logits, _ = transition(batch["before"], batch["after"], hard=False)
            lang_logits, lang_message = language(batch["text"], hard=True)
            state_predictions, action_logits = decoder(batch["before"], lang_message)
            state_loss, _ = typed_transition_loss(state_predictions, batch["after"], specs)
            action_loss = nn.functional.cross_entropy(action_logits, batch["action"])
            match_loss = symmetric_message_kl(lang_logits, env_logits)
            loss = state_loss + action_loss + config.match_weight * match_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def train_end_to_end(model: EndToEndModel, loader: DataLoader, specs, config: Config) -> float:
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    started = time.perf_counter()
    model.train()
    for _ in range(config.env_epochs + config.lang_epochs):
        for batch in loader:
            _, state_predictions, action_logits = model(batch["before"], batch["text"], hard=True)
            state_loss, _ = typed_transition_loss(state_predictions, batch["after"], specs)
            action_loss = nn.functional.cross_entropy(action_logits, batch["action"])
            loss = state_loss + action_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def train_state_only(model: StateOnlyModel, loader: DataLoader, specs, config: Config) -> float:
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    started = time.perf_counter()
    model.train()
    for _ in range(config.env_epochs + config.lang_epochs):
        for batch in loader:
            state_predictions, action_logits = model(batch["before"])
            state_loss, _ = typed_transition_loss(state_predictions, batch["after"], specs)
            action_loss = nn.functional.cross_entropy(action_logits, batch["action"])
            loss = state_loss + action_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def batch_mask(batch: dict[str, Any], condition: str) -> torch.Tensor:
    if condition == "all":
        return torch.ones(batch["action"].shape[0], dtype=torch.bool)
    return batch[condition].bool()


def task_success_values(rows: list[dict[str, Any]], condition: str) -> list[float]:
    selected = []
    for row in rows:
        if condition != "all" and not bool(row.get(condition, False)):
            continue
        if "task_success" in row:
            selected.append(float(bool(row["task_success"])))
    return selected


def evaluate(
    method: str,
    loader: DataLoader,
    rows: list[dict[str, Any]],
    specs,
    forward,
) -> dict[str, Any]:
    totals = {
        condition: {"n": 0, "correct": 0, "transition_loss_sum": 0.0, "batches": 0}
        for condition in CONDITIONS
    }
    latencies: list[float] = []
    with torch.inference_mode():
        for batch in loader:
            started = time.perf_counter_ns()
            state_predictions, action_logits = forward(batch)
            elapsed = time.perf_counter_ns() - started
            latencies.append(elapsed / 1e6 / max(1, batch["action"].shape[0]))
            predicted = action_logits.argmax(dim=-1)
            per_row_transition = torch.zeros(batch["action"].shape[0], dtype=torch.float32)
            for spec in specs:
                pred = state_predictions[spec.name]
                gold = batch["after"][spec.name]
                if spec.kind == "categorical":
                    loss = nn.functional.cross_entropy(
                        pred.flatten(0, 1), gold.long().flatten(), reduction="none"
                    ).reshape(batch["action"].shape[0], -1).mean(1)
                elif spec.kind == "binary":
                    loss = nn.functional.binary_cross_entropy_with_logits(
                        pred, gold.float(), reduction="none"
                    ).reshape(batch["action"].shape[0], -1).mean(1)
                else:
                    loss = nn.functional.mse_loss(
                        pred, gold.float(), reduction="none"
                    ).reshape(batch["action"].shape[0], -1).mean(1)
                per_row_transition += loss
            per_row_transition /= max(1, len(specs))
            for condition in CONDITIONS:
                mask = batch_mask(batch, condition)
                n = int(mask.sum())
                if not n:
                    continue
                totals[condition]["n"] += n
                totals[condition]["correct"] += int((predicted[mask] == batch["action"][mask]).sum())
                totals[condition]["transition_loss_sum"] += float(per_row_transition[mask].sum())
                totals[condition]["batches"] += 1
    metrics: dict[str, Any] = {}
    for condition, values in totals.items():
        n = values["n"]
        successes = task_success_values(rows, condition)
        metrics[condition] = {
            "n": n,
            "action_accuracy": None if not n else values["correct"] / n,
            "typed_next_state_loss": None if not n else values["transition_loss_sum"] / n,
            "task_success": None if not successes else statistics.fmean(successes),
            "task_success_status": "available_from_external_online_rollout" if successes else "not_available_offline",
        }
    return {
        "method": method,
        "conditions": metrics,
        "cpu_inference_ms_per_instance_mean": statistics.fmean(latencies) if latencies else None,
        "cpu_inference_ms_per_instance_median": statistics.median(latencies) if latencies else None,
    }


def save_checkpoint(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    torch.save(payload, path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=CANONICAL_SEEDS)
    parser.add_argument("--env-epochs", type=int, default=8)
    parser.add_argument("--lang-epochs", type=int, default=8)
    args = parser.parse_args()

    seed_all(args.seed)
    rows = load_rows(args.data)
    specs = validate_rows(rows)
    validate_seed(rows, args.seed)
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]
    if not train or not test:
        raise ValueError("both train and test rows are required")
    config = Config(
        vocab_size=max(max(row["text_tokens"], default=0) for row in rows) + 1,
        num_actions=max(int(row["action"]) for row in rows) + 1,
        env_epochs=args.env_epochs,
        lang_epochs=args.lang_epochs,
    )
    train_loader = make_loader(train, specs, config, shuffle=True)
    test_loader = make_loader(test, specs, config, shuffle=False)

    # Environment-first path.
    transition = TransitionMessageEncoder(specs, config)
    env_decoder = TypedDecoder(specs, config)
    env_language = LanguageMessageEncoder(config)
    env_pretrain_seconds = train_environment(transition, env_decoder, train_loader, specs, config)
    env_language_seconds = train_environment_first_language(
        transition, env_language, env_decoder, train_loader, specs, config
    )

    # End-to-end path with exactly the same inference topology and budget.
    end_to_end = EndToEndModel(specs, config)
    e2e_seconds = train_end_to_end(end_to_end, train_loader, specs, config)

    # State-only diagnostic control.
    state_only = StateOnlyModel(specs, config)
    state_seconds = train_state_only(state_only, train_loader, specs, config)

    env_inference_bytes = parameter_bytes(env_language, env_decoder)
    e2e_inference_bytes = parameter_bytes(end_to_end)
    if env_inference_bytes != e2e_inference_bytes:
        raise RuntimeError(
            f"inference parameter mismatch: environment_first={env_inference_bytes}, end_to_end={e2e_inference_bytes}"
        )

    env_language.eval()
    env_decoder.eval()
    end_to_end.eval()
    state_only.eval()
    evaluations = [
        evaluate(
            "environment_first",
            test_loader,
            test,
            specs,
            lambda batch: env_decoder(batch["before"], env_language(batch["text"], hard=True)[1]),
        ),
        evaluate(
            "end_to_end",
            test_loader,
            test,
            specs,
            lambda batch: end_to_end(batch["before"], batch["text"], hard=True)[1:],
        ),
        evaluate(
            "state_only",
            test_loader,
            test,
            specs,
            lambda batch: state_only(batch["before"]),
        ),
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    stem = args.out.with_suffix("")
    checkpoints = {
        "environment_first": save_checkpoint(
            Path(f"{stem}.environment_first.pt"),
            {
                "transition": transition.state_dict(),
                "language": env_language.state_dict(),
                "decoder": env_decoder.state_dict(),
                "config": asdict(config),
            },
        ),
        "end_to_end": save_checkpoint(
            Path(f"{stem}.end_to_end.pt"),
            {"model": end_to_end.state_dict(), "config": asdict(config)},
        ),
        "state_only": save_checkpoint(
            Path(f"{stem}.state_only.pt"),
            {"model": state_only.state_dict(), "config": asdict(config)},
        ),
    }
    result = {
        "status": "offline_matched_comparison_complete_online_task_success_requires_external_rollout",
        "method_reference_commit": METHOD_REFERENCE_COMMIT,
        "seed": args.seed,
        "config": asdict(config),
        "dataset": {
            "path": str(args.data),
            "sha256": sha256(args.data),
            "n_train": len(train),
            "n_test": len(test),
            "splits": sorted({str(row["split"]) for row in rows}),
        },
        "field_schema": [asdict(spec) for spec in specs],
        "parameter_budget": {
            "environment_first_inference_bytes": env_inference_bytes,
            "end_to_end_inference_bytes": e2e_inference_bytes,
            "equal": True,
            "environment_pretraining_only_bytes": parameter_bytes(transition),
            "state_only_inference_bytes": parameter_bytes(state_only),
        },
        "training": {
            "environment_pretraining_seconds": env_pretrain_seconds,
            "environment_first_language_seconds": env_language_seconds,
            "end_to_end_seconds": e2e_seconds,
            "state_only_seconds": state_seconds,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "evaluations": evaluations,
        "checkpoints": checkpoints,
        "limitations": [
            "task success is unavailable unless independently generated online rollout labels are present",
            "held-out metrics are reported only for non-empty externally defined entity/dynamics/language-form subsets",
            "no representation appearance or compression metric is counted as progress",
            "this result is not public-baseline reproduction until qualified SILG trajectories and online evaluation exist",
        ],
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
