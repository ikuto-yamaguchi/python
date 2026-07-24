#!/usr/bin/env python3
"""Native SILG matched-episode adapter for the R0 evaluation contract.

Consumes run_silg_matched_eval.py JSON directly. It checks canonical seeds,
method/episode coverage, immutable initial fingerprints, checkpoint provenance,
and paired win/return/length statistics. No model or benchmark logic lives here.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

CANONICAL_SEEDS={1,7,19}
CORE={"correct","random","language_blind","state_only","language_shuffle"}
STRICT={"correct","random","language_blind","state_only","target_label_shuffle","outcome_shuffle"}

def stable_hash(v:Any)->str:
 return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def mean_ci(xs:list[float])->tuple[float,float,float]:
 if not xs:return math.nan,math.nan,math.nan
 m=statistics.mean(xs)
 if len(xs)==1:return m,m,m
 d=1.959963984540054*statistics.stdev(xs)/math.sqrt(len(xs));return m,m-d,m+d

def sign_p(xs:list[float],trials:int=20000)->float:
 ys=[x for x in xs if x]
 if not ys:return 1.0
 obs=abs(statistics.mean(ys));rng=random.Random(20260725);n=0
 for _ in range(trials):n+=abs(statistics.mean(x if rng.random()<.5 else -x for x in ys))>=obs-1e-15
 return (n+1)/(trials+1)

def mcnemar(a:int,b:int)->float:
 n=a+b
 if not n:return 1.0
 k=min(a,b);return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/(2**n))

def cluster_ci(groups:dict[int,list[float]],trials:int=5000)->tuple[float,float]:
 if not groups:return math.nan,math.nan
 keys=sorted(groups);rng=random.Random(20260725);out=[]
 for _ in range(trials):
  sampled=[]
  for key in [keys[rng.randrange(len(keys))] for _ in keys]:
   xs=groups[key];sampled.extend(xs[rng.randrange(len(xs))] for _ in xs)
  out.append(statistics.mean(sampled))
 out.sort();return out[max(0,int(.025*len(out))-1)],out[min(len(out)-1,int(.975*len(out)))]

def paired(groups:dict[int,list[float]],pairs:list[tuple[float,float]]|None=None)->dict[str,Any]:
 vals=[x for xs in groups.values() for x in xs];cells=[statistics.mean(xs) for xs in groups.values()]
 m,lo,hi=mean_ci(cells);blo,bhi=cluster_ci(groups)
 out={"paired_seeds":len(cells),"paired_episodes":len(vals),"mean_gap":m,"min_seed_gap":min(cells) if cells else math.nan,"max_seed_gap":max(cells) if cells else math.nan,"positive_seed_fraction":sum(x>0 for x in cells)/len(cells) if cells else math.nan,"seed_ci95_low":lo,"seed_ci95_high":hi,"paired_sign_randomization_p":sign_p(cells),"episode_mean_gap":statistics.mean(vals) if vals else math.nan,"seed_cluster_bootstrap_ci95_low":blo,"seed_cluster_bootstrap_ci95_high":bhi,"passes_mean_gap_0_10":m>=.10 if not math.isnan(m) else False,"passes_all_seeds_positive":min(cells)>0 if cells else False,"passes_cluster_ci":blo>0 if not math.isnan(blo) else False}
 if pairs is not None:
  co=sum(a>b for a,b in pairs);oo=sum(b>a for a,b in pairs)
  out.update({"correct_only":co,"control_only":oo,"ties":len(pairs)-co-oo,"mcnemar_exact_p":mcnemar(co,oo)})
 return out

def audit(payload:dict[str,Any])->dict[str,Any]:
 errors=[];warnings=[];runs=payload.get("runs")
 if not isinstance(runs,list) or not runs:return {"valid":False,"errors":["runs must be a non-empty list"],"classification":"initial_reproduction_failure"}
 methods=set();seeds=set();by=defaultdict(dict);fps=defaultdict(set);duplicates=[]
 for i,run in enumerate(runs,1):
  try:method=str(run["method"]);seed=int(run["seed"]);records=run["episode_records"]
  except (KeyError,TypeError,ValueError) as e:errors.append(f"run {i}: invalid indexing fields: {e}");continue
  methods.add(method);seeds.add(seed)
  if not isinstance(records,list) or not records:errors.append(f"run {i}: episode_records empty");continue
  if run.get("episodes") is not None and int(run["episodes"])!=len(records):errors.append(f"run {i}: declared episode count mismatch")
  for j,r in enumerate(records,1):
   missing={"episode_seed","initial_instance_fingerprint","win","return","length"}-r.keys()
   if missing:errors.append(f"run {i} record {j}: missing {sorted(missing)}");continue
   key=(seed,int(r["episode_seed"]));duplicates.append((method,key)) if key in by[method] else None;by[method][key]=r;fps[key].add(str(r["initial_instance_fingerprint"]))
   if float(r["win"]) not in (0.,1.):errors.append(f"run {i} record {j}: win not binary")
   for field in ("win","return","length"):
    if not isinstance(r[field],(int,float)) or not math.isfinite(float(r[field])):errors.append(f"run {i} record {j}: {field} invalid")
 if duplicates:errors.append(f"duplicate method/episode keys: {duplicates[:5]}")
 missing_core=CORE-methods
 if missing_core:errors.append(f"missing core methods {sorted(missing_core)}")
 missing_strict=STRICT-methods
 if missing_strict:warnings.append(f"strict controls missing: {sorted(missing_strict)}")
 if seeds!=CANONICAL_SEEDS:errors.append(f"canonical seeds must be {sorted(CANONICAL_SEEDS)}, found {sorted(seeds)}")
 if payload.get("all_initial_streams_match") is not True:errors.append("all_initial_streams_match is not true")
 mismatches=[k for k,v in fps.items() if len(v)!=1]
 if mismatches:errors.append(f"fingerprint mismatch on {len(mismatches)} episodes")
 ref=set(by.get("correct",{}));coverage={}
 for method in sorted(methods):
  keys=set(by[method]);coverage[method]={"expected":len(ref),"observed":len(keys),"missing":len(ref-keys),"extra":len(keys-ref),"coverage":len(keys&ref)/max(1,len(ref))}
  if keys!=ref:errors.append(f"{method}: episode coverage differs from correct")
 gaps={}
 for control in sorted(methods-{"correct"}):
  gaps[control]={}
  for metric in ("win","return","length"):
   groups=defaultdict(list);pairs=[] if metric=="win" else None
   for key in sorted(ref&set(by[control])):
    a=float(by["correct"][key][metric]);b=float(by[control][key][metric]);groups[key[0]].append(a-b)
    if pairs is not None:pairs.append((a,b))
   gaps[control][metric]=paired(groups,pairs)
 checkpoints=payload.get("checkpoints",{});cp_ok=isinstance(checkpoints,dict) and CANONICAL_SEEDS<={int(k) for k in checkpoints}
 if not cp_ok:errors.append("checkpoint bytes/SHA-256 missing for canonical seeds")
 if not payload.get("source_pins"):errors.append("source_pins missing")
 strict_complete=not missing_strict;structural=not errors
 return {"valid":structural and strict_complete,"structurally_valid":structural,"classification":"matched_episode_reproduced" if structural and strict_complete else "initial_reproduction_failure","errors":errors,"warnings":warnings,"environment":payload.get("environment"),"methods":sorted(methods),"seeds":sorted(seeds),"episodes":len(ref),"coverage":coverage,"same_initial_instance_snapshot":not mismatches and payload.get("all_initial_streams_match") is True,"paired_gaps_vs_correct":gaps,"strict_controls_complete":strict_complete,"payload_sha256":stable_hash(payload)}

def main()->int:
 p=argparse.ArgumentParser();p.add_argument("payload",type=Path);p.add_argument("--output",type=Path);a=p.parse_args();result=audit(json.loads(a.payload.read_text()))
 text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if a.output:a.output.write_text(text)
 print(text,end="");return 0 if result["valid"] else 1
if __name__=="__main__":raise SystemExit(main())
