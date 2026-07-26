#!/usr/bin/env python3
"""Apply the single official SILG --stateful factor to the existing R0.1 harness.

This does not introduce a new architecture. It activates SILG's own parser flag,
which instantiates the LSTM core already present in model.multi.Model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PATCHES = {
    "run_silg_recurrent_smoke.py": [
        (
            '        "--model", "multi",\n        "--xpid", xpid,',
            '        "--model", "multi",\n        "--stateful",\n        "--xpid", xpid,',
        ),
        (
            'flags.model = "multi"; flags.disable_cuda = True',
            'flags.model = "multi"; flags.stateful = True; flags.disable_cuda = True',
        ),
    ],
    "run_silg_matched_eval.py": [
        (
            '    flags.model = "multi"\n    flags.disable_cuda = True',
            '    flags.model = "multi"\n    flags.stateful = True\n    flags.disable_cuda = True',
        ),
    ],
    "run_silg_policy_diagnostics.py": [
        (
            '    flags.model = "multi"\n    flags.disable_cuda = True',
            '    flags.model = "multi"\n    flags.stateful = True\n    flags.disable_cuda = True',
        ),
    ],
    "audit_silg_official_eval_parity.py": [
        (
            '    flags.model = "multi"\n    flags.disable_cuda = True',
            '    flags.model = "multi"\n    flags.stateful = True\n    flags.disable_cuda = True',
        ),
    ],
}


def main() -> None:
    manifest = {
        "classification": "official_stateful_flag_harness_patch",
        "single_changed_factor": {"name": "stateful", "from": False, "to": True},
        "new_mechanism_family": False,
        "files": {},
    }
    for name, replacements in PATCHES.items():
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        before = sha256(path)
        for old, new in replacements:
            count = text.count(old)
            if count != 1:
                raise RuntimeError(f"{name}: expected one patch anchor, found {count}: {old!r}")
            text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
        manifest["files"][name] = {"before_sha256": before, "after_sha256": sha256(path)}
    out = ROOT / "SILG_STATEFUL_HARNESS_PATCH.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
