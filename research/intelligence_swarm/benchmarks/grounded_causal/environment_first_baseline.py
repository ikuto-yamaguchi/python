from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


@dataclass
class Config:
    state_dim: int
    num_actions: int
    vocab_size: int
    hidden_dim: int = 96
    action_dim: int = 48
    text_dim: int = 64
    batch_size: int = 128
    env_epochs: int = 8
    lang_epochs: int = 8
    lr: float = 2e-3
    freeze_decoder: bool = True
    max_text_len: int = 128


class Rows(Dataset):
    def __init__(self, rows: list[dict[str, Any]], max_len: int):
        self.rows = rows
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.rows[index]
        ids = [int(v) for v in row.get("text_tokens", [])[: self.max_len]]
        ids += [0] * (self.max_len - len(ids))
        return {
            "before": torch.tensor(row["state_before"], dtype=torch.float32),
            "after": torch.tensor(row["state_after"], dtype=torch.float32),
            "action": torch.tensor(row["action"], dtype=torch.long),
            "text": torch.tensor(ids, dtype=torch.long),
            "entity_holdout": torch.tensor(bool(row.get("entity_holdout", False))),
            "dynamics_holdout": torch.tensor(bool(row.get("dynamics_holdout", False))),
            "language_holdout": torch.tensor(bool(row.get("language_holdout", False))),
        }


class TransitionEncoder(nn.Module):
    def __init__(self, config: Config):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.state_dim * 2, config.hidden_dim),
            nn.Tanh(),
            nn.Linear(config.hidden_dim, config.action_dim),
        )

    def forward(self, state: torch.Tensor, next_state: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([state, next_state], dim=-1))


