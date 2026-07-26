#!/usr/bin/env python3
"""Idempotently integrate canonical split scope into evaluation_contract.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "evaluation_contract.py"
TEST = ROOT / "test_evaluation_contract_split_scope_core.py"
REPORT = ROOT.parents[1] / "governance" / "REPORT_R0D_CYCLE_050.md"

text = TARGET.read_text(encoding="utf-8")

old = 'CANONICAL_SEEDS = {1, 7, 19}\nEVAL_SPLITS = {"test", "eval", "validation", "valid"}\n'
new = 'CANONICAL_SEEDS = {1, 7, 19}\nTRAIN_SPLITS = {"train"}\nEVAL_SPLITS = {"test", "eval", "validation", "valid"}\nALLOWED_SPLITS = TRAIN_SPLITS | EVAL_SPLITS\n'
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("split constants anchor not found")

old = '        if not split:\n            errors.append(f"row {index}: split must be non-empty")\n        if not condition:\n'
new = '        if not split:\n            errors.append(f"row {index}: split must be non-empty")\n        elif split not in ALLOWED_SPLITS:\n            errors.append(f"row {index}: unregistered split={split!r}; allowed={sorted(ALLOWED_SPLITS)}")\n        if not condition:\n'
if old in text:
    text = text.replace(old, new, 1)
elif 'unregistered split=' not in text:
    raise SystemExit("dataset split validation anchor not found")

old = '    adapted = adapt_dataset(data); by_id = {str(r["instance_id"]): r for r in adapted}; eval_ids = {i for i, r in by_id.items() if str(r["split"]).lower() != "train"}\n'
new = '    adapted = adapt_dataset(data); by_id = {str(r["instance_id"]): r for r in adapted}; eval_ids = {i for i, r in by_id.items() if str(r["split"]).lower() in EVAL_SPLITS}\n'
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("score eval_ids anchor not found")

old = '        if str(gold["split"]).lower() == "train": errors.append(f"prediction row {index}: prediction supplied for train instance={iid}"); continue\n'
new = '        gold_split = str(gold["split"]).lower()\n        if gold_split not in EVAL_SPLITS: errors.append(f"prediction row {index}: prediction supplied for non-evaluation split={gold_split!r} instance={iid}"); continue\n'
if old in text:
    text = text.replace(old, new, 1)
elif 'prediction supplied for non-evaluation split=' not in text:
    raise SystemExit("prediction split guard anchor not found")

old = '"alias_normalized_leakage_required": True}\n\n\ndef _mean_ci'
new = '"alias_normalized_leakage_required": True, "registered_split_scope_required": True, "allowed_train_splits": sorted(TRAIN_SPLITS), "allowed_evaluation_splits": sorted(EVAL_SPLITS)}\n\n\ndef _mean_ci'
if old in text:
    text = text.replace(old, new, 1)
elif '"registered_split_scope_required": True' not in text:
    raise SystemExit("validate result anchor not found")

old = '"internal_metrics_do_not_count": True}}\n\n\ndef audit_artifacts'
new = '"internal_metrics_do_not_count": True, "registered_split_scope_required": True}, "allowed_evaluation_splits": sorted(EVAL_SPLITS)}\n\n\ndef audit_artifacts'
if old in text:
    text = text.replace(old, new, 1)
elif '"allowed_evaluation_splits": sorted(EVAL_SPLITS)' not in text[text.find('def score'):]:
    raise SystemExit("score result anchor not found")

TARGET.write_text(text, encoding="utf-8")

TEST.write_text('''#!/usr/bin/env python3
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("contract", HERE / "evaluation_contract.py")
contract = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(contract)


def row(i, seed, split):
    return {
        "instance_id": f"{split}-{seed}-{i}", "domain": "rtfm", "seed": seed,
        "split": split, "condition": "in_distribution", "utterance": f"u-{split}-{seed}-{i}",
        "state_before": {"x": i}, "gold_action": 0, "gold_state_after": {"x": i + 1},
    }


def dataset(extra_split=None):
    rows = []
    for seed in (1, 7, 19):
        rows.append(row(0, seed, "train"))
        rows.append(row(1, seed, "test"))
        if extra_split:
            rows.append(row(2, seed, extra_split))
    return rows


def test_validate_rejects_debug_split():
    result = contract.validate_dataset(dataset("debug"))
    assert not result["valid"]
    assert any("unregistered split='debug'" in e for e in result["errors"])


def test_validate_rejects_posthoc_split():
    result = contract.validate_dataset(dataset("posthoc"))
    assert not result["valid"]
    assert any("unregistered split='posthoc'" in e for e in result["errors"])


def test_score_excludes_nonregistered_split_from_expected_coverage():
    rows = dataset("debug")
    result = contract.score(rows, [])
    assert result["expected_eval_instances"] == 3
    assert result["allowed_evaluation_splits"] == ["eval", "test", "valid", "validation"]


def test_score_rejects_prediction_for_debug_instance():
    rows = dataset("debug")
    debug = next(r for r in rows if r["split"] == "debug")
    pred = {
        "instance_id": debug["instance_id"], "method": "correct",
        "instance_fingerprint": contract.instance_fingerprint(contract.adapt_row(debug)),
        "pred_action": 0, "pred_state_after": debug["gold_state_after"],
    }
    result = contract.score(rows, [pred])
    assert not result["valid"]
    assert any("prediction supplied for non-evaluation split='debug'" in e for e in result["errors"])
''', encoding="utf-8")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text('''# R0-D Cycle 050 — Core evaluation split scope

## Finding

`evaluation_contract.score()` defined the evaluation set as every row whose split was not `train`. Consequently, unregistered `debug`, `calibration`, `analysis`, or `posthoc` rows could enter prediction coverage, cells, means, confidence intervals, and paired tests.

## Change

The core contract now registers exactly:

- training: `train`
- evaluation: `test`, `eval`, `validation`, `valid`

`validate_dataset()` rejects every other split. `score()` constructs `eval_ids` only from registered evaluation splits and rejects predictions attached to any non-evaluation split. The accepted split vocabulary is emitted in validation and scoring evidence.

## Classification

Any unregistered split is `initial_reproduction_failure`. No benchmark reproduction, capability progress, new mechanism, or intelligence principle is claimed.
''', encoding="utf-8")

# Trigger marker: retry workflow dispatch via canonical branch push (cycle 050 completion).
