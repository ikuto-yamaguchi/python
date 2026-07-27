#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

CORE = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", CORE)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def row(seed: int, split: str, domain: str = "RTFM", condition: str = "in_distribution") -> dict:
    suffix = f"{seed}-{split}-{domain}-{condition}"
    return {
        "instance_id": suffix,
        "domain": domain,
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": f"utterance-{suffix}",
        "state_before": {"x": seed},
        "gold_action": 0,
        "gold_state_after": {"x": seed + 1},
        "entity_id": f"entity-{suffix}",
        "dynamics_id": f"dynamics-{suffix}",
        "episode_id": f"episode-{suffix}",
        "episode_seed": f"episode-seed-{suffix}",
        "observation_fingerprint": f"observation-{suffix}",
    }


def bundle() -> list[dict]:
    return [row(seed, split) for seed in (1, 7, 19) for split in ("train", "test")]


def assert_has(audit: dict, fragment: str) -> None:
    assert any(fragment in error for error in audit["errors"]), audit["errors"]


def test_cell_key_normalizes_domain_and_condition() -> None:
    a = row(1, "test", "ＲＴＦＭ", "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT")
    b = row(1, "test", "rtfm", "entity_holdout+dynamics_holdout")
    assert contract._cell_key(a) == contract._cell_key(b)


def test_domain_alias_collision_is_rejected() -> None:
    rows = bundle()
    rows[1]["domain"] = "ＲＴＦＭ"
    audit = contract.validate_dataset(rows)
    assert not audit["valid"]
    assert_has(audit, "domain label normalization collision")
    assert audit["normalized_cell_identity_required"] is True


def test_condition_order_alias_collision_is_rejected() -> None:
    rows = bundle()
    rows[1]["condition"] = "entity_holdout+dynamics_holdout"
    rows[3]["condition"] = "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT"
    audit = contract.validate_dataset(rows)
    assert not audit["valid"]
    assert_has(audit, "condition label normalization collision")


def test_canonical_bundle_preserves_domain_local_coverage() -> None:
    audit = contract.validate_dataset(bundle())
    assert audit["valid"], audit["errors"]
    assert audit["normalized_cell_identity_required"] is True
    assert audit["canonical_domain_labels"] == {"rtfm": ["RTFM"]}
    assert audit["canonical_condition_labels"] == {"indistribution": ["in_distribution"]}


def main() -> None:
    test_cell_key_normalizes_domain_and_condition()
    test_domain_alias_collision_is_rejected()
    test_condition_order_alias_collision_is_rejected()
    test_canonical_bundle_preserves_domain_local_coverage()
    print("Cycle 072 normalized cell core regressions passed")


if __name__ == "__main__":
    main()
