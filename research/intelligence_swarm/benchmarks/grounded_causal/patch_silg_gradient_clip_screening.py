#!/usr/bin/env python3
"""Apply the single R0.1 learner factor: gradient clip 40.0 -> 10.0.

The official pinned SILG learner hard-codes ``clip_grad_norm_(..., 40.0)``.
This patch changes only that threshold in the installed pinned source. Model,
statefulness, unroll, optimizer defaults, frames, seeds, split and controls stay
fixed. It is not a new mechanism family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    target = args.silg_root / "run_exp.py"
    text = target.read_text(encoding="utf-8")
    before = sha256(target)
    old = "nn.utils.clip_grad_norm_(model.parameters(), 40.0)"
    new = "nn.utils.clip_grad_norm_(model.parameters(), 10.0)"
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one official gradient-clip anchor, found {count}")
    if new in text:
        raise RuntimeError("gradient-clipping factor is already present")
    text = text.replace(old, new, 1)
    target.write_text(text, encoding="utf-8")

    manifest = {
        "classification": "learner_gradient_clipping_single_factor_source_patch",
        "single_changed_factor": {"name": "gradient_clip_norm", "from": 40.0, "to": 10.0},
        "official_source_commit": "2af07578e1264029a240fcfb78d4ac0aea16f5de",
        "stateful_fixed": True,
        "unroll_length_fixed": 80,
        "learning_rate_fixed": "official default",
        "new_mechanism_family": False,
        "file": {
            "path": str(target),
            "before_sha256": before,
            "after_sha256": sha256(target),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
