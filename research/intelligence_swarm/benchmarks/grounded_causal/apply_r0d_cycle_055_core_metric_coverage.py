#!/usr/bin/env python3
"""Idempotently enforce complete optional-metric coverage in evaluation_contract.score()."""
from pathlib import Path

PATH = Path(__file__).with_name("evaluation_contract.py")
text = PATH.read_text(encoding="utf-8")

# Cycle 055 rerun marker: the focused regression fixture now exists on the canonical branch.
replacements = [
    (
        '''    errors, seen = [], set(); method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)
    if invalid_dataset_splits:
''',
        '''    errors, seen = [], set(); method_ids, grouped, snapshots, outcomes = defaultdict(set), defaultdict(list), defaultdict(set), defaultdict(dict)
    gold_inverse_ids = {iid for iid in eval_ids if "gold_inverse" in by_id[iid]}
    pred_inverse_ids = defaultdict(set)
    if invalid_dataset_splits:
''',
        'gold_inverse_ids = {iid for iid in eval_ids if "gold_inverse" in by_id[iid]}',
    ),
    (
        '''        if "gold_inverse" in gold and "pred_inverse" in pred: item["inverse"] = float(pred["pred_inverse"] == gold["gold_inverse"])
        grouped[(method, int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))].append(item); outcomes[method][iid] = item
''',
        '''        if "pred_inverse" in pred:
            pred_inverse_ids[method].add(iid)
        if "gold_inverse" in gold and "pred_inverse" in pred:
            item["inverse"] = float(pred["pred_inverse"] == gold["gold_inverse"])
        grouped[(method, int(gold["seed"]), str(gold["domain"]), str(gold["split"]).lower(), str(gold["condition"]))].append(item); outcomes[method][iid] = item
''',
        'pred_inverse_ids[method].add(iid)',
    ),
    (
        '''    absent = required - set(method_ids)
    if absent: errors.append(f"missing required methods: {sorted(absent)}")
    shuffle_errors, shuffle_audit = _validate_shuffle_assignments(preds, by_id, eval_ids); errors.extend(shuffle_errors)
    cells = []
''',
        '''    absent = required - set(method_ids)
    if absent: errors.append(f"missing required methods: {sorted(absent)}")
    inverse_metric_complete = False
    if gold_inverse_ids and gold_inverse_ids != eval_ids:
        errors.append(f"gold_inverse must cover all evaluation instances or none; found {len(gold_inverse_ids)}/{len(eval_ids)}")
    elif not gold_inverse_ids:
        leaking_methods = sorted(method for method, ids in pred_inverse_ids.items() if ids)
        if leaking_methods:
            errors.append(f"pred_inverse supplied without any evaluation gold_inverse by methods {leaking_methods}")
    else:
        inverse_metric_complete = True
        for method in sorted(required):
            ids = pred_inverse_ids.get(method, set())
            missing_inverse, extra_inverse = eval_ids - ids, ids - eval_ids
            if missing_inverse:
                inverse_metric_complete = False
                errors.append(f"method {method}: incomplete pred_inverse coverage ({len(missing_inverse)} missing)")
            if extra_inverse:
                inverse_metric_complete = False
                errors.append(f"method {method}: pred_inverse outside evaluation set ({len(extra_inverse)} extra)")
    shuffle_errors, shuffle_audit = _validate_shuffle_assignments(preds, by_id, eval_ids); errors.extend(shuffle_errors)
    reportable_metrics = {"prospective", "action"} | ({"inverse"} if inverse_metric_complete else set())
    cells = []
''',
        'inverse_metric_complete = False',
    ),
    (
        '''        for metric in sorted({k for item in items for k in item}): cell[metric] = statistics.mean(item[metric] for item in items if metric in item)
        cells.append(cell)
    metrics = sorted({k for c in cells for k in c if k in {"prospective", "action", "inverse"}}); summary, methods = defaultdict(dict), set(method_ids)
''',
        '''        for metric in sorted({k for item in items for k in item} & reportable_metrics):
            cell[metric] = statistics.mean(item[metric] for item in items)
        cells.append(cell)
    metrics = sorted(reportable_metrics); summary, methods = defaultdict(dict), set(method_ids)
''',
        'metrics = sorted(reportable_metrics)',
    ),
]

for old, new, marker in replacements:
    if marker in text:
        continue
    if old not in text:
        raise SystemExit(f"patch anchor not found for {marker}")
    text = text.replace(old, new, 1)

old = '"finite_prediction_values_checked": True, "valid_action_schema_checked": True, "shuffle_assignment_audit": shuffle_audit, "cells": cells,'
new = '"finite_prediction_values_checked": True, "valid_action_schema_checked": True, "optional_metric_coverage_required": True, "inverse_metric_complete": inverse_metric_complete, "gold_inverse_coverage": {"expected": len(eval_ids), "present": len(gold_inverse_ids)}, "pred_inverse_coverage": {method: {"expected": len(eval_ids), "present": len(pred_inverse_ids.get(method, set()))} for method in sorted(REQUIRED_METHODS)}, "shuffle_assignment_audit": shuffle_audit, "cells": cells,'
if '"optional_metric_coverage_required": True' not in text:
    if old not in text:
        raise SystemExit("score evidence anchor not found")
    text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8")
print("R0 core optional metric coverage patch applied")
