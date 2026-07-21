from __future__ import annotations

import argparse
import io
import json
import math
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

from architecture_map import benchmark_full_pass, evaluate
from model_registry import build_model
from suite import MixedSequenceDataset, TASKS, TOKENS, WEIGHTED_CHANCE, collate


ARCHITECTURES = ("gru", "transformer", "rwkv7", "deltanet")
OPTIMIZERS = ("adamw", "muon")


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def serialized_size(model: nn.Module) -> int:
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return buffer.tell()


def zeropower_via_newtonschulz5(matrix: torch.Tensor, steps: int = 5) -> torch.Tensor:
    if matrix.ndim != 2:
        raise ValueError("Muon orthogonalization expects a matrix")
    transposed = matrix.shape[0] > matrix.shape[1]
    x = matrix.T if transposed else matrix
    x = x / (x.norm() + 1e-7)
    a, b, c = 3.4445, -4.7750, 2.0315
    for _ in range(steps):
        gram = x @ x.T
        x = a * x + (b * gram + c * (gram @ gram)) @ x
    return x.T if transposed else x


class Muon(torch.optim.Optimizer):
    def __init__(self, params, lr: float = 0.02, momentum: float = 0.95, weight_decay: float = 0.01):
        super().__init__(params, dict(lr=lr, momentum=momentum, weight_decay=weight_decay))

    @torch.no_grad()
    def step(self, closure=None):
        loss = closure() if closure is not None else None
        for group in self.param_groups:
            lr = group["lr"]
            momentum = group["momentum"]
            weight_decay = group["weight_decay"]
            for parameter in group["params"]:
                if parameter.grad is None:
                    continue
                gradient = parameter.grad
                state = self.state[parameter]
                if "momentum_buffer" not in state:
                    state["momentum_buffer"] = torch.zeros_like(gradient)
                buffer = state["momentum_buffer"]
                buffer.mul_(momentum).add_(gradient)
                update = gradient.add(buffer, alpha=momentum)
                update = zeropower_via_newtonschulz5(update.float()).to(parameter.dtype)
                scale = math.sqrt(max(1.0, parameter.shape[0] / max(1, parameter.shape[1])))
                if weight_decay:
                    parameter.mul_(1.0 - lr * weight_decay)
                parameter.add_(update, alpha=-lr * scale)
        return loss


class CompositeOptimizer:
    def __init__(self, model: nn.Module, name: str):
        if name == "adamw":
            self.optimizers = [torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.01)]
            return
        matrix, vector = [], []
        for parameter in model.parameters():
            (matrix if parameter.ndim == 2 else vector).append(parameter)
        self.optimizers = [Muon(matrix, lr=0.02, momentum=0.95, weight_decay=0.01)]
        if vector:
            self.optimizers.append(torch.optim.AdamW(vector, lr=2e-3, weight_decay=0.0))

    def zero_grad(self) -> None:
        for optimizer in self.optimizers:
            optimizer.zero_grad(set_to_none=True)

    def step(self) -> None:
        for optimizer in self.optimizers:
            optimizer.step()


@dataclass
class CouplingMetrics:
    architecture: str
    optimizer: str
    seed: int
    train_examples: int
    epochs: int
    parameters: int
    model_bytes: int
    peak_rss_kib: int
    train_seconds: float
    answer_accuracy: float
    stress_accuracy: float
    validation_nll: float
    per_task_accuracy: dict[str, float]
    state_bytes_128: int
    token_latency_ms_128: float
    candidate_count: int
    state_reads_128: int
    gradient_steps: int
    mean_gradient_norm: float
    mean_update_proxy: float


