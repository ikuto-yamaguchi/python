#!/usr/bin/env python3
from __future__ import annotations

import audit_explicit_holdout_condition as target


SEEDS = (1, 7, 19)


def row(i: str, seed: int, split: str, condition: str, entity: str | None, dynamics: str | None) -> dict:
    value = {
        "instance_id": i,
        "domain": "rtfm",
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": f"instruction {i}",
        "state_before": {"room": i},
        "gold_action": 0,
        "gold_state_after": {"room": i, "done": True},
    }
    if entity is not None:
        value["entity_signature"] = entity
    if dynamics is not None:
        value["dynamics_signature"] = dynamics
    return value


def bundle(entity_eval: str = "entity-eval", dynamics_eval: str = "dyn-eval") -> list[dict]:
    rows: list[dict] = []
    for seed in SEEDS:
        rows.append(row(f"train-{seed}", seed, "train", "in_distribution", "entity-train", "dyn-train"))
        rows.append(row(f"entity-{seed}", seed, "test", "entity_holdout", entity_eval, "dyn-train"))
        rows.append(row(f"dynamics-{seed}", seed, "test", "dynamics_holdout", "entity-train", dynamics_eval))
    return rows


def test_explicit_condition_without_boolean_flags_is_enforced() -> None:
    result = target.audit(bundle(entity_eval="entity-train"))
    assert result["valid"] is False
    assert result["classification"] == "initial_reproduction_failure"
    assert any("entity_holdout" in error and "overlap" in error for error in result["errors"])


def test_dynamics_condition_without_boolean_flags_is_enforced() -> None:
    result = target.audit(bundle(dynamics_eval="dyn-train"))
    assert result["valid"] is False
    assert any("dynamics_holdout" in error and "overlap" in error for error in result["errors"])


def test_held_out_signature_is_required() -> None:
    rows = bundle()
    rows[1].pop("entity_signature")
    result = target.audit(rows)
    assert result["valid"] is False
    assert any("lack entity_id/entity_signature" in error for error in result["errors"])


def test_combined_condition_tokens_are_enforced() -> None:
    rows = bundle()
    rows[1]["condition"] = "entity_holdout+dynamics_holdout"
    rows[1]["entity_signature"] = "entity-train"
    rows[1]["dynamics_signature"] = "dyn-train"
    result = target.audit(rows)
    assert result["valid"] is False
    assert any("entity_holdout" in error for error in result["errors"])
    assert any("dynamics_holdout" in error for error in result["errors"])


def test_disjoint_explicit_holdouts_pass() -> None:
    result = target.audit(bundle())
    assert result["valid"] is True
    assert result["checks"]["entity"]["held_out_rows"] == 3
    assert result["checks"]["dynamics"]["held_out_rows"] == 3


if __name__ == "__main__":
    test_explicit_condition_without_boolean_flags_is_enforced()
    test_dynamics_condition_without_boolean_flags_is_enforced()
    test_held_out_signature_is_required()
    test_combined_condition_tokens_are_enforced()
    test_disjoint_explicit_holdouts_pass()
    print("ok")
