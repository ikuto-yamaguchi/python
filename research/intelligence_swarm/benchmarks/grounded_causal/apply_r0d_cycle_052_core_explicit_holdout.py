#!/usr/bin/env python3
"""Idempotently enforce explicit condition-based holdouts in evaluation_contract.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "evaluation_contract.py"
TEST = ROOT / "test_evaluation_contract_explicit_holdout_core.py"
REPORT = ROOT.parents[1] / "governance" / "REPORT_R0D_CYCLE_052.md"

text = TARGET.read_text(encoding="utf-8")

anchor = '''def _truthy(row: dict[str, Any], key: str) -> bool:
    return row.get(key) is True or row.get(key) == 1 or str(row.get(key, False)).lower() == "true"


'''
replacement = '''def _truthy(row: dict[str, Any], key: str) -> bool:
    return row.get(key) is True or row.get(key) == 1 or str(row.get(key, False)).lower() == "true"


def _condition_parts(row: dict[str, Any]) -> set[str]:
    raw = unicodedata.normalize("NFKC", str(row.get("condition", ""))).casefold()
    return {part for part in re.split(r"[+,|\\s]+", raw) if part}


def _declares_holdout(row: dict[str, Any], name: str) -> bool:
    key = f"{name}_holdout"
    return _truthy(row, key) or key in _condition_parts(row)


'''
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "def _declares_holdout(" not in text:
    raise SystemExit("holdout helper anchor not found")

anchor = '''    alias_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
'''
replacement = '''    alias_findings = []
    explicit_holdout_findings = []
    topology, per_seed_splits = defaultdict(set), defaultdict(set)
'''
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "explicit_holdout_findings = []" not in text:
    raise SystemExit("holdout findings anchor not found")

anchor = '''        es, ds = _split_sig(row, "entity_id", "entity_signature"), _split_sig(row, "dynamics_id", "dynamics_signature")
        if es: entities[split].add(es)
        if ds: dynamics[split].add(ds)
'''
replacement = '''        es, ds = _split_sig(row, "entity_id", "entity_signature"), _split_sig(row, "dynamics_id", "dynamics_signature")
        if es: entities[split].add(es)
        if ds: dynamics[split].add(ds)
        for holdout_name, signature in (("entity", es), ("dynamics", ds)):
            if not _declares_holdout(row, holdout_name):
                continue
            finding = {"row": index, "instance_id": iid, "split": split, "condition": condition, "holdout": holdout_name, "signature_present": signature is not None, "signature": signature}
            explicit_holdout_findings.append(finding)
            if split not in EVAL_SPLITS:
                errors.append(f"row {index}: explicit {holdout_name}_holdout must be on a registered evaluation split, found {split!r}")
            if signature is None:
                errors.append(f"row {index}: explicit {holdout_name}_holdout requires {holdout_name}_id or {holdout_name}_signature")
'''
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "explicit {holdout_name}_holdout requires" not in text:
    raise SystemExit("row holdout validation anchor not found")

anchor = '''    holdout = {}
    for name, mapping in (("entity", entities), ("dynamics", dynamics)):
        train_values = mapping.get("train", set())
        for split, values in mapping.items():
            if split == "train": continue
            shared = train_values & values
            holdout[f"{name}:train->{split}"] = {"train_unique": len(train_values), "eval_unique": len(values), "overlap": len(shared)}
            if any(str(r.get("split", "")).lower() == split and _truthy(r, f"{name}_holdout") for r in adapted) and shared:
                errors.append(f"{name} holdout violation train->{split}: {len(shared)} shared signatures")
'''
replacement = '''    holdout = {}
    mappings = {"entity": entities, "dynamics": dynamics}
    for name, mapping in mappings.items():
        train_values = mapping.get("train", set())
        for split, values in mapping.items():
            if split == "train": continue
            shared = train_values & values
            holdout[f"{name}:train->{split}"] = {"train_unique": len(train_values), "eval_unique": len(values), "overlap": len(shared)}
            if any(str(r.get("split", "")).lower() == split and _declares_holdout(r, name) for r in adapted) and shared:
                errors.append(f"{name} holdout violation train->{split}: {len(shared)} shared signatures")
    for finding in explicit_holdout_findings:
        signature = finding.get("signature")
        if signature is not None and signature in mappings[finding["holdout"]].get("train", set()):
            errors.append(f"row {finding['row']}: explicit {finding['holdout']}_holdout reuses a train signature for instance={finding['instance_id']}")
            finding["overlaps_train"] = True
        else:
            finding["overlaps_train"] = False
'''
if anchor in text:
    text = text.replace(anchor, replacement, 1)
elif "explicit_holdout_findings:" not in text:
    raise SystemExit("aggregate holdout validation anchor not found")

old = '"holdout_integrity": holdout, "split_identity_leakage": split_leakage'
new = '"holdout_integrity": holdout, "explicit_holdout_findings": explicit_holdout_findings, "explicit_condition_holdout_required": True, "split_identity_leakage": split_leakage'
if old in text:
    text = text.replace(old, new, 1)
elif '"explicit_condition_holdout_required": True' not in text:
    raise SystemExit("validation evidence anchor not found")

TARGET.write_text(text, encoding="utf-8")

TEST.write_text('''#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("contract", HERE / "evaluation_contract.py")
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

SEEDS = sorted(contract.CANONICAL_SEEDS)


def make_dataset(*, entity_overlap=False, dynamics_overlap=False, missing_entity=False, compound=False):
    rows = []
    condition = "entity_holdout+dynamics_holdout" if compound else "entity_holdout"
    for seed in SEEDS:
        rows.append({
            "instance_id": f"train-{seed}", "domain": "rtfm", "seed": seed,
            "split": "train", "condition": "in_distribution",
            "utterance": f"train utterance {seed}", "state_before": {"x": 0},
            "gold_action": 0, "gold_state_after": {"x": 1},
            "entity_id": f"train-entity-{seed}", "dynamics_id": f"train-dynamics-{seed}",
        })
        row = {
            "instance_id": f"test-{seed}", "domain": "rtfm", "seed": seed,
            "split": "test", "condition": condition,
            "utterance": f"test utterance {seed}", "state_before": {"x": 2},
            "gold_action": 1, "gold_state_after": {"x": 3},
            "dynamics_id": f"train-dynamics-{seed}" if dynamics_overlap else f"heldout-dynamics-{seed}",
        }
        if not missing_entity:
            row["entity_id"] = f"train-entity-{seed}" if entity_overlap else f"heldout-entity-{seed}"
        rows.append(row)
    return rows


clean = contract.validate_dataset(make_dataset())
assert clean["valid"], clean
assert clean["explicit_condition_holdout_required"] is True
assert len(clean["explicit_holdout_findings"]) == 3
assert all(not finding["overlaps_train"] for finding in clean["explicit_holdout_findings"])

entity_bad = contract.validate_dataset(make_dataset(entity_overlap=True))
assert not entity_bad["valid"]
assert any("explicit entity_holdout reuses a train signature" in error for error in entity_bad["errors"])

missing = contract.validate_dataset(make_dataset(missing_entity=True))
assert not missing["valid"]
assert any("explicit entity_holdout requires entity_id or entity_signature" in error for error in missing["errors"])

compound_bad = contract.validate_dataset(make_dataset(dynamics_overlap=True, compound=True))
assert not compound_bad["valid"]
assert any("explicit dynamics_holdout reuses a train signature" in error for error in compound_bad["errors"])
assert len(compound_bad["explicit_holdout_findings"]) == 6

legacy = make_dataset(entity_overlap=True)
for row in legacy:
    if row["split"] == "test":
        row["condition"] = "in_distribution"
        row["entity_holdout"] = True
legacy_bad = contract.validate_dataset(legacy)
assert not legacy_bad["valid"]
assert any("explicit entity_holdout reuses a train signature" in error for error in legacy_bad["errors"])

print("R0 core explicit-condition holdout regression: PASS")
''', encoding="utf-8")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text('''# R0-D Cycle 052 — explicit holdout conditions in the core contract

## Scope

R0 benchmark reproducibility, statistics, and leakage auditing only. No memory, replay, fast weights, sleep, forgetting, architecture, or toy mechanism was added.

## Defect closed

`evaluation_contract.validate_dataset()` previously rejected entity/dynamics overlap only when legacy boolean fields such as `entity_holdout=true` were present. A real-data row could instead declare `condition="entity_holdout"`, omit the boolean, and reuse a train entity signature. Missing signatures on explicitly held-out rows were also not fail-closed in the core path.

## Core contract

- `condition` is parsed into exact `+`, comma, pipe, or whitespace-delimited condition tokens after Unicode NFKC and case folding.
- `entity_holdout` and `dynamics_holdout` declarations are recognized from either the explicit condition token or the legacy boolean.
- Every declared holdout must be on a registered evaluation split.
- Every declared entity/dynamics holdout must provide the corresponding ID or signature.
- Each declared signature is checked per row against the train signature set.
- Compound conditions enforce every declared holdout dimension.
- Findings and overlap status are stored in validation evidence.

Any violation is an `initial_reproduction_failure`. No real R0 bundle, public baseline reproduction, capability progress, novelty, or intelligence principle is claimed.
''', encoding="utf-8")
