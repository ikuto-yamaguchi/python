#!/usr/bin/env python3
"""Patch only the local R0 harness to exercise SILG's official sampling defaults.

The pinned SILG source and model architecture remain unchanged.  This patch changes
only the repository-side harness command from the former reduced screening values
to the official RTFM launch defaults and preserves the exact official ``job.tar``
before temporary training directories are removed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--harness",
        type=Path,
        default=Path(__file__).with_name("run_silg_recurrent_smoke.py"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    path = args.harness.resolve()
    before = sha256(path)
    text = path.read_text(encoding="utf-8")

    replacements = [
        ('        "--num_actors", "2",', '        "--num_actors", "30",', "num_actors"),
        ('        "--num_threads", "1",', '        "--num_threads", "4",', "num_threads"),
        ('        "--batch_size", "2",', '        "--batch_size", "24",', "batch_size"),
        ('        "--unroll_length", "20",', '        "--unroll_length", "80",', "unroll_length"),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)

    old_checkpoint = '''    result = {
        "completed": True,
        "official_checkpoint": str(checkpoint),'''
    new_checkpoint = '''    preserved_checkpoint = output_dir / f"SILG_RTFM_OFFICIAL_CHECKPOINT_SEED_{seed}.job.tar"
    shutil.copy2(checkpoint, preserved_checkpoint)
    result = {
        "completed": True,
        "official_checkpoint": str(checkpoint),
        "preserved_checkpoint": str(preserved_checkpoint),
        "preserved_checkpoint_bytes": preserved_checkpoint.stat().st_size,
        "preserved_checkpoint_sha256": sha256(preserved_checkpoint),'''
    text = replace_once(text, old_checkpoint, new_checkpoint, "checkpoint_preservation")

    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")
    after = sha256(path)

    payload = {
        "classification": "official_contract_infrastructure_qualification_patch",
        "harness": str(path),
        "before_sha256": before,
        "after_sha256": after,
        "official_sampling_defaults": {
            "model": "multi",
            "stateful": False,
            "num_actors": 30,
            "batch_size": 24,
            "unroll_length": 80,
            "num_threads": 4,
            "learning_rate": 0.0005,
            "optimizer": "RMSprop",
            "gradient_clip_norm": 40.0,
        },
        "instrumentation_only": ["preserve exact official job.tar before cleanup"],
        "capability_progress_claimed": False,
        "new_intelligence_principle_claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
