#!/usr/bin/env python3
"""Preflight aggregate R0 summaries before strict instance-level scoring."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

REQUIRED_SEEDS={1,7,19}
REQUIRED_CONTROLS={"random","language_blind","state_only","target_label_shuffle","outcome_shuffle"}
REQUIRED_EXTERNAL={"task_success_measured","heldout_entity_measured","heldout_dynamics_measured","heldout_language_form_measured"}
REQUIRED_PROVENANCE={"workflow_head_sha","artifact","source_pins","seeds"}

def read_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): raise ValueError("top-level JSON must be an object")
    return obj

def present_methods(summary:dict[str,Any])->set[str]:
    keys=set(map(str,summary.get("mean_action_accuracy",{})))
    found=set()
    aliases={
      "random":("random",),
      "language_blind":("language_blind","language-blind"),
      "state_only":("state_only","state-only"),
      "target_label_shuffle":("target_label_shuffle","target-label-shuffle"),
      "outcome_shuffle":("outcome_shuffle","transition_shuffle","outcome-shuffle","transition-shuffle"),
    }
    for method,tokens in aliases.items():
        if any(any(t in key for t in tokens) for key in keys): found.add(method)
    return found

def audit(summary:dict[str,Any])->dict[str,Any]:
    errors=[]; warnings=[]
    missing_prov=REQUIRED_PROVENANCE-summary.keys()
    if missing_prov: errors.append(f"missing provenance fields: {sorted(missing_prov)}")
    seeds={int(x) for x in summary.get("seeds",[]) if str(x).lstrip("-").isdigit()}
    if seeds!=REQUIRED_SEEDS: errors.append(f"canonical seeds must be {sorted(REQUIRED_SEEDS)}, found {sorted(seeds)}")
    methods=present_methods(summary); missing_controls=REQUIRED_CONTROLS-methods
    if missing_controls: errors.append(f"missing required matched controls: {sorted(missing_controls)}")
    if not summary.get("instance_level_predictions_path"):
        errors.append("instance-level predictions are absent; domain×seed×condition paired cells cannot be reconstructed")
    if not summary.get("evaluation_dataset_path"):
        errors.append("evaluation dataset path/checksum is absent; train/test overlap and instance fingerprints cannot be independently audited")
    if not summary.get("instance_fingerprints_sha256"):
        errors.append("instance fingerprint digest is absent; same-instance comparison is unverified")
    if not summary.get("raw_logs"):
        errors.append("per-run raw logs and full SHA-256 values are absent")
    if not summary.get("model_sha256_by_seed"):
        errors.append("per-seed model SHA-256 values are absent")
    if not summary.get("data_sha256_by_seed"):
        errors.append("per-seed train/test data SHA-256 values are absent")
    for key in sorted(REQUIRED_EXTERNAL):
        if summary.get(key) is not True: errors.append(f"required external evaluation not measured: {key}")
    if summary.get("next_state_metric_valid") is not True:
        errors.append("next-state metric is invalid or absent")
    if summary.get("task_success_measured") is not True:
        warnings.append("offline action accuracy cannot substitute for online task success")
    accuracy=summary.get("mean_action_accuracy",{})
    ef=accuracy.get("environment_first_correct")
    blind=accuracy.get("environment_first_language_blind")
    shuffled=accuracy.get("environment_first_language_shuffle")
    state=accuracy.get("state_only")
    diagnostics={}
    if all(isinstance(v,(int,float)) for v in (ef,blind,shuffled,state)):
        diagnostics={
          "environment_first_minus_language_blind":ef-blind,
          "environment_first_minus_language_shuffle":ef-shuffled,
          "environment_first_minus_state_only":ef-state,
          "language_necessity_signal":(ef-blind)>=0.10 and (ef-shuffled)>=0.10,
        }
    classification="reproduced" if not errors else "initial_reproduction_failure"
    return {
      "valid":not errors,
      "classification":classification,
      "source_classification":summary.get("classification"),
      "errors":errors,
      "warnings":warnings,
      "canonical_seeds":sorted(seeds),
      "present_controls":sorted(methods),
      "missing_controls":sorted(missing_controls),
      "diagnostics_only":diagnostics,
      "capability_progress_eligible":False if errors else bool(diagnostics.get("language_necessity_signal")),
      "reason":"aggregate-only summary cannot satisfy strict paired benchmark contract" if errors else "strict preflight passed",
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("summary",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try: result=audit(read_json(args.summary))
    except (OSError,ValueError,json.JSONDecodeError) as e:
        result={"valid":False,"classification":"initial_reproduction_failure","errors":[str(e)]}
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(text+"\n",encoding="utf-8")
    print(text)
    return 0 if result["valid"] else 1
if __name__=="__main__": raise SystemExit(main())
