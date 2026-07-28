#!/usr/bin/env python3
"""Focused regression for exact JSON-integer seed identity."""
from pathlib import Path
import importlib.util

MODULE = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE)
ec = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ec)


def rows():
    out = []
    for seed in (1, 7, 19):
        for split in ("train", "test"):
            out.append({
                "instance_id": f"{split}-{seed}",
                "domain": "rtfm",
                "seed": seed,
                "split": split,
                "condition": "in_distribution",
                "utterance": f"{split} utterance {seed}",
                "state_before": [seed, 0],
                "gold_action": 0,
                "gold_state_after": [seed, 1],
            })
    return out


assert ec.canonical_seed(1) == 1
for bad in (True, False, 1.0, 1.9, "1", "１", None):
    try:
        ec.canonical_seed(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"seed alias unexpectedly accepted: {bad!r}")

valid = ec.validate_dataset(rows())
assert valid["valid"], valid["errors"]
assert valid["canonical_seed_identity_required"] is True

for bad in (True, 1.0, 1.9, "1", "１"):
    candidate = rows()
    candidate[0]["seed"] = bad
    audit = ec.validate_dataset(candidate)
    assert not audit["valid"], bad
    assert any("seed must be a JSON integer" in error for error in audit["errors"]), audit["errors"]

# Invalid seed identities must remain fail-closed rather than crashing cell/fingerprint code.
assert ec._cell_key({"seed": True, "domain": "rtfm", "split": "test", "condition": "in_distribution"})[0] == -1
assert ec.instance_fingerprint(rows()[0])
print("Cycle 083 strict seed identity regression passed")
