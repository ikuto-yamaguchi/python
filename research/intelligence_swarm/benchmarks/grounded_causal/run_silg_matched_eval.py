#!/usr/bin/env python3
"""Evaluate a trained official SILG recurrent checkpoint and matched controls
on independently seeded, identical RTFM test episodes.

This is an evaluation harness, not a new architecture. `correct` uses the
unaltered official model. Ablations only mask or permute declared observation
fields at inference time and never expose future state, reward, or completed
trajectory. Each episode is created in a fresh environment from a fixed episode
seed, so all methods receive exactly the same initial benchmark instance even
when their trajectories and episode lengths diverge.
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
from pathlib import Path
from typing import Any

import numpy as np
import torch

METHODS = ("correct", "random", "language_blind", "state_only", "language_shuffle")
LANGUAGE_FIELDS = ("wiki", "wiki_len", "task", "task_len")
STATE_TEXT_FIELDS = LANGUAGE_FIELDS + ("inv", "inv_len", "name", "name_len")


def stable_tensor_hash(obs: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    excluded = {"reward", "done", "episode_return", "episode_step", "last_action"}
    for key in sorted(k for k in obs if k not in excluded):
        tensor = obs[key].detach().cpu().contiguous()
        h.update(key.encode())
        h.update(str(tuple(tensor.shape)).encode())
        h.update(tensor.numpy().tobytes())
    return h.hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mask_text_fields(out: dict[str, torch.Tensor], fields: tuple[str, ...]) -> None:
    """Remove text content without creating invalid zero-length RNN samples.

    SILG's official text encoder uses ``pack_padded_sequence`` and therefore
    requires every declared sequence length to be at least one. A text-blind
    control should remove token information, not violate the model's input
    contract. Token tensors are zeroed and their matching ``*_len`` tensors are
    set to one. This leaves one padding/unknown position and no lexical content.
    """
    for key in fields:
        if key not in out:
            continue
        if key.endswith("_len"):
            out[key].fill_(1)
        else:
            out[key].zero_()


def sanitize_language_lengths(out: dict[str, torch.Tensor]) -> None:
    """Clamp copied donor lengths to the minimum accepted by the official RNN."""
    for key in ("wiki_len", "task_len"):
        if key in out:
            out[key].clamp_(min=1)


def transform_observation(
    obs: dict[str, torch.Tensor],
    method: str,
    donor_language: dict[str, torch.Tensor] | None = None,
) -> dict[str, torch.Tensor]:
    out = {key: value.clone() for key, value in obs.items()}
    if method == "language_blind":
        mask_text_fields(out, LANGUAGE_FIELDS)
    elif method == "state_only":
        mask_text_fields(out, STATE_TEXT_FIELDS)
    elif method == "language_shuffle":
        if donor_language is None:
            raise ValueError("language_shuffle requires a donor observation")
        for key in LANGUAGE_FIELDS:
            if key in out and key in donor_language:
                if out[key].shape != donor_language[key].shape:
                    raise ValueError(f"language donor shape mismatch for {key}")
                out[key].copy_(donor_language[key])
        sanitize_language_lengths(out)
    return out


def capture_language_donors(Model: Any, flags: Any, seed: int, episodes: int) -> tuple[list[dict[str, torch.Tensor]], list[int]]:
    donors: list[dict[str, torch.Tensor]] = []
    donor_seeds: list[int] = []
    for episode in range(episodes):
        donor_episode = (episode + 1) % episodes
        donor_seed = seed * 1_000_003 + donor_episode
        random.seed(donor_seed)
        np.random.seed(donor_seed)
        torch.manual_seed(donor_seed)
        gym_env = Model.create_env(flags)
        gym_env.seed(donor_seed)
        raw = gym_env.reset()
        donor = {
            key: torch.as_tensor(raw[key]).unsqueeze(0).unsqueeze(0).clone()
            for key in LANGUAGE_FIELDS
            if key in raw
        }
        sanitize_language_lengths(donor)
        donors.append(donor)
        donor_seeds.append(donor_seed)
        gym_env.close()
    return donors, donor_seeds


def run_method(root: Path, checkpoint: Path, seed: int, method: str, episodes: int) -> dict[str, Any]:
    sys.path.insert(0, str(root))
    import exp_utils
    from core import environment
    from model.multi import Model
    from silg import envs as _registered_envs  # noqa: F401

    flags = exp_utils.get_parser().parse_args([])
    flags.env = "silg:rtfm_test_s1-v0"
    flags.val_env = "silg:rtfm_test_s1-v0"
    flags.model = "multi"
    flags.disable_cuda = True
    flags.seed = seed

    template_env = Model.create_env(flags)
    model = Model.make(flags, template_env).eval()
    template_env.close()
    model.load_state_dict(torch.load(str(checkpoint), map_location="cpu"))

    donor_languages: list[dict[str, torch.Tensor]] = []
    donor_seeds: list[int] = []
    if method == "language_shuffle":
        donor_languages, donor_seeds = capture_language_donors(Model, flags, seed, episodes)

    returns: list[float] = []
    wins: list[float] = []
    lengths: list[int] = []
    fingerprints: list[str] = []
    episode_seeds: list[int] = []
    inference_ns: list[int] = []
    episode_records: list[dict[str, Any]] = []
    started = time.perf_counter()

    for episode in range(episodes):
        episode_seed = seed * 1_000_003 + episode
        episode_seeds.append(episode_seed)
        random.seed(episode_seed)
        np.random.seed(episode_seed)
        torch.manual_seed(episode_seed)

        gym_env = Model.create_env(flags)
        gym_env.seed(episode_seed)
        env = environment.Environment(gym_env)
        observation = env.initial()
        fingerprint = stable_tensor_hash(observation)
        fingerprints.append(fingerprint)
        agent_state = model.initial_state(batch_size=1)
        done = False
        steps = 0
        rng = random.Random(episode_seed)
        donor = donor_languages[episode] if donor_languages else None

        while not done:
            if method == "random":
                valid = [i for i, flag in enumerate(observation["valid"].flatten().tolist()) if flag]
                t0 = time.perf_counter_ns()
                action = torch.tensor([[rng.choice(valid)]], dtype=torch.int64)
                inference_ns.append(time.perf_counter_ns() - t0)
            else:
                model_obs = transform_observation(observation, method, donor)
                t0 = time.perf_counter_ns()
                with torch.no_grad():
                    output, agent_state = model(model_obs, agent_state)
                inference_ns.append(time.perf_counter_ns() - t0)
                action = output["action"]
            observation = env.step(action)
            steps += 1
            done = bool(observation["done"].item())

        episode_return = float(observation["episode_return"].item())
        win = float(observation["reward"][0][0].item() > 0.5)
        returns.append(episode_return)
        wins.append(win)
        lengths.append(steps)
        episode_records.append({
            "episode_index": episode,
            "episode_seed": episode_seed,
            "initial_instance_fingerprint": fingerprint,
            "language_donor_seed": donor_seeds[episode] if donor_seeds else None,
            "win": win,
            "return": episode_return,
            "length": steps,
        })
        env.close()

    return {
        "method": method,
        "seed": seed,
        "episodes": episodes,
        "episode_seeds": episode_seeds,
        "win_rate": statistics.fmean(wins),
        "return_mean": statistics.fmean(returns),
        "episode_length_mean": statistics.fmean(lengths),
        "wall_seconds": time.perf_counter() - started,
        "cpu_inference_ms_per_step": statistics.fmean(inference_ns) / 1e6,
        "initial_instance_fingerprints": fingerprints,
        "episode_records": episode_records,
    }


def paired_episode_gaps(runs: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    indexed: dict[str, dict[tuple[int, int], dict[str, Any]]] = {}
    for run in runs:
        indexed[run["method"]] = {
            (int(run["seed"]), int(record["episode_seed"])): record
            for record in run["episode_records"]
        }
    correct = indexed["correct"]
    out: dict[str, dict[str, float]] = {}
    for control in METHODS:
        if control == "correct":
            continue
        keys = sorted(correct.keys() & indexed[control].keys())
        return_diffs = [float(correct[key]["return"]) - float(indexed[control][key]["return"]) for key in keys]
        win_diffs = [float(correct[key]["win"]) - float(indexed[control][key]["win"]) for key in keys]
        out[control] = {
            "paired_episodes": len(keys),
            "return_mean_gap": statistics.fmean(return_diffs),
            "return_min_gap": min(return_diffs),
            "return_positive_fraction": sum(x > 0 for x in return_diffs) / len(return_diffs),
            "win_rate_mean_gap": statistics.fmean(win_diffs),
            "win_positive_fraction": sum(x > 0 for x in win_diffs) / len(win_diffs),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 7, 19])
    parser.add_argument("--episodes", type=int, default=20)
    args = parser.parse_args()
    args.results = args.results.resolve()
    runs: list[dict[str, Any]] = []
    started = time.perf_counter()

    for seed in args.seeds:
        checkpoint = args.results / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(checkpoint)
        for method in METHODS:
            runs.append(run_method(args.silg_root, checkpoint, seed, method, args.episodes))

    consistency: dict[str, dict[str, bool]] = {}
    for seed in args.seeds:
        seed_runs = [run for run in runs if run["seed"] == seed]
        base_fingerprints = seed_runs[0]["initial_instance_fingerprints"]
        base_episode_seeds = seed_runs[0]["episode_seeds"]
        consistency[str(seed)] = {
            run["method"]: (
                run["initial_instance_fingerprints"] == base_fingerprints
                and run["episode_seeds"] == base_episode_seeds
            )
            for run in seed_runs
        }

    aggregate: dict[str, dict[str, float]] = {}
    for method in METHODS:
        selected = [run for run in runs if run["method"] == method]
        aggregate[method] = {
            "win_rate": statistics.fmean(run["win_rate"] for run in selected),
            "return_mean": statistics.fmean(run["return_mean"] for run in selected),
            "episode_length_mean": statistics.fmean(run["episode_length_mean"] for run in selected),
            "cpu_inference_ms_per_step": statistics.fmean(run["cpu_inference_ms_per_step"] for run in selected),
        }

    payload = {
        "status": "success",
        "classification": "matched_fixed_episode_staged_training_not_full_paper_reproduction",
        "environment": "silg:rtfm_test_s1-v0",
        "source_pins": {
            "silg": "2af07578e1264029a240fcfb78d4ac0aea16f5de",
            "rtfm": "58f17955595b5a127c96d045d896fcbcc7d4b570",
        },
        "seeds": args.seeds,
        "episodes_per_method_seed": args.episodes,
        "methods": list(METHODS),
        "runs": runs,
        "aggregate": aggregate,
        "paired_episode_gaps_vs_correct": paired_episode_gaps(runs),
        "same_initial_instance_stream": consistency,
        "all_initial_streams_match": all(all(values.values()) for values in consistency.values()),
        "language_shuffle_protocol": {
            "type": "within-seed cyclic episode permutation",
            "fields": list(LANGUAGE_FIELDS),
            "donor_episode": "(episode_index + 1) mod episodes",
            "state_and_valid_actions_unchanged": True,
            "zero_length_sequences_prevented": True,
        },
        "text_ablation_protocol": {
            "token_values": "zeroed",
            "declared_lengths": "set to one to preserve official pack_padded_sequence input contract",
            "future_information_used": False,
        },
        "checkpoints": {
            str(seed): {
                "bytes": (args.results / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt").stat().st_size,
                "sha256": sha256(args.results / f"SILG_RTFM_TRAINED_STATE_SEED_{seed}.pt"),
            }
            for seed in args.seeds
        },
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "total_wall_seconds": time.perf_counter() - started,
        "answer_leakage": False,
        "pretrained_language_model": False,
        "official_full_baseline_completed": False,
        "capability_progress_claimed": False,
    }
    output = args.results / "SILG_RTFM_MATCHED_EVAL_3SEED.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["all_initial_streams_match"]:
        raise SystemExit("matched-instance contract failed")


if __name__ == "__main__":
    main()
