#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('m',Path(__file__).with_name('evaluation_contract_silg_episode.py'));assert SPEC and SPEC.loader
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
class T(unittest.TestCase):
 def payload(self,strict=False):
  methods=['correct','random','language_blind','state_only','language_shuffle']
  if strict:methods+=['target_label_shuffle','outcome_shuffle']
  runs=[]
  for seed in (1,7,19):
   for method in methods:
    records=[{'episode_seed':seed*1000003+i,'initial_instance_fingerprint':f'f-{seed}-{i}','win':1.0 if method=='correct' else 0.0,'return':1.0 if method=='correct' else -1.0,'length':10} for i in range(3)]
    runs.append({'method':method,'seed':seed,'episodes':3,'episode_records':records})
  return {'environment':'silg:rtfm_test_s1-v0','all_initial_streams_match':True,'source_pins':{'silg':'x','rtfm':'y'},'checkpoints':{str(s):{'bytes':1,'sha256':'a'*64} for s in (1,7,19)},'runs':runs}
 def test_structural_but_incomplete(self):
  q=m.audit(self.payload());self.assertTrue(q['structurally_valid']);self.assertFalse(q['valid']);self.assertIn('target_label_shuffle',q['warnings'][0]);self.assertEqual(q['paired_gaps_vs_correct']['random']['win']['correct_only'],9)
 def test_strict_complete(self):
  q=m.audit(self.payload(True));self.assertTrue(q['valid']);self.assertEqual(q['classification'],'matched_episode_reproduced')
 def test_fingerprint_mismatch(self):
  p=self.payload(True);p['runs'][1]['episode_records'][0]['initial_instance_fingerprint']='bad';q=m.audit(p);self.assertFalse(q['structurally_valid']);self.assertTrue(any('fingerprint mismatch' in e for e in q['errors']))
 def test_seed_missing(self):
  p=self.payload(True);p['runs']=[r for r in p['runs'] if r['seed']!=19];p['checkpoints'].pop('19');q=m.audit(p);self.assertFalse(q['valid']);self.assertTrue(any('canonical seeds' in e for e in q['errors']))
if __name__=='__main__':unittest.main()