class Decoder(nn.Module):
    """Gaddy/Klein-style conditional decoder.

    Both next-state and low-level action predictions are conditioned on current
    state and latent transition. Conditioning action on state is required for
    sequential RTFM: the same task language permits different navigation actions
    at different locations.
    """

    def __init__(self, config: Config):
        super().__init__()
        joint = config.state_dim + config.action_dim
        self.state = nn.Sequential(
            nn.Linear(joint, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.state_dim),
        )
        self.action = nn.Sequential(
            nn.Linear(joint, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.num_actions),
        )

    def forward(self, state: torch.Tensor, latent: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        joint = torch.cat([state, latent], dim=-1)
        return self.state(joint), self.action(joint)


class LanguageEncoder(nn.Module):
    def __init__(self, config: Config):
        super().__init__()
        self.emb = nn.Embedding(config.vocab_size, config.text_dim, padding_idx=0)
        self.gru = nn.GRU(config.text_dim, config.hidden_dim, batch_first=True)
        self.out = nn.Linear(config.hidden_dim, config.action_dim)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        _, hidden = self.gru(self.emb(tokens))
        return self.out(hidden[-1])


class InstructionModel(nn.Module):
    def __init__(self, config: Config):
        super().__init__()
        self.language = LanguageEncoder(config)
        self.decoder = Decoder(config)

    def forward(self, state: torch.Tensor, tokens: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return self.decoder(state, self.language(tokens))


class StateOnlyModel(nn.Module):
    def __init__(self, config: Config):
        super().__init__()
        self.state_encoder = nn.Sequential(
            nn.Linear(config.state_dim, config.hidden_dim),
            nn.Tanh(),
            nn.Linear(config.hidden_dim, config.action_dim),
        )
        self.decoder = Decoder(config)

    def forward(self, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return self.decoder(state, self.state_encoder(state))


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


def loss_fn(next_hat: torch.Tensor, action_hat: torch.Tensor, batch: dict[str, torch.Tensor]) -> torch.Tensor:
    return nn.functional.mse_loss(next_hat, batch["after"]) + nn.functional.cross_entropy(
        action_hat, batch["action"]
    )


def train_environment(
    encoder: TransitionEncoder, decoder: Decoder, loader: DataLoader, config: Config
) -> float:
    optimizer = torch.optim.Adam(list(encoder.parameters()) + list(decoder.parameters()), lr=config.lr)
    started = time.perf_counter()
    for _ in range(config.env_epochs):
        for batch in loader:
            latent = encoder(batch["before"], batch["after"])
            next_hat, action_hat = decoder(batch["before"], latent)
            loss = loss_fn(next_hat, action_hat, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def train_language(
    language: LanguageEncoder, decoder: Decoder, loader: DataLoader, config: Config
) -> float:
    if config.freeze_decoder:
        for parameter in decoder.parameters():
            parameter.requires_grad = False
    parameters = [p for p in list(language.parameters()) + list(decoder.parameters()) if p.requires_grad]
    optimizer = torch.optim.Adam(parameters, lr=config.lr)
    started = time.perf_counter()
    for _ in range(config.lang_epochs):
        for batch in loader:
            next_hat, action_hat = decoder(batch["before"], language(batch["text"]))
            loss = loss_fn(next_hat, action_hat, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def train_model(model: nn.Module, loader: DataLoader, config: Config, state_only: bool = False) -> float:
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    started = time.perf_counter()
    for _ in range(config.lang_epochs):
        for batch in loader:
            if state_only:
                next_hat, action_hat = model(batch["before"])
            else:
                next_hat, action_hat = model(batch["before"], batch["text"])
            loss = loss_fn(next_hat, action_hat, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return time.perf_counter() - started


def evaluate(
    kind: str,
    model: Any,
    loader: DataLoader,
    condition: str = "correct",
) -> dict[str, Any]:
    modules = model if isinstance(model, tuple) else (model,)
    for module in modules:
        module.eval()
    count = 0
    action_correct = 0
    mse_sum = 0.0
    transition_joint = 0
    buckets = {key: [0, 0] for key in ("entity", "dynamics", "language")}
    latencies: list[float] = []
    generator = torch.Generator().manual_seed(20260725)
    with torch.no_grad():
        for batch in loader:
            tokens = batch["text"].clone()
            if condition == "language_blind":
                tokens.zero_()
            elif condition == "language_shuffle":
                tokens = tokens[torch.randperm(tokens.shape[0], generator=generator)]
            started = time.perf_counter_ns()
            if kind == "environment_first":
                language, decoder = model
                next_hat, action_hat = decoder(batch["before"], language(tokens))
            elif kind == "end_to_end":
                next_hat, action_hat = model(batch["before"], tokens)
            elif kind == "state_only":
                next_hat, action_hat = model(batch["before"])
            else:
                raise ValueError(kind)
            latencies.append((time.perf_counter_ns() - started) / 1e6 / len(tokens))
            predicted = action_hat.argmax(dim=-1)
            correct = predicted.eq(batch["action"])
            per_row_error = (next_hat - batch["after"]).abs().mean(dim=-1)
            action_correct += int(correct.sum().item())
            transition_joint += int(correct.logical_and(per_row_error < 0.25).sum().item())
            count += len(tokens)
            mse_sum += nn.functional.mse_loss(next_hat, batch["after"], reduction="sum").item()
            for key, field in (
                ("entity", "entity_holdout"),
                ("dynamics", "dynamics_holdout"),
                ("language", "language_holdout"),
            ):
                mask = batch[field].bool()
                buckets[key][0] += int(correct[mask].sum().item())
                buckets[key][1] += int(mask.sum().item())
    dimension = len(loader.dataset.rows[0]["state_after"])
    return {
        "task_success": None,
        "task_success_reason": "offline transition dataset cannot measure environment-level success",
        "transition_joint_success": transition_joint / count,
        "action_accuracy": action_correct / count,
        "next_state_mse": mse_sum / (count * dimension),
        "cpu_inference_ms_per_item": statistics.fmean(latencies),
        "heldout_action_accuracy": {
            key: (hits / total if total else None) for key, (hits, total) in buckets.items()
        },
    }


def model_bytes(model: nn.Module) -> int:
    return sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--hidden-dim", type=int, default=96)
    parser.add_argument("--action-dim", type=int, default=48)
    parser.add_argument("--env-epochs", type=int, default=8)
    parser.add_argument("--lang-epochs", type=int, default=8)
    args = parser.parse_args()
    seed_all(args.seed)

    rows = load_rows(args.data)
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]
    if not train or not test:
        raise ValueError("both train and test rows are required")
    vocabulary_size = max((max(row.get("text_tokens", [0])) for row in rows), default=0) + 1
    config = Config(
        state_dim=len(train[0]["state_before"]),
        num_actions=max(int(row["action"]) for row in rows) + 1,
        vocab_size=vocabulary_size,
        hidden_dim=args.hidden_dim,
        action_dim=args.action_dim,
        env_epochs=args.env_epochs,
        lang_epochs=args.lang_epochs,
    )
    train_loader = DataLoader(
        Rows(train, config.max_text_len), batch_size=config.batch_size, shuffle=True
    )
    test_loader = DataLoader(Rows(test, config.max_text_len), batch_size=config.batch_size)

    transition_encoder = TransitionEncoder(config)
    decoder = Decoder(config)
    language = LanguageEncoder(config)
    environment_seconds = train_environment(transition_encoder, decoder, train_loader, config)
    language_seconds = train_language(language, decoder, train_loader, config)
    environment_first = {
        condition: evaluate("environment_first", (language, decoder), test_loader, condition)
        for condition in ("correct", "language_blind", "language_shuffle")
    }

    seed_all(args.seed)
    end_to_end = InstructionModel(config)
    end_to_end_seconds = train_model(end_to_end, train_loader, config)
    end_to_end_metrics = {
        condition: evaluate("end_to_end", end_to_end, test_loader, condition)
        for condition in ("correct", "language_blind", "language_shuffle")
    }

    seed_all(args.seed)
    state_only = StateOnlyModel(config)
    state_only_seconds = train_model(state_only, train_loader, config, state_only=True)
    state_only_metrics = evaluate("state_only", state_only, test_loader)

    result = {
        "status": "public_silg_trajectory_offline_baseline_not_online_task_reproduction",
        "seed": args.seed,
        "config": asdict(config),
        "dataset": {
            "path": str(args.data),
            "sha256": sha256(args.data),
            "n_train": len(train),
            "n_test": len(test),
        },
        "environment_first": {
            "environment_pretrain_seconds": environment_seconds,
            "language_train_seconds": language_seconds,
            "training_model_bytes": model_bytes(transition_encoder) + model_bytes(decoder) + model_bytes(language),
            "inference_model_bytes": model_bytes(decoder) + model_bytes(language),
            "metrics": environment_first,
        },
        "end_to_end": {
            "train_seconds": end_to_end_seconds,
            "inference_model_bytes": model_bytes(end_to_end),
            "metrics": end_to_end_metrics,
        },
        "state_only": {
            "train_seconds": state_only_seconds,
            "inference_model_bytes": model_bytes(state_only),
            "metrics": state_only_metrics,
        },
        "parameter_budget_match": model_bytes(decoder) + model_bytes(language) == model_bytes(end_to_end),
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "torch_version": torch.__version__,
        "python": os.sys.version,
        "pretrained_language_model": False,
        "capability_progress_claimed": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
