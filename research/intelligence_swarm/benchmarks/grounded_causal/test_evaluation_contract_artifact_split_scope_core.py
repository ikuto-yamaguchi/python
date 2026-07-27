#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from evaluation_contract import CANONICAL_SEEDS, REQUIRED_METHODS, audit_artifacts


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(root: Path, split: str) -> dict:
    data = root / "dataset.jsonl"
    data.write_text('{"instance_id":"x"}\n', encoding="utf-8")
    data_sha = sha256(data)
    runs = []
    for method in sorted(REQUIRED_METHODS):
        for seed in sorted(CANONICAL_SEEDS):
            model = root / f"model-{method}-{seed}.bin"
            log = root / f"raw-{method}-{seed}.log"
            model.write_bytes(f"model:{method}:{seed}".encode())
            log.write_text(f"run {method} {seed}\n", encoding="utf-8")
            runs.append({
                "method": method,
                "seed": seed,
                "domain": "rtfm",
                "split": split,
                "condition": "entity_holdout",
                "model_bytes": model.stat().st_size,
                "peak_rss_bytes": 4096,
                "training_wall_seconds": 1.0,
                "cpu_inference_ms_per_item": 0.1,
                "raw_log_path": log.name,
                "raw_log_sha256": sha256(log),
                "model_path": model.name,
                "model_sha256": sha256(model),
                "data_path": data.name,
                "data_sha256": data_sha,
                "code_commit": "a" * 40,
            })
    return {"runs": runs}


def check(split: str, expected_valid: bool) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = audit_artifacts(build_manifest(root, split), root)
        assert result["valid"] is expected_valid, (split, result)
        assert result["classification"] == ("reproduced" if expected_valid else "initial_reproduction_failure")
        assert result["artifact_split_scope_fail_closed"] is True
        assert result["allowed_evaluation_splits"] == ["eval", "test", "valid", "validation"]
        if not expected_valid:
            assert any("not a registered evaluation split" in error for error in result["errors"]), result


def main() -> None:
    check("test", True)
    check("VALIDATION", True)
    check("train", False)
    check("debug", False)
    check("posthoc", False)
    print("Cycle 059 core artifact split-scope regressions passed")


if __name__ == "__main__":
    main()
