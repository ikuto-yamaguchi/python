#!/usr/bin/env python3
"""Apply one learner-optimization factor for R0.1 SILG screening.

Run after the verified stateful and unroll-80 patches.  This keeps model,
statefulness, unroll, frames, seeds, split and controls fixed, and adds an
explicit lower learning rate to test whether the highly oscillatory policy
loss is caused by an overly aggressive optimizer step size.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "run_silg_recurrent_smoke.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    before = sha256(TARGET)
    anchor = '        "--entropy_cost", str(entropy_cost),\n'
    insertion = anchor + '        "--learning_rate", "0.0001",\n'
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"expected one learning-rate patch anchor, found {count}: {anchor!r}")
    if '"--learning_rate", "0.0001"' in text:
        raise RuntimeError("learning-rate factor is already present")
    text = text.replace(anchor, insertion, 1)
    TARGET.write_text(text, encoding="utf-8")
    manifest = {
        "classification": "learner_learning_rate_single_factor_harness_patch",
        "single_changed_factor": {
            "name": "learning_rate",
            "from": "official/default implicit value",
            "to": 0.0001,
        },
        "stateful_fixed": True,
        "unroll_length_fixed": 80,
        "new_mechanism_family": False,
        "evidence": "unroll-80 learner logs show large sign-changing policy-gradient and total-loss oscillations through the final updates",
        "file": {
            "path": TARGET.name,
            "before_sha256": before,
            "after_sha256": sha256(TARGET),
        },
    }
    out = ROOT / "SILG_LEARNING_RATE_HARNESS_PATCH.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
