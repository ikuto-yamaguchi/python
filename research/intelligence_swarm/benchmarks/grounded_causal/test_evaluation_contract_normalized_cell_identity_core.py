#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def row(instance_id: str, seed: int, split: str, domain: str, condition: str) -> dict:
    return {
        "instance_id": instance_id,
        "domain": domain,
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": f"utterance-{instance_id}",
        "state_before": {"x": instance_id},
        "gold_action": 0,
        "gold_state_after": {"x": f"after-{instance_id}"},
        "model_input_fields": ["utterance", "state_before"],
        "model_input": {"utterance": f"utterance-{instance_id}", "state_before": {"x": instance_id}},
    }


def canonical_dataset() -> list[dict]:
    rows = []
    for seed in sorted(contract.CANONICAL_SEEDS):
        rows.append(row(f"train-{seed}", seed, "train", "rtfm", "in_distribution"))
        rows.append(row(f"eval-{seed}", seed, "test", "rtfm", "entity_holdout"))
    return rows


def main() -> None:
    assert contract.canonical_domain_label("ＲＴＦＭ") == contract.canonical_domain_label("rtfm")
    assert contract.canonical_condition_label("DYNAMICS_HOLDOUT | ENTITY_HOLDOUT") == contract.canonical_condition_label("entity_holdout+dynamics_holdout")

    audit = contract.validate_dataset(canonical_dataset())
    assert audit["valid"], audit["errors"]
    assert audit["normalized_cell_identity_required"] is True

    domain_alias = canonical_dataset()
    domain_alias[1]["domain"] = "ＲＴＦＭ"
    audit = contract.validate_dataset(domain_alias)
    assert not audit["valid"]
    assert audit["classification"] if "classification" in audit else True
    assert any("domain labels collide after canonicalization" in error for error in audit["errors"])

    condition_alias = canonical_dataset()
    condition_alias[1]["condition"] = "ENTITY_HOLDOUT"
    audit = contract.validate_dataset(condition_alias)
    assert not audit["valid"]
    assert any("condition labels collide after canonicalization" in error for error in audit["errors"])

    left = row("a", 1, "test", "ＲＴＦＭ", "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT")
    right = row("b", 1, "TEST", "rtfm", "entity_holdout+dynamics_holdout")
    assert contract._cell_key(left) == contract._cell_key(right)

    fp_left = copy.deepcopy(left)
    fp_right = copy.deepcopy(left)
    fp_right["domain"] = "rtfm"
    fp_right["condition"] = "entity_holdout+dynamics_holdout"
    assert contract.instance_fingerprint(fp_left) == contract.instance_fingerprint(fp_right)

    print("Cycle 073 normalized cell identity regressions passed")


if __name__ == "__main__":
    main()
