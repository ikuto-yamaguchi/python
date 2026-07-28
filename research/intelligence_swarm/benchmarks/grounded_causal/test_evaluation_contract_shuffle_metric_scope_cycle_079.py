#!/usr/bin/env python3
"""Focused regression for Cycle 079 shuffle metric scoping."""
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

all_metrics = {"action", "prospective", "inverse"}
assert module._reportable_metrics_for_method("target_label_shuffle", all_metrics) == {"action"}
assert module._reportable_metrics_for_method("outcome_shuffle", all_metrics) == {"prospective"}
assert module._reportable_metrics_for_method("random", all_metrics) == all_metrics
assert module._reportable_metrics_for_method("language_blind", all_metrics) == all_metrics
assert module._reportable_metrics_for_method("state_only", all_metrics) == all_metrics
assert module._reportable_metrics_for_method("correct", all_metrics) == all_metrics

source = MODULE_PATH.read_text(encoding="utf-8")
assert '"shuffle_metric_scope_required": True' in source
assert '"target_label_shuffle": ["action"]' in source
assert '"outcome_shuffle": ["prospective"]' in source
print("Cycle 079 shuffle metric-scope regression passed")
