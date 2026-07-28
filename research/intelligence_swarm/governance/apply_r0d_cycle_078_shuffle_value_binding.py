#!/usr/bin/env python3
"""Apply Cycle 078 fail-closed shuffle donor value binding to the R0 core."""
from pathlib import Path

CORE = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")
REPORT = Path("research/intelligence_swarm/governance/REPORT_R0D_CYCLE_078.md")

text = CORE.read_text(encoding="utf-8")
old = '''            if str(pred["control_source_fingerprint"]) != instance_fingerprint(donor): errors.append(f"{method} row {i}: donor fingerprint mismatch for {iid}<-{donor_id}")
            tc, dc = _cell_key(target), _cell_key(donor)
'''
new = '''            if str(pred["control_source_fingerprint"]) != instance_fingerprint(donor): errors.append(f"{method} row {i}: donor fingerprint mismatch for {iid}<-{donor_id}")
            if method == "target_label_shuffle" and pred.get("pred_action") != donor.get("gold_action"):
                errors.append(f"{method} row {i}: pred_action is not bound to donor gold_action for {iid}<-{donor_id}")
            if method == "outcome_shuffle" and pred.get("pred_state_after") != donor.get("gold_state_after"):
                errors.append(f"{method} row {i}: pred_state_after is not bound to donor gold_state_after for {iid}<-{donor_id}")
            tc, dc = _cell_key(target), _cell_key(donor)
'''
if new not in text:
    if old not in text:
        raise SystemExit("Cycle 078 patch anchor not found; refusing ambiguous rewrite")
    text = text.replace(old, new, 1)

old_audit = '''        audit[method] = {"rows": len(rows), "cells": cells, "provenance_required": True}
'''
new_audit = '''        audit[method] = {
            "rows": len(rows),
            "cells": cells,
            "provenance_required": True,
            "donor_value_binding_required": True,
            "bound_field": "pred_action<-donor.gold_action" if method == "target_label_shuffle" else "pred_state_after<-donor.gold_state_after",
        }
'''
if new_audit not in text:
    if old_audit not in text:
        raise SystemExit("Cycle 078 audit anchor not found; refusing ambiguous rewrite")
    text = text.replace(old_audit, new_audit, 1)

old_contract = '''"requires_shuffle_provenance": True, "requires_within_cell_derangement": True'''
new_contract = '''"requires_shuffle_provenance": True, "requires_shuffle_donor_value_binding": True, "requires_within_cell_derangement": True'''
if new_contract not in text:
    if old_contract not in text:
        raise SystemExit("Cycle 078 progress-contract anchor not found")
    text = text.replace(old_contract, new_contract, 1)

CORE.write_text(text, encoding="utf-8")
REPORT.write_text("""# R0-D Cycle 078 — shuffle donor value binding\n\n## Finding\n\nThe core previously verified shuffle provenance, same-cell assignment, bijection, derangement, and donor fingerprints, but did not verify that the submitted shuffled prediction actually used the donor value. A valid donor permutation could therefore accompany arbitrary predictions.\n\n## Fail-closed rule\n\n- `target_label_shuffle.pred_action` must equal the selected donor instance's `gold_action`.\n- `outcome_shuffle.pred_state_after` must equal the selected donor instance's `gold_state_after`.\n- Provenance-only assignments are rejected.\n- Any mismatch suppresses all score statistics and is classified as `initial_reproduction_failure`.\n\nNo memory, replay, fast weights, sleep, or forgetting mechanism was added.\n""", encoding="utf-8")
print("Cycle 078 patch applied")