def train_one(architecture: str, optimizer_name: str, seed: int, train_examples: int, epochs: int) -> CouplingMetrics:
    seed_everything(seed)
    model = build_model(architecture)
    train = MixedSequenceDataset(train_examples, seed * 1009 + train_examples, False, 6)
    valid = MixedSequenceDataset(256, 810_000 + seed, True, 6)
    stress = MixedSequenceDataset(256, 910_000 + seed, True, 18)
    generator = torch.Generator().manual_seed(seed)
    train_loader = torch.utils.data.DataLoader(train, 128, True, generator=generator, collate_fn=collate)
    valid_loader = torch.utils.data.DataLoader(valid, 256, False, collate_fn=collate)
    stress_loader = torch.utils.data.DataLoader(stress, 256, False, collate_fn=collate)
    optimizer = CompositeOptimizer(model, optimizer_name)

    gradient_norms: list[float] = []
    update_proxies: list[float] = []
    gradient_steps = 0
    started = time.perf_counter()
    model.train()
    for _ in range(epochs):
        for inputs, targets, answer_mask, _ in train_loader:
            optimizer.zero_grad()
            logits, _ = model(inputs)
            token_loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1), ignore_index=-100)
            answer_loss = F.cross_entropy(logits[answer_mask], targets[answer_mask])
            loss = 0.20 * token_loss + 0.80 * answer_loss
            loss.backward()
            gradient_norm = float(nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            before = sum(float(parameter.detach().square().sum()) for parameter in model.parameters())
            optimizer.step()
            after = sum(float(parameter.detach().square().sum()) for parameter in model.parameters())
            gradient_norms.append(gradient_norm)
            update_proxies.append(abs(after - before) ** 0.5)
            gradient_steps += 1
    train_seconds = time.perf_counter() - started

    accuracy, nll, per_task = evaluate(model, valid_loader)
    stress_accuracy, _, _ = evaluate(model, stress_loader)
    return CouplingMetrics(
        architecture=architecture,
        optimizer=optimizer_name,
        seed=seed,
        train_examples=train_examples,
        epochs=epochs,
        parameters=sum(parameter.numel() for parameter in model.parameters()),
        model_bytes=serialized_size(model),
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        train_seconds=train_seconds,
        answer_accuracy=accuracy,
        stress_accuracy=stress_accuracy,
        validation_nll=nll,
        per_task_accuracy=per_task,
        state_bytes_128=model.state_bytes(128),
        token_latency_ms_128=benchmark_full_pass(model, 128, 2),
        candidate_count=len(TOKENS),
        state_reads_128=model.state_reads(128),
        gradient_steps=gradient_steps,
        mean_gradient_norm=statistics.mean(gradient_norms),
        mean_update_proxy=statistics.mean(update_proxies),
    )


def aggregate(rows: list[CouplingMetrics]) -> dict:
    result: dict[str, dict] = {}
    for architecture in ARCHITECTURES:
        result[architecture] = {}
        for optimizer in OPTIMIZERS:
            result[architecture][optimizer] = {}
            for scale in sorted({row.train_examples for row in rows if row.architecture == architecture and row.optimizer == optimizer}):
                subset = [row for row in rows if row.architecture == architecture and row.optimizer == optimizer and row.train_examples == scale]
                result[architecture][optimizer][str(scale)] = {
                    "parameters": subset[0].parameters,
                    "answer_accuracy_mean": statistics.mean(row.answer_accuracy for row in subset),
                    "answer_accuracy_min": min(row.answer_accuracy for row in subset),
                    "stress_accuracy_mean": statistics.mean(row.stress_accuracy for row in subset),
                    "validation_nll_mean": statistics.mean(row.validation_nll for row in subset),
                    "train_seconds_mean": statistics.mean(row.train_seconds for row in subset),
                    "model_bytes_max": max(row.model_bytes for row in subset),
                    "peak_rss_kib_max": max(row.peak_rss_kib for row in subset),
                    "state_bytes_128": subset[0].state_bytes_128,
                    "token_latency_ms_128_mean": statistics.mean(row.token_latency_ms_128 for row in subset),
                    "candidate_count": subset[0].candidate_count,
                    "state_reads_128": subset[0].state_reads_128,
                    "mean_gradient_norm": statistics.mean(row.mean_gradient_norm for row in subset),
                    "mean_update_proxy": statistics.mean(row.mean_update_proxy for row in subset),
                    "per_task_accuracy_mean": {
                        task: statistics.mean(row.per_task_accuracy[task] for row in subset) for task in TASKS
                    },
                }
    return result


def run_experiment(output: Path, quick: bool = False) -> dict:
    scales, seeds, epochs = ((256,), (1,), 2) if quick else ((512, 2048), (1, 7, 19), 12)
    checkpoint = output.with_suffix(".jsonl")
    rows = [CouplingMetrics(**json.loads(line)) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    completed = {(row.architecture, row.optimizer, row.seed, row.train_examples) for row in rows}
    for scale in scales:
        for seed in seeds:
            for architecture in ARCHITECTURES:
                for optimizer in OPTIMIZERS:
                    key = architecture, optimizer, seed, scale
                    if key in completed:
                        continue
                    print(f"running architecture={architecture} optimizer={optimizer} scale={scale} seed={seed}", flush=True)
                    row = train_one(architecture, optimizer, seed, scale, epochs)
                    rows.append(row)
                    checkpoint.parent.mkdir(parents=True, exist_ok=True)
                    with checkpoint.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
                    completed.add(key)
    table = aggregate(rows)
    report = {
        "hypothesis": "Sequence architectures have optimizer-dependent learning geometry; apparent architectural advantages that disappear when the optimizer changes are not stable intelligence principles.",
        "negative_controls": [
            "same model factory, data, objective, seeds, epochs and evaluation episodes",
            "AdamW retained as the established baseline",
            "Muon is applied only to matrix parameters; vectors and normalization parameters use AdamW",
            "short-distribution and length-extrapolation metrics are reported separately",
        ],
        "chance_weighted": WEIGHTED_CHANCE,
        "claim_scope": {
            "official_muon_reproduction": False,
            "official_architecture_reproduction": False,
            "free_japanese_dialogue": False,
            "highschool_level_passed": False,
            "native_japanese_communication_passed": False,
            "weak_smartphone_verified": False,
            "completion": False,
        },
        "aggregate": table,
        "runs": [asdict(row) for row in rows],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/optimizer_coupling_report.json"))
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    print(json.dumps(run_experiment(args.output, args.quick)["aggregate"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
