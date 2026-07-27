#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def row(instance_id: str, seed: int, split: str, condition: str, entity_id: object, utterance: str) -> dict:
    return {
        "instance_id": instance_id,
        "domain": "r0-domain",
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": utterance,
        "state_before": {"x": seed},
        "gold_action": 0,
        "gold_state_after": {"x": seed + 1},
        "entity_id": entity_id,
    }


def dataset(train_identity: object, eval_identity: object) -> list[dict]:
    rows = []
    for seed in (1, 7, 19):
        rows.append(row(f"train-{seed}", seed, "train", "in_distribution", train_identity, f"train utterance {seed}"))
        rows.append(row(f"test-{seed}", seed, "test", "entity_holdout", eval_identity, f"test utterance {seed}"))
    return rows


def assert_alias(left: object, right: object) -> None:
    a = contract._split_sig({"entity_id": left}, "entity_id", "entity_signature")
    b = contract._split_sig({"entity_id": right}, "entity_id", "entity_signature")
    assert a == b, (left, right, a, b)


def main() -> None:
    assert_alias("Goblin", "ＧＯＢＬＩＮ")
    assert_alias("dark knight", "dark\u200bknight")
    assert_alias(7, "７")
    assert_alias({"Mode": "CHASE", "rate": "１"}, {"ｍｏｄｅ": "chase", "rate": 1})

    report = contract.validate_dataset(dataset("Goblin", "ＧＯＢＬＩＮ"))
    assert not report["valid"]
    assert any("entity holdout violation" in error or "reuses a train signature" in error for error in report["errors"])
    assert report["normalized_holdout_identity_required"] is True

    clean = contract.validate_dataset(dataset("Goblin", "Orc"))
    assert clean["valid"], clean["errors"]


if __name__ == "__main__":
    main()
