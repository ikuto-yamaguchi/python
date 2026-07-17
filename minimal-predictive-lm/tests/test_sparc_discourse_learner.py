import unittest
from minimal_predictive_lm.sparc_discourse_learner import DiscourseTextbookLearner
from minimal_predictive_lm.sparc_open_textbook_gate import RELATIONS,QUERIES,base_training,train_queries

class DiscourseLearnerTests(unittest.TestCase):
    def model(self):
        m=DiscourseTextbookLearner(); records,_,chains=base_training(); m.learn_paragraphs(records); m.induce_rules(min_support=6); train_queries(m,chains); return m
    def test_single_exposure_chain_and_anaphora(self):
        m=self.model(); text=RELATIONS['tax'][3].format(a='ラッコ',b='哺乳類')+'この分類群は脊椎動物の一種である。この分類群は動物の一種である。'
        r=m.read_document(text,'doc'); self.assertEqual((r.accepted,r.resolved_anaphors),(3,2))
        a=m.ask(QUERIES['tax']['closure'][0].format(a='ラッコ')); self.assertEqual(a.value,'動物'); self.assertEqual(len(a.proof),3)
    def test_unknown_document_does_not_mutate(self):
        m=self.model(); before=set(m.facts); r=m.read_document('未知概念は不可思議に共鳴する。これは無限へ跳躍する。','u'); self.assertEqual(r.accepted,0); self.assertEqual(before,set(m.facts))
    def test_round_trip(self):
        m=self.model(); m.read_document(RELATIONS['loc'][3].format(a='研究棟',b='大学')+'この地域は茨城県に位置する。','d'); restored=DiscourseTextbookLearner.from_bytes(m.to_bytes()); self.assertEqual(restored.documents,1)

if __name__=='__main__':unittest.main()
