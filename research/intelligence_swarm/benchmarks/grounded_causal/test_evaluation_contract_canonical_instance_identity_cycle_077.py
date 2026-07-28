#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract_cycle_077", MODULE_PATH)
assert spec and spec.loader
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def row(instance_id: str, *, split: str = "test") -> dict:
    return {
        "instance_id": instance_id,
        "domain": "rtfm",
        "seed": 1,
        "split": split,
        "condition": "entity_holdout",
        "utterance": f"utterance-{instance_id}",
        "state_before": {"x": 0},
        "gold_action": 0,
        "gold_state_after": {"x": 1},
        "entity_id": f"entity-{instance_id}",
    }


def main() -> None:
    assert contract.canonical_instance_id("Episode １") == contract.canonical_instance_id("ｅｐｉｓｏｄｅ1")
    assert contract.canonical_instance_id("\u200b\t") == ""

    collision = contract.validate_dataset([row("Episode １"), row("ｅｐｉｓｏｄｅ1")])
    assert not collision["valid"]
    assert collision["canonical_instance_identity_required"] is True
    assert collision["instance_id_collisions"]
    assert any("instance_id aliases collide" in error for error in collision["errors"])

    empty = contract.validate_dataset([row("\u200b\t")])
    assert not empty["valid"]
    assert any("instance_id must be non-empty after canonicalization" in error for error in empty["errors"])

    dataset = [row("Episode １")]
    prediction = [{
        "instance_id": "ｅｐｉｓｏｄｅ1",
        "method": "correct",
        "instance_fingerprint": contract.instance_fingerprint(dataset[0]),
        "pred_action": 0,
        "pred_state_after": {"x": 1},
    }]
    scored = contract.score(dataset, prediction)
    assert not scored["valid"]
    assert scored["statistics_emitted"] is False
    assert scored["cells"] == []
    assert scored["summary"] == {}
    assert scored["paired_gaps_vs_correct"] == {}
    assert any("must exactly match dataset ID" in error for error in scored["errors"])
    assert scored["classification"] == "initial_reproduction_failure"


if __name__ == "__main__":
    main()
    print("cycle 077 canonical instance identity regression: PASS")
