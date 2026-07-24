#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("evaluation_contract",HERE/"evaluation_contract.py"); assert SPEC and SPEC.loader
ec=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(ec)
METHODS=["correct","random","language_blind","state_only","target_label_shuffle","outcome_shuffle"]
class Tests(unittest.TestCase):
 def rows(self):
  out=[]
  for seed in (1,7,19):
   out.append({"instance_id":f"train-{seed}","domain":"rtfm_s1","seed":seed,"split":"train","utterance":f"train {seed}","state_before":[0,seed],"state_after":[1,seed],"action":1})
   for c in ("entity_holdout","dynamics_holdout","language_holdout"):
    out.append({"instance_id":f"test-{seed}-{c}","domain":"rtfm_s1","seed":seed,"split":"test","utterance":f"test {seed} {c}","state_before":[0,seed],"state_after":[1,seed],"action":1,c:True,"entity_signature":f"e-{seed}-{c}","dynamics_signature":f"d-{seed}-{c}"})
  return out
 def preds(self,rows):
  out=[]
  for r in rows:
   if r["split"]=="train":continue
   fp=ec.instance_fingerprint(ec.adapt_row(r))
   for m in METHODS:out.append({"instance_id":r["instance_id"],"method":m,"instance_fingerprint":fp,"pred_action":r["action"] if m=="correct" else 0,"pred_state_after":r["state_after"] if m=="correct" else r["state_before"]})
  return out
 def test_valid(self):
  r=self.rows();self.assertTrue(ec.validate_dataset(r)["valid"]);s=ec.score(r,self.preds(r));self.assertTrue(s["valid"]);self.assertTrue(s["same_instance_snapshot"]);g=s["paired_gaps_vs_correct"]["random"]["action"];self.assertEqual(g["paired_instances"],9);self.assertEqual(g["correct_only_instances"],9);self.assertEqual(g["control_only_instances"],0);self.assertLess(g["mcnemar_exact_p_two_sided"],.01);self.assertGreater(g["instance_cluster_bootstrap_ci95_low"],0)
 def test_snapshot_mismatch(self):
  r=self.rows();p=self.preds(r);p[0]["instance_fingerprint"]="bad";s=ec.score(r,p);self.assertFalse(s["valid"]);self.assertTrue(any("snapshot mismatch" in e for e in s["errors"]))
 def test_fingerprint_required(self):
  r=self.rows();p=self.preds(r);p[0].pop("instance_fingerprint");s=ec.score(r,p);self.assertFalse(s["valid"]);self.assertTrue(any("instance_fingerprint" in e for e in s["errors"]))
 def test_leakage(self):
  r=self.rows();r[0]["model_input"]={"completed_trajectory":[]};self.assertFalse(ec.validate_dataset(r)["valid"])
 def test_overlap(self):
  r=self.rows();r[3]["utterance"]=r[0]["utterance"];self.assertFalse(ec.validate_dataset(r)["valid"])
 def test_coverage(self):
  r=self.rows();p=[x for x in self.preds(r) if not(x["method"]=="state_only" and x["instance_id"].endswith("language_holdout"))];self.assertFalse(ec.score(r,p)["valid"])
 def test_manifest_cartesian(self):
  with tempfile.TemporaryDirectory() as td:
   b=Path(td);raw=b/"r";model=b/"m";data=b/"d";raw.write_text("x");model.write_bytes(b"m");data.write_text("d");sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();runs=[]
   for seed in (1,7,19):
    for m in METHODS:runs.append({"method":m,"seed":seed,"domain":"rtfm_s1","split":"test","model_bytes":1,"peak_rss_bytes":2,"training_wall_seconds":1,"cpu_inference_ms_per_item":.1,"raw_log_path":"r","raw_log_sha256":sha(raw),"model_path":"m","model_sha256":sha(model),"data_path":"d","data_sha256":sha(data),"code_commit":"abc"})
   self.assertTrue(ec.audit_artifacts({"runs":runs},b)["valid"]);runs.pop();q=ec.audit_artifacts({"runs":runs},b);self.assertFalse(q["valid"]);self.assertGreater(q["missing_run_cells"],0)
if __name__=="__main__":unittest.main()
