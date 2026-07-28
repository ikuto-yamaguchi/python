#!/usr/bin/env python3
"""Focused regressions for normalized completed-trajectory split leakage."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py"
spec = spec_from_file_location("evaluation_contract", CORE)
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def dataset():
    rows = []
    for seed in (1, 7, 19):
        for split in ("train", "test"):
            suffix = f"{seed}-{split}"
            rows.append({
                "instance_id": suffix,
                "domain": "rtfm",
                "seed": seed,
                "split": split,
                "condition": "in_distribution",
                "utterance": f"utterance-{suffix}",
                "state_before": {"step": seed, "split": split},
                "gold_action": 0,
                "gold_state_after": {"done": False, "id": suffix},
                "episode_id": f"episode-{suffix}",
                "episode_seed": f"episode-seed-{suffix}",
                "observation_fingerprint": f"observation-{suffix}",
            })
    return rows


def assert_failure(rows, field):
    result = module.validate_dataset(rows)
    assert not result["valid"], result
    assert any(field in error and "leakage" in error for error in result["errors"]), result["errors"]
    assert result["normalized_trajectory_identity_required"] is True
    assert "NFKC" in result["trajectory_identity_normalization"]


def main():
    clean = module.validate_dataset(dataset())
    assert clean["valid"], clean

    rows = deepcopy(dataset())
    train = next(row for row in rows if row["seed"] == 1 and row["split"] == "train")
    test = next(row for row in rows if row["seed"] == 1 and row["split"] == "test")
    train["episode_id"] = "Episode Alpha"
    test["episode_id"] = "ＥＰＩＳＯＤＥ\u200bＡＬＰＨＡ"
    assert_failure(rows, "episode_id")

    rows = deepcopy(dataset())
    train = next(row for row in rows if row["seed"] == 7 and row["split"] == "train")
    test = next(row for row in rows if row["seed"] == 7 and row["split"] == "test")
    train["episode_seed"] = 7
    test["episode_seed"] = "７"
    assert_failure(rows, "episode_seed")

    rows = deepcopy(dataset())
    train = next(row for row in rows if row["seed"] == 19 and row["split"] == "train")
    test = next(row for row in rows if row["seed"] == 19 and row["split"] == "test")
    train["observation_fingerprint"] = {"Frame": "Final State", "index": 1}
    test["observation_fingerprint"] = {"ｆｒａｍｅ": "FINAL\u200bSTATE", "index": "１"}
    assert_failure(rows, "observation_fingerprint")


if __name__ == "__main__":
    main()
