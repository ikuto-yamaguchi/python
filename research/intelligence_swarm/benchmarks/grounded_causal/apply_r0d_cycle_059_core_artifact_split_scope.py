#!/usr/bin/env python3
"""Idempotently integrate evaluation split scope into core artifact auditing."""
from pathlib import Path

TARGET = Path(__file__).with_name("evaluation_contract.py")
text = TARGET.read_text(encoding="utf-8")

old_index = '''        try: method, seed, domain, split, condition = str(run["method"]), int(run["seed"]), str(run["domain"]), str(run["split"]), str(run["condition"])
        except (KeyError, TypeError, ValueError) as exc: errors.append(f"run {index}: invalid indexing field {exc}"); continue
        if not domain: errors.append(f"run {index}: domain must be non-empty")
        if not split: errors.append(f"run {index}: split must be non-empty")
        if not condition: errors.append(f"run {index}: condition must be non-empty")
'''
new_index = '''        try:
            method = str(run["method"])
            seed = int(run["seed"])
            domain = str(run["domain"])
            split = unicodedata.normalize("NFKC", str(run["split"])).casefold()
            condition = str(run["condition"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"run {index}: invalid indexing field {exc}")
            continue
        if not domain: errors.append(f"run {index}: domain must be non-empty")
        if not split:
            errors.append(f"run {index}: split must be non-empty")
        elif split not in EVAL_SPLITS:
            errors.append(f"run {index}: artifact split={split!r} is not a registered evaluation split; allowed={sorted(EVAL_SPLITS)}")
        if not condition: errors.append(f"run {index}: condition must be non-empty")
'''

old_return = '''"same_dataset_per_cell_required": True, "canonical_seeds": sorted(CANONICAL_SEEDS), "classification": "reproduced" if not errors else "initial_reproduction_failure"}'''
new_return = '''"same_dataset_per_cell_required": True, "canonical_seeds": sorted(CANONICAL_SEEDS), "allowed_evaluation_splits": sorted(EVAL_SPLITS), "artifact_split_scope_fail_closed": True, "classification": "reproduced" if not errors else "initial_reproduction_failure"}'''

changed = False
if old_index in text:
    text = text.replace(old_index, new_index, 1)
    changed = True
elif "artifact split={split!r} is not a registered evaluation split" not in text:
    raise SystemExit("Cycle 059: expected audit_artifacts indexing block not found")

if old_return in text:
    text = text.replace(old_return, new_return, 1)
    changed = True
elif '"artifact_split_scope_fail_closed": True' not in text:
    raise SystemExit("Cycle 059: expected audit_artifacts return block not found")

if changed:
    TARGET.write_text(text, encoding="utf-8")
    print("Cycle 059 core artifact split-scope patch applied")
else:
    print("Cycle 059 core artifact split-scope patch already applied")
