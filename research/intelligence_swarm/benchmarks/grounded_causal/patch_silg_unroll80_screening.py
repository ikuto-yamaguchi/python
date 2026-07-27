#!/usr/bin/env python3
"""Apply the single official SILG unroll-length factor for R0.1 screening.

Run after ``patch_silg_stateful_screening.py``.  This keeps the already verified
stateful official path and changes only SILG's exposed ``unroll_length`` from
20 to its official default value 80.
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
    old = '        "--unroll_length", "20",'
    new = '        "--unroll_length", "80",'
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one unroll patch anchor, found {count}: {old!r}")
    text = text.replace(old, new, 1)
    TARGET.write_text(text, encoding="utf-8")
    manifest = {
        "classification": "official_unroll_length_single_factor_harness_patch",
        "single_changed_factor": {"name": "unroll_length", "from": 20, "to": 80},
        "stateful_fixed": True,
        "new_mechanism_family": False,
        "file": {
            "path": TARGET.name,
            "before_sha256": before,
            "after_sha256": sha256(TARGET),
        },
    }
    out = ROOT / "SILG_UNROLL80_HARNESS_PATCH.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
