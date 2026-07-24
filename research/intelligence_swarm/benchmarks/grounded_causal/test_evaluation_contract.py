#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("evaluation_contract",HERE/"evaluation_contract.py"); assert SPEC and SPEC.loader
ec=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(ec)
METHODS=["correct","random","language_blind","state_only","target_label_shuffle","outcome_shuffle"]
COMMIT="a"*40
class Tests(unittest.TestCase):
 def rows(self):
  out=[]
  for seed in (1,7,19):
   out.append({"instance_id":f"train-{seed}","domain":"rtfm_s1","seed":seed,"split":"train","utterance":f"train {seed}","state_before":[0,seed],"state_after":[1,seed],"action":1})
   for c in ("entity_holdout","dynamics_holdout","language_holdout"):
    out.append({"instance_id":f"test-{seed}-{c}","domain":"rtfm_s1","seed":seed,"split":"test","condition":"all_holdouts","utterance":f"test {seed} {c}","state_before":[0,seed],"state_after":[1,seed],"action":1,c:True,"entity_signature":f"e-{seed}-{c}","dynamics_signature":f"d-{seed}-{c}"})
  return out
 def preds(self,rows):
  out=[];eval_rows=[r for r in rows if r["split"]!="train"];donors={}
  for seed in (1,7,19):
   values=[r for r in eval_rows if r["seed"]==seed]
   for i,r in enumerate(values):donors[r["instance_id"]]=values[(i+1)%len(values)]
  for r in eval_rows:
   fp=ec.instance_fingerprint(ec.adapt_row(r))
   for m in METHODS:
    p={"instance_id":r["instance_id"],"method":m,"instance_fingerprint":fp,"pred_action":r["action"] if m=="correct" else 0,"pred_state_after":r["state_after"] if m=="correct" else r["state_before"]}
    if m in ec.SHUFFLE_METHODS:
     donor=donors[r["instance_id"]];p["control_source_instance_id"]=donor["instance_id"];p["control_source_fingerprint"]=ec.instance_fingerprint(ec.adapt_row(donor))
    out.append(p)
  return out
 def manifest(self,b:Path):
  raw=b/"r";model=b/"m";data=b/"d";raw.write_text("x");model.write_bytes(b"m");data.write_text("d");sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();runs=[]
  for condition in ("in_distribution","entity_holdout"):
   for seed in (1,7,19):
    for m in METHODS:runs.append({"method":m,"seed":seed,"domain":"rtfm_s1","split":"test","condition":condition,"model_bytes":model.stat().st_size,"peak_rss_bytes":2,"training_wall_seconds":1,"cpu_inference_ms_per_item":.1,"raw_log_path":"r","raw_log_sha256":sha(raw),"model_path":"m","model_sha256":sha(model),"data_path":"d","data_sha256":sha(data),"code_commit":COMMIT})
  return {"runs":runs}
 def test_valid(self):
  r=self.rows();self.assertTrue(ec.validate_dataset(r)["valid"]);s=ec.score(r,self.preds(r));self.assertTrue(s["valid"],s["errors"]);g=s["paired_gaps_vs_correct"]["random"]["action"];self.assertEqual(g["paired_instances"],9);self.assertLess(g["mcnemar_exact_p_two_sided"],.01);self.assertTrue(s["shuffle_assignment_audit"]["outcome_shuffle"]["provenance_required"]);self.assertTrue(all("split" in c for c in s["cells"]));self.assertTrue(s["progress_contract"]["requires_split_condition_cells"])
 def test_snapshot_mismatch(self):
  r=self.rows();p=self.preds(r);p[0]["instance_fingerprint"]="bad";self.assertFalse(ec.score(r,p)["valid"])
 def test_fingerprint_required(self):
  r=self.rows();p=self.preds(r);p[0].pop("instance_fingerprint");self.assertFalse(ec.score(r,p)["valid"])
 def test_leakage(self):
  r=self.rows();r[0]["model_input"]={"completed_trajectory":[]};self.assertFalse(ec.validate_dataset(r)["valid"])
 def test_overlap(self):
  r=self.rows();r[3]["utterance"]=r[0]["utterance"];self.assertFalse(ec.validate_dataset(r)["valid"])
 def test_coverage(self):
  r=self.rows();p=[x for x in self.preds(r) if not(x["method"]=="state_only" and x["instance_id"].endswith("language_holdout"))];self.assertFalse(ec.score(r,p)["valid"])
 def test_shuffle_requires_provenance(self):
  r=self.rows();p=self.preds(r);row=next(x for x in p if x["method"]=="outcome_shuffle");row.pop("control_source_instance_id");q=ec.score(r,p);self.assertFalse(q["valid"]);self.assertTrue(any("shuffle provenance" in e for e in q["errors"]))
 def test_shuffle_rejects_self_and_duplicate_donor(self):
  r=self.rows();p=self.preds(r);rows=[x for x in p if x["method"]=="target_label_shuffle"];rows[0]["control_source_instance_id"]=rows[0]["instance_id"];rows[0]["control_source_fingerprint"]=rows[0]["instance_fingerprint"];rows[1]["control_source_instance_id"]=rows[2]["control_source_instance_id"];rows[1]["control_source_fingerprint"]=rows[2]["control_source_fingerprint"];q=ec.score(r,p);self.assertFalse(q["valid"]);self.assertTrue(any("self-shuffle" in e for e in q["errors"]));self.assertTrue(any("not a bijection" in e for e in q["errors"]))
 def test_shuffle_rejects_cross_cell_donor(self):
  r=self.rows();p=self.preds(r);row=next(x for x in p if x["method"]=="outcome_shuffle" and x["instance_id"].startswith("test-1"));donor=next(x for x in r if x["instance_id"].startswith("test-7"));row["control_source_instance_id"]=donor["instance_id"];row["control_source_fingerprint"]=ec.instance_fingerprint(ec.adapt_row(donor));q=ec.score(r,p);self.assertFalse(q["valid"]);self.assertTrue(any("crosses seed/domain/split/condition" in e for e in q["errors"]))
 def test_manifest_cartesian_and_provenance(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);q=ec.audit_artifacts(manifest,b);self.assertTrue(q["valid"],q["errors"]);self.assertEqual(q["conditions"],["entity_holdout","in_distribution"]);manifest["runs"].pop();q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertGreater(q["missing_run_cells"],0)
 def test_manifest_requires_condition(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);manifest["runs"][0].pop("condition");q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertTrue(any("condition" in e for e in q["errors"]))
 def test_manifest_rejects_condition_cell_collapse(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);manifest["runs"]=[r for r in manifest["runs"] if not(r["condition"]=="entity_holdout" and r["method"]=="random" and r["seed"]==19)];q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertGreater(q["missing_run_cells"],0)
 def test_manifest_requires_artifact_paths(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);manifest["runs"][0].pop("raw_log_path");q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertTrue(any("raw_log_path is required" in e for e in q["errors"]))
 def test_manifest_rejects_short_hash_and_commit(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);manifest["runs"][0]["model_sha256"]="abc";manifest["runs"][1]["code_commit"]="abc";q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertTrue(any("64-hex" in e for e in q["errors"]));self.assertTrue(any("40-hex" in e for e in q["errors"]))
 def test_manifest_rejects_model_size_mismatch_and_noncanonical_seed(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);manifest=self.manifest(b);manifest["runs"][0]["model_bytes"]=99;manifest["runs"][0]["seed"]=2;q=ec.audit_artifacts(manifest,b);self.assertFalse(q["valid"]);self.assertTrue(any("model_bytes" in e for e in q["errors"]));self.assertTrue(any("exactly" in e for e in q["errors"]))
if __name__=="__main__":unittest.main()
