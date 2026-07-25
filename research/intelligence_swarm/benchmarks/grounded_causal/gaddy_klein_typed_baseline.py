#!/usr/bin/env python3
"""Faithful-method R0.2 baseline for typed SILG trajectories.

This module ports the method contract of Gaddy & Klein (2019) without adding a
new architecture family:

1. learn a structured discrete message from language-free state transitions;
2. decode the next typed state and low-level action from current state+message;
3. freeze the pretrained decoder by default;
4. train an LSTM instruction encoder to match the environment message and use
   the same decoder;
5. compare against a topology-matched end-to-end model and state-only control.

The module intentionally rejects the legacy flat ``state_before`` /
``state_after`` SILG export. A typed field schema is required so categorical,
binary and continuous state fields receive valid losses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

CANONICAL_SEEDS = (1, 7, 19)
METHOD_REFERENCE_COMMIT = "ac1e7cb62ae94c76f545bf942f0c8febce43891f"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str  # categorical | binary | continuous
    shape: tuple[int, ...]
    cardinality: int | None = None

    @property
    def width(self) -> int:
        return math.prod(self.shape)


@dataclass
class Config:
    vocab_size: int
    num_actions: int
    message_variables: int = 20
    message_symbols: int = 30
    hidden_dim: int = 128
    text_dim: int = 96
    batch_size: int = 128
    env_epochs: int = 8
    lang_epochs: int = 8
    learning_rate: float = 2e-3
    match_weight: float = 0.01
    temperature: float = 1.0
    freeze_decoder: bool = True
    max_text_len: int = 160


class TypedRows(Dataset):
    def __init__(self, rows: list[dict[str, Any]], specs: list[FieldSpec], max_text_len: int):
        self.rows = rows
        self.specs = specs
        self.max_text_len = max_text_len

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        tokens = [int(x) for x in row["text_tokens"][: self.max_text_len]]
        tokens += [0] * (self.max_text_len - len(tokens))
        before: dict[str, torch.Tensor] = {}
        after: dict[str, torch.Tensor] = {}
        for spec in self.specs:
            dtype = torch.float32 if spec.kind == "continuous" else torch.long
            before[spec.name] = torch.tensor(row["state_before_fields"][spec.name], dtype=dtype).reshape(-1)
            after[spec.name] = torch.tensor(row["state_after_fields"][spec.name], dtype=dtype).reshape(-1)
        return {
            "before": before,
            "after": after,
            "action": torch.tensor(int(row["action"]), dtype=torch.long),
            "text": torch.tensor(tokens, dtype=torch.long),
            "instance_id": row["instance_id"],
            "episode_id": row["episode_id"],
            "entity_holdout": torch.tensor(bool(row.get("entity_holdout", False))),
            "dynamics_holdout": torch.tensor(bool(row.get("dynamics_holdout", False))),
            "language_holdout": torch.tensor(bool(row.get("language_holdout", False))),
        }


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    keys = batch[0]["before"].keys()
    return {
        "before": {key: torch.stack([row["before"][key] for row in batch]) for key in keys},
        "after": {key: torch.stack([row["after"][key] for row in batch]) for key in keys},
        "action": torch.stack([row["action"] for row in batch]),
        "text": torch.stack([row["text"] for row in batch]),
        "instance_id": [row["instance_id"] for row in batch],
        "episode_id": [row["episode_id"] for row in batch],
        "entity_holdout": torch.stack([row["entity_holdout"] for row in batch]),
        "dynamics_holdout": torch.stack([row["dynamics_holdout"] for row in batch]),
        "language_holdout": torch.stack([row["language_holdout"] for row in batch]),
    }


class TypedStateEncoder(nn.Module):
    def __init__(self, specs: list[FieldSpec], hidden_dim: int):
        super().__init__()
        self.specs = specs
        self.embeddings = nn.ModuleDict()
        input_width = 0
        for spec in specs:
            if spec.kind == "categorical":
                if not spec.cardinality or spec.cardinality < 2:
                    raise ValueError(f"categorical field {spec.name} needs cardinality>=2")
                dim = min(32, max(4, int(math.ceil(math.log2(spec.cardinality + 1))) * 2))
                self.embeddings[spec.name] = nn.Embedding(spec.cardinality, dim)
                input_width += spec.width * dim
            else:
                input_width += spec.width
        self.net = nn.Sequential(nn.Linear(input_width, hidden_dim), nn.Tanh())

    def forward(self, fields: dict[str, torch.Tensor]) -> torch.Tensor:
        parts: list[torch.Tensor] = []
        for spec in self.specs:
            value = fields[spec.name]
            if spec.kind == "categorical":
                parts.append(self.embeddings[spec.name](value.long()).flatten(1))
            else:
                parts.append(value.float().flatten(1))
        return self.net(torch.cat(parts, dim=-1))


class StructuredMessage(nn.Module):
    def __init__(self, input_dim: int, config: Config):
        super().__init__()
        self.variables = config.message_variables
        self.symbols = config.message_symbols
        self.temperature = config.temperature
        self.projection = nn.Linear(input_dim, self.variables * self.symbols)

    def logits(self, representation: torch.Tensor) -> torch.Tensor:
        return self.projection(representation).reshape(-1, self.variables, self.symbols)

    def sample(self, logits: torch.Tensor, hard: bool) -> torch.Tensor:
        return nn.functional.gumbel_softmax(logits, tau=self.temperature, hard=hard, dim=-1)


class TransitionMessageEncoder(nn.Module):
    def __init__(self, specs: list[FieldSpec], config: Config):
        super().__init__()
        self.before = TypedStateEncoder(specs, config.hidden_dim)
        self.after = TypedStateEncoder(specs, config.hidden_dim)
        self.message = StructuredMessage(config.hidden_dim * 2, config)

    def forward(self, before: dict[str, torch.Tensor], after: dict[str, torch.Tensor], hard: bool):
        rep = torch.cat([self.before(before), self.after(after)], dim=-1)
        logits = self.message.logits(rep)
        return logits, self.message.sample(logits, hard=hard)


class LanguageMessageEncoder(nn.Module):
    def __init__(self, config: Config):
        super().__init__()
        self.embedding = nn.Embedding(config.vocab_size, config.text_dim, padding_idx=0)
        self.lstm = nn.LSTM(config.text_dim, config.hidden_dim, batch_first=True)
        self.message = StructuredMessage(config.hidden_dim, config)

    def forward(self, tokens: torch.Tensor, hard: bool):
        embedded = self.embedding(tokens)
        _, (hidden, _) = self.lstm(embedded)
        logits = self.message.logits(hidden[-1])
        return logits, self.message.sample(logits, hard=hard)


class TypedDecoder(nn.Module):
    def __init__(self, specs: list[FieldSpec], config: Config):
        super().__init__()
        self.specs = specs
        self.state = TypedStateEncoder(specs, config.hidden_dim)
        message_width = config.message_variables * config.message_symbols
        joint = config.hidden_dim + message_width
        self.trunk = nn.Sequential(nn.Linear(joint, config.hidden_dim), nn.ReLU())
        self.field_heads = nn.ModuleDict()
        for spec in specs:
            width = spec.width * spec.cardinality if spec.kind == "categorical" else spec.width
            self.field_heads[spec.name] = nn.Linear(config.hidden_dim, int(width))
        self.action_head = nn.Linear(config.hidden_dim, config.num_actions)

    def forward(self, before: dict[str, torch.Tensor], message: torch.Tensor):
        hidden = self.trunk(torch.cat([self.state(before), message.flatten(1)], dim=-1))
        fields: dict[str, torch.Tensor] = {}
        for spec in self.specs:
            raw = self.field_heads[spec.name](hidden)
            if spec.kind == "categorical":
                fields[spec.name] = raw.reshape(-1, spec.width, int(spec.cardinality))
            else:
                fields[spec.name] = raw.reshape(-1, spec.width)
        return fields, self.action_head(hidden)


def typed_transition_loss(
    predictions: dict[str, torch.Tensor],
    target: dict[str, torch.Tensor],
    specs: list[FieldSpec],
) -> tuple[torch.Tensor, dict[str, float]]:
    losses: list[torch.Tensor] = []
    metrics: dict[str, float] = {}
    for spec in specs:
        pred = predictions[spec.name]
        gold = target[spec.name]
        if spec.kind == "categorical":
            loss = nn.functional.cross_entropy(pred.flatten(0, 1), gold.long().flatten())
        elif spec.kind == "binary":
            loss = nn.functional.binary_cross_entropy_with_logits(pred, gold.float())
        elif spec.kind == "continuous":
            loss = nn.functional.mse_loss(pred, gold.float())
        else:
            raise ValueError(f"unsupported field kind: {spec.kind}")
        losses.append(loss)
        metrics[f"loss_{spec.name}"] = float(loss.detach())
    return torch.stack(losses).mean(), metrics


def symmetric_message_kl(language_logits: torch.Tensor, environment_logits: torch.Tensor) -> torch.Tensor:
    p_log = nn.functional.log_softmax(language_logits, dim=-1)
    q_log = nn.functional.log_softmax(environment_logits.detach(), dim=-1)
    p = p_log.exp()
    q = q_log.exp()
    return 0.5 * (
        nn.functional.kl_div(p_log, q, reduction="batchmean")
        + nn.functional.kl_div(q_log, p, reduction="batchmean")
    )


def train_environment(
    transition: TransitionMessageEncoder,
    decoder: TypedDecoder,
    loader: DataLoader,
    specs: list[FieldSpec],
    config: Config,
) -> float:
    optimizer = torch.optim.Adam(list(transition.parameters()) + list(decoder.parameters()), lr=config.learning_rate)
    started = time.perf_counter()
    for _ in range(config.env_epochs):
        for batch in loader:
            _, message = transition(batch["before"], batch["after"], hard=True)
            state_predictions, action_logits = decoder(batch["before"], message)
            state_loss, _ = typed_transition_loss(state_predictions, batch["after"], specs)
            loss = state_loss + nn.functional.cross_entropy(action_logits, batch["action"])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def train_language(
    transition: TransitionMessageEncoder,
    language: LanguageMessageEncoder,
    decoder: TypedDecoder,
    loader: DataLoader,
    specs: list[FieldSpec],
    config: Config,
) -> float:
    transition.eval()
    for parameter in transition.parameters():
        parameter.requires_grad = False
    if config.freeze_decoder:
        decoder.eval()
        for parameter in decoder.parameters():
            parameter.requires_grad = False
    parameters = [parameter for parameter in list(language.parameters()) + list(decoder.parameters()) if parameter.requires_grad]
    optimizer = torch.optim.Adam(parameters, lr=config.learning_rate)
    started = time.perf_counter()
    for _ in range(config.lang_epochs):
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


def validate_rows(rows: list[dict[str, Any]]) -> list[FieldSpec]:
    if not rows:
        raise ValueError("empty dataset")
    if "state_before_fields" not in rows[0] or "state_after_fields" not in rows[0]:
        raise ValueError(
            "typed SILG export required: legacy flat state_before/state_after is rejected; "
            "export state_before_fields, state_after_fields and state_schema"
        )
    raw_schema = rows[0].get("state_schema")
    if not isinstance(raw_schema, list) or not raw_schema:
        raise ValueError("state_schema must be a non-empty list")
    specs = [
        FieldSpec(
            name=str(item["name"]),
            kind=str(item["kind"]),
            shape=tuple(int(x) for x in item["shape"]),
            cardinality=int(item["cardinality"]) if item.get("cardinality") is not None else None,
        )
        for item in raw_schema
    ]
    schema_signature = json.dumps(raw_schema, sort_keys=True, separators=(",", ":"))
    for row in rows:
        if json.dumps(row.get("state_schema"), sort_keys=True, separators=(",", ":")) != schema_signature:
            raise ValueError("state_schema changed across rows")
        for spec in specs:
            for key in ("state_before_fields", "state_after_fields"):
                if spec.name not in row[key]:
                    raise ValueError(f"missing {key}.{spec.name}")
                if len(row[key][spec.name]) != spec.width:
                    raise ValueError(f"invalid width for {key}.{spec.name}")
    train_episodes = {row["episode_id"] for row in rows if row["split"] == "train"}
    test_episodes = {row["episode_id"] for row in rows if row["split"] == "test"}
    if train_episodes & test_episodes:
        raise ValueError("train/test episode overlap")
    return specs


def parameter_bytes(*modules: nn.Module) -> int:
    return sum(p.numel() * p.element_size() for module in modules for p in module.parameters())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


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
    train_loader = DataLoader(TypedRows(train, specs, config.max_text_len), batch_size=config.batch_size, shuffle=True, collate_fn=collate)

    transition = TransitionMessageEncoder(specs, config)
    decoder = TypedDecoder(specs, config)
    language = LanguageMessageEncoder(config)
    env_seconds = train_environment(transition, decoder, train_loader, specs, config)
    lang_seconds = train_language(transition, language, decoder, train_loader, specs, config)

    result = {
        "status": "trained_typed_discrete_message_offline_baseline_online_evaluation_pending",
        "method_reference_commit": METHOD_REFERENCE_COMMIT,
        "seed": args.seed,
        "config": asdict(config),
        "dataset": {"path": str(args.data), "sha256": sha256(args.data), "n_train": len(train), "n_test": len(test)},
        "field_schema": [asdict(spec) for spec in specs],
        "resources": {
            "environment_training_seconds": env_seconds,
            "language_training_seconds": lang_seconds,
            "training_parameter_bytes": parameter_bytes(transition, decoder, language),
            "inference_parameter_bytes": parameter_bytes(decoder, language),
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "limitations": [
            "online task success is not measured by this offline entry point",
            "end-to-end parameter matching and held-out transfer evaluation must be run by the comparison harness",
            "result is not a completed public baseline reproduction",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
