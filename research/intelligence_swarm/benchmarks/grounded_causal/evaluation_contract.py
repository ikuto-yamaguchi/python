#!/usr/bin/env python3
"""Fail-closed reproducibility, leakage and paired-statistics contract for R0.

Accepts canonical rows and the concrete SILG/RTFM typed trajectory schema.
Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

CANONICAL_REQUIRED = {"instance_id", "domain", "seed", "split", "condition", "utterance", "state_before", "gold_action", "gold_state_after"}
PRED_REQUIRED = {"instance_id", "method", "instance_fingerprint", "pred_action", "pred_state_after"}
REQUIRED_CONTROL_METHODS = {"random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"}
SHUFFLE_METHODS = {"target_label_shuffle", "outcome_shuffle"}
SHUFFLE_REQUIRED = {"control_source_instance_id", "control_source_fingerprint"}
HELD_OUT_CONDITIONS = {"entity_holdout", "dynamics_holdout", "language_holdout"}
FORBIDDEN_MODEL_INPUT_FIELDS = {
    "gold_action", "gold_state_after", "gold_inverse", "answer", "label",
    "completed_trajectory", "post_treatment_state", "state_after", "action",
    "reward", "done", "terminal_observation", "episode_return", "episode_success",
}
GOLD_LIKE_KEYS = set(FORBIDDEN_MODEL_INPUT_FIELDS)
RESOURCE_FIELDS = {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item", "raw_log_sha256", "model_sha256", "data_sha256", "code_commit"}
ARTIFACT_FIELDS = (("raw_log_path", "raw_log_sha256"), ("model_path", "model_sha256"), ("data_path", "data_sha256"))
CANONICAL_SEEDS = {1, 7, 19}
EVAL_SPLITS = {"test", "eval", "validation", "valid"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows=[]
    with path.open(encoding="utf-8") as fh:
        for n,line in enumerate(fh,1):
            if not line.strip(): continue
            obj=json.loads(line)
            if not isinstance(obj,dict): raise ValueError(f"{path}:{n}: each row must be an object")
            rows.append(obj)
    return rows


def read_json(path: Path) -> dict[str, Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): raise ValueError(f"{path}: top-level JSON must be an object")
    return obj


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda:fh.read(1<<20),b""): h.update(block)
    return h.hexdigest()


def _is_hex(value: Any,n:int)->bool:
    text=str(value); return len(text)==n and all(ch in "0123456789abcdefABCDEF" for ch in text)


def _finite_nonnegative(value: Any)->bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value)) and float(value)>=0


def canonical_text(value: Any)->str:
    if isinstance(value,(list,tuple)): return "tokens:"+",".join(str(int(x)) for x in value)
    return "".join(str(value).split()).casefold()


def _truthy(row:dict[str,Any],key:str)->bool:
    return row.get(key) is True or row.get(key)==1 or str(row.get(key,False)).lower()=="true"


def adapt_row(row:dict[str,Any])->dict[str,Any]:
    out=dict(row)
    if "utterance" not in out and isinstance(out.get("text_tokens"),list):
        out["utterance"]=[int(x) for x in out["text_tokens"]]; out["utterance_source"]="text_tokens"
    if "gold_action" not in out and "action" in out: out["gold_action"]=out["action"]
    if "gold_state_after" not in out and "state_after" in out: out["gold_state_after"]=out["state_after"]
    if "valid_action_mask" not in out and "valid" in out: out["valid_action_mask"]=out["valid"]
    if "condition" not in out:
        flags=[name for name in HELD_OUT_CONDITIONS if _truthy(out,name)]
        out["condition"]="+".join(sorted(flags)) if flags else "in_distribution"
    if "model_input_fields" not in out:
        out["model_input_fields"]=[k for k in ("utterance","state_before","history","valid_action_mask") if k in out]
    if "model_input" not in out:
        out["model_input"]={k:out[k] for k in out["model_input_fields"] if k in out}
    return out


def adapt_dataset(rows:Iterable[dict[str,Any]])->list[dict[str,Any]]: return [adapt_row(r) for r in rows]


def _find_forbidden_nested(value:Any,prefix:str="")->list[str]:
    found=[]
    if isinstance(value,dict):
        for key,nested in value.items():
            path=f"{prefix}.{key}" if prefix else str(key)
            if str(key) in GOLD_LIKE_KEYS: found.append(path)
            found.extend(_find_forbidden_nested(nested,path))
    elif isinstance(value,list):
        for i,nested in enumerate(value[:32]): found.extend(_find_forbidden_nested(nested,f"{prefix}[{i}]"))
    return found


def _split_sig(row:dict[str,Any],*keys:str)->str|None:
    for key in keys:
        if row.get(key) is not None: return stable_hash(row[key])
    return None


def _cell_key(row:dict[str,Any])->tuple[int,str,str,str]: return (int(row["seed"]),str(row["domain"]),str(row["split"]).lower(),str(row["condition"]))


def instance_fingerprint(row:dict[str,Any])->str:
    keys=("domain","seed","split","condition","utterance","state_before","history","valid_action_mask","entity_id","entity_signature","dynamics_id","dynamics_signature","episode_id","episode_seed","observation_fingerprint")
    return stable_hash({k:row.get(k) for k in keys})


def validate_dataset(rows:list[dict[str,Any]])->dict[str,Any]:
    adapted=adapt_dataset(rows); errors=[]; warnings=[]; seen=set(); domains=set(); seeds=set(); conditions=set(); splits=Counter()
    texts=defaultdict(set); entities=defaultdict(set); dynamics=defaultdict(set); episode_splits=defaultdict(set); episode_seed_splits=defaultdict(set); observation_splits=defaultdict(set)
    fingerprints={}; leakage=0; silg_rows=0; topology=defaultdict(set); per_seed_splits=defaultdict(set)
    for index,row in enumerate(adapted,1):
        missing=CANONICAL_REQUIRED-row.keys()
        if missing: errors.append(f"row {index}: missing fields {sorted(missing)}"); continue
        iid=str(row["instance_id"])
        if iid in seen: errors.append(f"row {index}: duplicate instance_id={iid}")
        seen.add(iid); fingerprints[iid]=instance_fingerprint(row)
        domain=str(row["domain"]); condition=str(row["condition"]); split=str(row["split"]).lower()
        if not domain: errors.append(f"row {index}: domain must be non-empty")
        if not split: errors.append(f"row {index}: split must be non-empty")
        if not condition: errors.append(f"row {index}: condition must be non-empty")
        domains.add(domain); conditions.add(condition); splits[split]+=1
        try: seed=int(row["seed"]); seeds.add(seed); topology[(domain,split,condition)].add(seed); per_seed_splits[seed].add(split)
        except (TypeError,ValueError): errors.append(f"row {index}: seed must be integer-like")
        if "text_tokens" in row:
            silg_rows+=1
            if row.get("utterance_source")!="text_tokens": errors.append(f"row {index}: SILG text_tokens were not adapted as utterance")
        text=canonical_text(row["utterance"]); texts[split].add(text)
        if not text or text=="tokens:": warnings.append(f"row {index}: empty utterance")
        bad={str(v) for v in row.get("model_input_fields",[])} & FORBIDDEN_MODEL_INPUT_FIELDS
        if bad: leakage+=1; errors.append(f"row {index}: forbidden model input fields {sorted(bad)}")
        nested=_find_forbidden_nested(row.get("model_input",{}))
        if nested: leakage+=1; errors.append(f"row {index}: forbidden keys inside model_input {sorted(set(nested))}")
        es=_split_sig(row,"entity_id","entity_signature"); ds=_split_sig(row,"dynamics_id","dynamics_signature")
        if es: entities[split].add(es)
        if ds: dynamics[split].add(ds)
        if row.get("episode_id") is not None: episode_splits[str(row["episode_id"])].add(split)
        if row.get("episode_seed") is not None: episode_seed_splits[str(row["episode_seed"])].add(split)
        if row.get("observation_fingerprint") is not None: observation_splits[str(row["observation_fingerprint"])].add(split)
    overlap={}; train_text=texts.get("train",set())
    for split,values in texts.items():
        if split=="train": continue
        shared=train_text&values; overlap[split]={"count":len(shared),"examples":sorted(shared)[:5]}
        if shared: errors.append(f"exact normalized utterance leakage train->{split}: {len(shared)} texts")
    holdout={}
    for name,mapping in (("entity",entities),("dynamics",dynamics)):
        train_values=mapping.get("train",set())
        for split,values in mapping.items():
            if split=="train": continue
            shared=train_values&values; holdout[f"{name}:train->{split}"]={"train_unique":len(train_values),"eval_unique":len(values),"overlap":len(shared)}
            if any(str(r.get("split","")).lower()==split and _truthy(r,f"{name}_holdout") for r in adapted) and shared:
                errors.append(f"{name} holdout violation train->{split}: {len(shared)} shared signatures")
    split_leakage={}
    for name,mapping in (("episode_id",episode_splits),("episode_seed",episode_seed_splits),("observation_fingerprint",observation_splits)):
        shared=sorted(k for k,v in mapping.items() if "train" in v and v&EVAL_SPLITS); split_leakage[name]=shared[:10]
        if shared: errors.append(f"train/eval {name} leakage: {len(shared)} shared values")
    if seeds!=CANONICAL_SEEDS: errors.append(f"dataset seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    for cell,cell_seeds in sorted(topology.items()):
        if cell_seeds!=CANONICAL_SEEDS: errors.append(f"dataset cell {cell} must contain seeds {sorted(CANONICAL_SEEDS)}, found {sorted(cell_seeds)}")
    for seed in sorted(CANONICAL_SEEDS):
        if "train" not in per_seed_splits.get(seed,set()): errors.append(f"seed {seed}: train split is missing")
        if not (EVAL_SPLITS & per_seed_splits.get(seed,set())): errors.append(f"seed {seed}: evaluation split is missing")
    if not domains: errors.append("need >=1 domain")
    missing_holdouts=HELD_OUT_CONDITIONS-{name for c in conditions for name in HELD_OUT_CONDITIONS if name in c}
    if missing_holdouts: warnings.append(f"missing held-out conditions: {sorted(missing_holdouts)}")
    topology_json={str(k):sorted(v) for k,v in sorted(topology.items())}
    return {"valid":not errors,"errors":errors,"warnings":sorted(set(warnings)),"instances":len(adapted),"domains":sorted(domains),"seeds":sorted(seeds),"conditions":sorted(conditions),"split_counts":dict(sorted(splits.items())),"utterance_overlap":overlap,"holdout_integrity":holdout,"split_identity_leakage":split_leakage,"leakage_rows":leakage,"silg_rows_adapted":silg_rows,"dataset_sha256":stable_hash(adapted),"instance_fingerprints_sha256":stable_hash(fingerprints),"seed_domain_split_condition_topology":topology_json,"canonical_seed_topology_required":True,"adapted_schema":True,"silg_text_tokens_supported":True,"episode_split_isolation_required":True}


def _mean_ci(values:list[float])->tuple[float,float,float]:
    if not values:return math.nan,math.nan,math.nan
    mean=statistics.mean(values)
    if len(values)==1:return mean,mean,mean
    se=statistics.stdev(values)/math.sqrt(len(values)); z=1.959963984540054
    return mean,mean-z*se,mean+z*se


def _paired_p(diffs:list[float],trials:int=20000,seed:int=20260724)->float:
    values=[v for v in diffs if v!=0]
    if not values:return 1.0
    observed=abs(statistics.mean(values)); n=len(values)
    if n<=18:
        samples=[abs(statistics.mean(v if (mask>>i)&1 else -v for i,v in enumerate(values))) for mask in range(1<<n)]
        return sum(v>=observed-1e-15 for v in samples)/len(samples)
    rng=random.Random(seed); extreme=0
    for _ in range(trials): extreme+=abs(statistics.mean(v if rng.random()<.5 else -v for v in values))>=observed-1e-15
    return (extreme+1)/(trials+1)


def _mcnemar_exact(a:int,b:int)->float:
    n=a+b
    if n==0:return 1.0
    k=min(a,b); return min(1.0,2.0*sum(math.comb(n,i) for i in range(k+1))/(2**n))


def _cluster_bootstrap_ci(groups:dict[tuple[int,str,str,str],list[float]],trials:int=5000,seed:int=20260724)->tuple[float,float]:
    keys=sorted(groups)
    if not keys:return math.nan,math.nan
    rng=random.Random(seed); estimates=[]
    for _ in range(trials):
        sampled=[]
        for key in [keys[rng.randrange(len(keys))] for _ in keys]:
            vals=groups[key]; sampled.extend(vals[rng.randrange(len(vals))] for _ in vals)
        estimates.append(statistics.mean(sampled))
    estimates.sort(); return estimates[max(0,int(.025*len(estimates))-1)],estimates[min(len(estimates)-1,int(.975*len(estimates)))]


def _validate_shuffle_assignments(preds:list[dict[str,Any]],by_id:dict[str,dict[str,Any]],eval_ids:set[str])->tuple[list[str],dict[str,Any]]:
    errors=[]; audit={}
    for method in sorted(SHUFFLE_METHODS):
        rows=[r for r in preds if str(r.get("method"))==method and str(r.get("instance_id")) in eval_ids]; by_cell=defaultdict(list); donors=defaultdict(list)
        for i,pred in enumerate(rows,1):
            missing=SHUFFLE_REQUIRED-pred.keys()
            if missing: errors.append(f"{method} row {i}: missing shuffle provenance {sorted(missing)}"); continue
            iid=str(pred["instance_id"]); donor_id=str(pred["control_source_instance_id"]); target=by_id[iid]; donor=by_id.get(donor_id)
            if donor is None or donor_id not in eval_ids: errors.append(f"{method} row {i}: unknown/non-eval donor {donor_id}"); continue
            if donor_id==iid: errors.append(f"{method} row {i}: self-shuffle is not allowed for {iid}")
            if str(pred["control_source_fingerprint"])!=instance_fingerprint(donor): errors.append(f"{method} row {i}: donor fingerprint mismatch for {iid}<-{donor_id}")
            tc=_cell_key(target); dc=_cell_key(donor)
            if tc!=dc: errors.append(f"{method} row {i}: donor crosses seed/domain/split/condition cell")
            by_cell[tc].append(iid); donors[tc].append(donor_id)
        cells={}
        for cell in sorted(by_cell):
            targets=by_cell[cell]; ds=donors[cell]; bijective=len(targets)==len(set(ds)) and set(targets)==set(ds); deranged=all(a!=b for a,b in zip(targets,ds))
            if not bijective: errors.append(f"{method} cell {cell}: donor assignment is not a bijection")
            if not deranged: errors.append(f"{method} cell {cell}: donor assignment is not a derangement")
            cells[str(cell)]={"n":len(targets),"unique_donors":len(set(ds)),"bijective":bijective,"deranged":deranged}
        audit[method]={"rows":len(rows),"cells":cells,"provenance_required":True}
    return errors,audit


def score(data:list[dict[str,Any]],preds:list[dict[str,Any]])->dict[str,Any]:
    adapted=adapt_dataset(data); by_id={str(r["instance_id"]):r for r in adapted}; eval_ids={i for i,r in by_id.items() if str(r["split"]).lower()!="train"}
    errors=[]; seen=set(); method_ids=defaultdict(set); grouped=defaultdict(list); snapshots=defaultdict(set); outcomes=defaultdict(dict)
    for index,pred in enumerate(preds,1):
        missing=PRED_REQUIRED-pred.keys()
        if missing: errors.append(f"prediction row {index}: missing {sorted(missing)}"); continue
        iid=str(pred["instance_id"]); method=str(pred["method"]); key=(iid,method)
        if key in seen: errors.append(f"prediction row {index}: duplicate instance/method={key}"); continue
        seen.add(key); gold=by_id.get(iid)
        if gold is None: errors.append(f"prediction row {index}: unknown instance_id={iid}"); continue
        if str(gold["split"]).lower()=="train": errors.append(f"prediction row {index}: prediction supplied for train instance={iid}"); continue
        fp=str(pred["instance_fingerprint"])
        if fp!=instance_fingerprint(gold): errors.append(f"prediction row {index}: instance snapshot mismatch for {iid}/{method}")
        snapshots[iid].add(fp); method_ids[method].add(iid)
        item={"prospective":float(pred["pred_state_after"]==gold["gold_state_after"]),"action":float(pred["pred_action"]==gold["gold_action"])}
        if "gold_inverse" in gold and "pred_inverse" in pred:item["inverse"]=float(pred["pred_inverse"]==gold["gold_inverse"])
        grouped[(method,int(gold["seed"]),str(gold["domain"]),str(gold["split"]).lower(),str(gold["condition"]))].append(item); outcomes[method][iid]=item
    for iid,fps in snapshots.items():
        if len(fps)!=1: errors.append(f"instance {iid}: methods used different input snapshots")
    required={"correct"}|REQUIRED_CONTROL_METHODS; coverage={}
    for method in sorted(required|set(method_ids)):
        ids=method_ids.get(method,set()); missing=eval_ids-ids; extra=ids-eval_ids
        coverage[method]={"expected":len(eval_ids),"predicted":len(ids&eval_ids),"coverage":len(ids&eval_ids)/max(1,len(eval_ids)),"missing":len(missing),"extra":len(extra),"missing_examples":sorted(missing)[:5]}
        if missing: errors.append(f"method {method}: incomplete prediction coverage")
        if extra: errors.append(f"method {method}: predictions outside evaluation set")
    absent=REQUIRED_CONTROL_METHODS-set(method_ids)
    if absent: errors.append(f"missing required control methods: {sorted(absent)}")
    if "correct" not in method_ids: errors.append("missing method='correct'")
    shuffle_errors,shuffle_audit=_validate_shuffle_assignments(preds,by_id,eval_ids); errors.extend(shuffle_errors)
    cells=[]
    for (method,seed,domain,split,condition),items in sorted(grouped.items()):
        cell={"method":method,"seed":seed,"domain":domain,"split":split,"condition":condition,"n":len(items)}
        for metric in sorted({k for item in items for k in item}): cell[metric]=statistics.mean(item[metric] for item in items if metric in item)
        cells.append(cell)
    metrics=sorted({k for c in cells for k in c if k in {"prospective","action","inverse"}}); summary=defaultdict(dict); methods=set(method_ids)
    for method in methods:
        method_cells=[c for c in cells if c["method"]==method]
        for metric in metrics:
            vals=[float(c[metric]) for c in method_cells if metric in c]
            if vals:
                mean,low,high=_mean_ci(vals); summary[method].update({metric:mean,f"{metric}_cell_ci95_low":low,f"{metric}_cell_ci95_high":high})
    correct_cells={(c["seed"],c["domain"],c["split"],c["condition"]):c for c in cells if c["method"]=="correct"}; gaps={}
    for control in sorted(methods-{"correct"}):
        control_cells={(c["seed"],c["domain"],c["split"],c["condition"]):c for c in cells if c["method"]==control}; gaps[control]={}; shared=sorted(eval_ids&method_ids.get("correct",set())&method_ids.get(control,set()))
        for metric in metrics:
            diffs=[float(correct_cells[k][metric])-float(control_cells[k][metric]) for k in sorted(correct_cells.keys()&control_cells.keys()) if metric in correct_cells[k] and metric in control_cells[k]]
            if not diffs:continue
            groups=defaultdict(list); a=b=ties=0
            for iid in shared:
                left=outcomes["correct"][iid].get(metric); right=outcomes[control][iid].get(metric)
                if left is None or right is None:continue
                groups[_cell_key(by_id[iid])].append(float(left-right))
                if left>right:a+=1
                elif right>left:b+=1
                else:ties+=1
            values=[v for vs in groups.values() for v in vs]; boot_low,boot_high=_cluster_bootstrap_ci(groups) if values else (math.nan,math.nan); mean,low,high=_mean_ci(diffs)
            gaps[control][metric]={"paired_cells":len(diffs),"mean_gap":mean,"min_cell_gap":min(diffs),"max_cell_gap":max(diffs),"positive_cell_fraction":sum(v>0 for v in diffs)/len(diffs),"ci95_low":low,"ci95_high":high,"paired_randomization_p_two_sided":_paired_p(diffs),"paired_instances":len(values),"instance_mean_gap":statistics.mean(values) if values else math.nan,"instance_cluster_bootstrap_ci95_low":boot_low,"instance_cluster_bootstrap_ci95_high":boot_high,"correct_only_instances":a,"control_only_instances":b,"tied_instances":ties,"mcnemar_exact_p_two_sided":_mcnemar_exact(a,b),"passes_mean_gap_0_10":mean>=.10,"passes_every_cell_positive":min(diffs)>0,"passes_ci_excludes_zero":low>0,"passes_instance_cluster_ci_excludes_zero":boot_low>0 if not math.isnan(boot_low) else False}
    return {"valid":not errors,"errors":errors,"prediction_rows":len(preds),"expected_eval_instances":len(eval_ids),"coverage":coverage,"same_instance_snapshot":not any("snapshot" in e for e in errors),"fingerprints_required":True,"shuffle_assignment_audit":shuffle_audit,"cells":cells,"summary":dict(summary),"paired_gaps_vs_correct":gaps,"progress_contract":{"required_mean_gap":.10,"requires_all_three_seeds":True,"requires_same_instance_snapshot":True,"requires_explicit_instance_fingerprint":True,"requires_complete_prediction_coverage":True,"requires_shuffle_provenance":True,"requires_within_cell_derangement":True,"requires_split_condition_cells":True,"requires_ci_excludes_zero":True,"requires_instance_cluster_ci_excludes_zero":True,"internal_metrics_do_not_count":True}}


def audit_artifacts(manifest:dict[str,Any],base_dir:Path)->dict[str,Any]:
    errors=[]; checks=[]; runs=manifest.get("runs")
    if not isinstance(runs,list) or not runs:return {"valid":False,"errors":["manifest.runs must be a non-empty list"],"checks":[],"classification":"initial_reproduction_failure"}
    methods=set(); cells=set(); seeds=set(); domains=set(); topology=set()
    for index,run in enumerate(runs,1):
        if not isinstance(run,dict): errors.append(f"run {index}: must be an object"); continue
        missing=RESOURCE_FIELDS-run.keys()
        if missing: errors.append(f"run {index}: missing resource/provenance fields {sorted(missing)}")
        try: method=str(run["method"]); seed=int(run["seed"]); domain=str(run["domain"]); split=str(run["split"]); condition=str(run["condition"])
        except (KeyError,TypeError,ValueError) as exc: errors.append(f"run {index}: invalid indexing field {exc}"); continue
        if not domain: errors.append(f"run {index}: domain must be non-empty")
        if not split: errors.append(f"run {index}: split must be non-empty")
        if not condition: errors.append(f"run {index}: condition must be non-empty")
        cell=(method,seed,domain,split,condition)
        if cell in cells: errors.append(f"run {index}: duplicate run cell {cell}")
        cells.add(cell); methods.add(method); seeds.add(seed); domains.add(domain); topology.add((domain,split,condition))
        for key in ("model_bytes","peak_rss_bytes","training_wall_seconds","cpu_inference_ms_per_item"):
            if not _finite_nonnegative(run.get(key)): errors.append(f"run {index}: {key} must be a finite non-negative number")
        if not _is_hex(run.get("code_commit"),40): errors.append(f"run {index}: code_commit must be a full 40-hex commit SHA")
        for path_key,hash_key in ARTIFACT_FIELDS:
            rel=run.get(path_key); expected=run.get(hash_key)
            if not rel: errors.append(f"run {index}: {path_key} is required for independent checksum verification"); continue
            if not _is_hex(expected,64): errors.append(f"run {index}: {hash_key} must be a full 64-hex SHA-256"); continue
            path=base_dir/str(rel)
            if not path.is_file(): errors.append(f"run {index}: missing artifact {path}"); continue
            actual=file_sha256(path); ok=actual==str(expected).lower(); checks.append({"run":index,"path":str(path),"expected":expected,"actual":actual,"ok":ok,"size_bytes":path.stat().st_size})
            if not ok: errors.append(f"run {index}: checksum mismatch for {path_key}")
            if path_key=="model_path" and _finite_nonnegative(run.get("model_bytes")) and int(run["model_bytes"])!=path.stat().st_size: errors.append(f"run {index}: model_bytes does not match model artifact size")
    required={"correct"}|REQUIRED_CONTROL_METHODS; missing_methods=required-methods
    if missing_methods: errors.append(f"manifest missing required methods {sorted(missing_methods)}")
    if seeds!=CANONICAL_SEEDS: errors.append(f"manifest seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    expected={(m,s,d,sp,c) for m in required for s in CANONICAL_SEEDS for d,sp,c in topology}; missing_cells=expected-cells
    if missing_cells: errors.append(f"manifest incomplete observed-topology coverage: {len(missing_cells)} missing cells")
    return {"valid":not errors,"errors":errors,"warnings":[],"checks":checks,"methods":sorted(methods),"seeds":sorted(seeds),"domains":sorted(domains),"observed_topology":[list(v) for v in sorted(topology)],"runs":len(runs),"missing_run_cells":len(missing_cells),"missing_run_cell_examples":[list(v) for v in sorted(missing_cells)[:10]],"independent_artifacts_required":True,"condition_index_required":True,"canonical_seeds":sorted(CANONICAL_SEEDS),"classification":"reproduced" if not errors else "initial_reproduction_failure"}


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate"); v.add_argument("data",type=Path)
    s=sub.add_parser("score"); s.add_argument("data",type=Path); s.add_argument("predictions",type=Path)
    a=sub.add_parser("audit-artifacts"); a.add_argument("manifest",type=Path); a.add_argument("--base-dir",type=Path,default=Path("."))
    args=p.parse_args(argv)
    try:
        if args.command=="audit-artifacts": result=audit_artifacts(read_json(args.manifest),args.base_dir)
        else:
            data=read_jsonl(args.data); result=validate_dataset(data)
            if args.command=="score": result["scores"]=score(data,read_jsonl(args.predictions)); result["valid"]=result["valid"] and result["scores"]["valid"]
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print(json.dumps({"valid":False,"errors":[str(exc)]},ensure_ascii=False,indent=2)); return 2
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result["valid"] else 1


if __name__=="__main__": raise SystemExit(main())
