#!/usr/bin/env python3
"""Online SILG/RTFM evaluation for the matched R0.2 baselines.

This evaluator adds no new mechanism.  It reloads the already trained
Environment-first, parameter-matched End-to-end, and State-only checkpoints and
runs them on exactly the same independently seeded RTFM test instances.

Offline action accuracy and next-state prediction are not substituted for task
success.  A win uses the same terminal reward > 0.5 rule as the canonical R0.1
matched evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import statistics
import sys
import time
from dataclasses import fields
from pathlib import Path
from typing import Any

import numpy as np
import torch

from export_silg_typed_policy_trajectories import observation_fingerprint, state_fields, text_tokens
from gaddy_klein_typed_baseline import Config, LanguageMessageEncoder, TypedDecoder, load_rows, validate_rows
from r02_typed_comparison import EndToEndModel, StateOnlyModel

METHODS = ("environment_first", "end_to_end", "state_only")
CANONICAL_SEEDS = (1, 7, 19)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def config_from_payload(payload: dict[str, Any]) -> Config:
    allowed = {item.name for item in fields(Config)}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError(f"unknown checkpoint config fields: {sorted(unknown)}")
    return Config(**payload)


def make_live_batch(obs: dict[str, torch.Tensor], specs, config: Config) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    values = state_fields(obs)
    before: dict[str, torch.Tensor] = {}
    for spec in specs:
        if spec.name not in values:
            raise RuntimeError(f"live observation missing typed field {spec.name!r}")
        dtype = torch.float32 if spec.kind == "continuous" else torch.long
        tensor = torch.tensor(values[spec.name], dtype=dtype).reshape(1, -1)
        if tensor.shape[1] != spec.width:
            raise RuntimeError(f"live field width changed for {spec.name}: {tensor.shape[1]} != {spec.width}")
        before[spec.name] = tensor

    tokens = [int(value) for value in text_tokens(obs)[: config.max_text_len]]
    tokens += [0] * (config.max_text_len - len(tokens))
    return before, torch.tensor([tokens], dtype=torch.long)


def load_method(method: str, checkpoint: Path, specs):
    payload = torch.load(str(checkpoint), map_location="cpu")
    if not isinstance(payload, dict) or "config" not in payload:
        raise RuntimeError(f"invalid R0.2 checkpoint schema: {checkpoint}")
    config = config_from_payload(payload["config"])

    if method == "environment_first":
        if not {"language", "decoder"}.issubset(payload):
            raise RuntimeError("environment-first checkpoint lacks language/decoder state")
        language = LanguageMessageEncoder(config)
        decoder = TypedDecoder(specs, config)
        language.load_state_dict(payload["language"])
        decoder.load_state_dict(payload["decoder"])
        language.eval()
        decoder.eval()

        def forward(before, text):
            _, message = language(text, hard=True)
            return decoder(before, message)[1]

        modules = [language, decoder]
    elif method == "end_to_end":
        model = EndToEndModel(specs, config)
        model.load_state_dict(payload["model"])
        model.eval()

        def forward(before, text):
            return model(before, text, hard=True)[2]

        modules = [model]
    elif method == "state_only":
        model = StateOnlyModel(specs, config)
        model.load_state_dict(payload["model"])
        model.eval()

        def forward(before, text):
            del text
            return model(before)[1]

        modules = [model]
    else:
        raise ValueError(method)

    parameters = sum(parameter.numel() for module in modules for parameter in module.parameters())
    parameter_bytes = sum(parameter.numel() * parameter.element_size() for module in modules for parameter in module.parameters())
    return config, forward, parameters, parameter_bytes


def valid_action(logits: torch.Tensor, obs: dict[str, torch.Tensor]) -> torch.Tensor:
    valid = obs["valid"].detach().reshape(-1).bool()
    flat_logits = logits.reshape(-1)
    if flat_logits.numel() != valid.numel():
        raise RuntimeError(f"action schema mismatch: logits={flat_logits.numel()} valid={valid.numel()}")
    if not bool(valid.any()):
        raise RuntimeError("RTFM observation exposes no valid action")
    masked = flat_logits.masked_fill(~valid, float("-inf"))
    return masked.argmax().reshape(1, 1).to(torch.int64)


def evaluate_method(
    silg_root: Path,
    data: Path,
    checkpoint: Path,
    method: str,
    seed: int,
    episodes: int,
) -> dict[str, Any]:
    sys.path.insert(0, str(silg_root))
    import exp_utils
    from core import environment
    from model.multi import Model
    from silg import envs as _registered_envs  # noqa: F401

    rows = load_rows(data)
    specs = validate_rows(rows)
    observed_seeds = {int(row["seed"]) for row in rows if "seed" in row}
    if observed_seeds and observed_seeds != {seed}:
        raise ValueError(f"dataset seed mismatch: requested={seed}, observed={sorted(observed_seeds)}")
    config, forward, parameters, parameter_bytes = load_method(method, checkpoint, specs)

    flags = exp_utils.get_parser().parse_args([])
    flags.env = "silg:rtfm_test_s1-v0"
    flags.val_env = flags.env
    flags.model = "multi"
    flags.disable_cuda = True
    flags.seed = seed

    wins: list[float] = []
    returns: list[float] = []
    lengths: list[int] = []
    inference_ns: list[int] = []
    records: list[dict[str, Any]] = []
    started = time.perf_counter()

    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        random.seed(episode_seed)
        np.random.seed(episode_seed)
        torch.manual_seed(episode_seed)
        gym_env = Model.create_env(flags)
        gym_env.seed(episode_seed)
        env = environment.Environment(gym_env)
        obs = env.initial()
        fingerprint = observation_fingerprint(obs)
        done = False
        steps = 0

        while not done:
            before, text = make_live_batch(obs, specs, config)
            t0 = time.perf_counter_ns()
            with torch.inference_mode():
                logits = forward(before, text)
                action = valid_action(logits, obs)
            inference_ns.append(time.perf_counter_ns() - t0)
            obs = env.step(action)
            steps += 1
            done = bool(obs["done"].item())

        episode_return = float(obs["episode_return"].item())
        win = float(obs["reward"][0][0].item() > 0.5)
        wins.append(win)
        returns.append(episode_return)
        lengths.append(steps)
        records.append(
            {
                "episode_index": episode,
                "episode_seed": episode_seed,
                "initial_instance_fingerprint": fingerprint,
                "win": win,
                "return": episode_return,
                "length": steps,
            }
        )
        env.close()

    return {
        "method": method,
        "seed": seed,
        "episodes": episodes,
        "dataset": {"path": str(data), "sha256": sha256(data)},
        "checkpoint": {"path": str(checkpoint), "bytes": checkpoint.stat().st_size, "sha256": sha256(checkpoint)},
        "parameters": parameters,
        "parameter_bytes": parameter_bytes,
        "win_rate": statistics.fmean(wins),
        "return_mean": statistics.fmean(returns),
        "episode_length_mean": statistics.fmean(lengths),
        "cpu_inference_ms_per_step": statistics.fmean(inference_ns) / 1e6,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "episode_records": records,
    }


def paired_gaps(runs: list[dict[str, Any]]) -> dict[str, Any]:
    indexed = {
        run["method"]: {int(row["episode_seed"]): row for row in run["episode_records"]}
        for run in runs
    }
    reference = indexed["environment_first"]
    result: dict[str, Any] = {}
    for control in ("end_to_end", "state_only"):
        keys = sorted(reference.keys() & indexed[control].keys())
        if keys != sorted(reference) or keys != sorted(indexed[control]):
            raise RuntimeError(f"incomplete paired episode coverage for {control}")
        win = [float(reference[key]["win"]) - float(indexed[control][key]["win"]) for key in keys]
        ret = [float(reference[key]["return"]) - float(indexed[control][key]["return"]) for key in keys]
        result[control] = {
            "paired_episodes": len(keys),
            "win_rate_mean_gap": statistics.fmean(win),
            "return_mean_gap": statistics.fmean(ret),
            "return_min_gap": min(ret),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True, help="stem used to locate the three R0.2 checkpoints")
    parser.add_argument("--seed", type=int, choices=CANONICAL_SEEDS, required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    stem = args.comparison.with_suffix("")
    checkpoints = {
        method: Path(f"{stem}.{method}.pt")
        for method in METHODS
    }
    missing = [str(path) for path in checkpoints.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing R0.2 checkpoints: {missing}")

    runs = [
        evaluate_method(args.silg_root, args.data, checkpoints[method], method, args.seed, args.episodes)
        for method in METHODS
    ]
    fingerprints = {
        run["method"]: [row["initial_instance_fingerprint"] for row in run["episode_records"]]
        for run in runs
    }
    base = fingerprints["environment_first"]
    same_stream = {method: values == base for method, values in fingerprints.items()}
    if not all(same_stream.values()):
        raise RuntimeError(f"methods did not receive the same initial instance stream: {same_stream}")

    payload = {
        "status": "online_silg_evaluation_complete",
        "classification": "R0.2 online baseline evaluation; transfer claims require preregistered real holdouts",
        "environment": "silg:rtfm_test_s1-v0",
        "source_pins": {
            "silg": "2af07578e1264029a240fcfb78d4ac0aea16f5de",
            "rtfm": "58f17955595b5a127c96d045d896fcbcc7d4b570",
        },
        "seed": args.seed,
        "episodes_per_method": args.episodes,
        "same_initial_instance_stream": same_stream,
        "runs": runs,
        "paired_gaps_environment_first_minus_control": paired_gaps(runs),
        "limitations": [
            "entity/dynamics/language-form transfer is unqualified until externally preregistered generator signatures are attached",
            "no representation appearance or compression metric is counted as progress",
            "no novelty, intelligence-principle, or capability-progress claim follows from this evaluator alone",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
