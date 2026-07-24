#!/usr/bin/env python3
"""Strict reproducibility, leakage and paired-statistics contract for grounded benchmarks.

Accepts canonical rows and SILG trajectory-export rows. Standard library only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

CANONICAL_REQUIRED={"instance_id","domain","seed","split","condition","utterance","state_before","gold_action","gold_state_after"}
PRED_REQUIRED={"instance_id","method","instance_fingerprint","pred_action","pred_state_after"}
REQUIRED_CONTROL_METHODS={"random","language_blind","state_only","target_label_shuffle","outcome_shuffle"}
HELD_OUT_CONDITIONS={"entity_holdout","dynamics_holdout","language_holdout"}
FORBIDDEN_MODEL_INPUT_FIELDS={"gold_action","gold_state_after","gold_inverse","answer","label","completed_trajectory","post_treatment_state","state_after","action","reward","done","terminal_observation"}
GOLD_LIKE_KEYS=set(FORBIDDEN_MODEL_INPUT_FIELDS)
RESOURCE_FIELDS={"model_bytes","peak_rss_bytes","training_wall_seconds","cpu_inference_ms_per_item","raw_log_sha256","model_sha256","data_sha256","code_commit"}
ARTIFACT_FIELDS=(("raw_log_path","raw_log_sha256"),("model_path","model_sha256"),("data_path","data_sha256"))
CANONICAL_SEEDS={1,7,19}

def read_jsonl(path:Path)->list[dict[str,Any]]:
    rows=[]
    with path.open(encoding="utf-8") as fh:
        for n,line in enumerate(fh,1):
            line=line.strip()
            if not line: continue
            obj=json.loads(line)
            if not isinstance(obj,dict): raise ValueError(f"{path}:{n}: each row must be an object")
            rows.append(obj)
    return rows

def read_json(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict): raise ValueError(f"{path}: top-level JSON must be an object")
    return obj

def stable_hash(value:Any)->str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def file_sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda:fh.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def _is_hex(value:Any,n:int)->bool:
    s=str(value)
    return len(s)==n and all(c in "0123456789abcdefABCDEF" for c in s)

def _finite_nonnegative(value:Any)->bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(float(value)) and float(value)>=0

def canonical_text(text:str)->str: return "".join(str(text).split()).casefold()
def _truthy(row:dict[str,Any],key:str)->bool: return row.get(key) is True or row.get(key)==1 or str(row.get(key,False)).lower()=="true"

def adapt_row(row:dict[str,Any])->dict[str,Any]:
    out=dict(row)
    if "gold_action" not in out and "action" in out: out["gold_action"]=out["action"]
    if "gold_state_after" not in out and "state_after" in out: out["gold_state_after"]=out["state_after"]
    if "condition" not in out:
        flags=[k for k in HELD_OUT_CONDITIONS if _truthy(out,k)]
        out["condition"]="+".join(sorted(flags)) if flags else "in_distribution"
    if "model_input_fields" not in out:
        out["model_input_fields"]=[k for k in ("utterance","state_before","history","valid_action_mask") if k in out]
    return out

def adapt_dataset(rows:Iterable[dict[str,Any]])->list[dict[str,Any]]: return [adapt_row(r) for r in rows]

def _find_forbidden_nested(value:Any,prefix:str="")->list[str]:
    out=[]
    if isinstance(value,dict):
        for k,v in value.items():
            p=f"{prefix}.{k}" if prefix else str(k)
            if str(k) in GOLD_LIKE_KEYS: out.append(p)
            out.extend(_find_forbidden_nested(v,p))
    elif isinstance(value,list):
        for i,v in enumerate(value[:32]): out.extend(_find_forbidden_nested(v,f"{prefix}[{i}]"))
    return out

def _split_sig(row:dict[str,Any],*keys:str)->str|None:
    for key in keys:
        if row.get(key) is not None: return stable_hash(row[key])
    return None

def instance_fingerprint(row:dict[str,Any])->str:
    payload={k:row.get(k) for k in ("domain","seed","split","condition","utterance","state_before","history","valid_action_mask","entity_id","entity_signature","dynamics_id","dynamics_signature")}
    return stable_hash(payload)

def validate_dataset(rows:list[dict[str,Any]])->dict[str,Any]:
    rows=adapt_dataset(rows); errors=[]; warnings=[]; seen=set(); domains=set(); seeds=set(); conditions=set(); splits=Counter(); leakage=0
    texts=defaultdict(set); entities=defaultdict(set); dynamics=defaultdict(set); fingerprints={}
    for i,row in enumerate(rows,1):
        miss=CANONICAL_REQUIRED-row.keys()
        if miss: errors.append(f"row {i}: missing fields {sorted(miss)}"); continue
        iid=str(row["instance_id"])
        if iid in seen: errors.append(f"row {i}: duplicate instance_id={iid}")
        seen.add(iid); fingerprints[iid]=instance_fingerprint(row)
        domains.add(str(row["domain"])); conditions.add(str(row["condition"])); split=str(row["split"]).lower(); splits[split]+=1
        try: seeds.add(int(row["seed"]))
        except Exception: errors.append(f"row {i}: seed must be integer-like")
        text=canonical_text(str(row["utterance"])); texts[split].add(text)
        if not text: warnings.append(f"row {i}: empty utterance")
        declared={str(x) for x in row.get("model_input_fields",[])}; bad=declared&FORBIDDEN_MODEL_INPUT_FIELDS
        if bad: leakage+=1; errors.append(f"row {i}: forbidden model input fields {sorted(bad)}")
        nested=_find_forbidden_nested(row.get("model_input",{}))
        if nested: leakage+=1; errors.append(f"row {i}: forbidden keys inside model_input {sorted(set(nested))}")
        es=_split_sig(row,"entity_id","entity_signature"); ds=_split_sig(row,"dynamics_id","dynamics_signature")
        if es: entities[split].add(es)
        if ds: dynamics[split].add(ds)
    overlap={}; train=texts.get("train",set())
    for split,vals in texts.items():
        if split=="train": continue
        ov=train&vals; overlap[split]={"count":len(ov),"examples":sorted(ov)[:5]}
        if ov: errors.append(f"exact normalized utterance leakage train->{split}: {len(ov)} texts")
    holdout={}
    for name,mapping in (("entity",entities),("dynamics",dynamics)):
        tr=mapping.get("train",set())
        for split,vals in mapping.items():
            if split=="train": continue
            ov=tr&vals; holdout[f"{name}:train->{split}"]={"train_unique":len(tr),"eval_unique":len(vals),"overlap":len(ov)}
            flagged=any(str(r.get("split","")).lower()==split and _truthy(r,f"{name}_holdout") for r in rows)
            if flagged and ov: errors.append(f"{name} holdout violation train->{split}: {len(ov)} shared signatures")
    if len(seeds)<3: errors.append(f"need >=3 seeds, found {sorted(seeds)}")
    if not domains: errors.append("need >=1 domain")
    if "train" not in splits: errors.append("train split is missing")
    if not ({"test","eval","validation","valid"}&set(splits)): errors.append("evaluation split is missing")
    missing=HELD_OUT_CONDITIONS-{c for h in conditions for c in HELD_OUT_CONDITIONS if c in h}
    if missing: warnings.append(f"missing held-out conditions: {sorted(missing)}")
    return {"valid":not errors,"errors":errors,"warnings":sorted(set(warnings)),"instances":len(rows),"domains":sorted(domains),"seeds":sorted(seeds),"conditions":sorted(conditions),"split_counts":dict(sorted(splits.items())),"utterance_overlap":overlap,"holdout_integrity":holdout,"leakage_rows":leakage,"dataset_sha256":stable_hash(rows),"instance_fingerprints_sha256":stable_hash(fingerprints),"adapted_schema":True}

def _mean_ci(vals:list[float])->tuple[float,float,float]:
    if not vals:return math.nan,math.nan,math.nan
    m=statistics.mean(vals)
    if len(vals)==1:return m,m,m
    se=statistics.stdev(vals)/math.sqrt(len(vals)); z=1.959963984540054
    return m,m-z*se,m+z*se

def _paired_p(diffs:list[float],trials:int=20000,seed:int=20260724)->float:
    xs=[x for x in diffs if x!=0]
    if not xs:return 1.0
    obs=abs(statistics.mean(xs)); n=len(xs)
    if n<=18:
        vals=[abs(statistics.mean(x if (mask>>i)&1 else -x for i,x in enumerate(xs))) for mask in range(1<<n)]
        return sum(v>=obs-1e-15 for v in vals)/len(vals)
    rng=random.Random(seed); ext=0
    for _ in range(trials):
        v=abs(statistics.mean(x if rng.random()<.5 else -x for x in xs)); ext+=v>=obs-1e-15
    return (ext+1)/(trials+1)

def _mcnemar_exact(correct_only:int,control_only:int)->float:
    n=correct_only+control_only
    if n==0:return 1.0
    k=min(correct_only,control_only); tail=sum(math.comb(n,i) for i in range(k+1))/(2**n)
    return min(1.0,2.0*tail)

def _cluster_bootstrap_ci(instance_diffs:dict[tuple[int,str,str],list[float]],trials:int=5000,seed:int=20260724)->tuple[float,float]:
    keys=sorted(instance_diffs)
    if not keys:return math.nan,math.nan
    rng=random.Random(seed); vals=[]
    for _ in range(trials):
        chosen=[keys[rng.randrange(len(keys))] for _ in keys]; sampled=[]
        for key in chosen:
            xs=instance_diffs[key]; sampled.extend(xs[rng.randrange(len(xs))] for _ in xs)
        vals.append(statistics.mean(sampled))
    vals.sort(); return vals[max(0,int(.025*len(vals))-1)],vals[min(len(vals)-1,int(.975*len(vals)))]

def score(data:list[dict[str,Any]],preds:list[dict[str,Any]])->dict[str,Any]:
    data=adapt_dataset(data); by_id={str(r["instance_id"]):r for r in data}; eval_ids={i for i,r in by_id.items() if str(r["split"]).lower()!="train"}
    errors=[]; seen=set(); method_ids=defaultdict(set); grouped=defaultdict(list); snapshots=defaultdict(set); outcomes=defaultdict(dict)
    for i,p in enumerate(preds,1):
        miss=PRED_REQUIRED-p.keys()
        if miss: errors.append(f"prediction row {i}: missing {sorted(miss)}"); continue
        iid=str(p["instance_id"]); method=str(p["method"]); key=(iid,method)
        if key in seen: errors.append(f"prediction row {i}: duplicate instance/method={key}"); continue
        seen.add(key); gold=by_id.get(iid)
        if gold is None: errors.append(f"prediction row {i}: unknown instance_id={iid}"); continue
        if str(gold["split"]).lower()=="train": errors.append(f"prediction row {i}: prediction supplied for train instance={iid}"); continue
        expected_fp=instance_fingerprint(gold); supplied=str(p["instance_fingerprint"])
        if supplied!=expected_fp: errors.append(f"prediction row {i}: instance snapshot mismatch for {iid}/{method}")
        snapshots[iid].add(supplied); method_ids[method].add(iid)
        item={"prospective":float(p["pred_state_after"]==gold["gold_state_after"]),"action":float(p["pred_action"]==gold["gold_action"])}
        if "gold_inverse" in gold and "pred_inverse" in p:item["inverse"]=float(p["pred_inverse"]==gold["gold_inverse"])
        grouped[(method,int(gold["seed"]),str(gold["domain"]),str(gold["condition"]))].append(item); outcomes[method][iid]=item
    for iid,fps in snapshots.items():
        if len(fps)!=1: errors.append(f"instance {iid}: methods used different input snapshots")
    coverage={}
    for method,ids in sorted(method_ids.items()):
        missing=eval_ids-ids; coverage[method]={"expected":len(eval_ids),"predicted":len(ids&eval_ids),"coverage":len(ids&eval_ids)/max(1,len(eval_ids)),"missing":len(missing),"extra":len(ids-eval_ids),"missing_examples":sorted(missing)[:5]}
        if missing: errors.append(f"method {method}: incomplete prediction coverage")
    methods=set(method_ids); absent=REQUIRED_CONTROL_METHODS-methods
    if absent: errors.append(f"missing required control methods: {sorted(absent)}")
    if "correct" not in methods: errors.append("missing method='correct'")
    cells=[]
    for (method,seed,domain,condition),items in sorted(grouped.items()):
        cell={"method":method,"seed":seed,"domain":domain,"condition":condition,"n":len(items)}
        for metric in sorted({k for x in items for k in x}):cell[metric]=statistics.mean(x[metric] for x in items if metric in x)
        cells.append(cell)
    metrics=sorted({k for c in cells for k in c if k in {"prospective","action","inverse"}}); summary=defaultdict(dict)
    for method in methods:
        cs=[c for c in cells if c["method"]==method]
        for metric in metrics:
            vals=[float(c[metric]) for c in cs if metric in c]
            if vals:
                m,lo,hi=_mean_ci(vals); summary[method].update({metric:m,f"{metric}_cell_ci95_low":lo,f"{metric}_cell_ci95_high":hi})
    correct={(c["seed"],c["domain"],c["condition"]):c for c in cells if c["method"]=="correct"}; gaps={}
    for ctrl in sorted(methods-{"correct"}):
        cc={(c["seed"],c["domain"],c["condition"]):c for c in cells if c["method"]==ctrl}; gaps[ctrl]={}
        shared_ids=sorted(eval_ids & method_ids.get("correct",set()) & method_ids.get(ctrl,set()))
        for metric in metrics:
            diffs=[float(correct[k][metric])-float(cc[k][metric]) for k in sorted(correct.keys()&cc.keys()) if metric in correct[k] and metric in cc[k]]
            if not diffs:continue
            inst_by_cell=defaultdict(list); correct_only=control_only=ties=0
            for iid in shared_ids:
                a=outcomes["correct"][iid].get(metric); b=outcomes[ctrl][iid].get(metric)
                if a is None or b is None:continue
                gold=by_id[iid]; cell_key=(int(gold["seed"]),str(gold["domain"]),str(gold["condition"])); inst_by_cell[cell_key].append(float(a-b))
                if a>b:correct_only+=1
                elif b>a:control_only+=1
                else:ties+=1
            instance_values=[x for xs in inst_by_cell.values() for x in xs]; blo,bhi=_cluster_bootstrap_ci(inst_by_cell) if instance_values else (math.nan,math.nan); m,lo,hi=_mean_ci(diffs)
            gaps[ctrl][metric]={"paired_cells":len(diffs),"mean_gap":m,"min_cell_gap":min(diffs),"max_cell_gap":max(diffs),"positive_cell_fraction":sum(x>0 for x in diffs)/len(diffs),"ci95_low":lo,"ci95_high":hi,"paired_randomization_p_two_sided":_paired_p(diffs),"paired_instances":len(instance_values),"instance_mean_gap":statistics.mean(instance_values) if instance_values else math.nan,"instance_cluster_bootstrap_ci95_low":blo,"instance_cluster_bootstrap_ci95_high":bhi,"correct_only_instances":correct_only,"control_only_instances":control_only,"tied_instances":ties,"mcnemar_exact_p_two_sided":_mcnemar_exact(correct_only,control_only),"passes_mean_gap_0_10":m>=.10,"passes_every_cell_positive":min(diffs)>0,"passes_ci_excludes_zero":lo>0,"passes_instance_cluster_ci_excludes_zero":blo>0 if not math.isnan(blo) else False}
    return {"valid":not errors,"errors":errors,"prediction_rows":len(preds),"expected_eval_instances":len(eval_ids),"coverage":coverage,"same_instance_snapshot":not any("snapshot" in e for e in errors),"fingerprints_required":True,"cells":cells,"summary":dict(summary),"paired_gaps_vs_correct":gaps,"progress_contract":{"required_mean_gap":.10,"requires_all_three_seeds":True,"requires_same_instance_snapshot":True,"requires_explicit_instance_fingerprint":True,"requires_complete_prediction_coverage":True,"requires_ci_excludes_zero":True,"requires_instance_cluster_ci_excludes_zero":True,"internal_metrics_do_not_count":True}}

def audit_artifacts(manifest:dict[str,Any],base_dir:Path)->dict[str,Any]:
    errors=[]; checks=[]; runs=manifest.get("runs")
    if not isinstance(runs,list) or not runs:return {"valid":False,"errors":["manifest.runs must be a non-empty list"],"checks":[],"classification":"initial_reproduction_failure"}
    methods=set(); cells=set(); seeds=set(); domains=set(); splits=set()
    for i,run in enumerate(runs,1):
        if not isinstance(run,dict):errors.append(f"run {i}: must be an object");continue
        miss=RESOURCE_FIELDS-run.keys()
        if miss:errors.append(f"run {i}: missing resource/provenance fields {sorted(miss)}")
        try: method=str(run["method"]);seed=int(run["seed"]);domain=str(run["domain"]);split=str(run["split"])
        except (KeyError,TypeError,ValueError) as e:errors.append(f"run {i}: invalid indexing field {e}");continue
        if not domain:errors.append(f"run {i}: domain must be non-empty")
        if not split:errors.append(f"run {i}: split must be non-empty")
        cell=(method,seed,domain,split)
        if cell in cells:errors.append(f"run {i}: duplicate run cell {cell}")
        cells.add(cell);methods.add(method);seeds.add(seed);domains.add(domain);splits.add(split)
        for key in ("model_bytes","peak_rss_bytes","training_wall_seconds","cpu_inference_ms_per_item"):
            if not _finite_nonnegative(run.get(key)):errors.append(f"run {i}: {key} must be a finite non-negative number")
        if not _is_hex(run.get("code_commit"),40):errors.append(f"run {i}: code_commit must be a full 40-hex commit SHA")
        for pk,hk in ARTIFACT_FIELDS:
            p=run.get(pk); expected=run.get(hk)
            if not p:errors.append(f"run {i}: {pk} is required for independent checksum verification");continue
            if not _is_hex(expected,64):errors.append(f"run {i}: {hk} must be a full 64-hex SHA-256");continue
            path=base_dir/str(p)
            if not path.exists() or not path.is_file():errors.append(f"run {i}: missing artifact {path}");continue
            actual=file_sha256(path);ok=actual==str(expected).lower();check={"run":i,"path":str(path),"expected":expected,"actual":actual,"ok":ok,"size_bytes":path.stat().st_size};checks.append(check)
            if not ok:errors.append(f"run {i}: checksum mismatch for {pk}")
            if pk=="model_path" and _finite_nonnegative(run.get("model_bytes")) and int(run["model_bytes"])!=path.stat().st_size:errors.append(f"run {i}: model_bytes does not match model artifact size")
    required={"correct"}|REQUIRED_CONTROL_METHODS; missing_methods=required-methods
    if missing_methods:errors.append(f"manifest missing required methods {sorted(missing_methods)}")
    if seeds!=CANONICAL_SEEDS:errors.append(f"manifest seeds must be exactly {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
    expected={(m,s,d,sp) for m in required for s in CANONICAL_SEEDS for d in domains for sp in splits}; missing_cells=expected-cells
    if missing_cells:errors.append(f"manifest incomplete Cartesian coverage: {len(missing_cells)} missing cells")
    return {"valid":not errors,"errors":errors,"warnings":[],"checks":checks,"methods":sorted(methods),"seeds":sorted(seeds),"domains":sorted(domains),"splits":sorted(splits),"runs":len(runs),"missing_run_cells":len(missing_cells),"missing_run_cell_examples":[list(x) for x in sorted(missing_cells)[:10]],"independent_artifacts_required":True,"canonical_seeds":sorted(CANONICAL_SEEDS),"classification":"reproduced" if not errors else "initial_reproduction_failure"}

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate");v.add_argument("data",type=Path)
    s=sub.add_parser("score");s.add_argument("data",type=Path);s.add_argument("predictions",type=Path)
    a=sub.add_parser("audit-artifacts");a.add_argument("manifest",type=Path);a.add_argument("--base-dir",type=Path,default=Path("."))
    args=p.parse_args(argv)
    try:
        if args.command=="audit-artifacts":result=audit_artifacts(read_json(args.manifest),args.base_dir)
        else:
            data=read_jsonl(args.data);result=validate_dataset(data)
            if args.command=="score":result["scores"]=score(data,read_jsonl(args.predictions));result["valid"]=result["valid"] and result["scores"]["valid"]
    except (OSError,ValueError,json.JSONDecodeError) as e: print(json.dumps({"valid":False,"errors":[str(e)]},ensure_ascii=False,indent=2));return 2
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
