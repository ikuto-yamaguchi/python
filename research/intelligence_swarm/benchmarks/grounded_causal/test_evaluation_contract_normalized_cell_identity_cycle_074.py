#!/usr/bin/env python3
from copy import deepcopy

from evaluation_contract import (
    _cell_key,
    canonical_condition,
    canonical_domain,
    instance_fingerprint,
    validate_dataset,
)


def row(i: str, seed: int, split: str, condition: str, domain: str = "rtfm") -> dict:
    return {
        "instance_id": i,
        "domain": domain,
        "seed": seed,
        "split": split,
        "condition": condition,
        "utterance": f"utterance-{i}",
        "state_before": {"x": i},
        "gold_action": 0,
        "gold_state_after": {"x": i, "done": True},
        "entity_id": f"entity-{i}",
        "dynamics_id": f"dynamics-{i}",
    }


def canonical_bundle() -> list[dict]:
    rows = []
    for seed in (1, 7, 19):
        rows.append(row(f"train-{seed}", seed, "train", "in_distribution"))
        rows.append(row(f"eval-{seed}", seed, "test", "entity_holdout"))
    return rows


def main() -> None:
    assert canonical_domain("ＲＴＦＭ") == canonical_domain("r t f m") == "rtfm"
    assert canonical_condition("DYNAMICS_HOLDOUT | ENTITY_HOLDOUT") == "dynamics_holdout+entity_holdout"
    assert canonical_condition("entity_holdout+dynamics_holdout") == "dynamics_holdout+entity_holdout"

    a = row("x", 1, "test", "entity_holdout+dynamics_holdout", "RTFM")
    b = deepcopy(a)
    b["domain"] = "ＲＴＦＭ"
    b["condition"] = "DYNAMICS_HOLDOUT | ENTITY_HOLDOUT"
    assert _cell_key(a) == _cell_key(b)
    assert instance_fingerprint(a) == instance_fingerprint(b)

    valid = validate_dataset(canonical_bundle())
    assert valid["valid"], valid["errors"]
    assert valid["normalized_cell_identity_required"] is True

    domain_alias = canonical_bundle()
    domain_alias[1]["domain"] = "ＲＴＦＭ"
    audit = validate_dataset(domain_alias)
    assert not audit["valid"]
    assert audit["domain_label_collisions"]
    assert any("domain labels collide" in error for error in audit["errors"])

    condition_alias = canonical_bundle()
    condition_alias[1]["condition"] = "ENTITY_HOLDOUT"
    condition_alias[3]["condition"] = "ｅｎｔｉｔｙ＿ｈｏｌｄｏｕｔ"
    audit = validate_dataset(condition_alias)
    assert not audit["valid"]
    assert audit["condition_label_collisions"]
    assert any("condition labels collide" in error for error in audit["errors"])


if __name__ == "__main__":
    main()
