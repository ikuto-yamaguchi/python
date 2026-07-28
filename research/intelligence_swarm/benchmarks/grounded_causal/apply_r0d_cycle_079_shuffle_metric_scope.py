#!/usr/bin/env python3
"""Apply Cycle 079 fail-closed metric scoping for shuffle controls."""
from pathlib import Path

CORE = Path(__file__).with_name("evaluation_contract.py")
text = CORE.read_text(encoding="utf-8")

helper = '''\n\ndef _reportable_metrics_for_method(method: str, metrics: set[str]) -> set[str]:
    """Only report metrics whose prediction field is contract-bound for a shuffle control."""
    scoped = set(metrics)
    if method == "target_label_shuffle":
        return scoped & {"action"}
    if method == "outcome_shuffle":
        return scoped & {"prospective"}
    return scoped
'''
anchor = '\n\ndef score(data: list[dict[str, Any]], preds: list[dict[str, Any]]) -> dict[str, Any]:\n'
if helper.strip() not in text:
    if anchor not in text:
        raise SystemExit("Cycle 079 anchor missing: score()")
    text = text.replace(anchor, helper + anchor, 1)

old_loop = '''        for metric in sorted({k for item in items for k in item} & reportable_metrics):
            cell[metric] = statistics.mean(item[metric] for item in items)
'''
new_loop = '''        method_metrics = _reportable_metrics_for_method(method, reportable_metrics)
        for metric in sorted({k for item in items for k in item} & method_metrics):
            cell[metric] = statistics.mean(item[metric] for item in items)
'''
if new_loop not in text:
    if old_loop not in text:
        raise SystemExit("Cycle 079 anchor missing: cell metric loop")
    text = text.replace(old_loop, new_loop, 1)

old_return = '"shuffle_assignment_audit": shuffle_audit, "cells": cells,'
new_return = '"shuffle_assignment_audit": shuffle_audit, "shuffle_metric_scope_required": True, "shuffle_metric_scope": {"target_label_shuffle": ["action"], "outcome_shuffle": ["prospective"]}, "cells": cells,'
if new_return not in text:
    if old_return not in text:
        raise SystemExit("Cycle 079 anchor missing: score audit return")
    text = text.replace(old_return, new_return, 1)

CORE.write_text(text, encoding="utf-8")
print("Cycle 079 shuffle metric scope applied")
