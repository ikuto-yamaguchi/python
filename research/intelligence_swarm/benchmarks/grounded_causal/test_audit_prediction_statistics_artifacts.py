#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from audit_prediction_statistics_artifacts import REQUIRED_METHODS, audit


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def make_bundle(root: Path) -> dict:
    runs = []
    for seed in (1, 7, 19):
        for method in sorted(REQUIRED_METHODS):
            pred = root / f"pred-{method}-{seed}.jsonl"
            write_jsonl(pred, [{
                "instance_id": f"eval-{seed}",
                "method": method,
                "instance_fingerprint": "a" * 64,
                "pred_action": 0,
                "pred_state_after": [0, 1],
                **({
                    "control_source_instance_id": f"eval-{seed}-donor",
                    "control_source_fingerprint": "b" * 64,
                } if method in {"target_label_shuffle", "outcome_shuffle"} else {}),
            }])
            runs.append({
                "method": method,
                "seed": seed,
                "domain": "rtfm",
                "split": "test",
                "condition": "dynamics_holdout",
                "predictions_path": pred.name,
                "predictions_sha256": sha(pred),
            })

    statistics = root / "statistics.json"
    statistics.write_text(json.dumps({
        "valid": True,
        "scores": {
            "valid": True,
            "coverage": {method: {"coverage": 1.0} for method in REQUIRED_METHODS},
            "cells": [{"method": method, "seed": seed} for seed in (1, 7, 19) for method in REQUIRED_METHODS],
            "summary": {method: {"action": 0.5} for method in REQUIRED_METHODS},
            "paired_gaps_vs_correct": {method: {"action": {"mean_gap": 0.0}} for method in REQUIRED_METHODS - {"correct"}},
        },
    }, allow_nan=False), encoding="utf-8")
    return {
        "runs": runs,
        "statistics_path": statistics.name,
        "statistics_sha256": sha(statistics),
    }


def expect_invalid(manifest: dict, root: Path, needle: str) -> None:
    result = audit(manifest, root)
    assert not result["valid"], result
    assert result["classification"] == "initial_reproduction_failure"
    assert any(needle in error for error in result["errors"]), result


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = make_bundle(root)
        clean = audit(manifest, root)
        assert clean["valid"], clean
        assert clean["classification"] == "reproduced"

        tampered = json.loads(json.dumps(manifest))
        path = root / tampered["runs"][0]["predictions_path"]
        path.write_text(path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
        expect_invalid(tampered, root, "prediction checksum mismatch")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = make_bundle(root)
        manifest.pop("statistics_sha256")
        expect_invalid(manifest, root, "statistics evidence fields")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = make_bundle(root)
        run = manifest["runs"][0]
        path = root / run["predictions_path"]
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["method"] = "state_only"
        write_jsonl(path, rows)
        run["predictions_sha256"] = sha(path)
        expect_invalid(manifest, root, "prediction rows must contain only method")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = make_bundle(root)
        stats = root / manifest["statistics_path"]
        report = json.loads(stats.read_text(encoding="utf-8"))
        report["valid"] = False
        report["classification"] = "initial_reproduction_failure"
        stats.write_text(json.dumps(report, allow_nan=False), encoding="utf-8")
        manifest["statistics_sha256"] = sha(stats)
        expect_invalid(manifest, root, "not a valid accepted evaluation")

    print("prediction/statistics artifact audit regression: PASS")


if __name__ == "__main__":
    main()
