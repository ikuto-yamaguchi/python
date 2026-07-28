#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("contract", HERE / "evaluation_contract.py")
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

SEEDS = sorted(contract.CANONICAL_SEEDS)


def make_dataset(*, entity_overlap=False, dynamics_overlap=False, missing_entity=False, compound=False):
    rows = []
    condition = "entity_holdout+dynamics_holdout" if compound else "entity_holdout"
    for seed in SEEDS:
        rows.append({
            "instance_id": f"train-{seed}", "domain": "rtfm", "seed": seed,
            "split": "train", "condition": "in_distribution",
            "utterance": f"train utterance {seed}", "state_before": {"x": 0},
            "gold_action": 0, "gold_state_after": {"x": 1},
            "entity_id": f"train-entity-{seed}", "dynamics_id": f"train-dynamics-{seed}",
        })
        row = {
            "instance_id": f"test-{seed}", "domain": "rtfm", "seed": seed,
            "split": "test", "condition": condition,
            "utterance": f"test utterance {seed}", "state_before": {"x": 2},
            "gold_action": 1, "gold_state_after": {"x": 3},
            "dynamics_id": f"train-dynamics-{seed}" if dynamics_overlap else f"heldout-dynamics-{seed}",
        }
        if not missing_entity:
            row["entity_id"] = f"train-entity-{seed}" if entity_overlap else f"heldout-entity-{seed}"
        rows.append(row)
    return rows


clean = contract.validate_dataset(make_dataset())
assert clean["valid"], clean
assert clean["explicit_condition_holdout_required"] is True
assert len(clean["explicit_holdout_findings"]) == 3
assert all(not finding["overlaps_train"] for finding in clean["explicit_holdout_findings"])

entity_bad = contract.validate_dataset(make_dataset(entity_overlap=True))
assert not entity_bad["valid"]
assert any("explicit entity_holdout reuses a train signature" in error for error in entity_bad["errors"])

missing = contract.validate_dataset(make_dataset(missing_entity=True))
assert not missing["valid"]
assert any("explicit entity_holdout requires entity_id or entity_signature" in error for error in missing["errors"])

compound_bad = contract.validate_dataset(make_dataset(dynamics_overlap=True, compound=True))
assert not compound_bad["valid"]
assert any("explicit dynamics_holdout reuses a train signature" in error for error in compound_bad["errors"])
assert len(compound_bad["explicit_holdout_findings"]) == 6

legacy = make_dataset(entity_overlap=True)
for row in legacy:
    if row["split"] == "test":
        row["condition"] = "in_distribution"
        row["entity_holdout"] = True
legacy_bad = contract.validate_dataset(legacy)
assert not legacy_bad["valid"]
assert any("explicit entity_holdout reuses a train signature" in error for error in legacy_bad["errors"])

print("R0 core explicit-condition holdout regression: PASS")
