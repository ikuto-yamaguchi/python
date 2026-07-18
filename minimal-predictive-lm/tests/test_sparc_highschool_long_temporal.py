import random
import unittest

from minimal_predictive_lm.sparc_highschool_general import Edit, Program, World
from minimal_predictive_lm.sparc_highschool_long_temporal import LongTemporalNarrativeLearner


def numeric_corpus():
    rows = []
    for subject, value in [("青箱", 2), ("赤容器", 4), ("大型倉庫", 7), ("小型ケース", 9)]:
        rows += [f"{subject}には{value}個ある", f"{value}個入っている対象は{subject}だ", f"{subject}の個数は{value}である"]
    for subject, value in [("試料甲", 10), ("検体乙", 20), ("素材丙", 15), ("サンプル丁", 25)]:
        rows += [f"{subject}の温度は{value}度である", f"{value}度を示す対象は{subject}だ", f"{subject}は温度{value}度の状態にある"]
    records = [(text, f"N{index}") for index, text in enumerate(rows)]
    random.Random(23).shuffle(records)
    return records


def long_corpus():
    return [
        ("朝の記録を始める。箱Aには2個ある。窓の外は曇っている。箱Aに3個加える。担当者がメモを取った。箱Aには5個ある。作業を終了した。", "L1"),
        ("箱Bには4個ある。試料Xの温度は10度である。箱Bに3個加える。時計が正午を示した。箱Bには7個ある。試料Xの温度は10度である。", "L2"),
        ("箱Aには3個ある。別室では会議が続いた。箱Aを2倍にする。確認者が到着した。箱Aには6個ある。", "L3"),
        ("箱Bには5個ある。雨音が聞こえた。箱Bを2倍にする。記録用紙を交換した。箱Bには10個ある。", "L4"),
        ("試料Aの温度は10度である。箱Qには1個ある。試料Aの温度を5度上げる。装置のランプが点灯した。箱Qには1個ある。試料Aの温度は15度である。", "L5"),
        ("試料Bの温度は20度である。担当者が席を外した。試料Bの温度を5度上げる。数分後に担当者が戻った。試料Bの温度は25度である。", "L6"),
    ]


class LongTemporalNarrativeLearnerTests(unittest.TestCase):
    def make_learner(self):
        learner = LongTemporalNarrativeLearner()
        learner.learn_independent_numeric_documents(numeric_corpus())
        return learner

    @staticmethod
    def fact_program():
        return Program(
            "P",
            (),
            (Edit("add_fact", "R", 0, 1),),
            {
                "<V0>は<V1>である",
                "<V0>というものは<V1>に分類される",
                "歴史上の<V0>は一つの<V1>だった",
                "<V1>の仲間に数えられるものが<V0>だ",
                "<V0>を分類すると<V1>に入る",
            },
        )

    def test_discovers_delayed_events_with_distractors(self):
        learner = self.make_learner()
        result = learner.learn_long_chronological_documents(long_corpus())
        self.assertEqual(result.transitions_found, 6)
        self.assertEqual(len(learner.programs), 3)
        self.assertGreaterEqual(result.distractor_sentences_ignored, 8)
        self.assertGreaterEqual(result.maximum_delay, 3)
        report = learner.report()
        self.assertFalse(report["fixed_three_sentence_layout_supplied"])
        self.assertFalse(report["event_boundaries_supplied"])

    def test_aligns_partial_literal_boundaries_without_global_replacement(self):
        bindings, score, reads = LongTemporalNarrativeLearner._schema_bind(
            self.fact_program(), "歴史上の鎌倉幕府は政権の仲間に数えられる"
        )
        self.assertEqual(bindings, ("鎌倉幕府", "政権"))
        self.assertGreaterEqual(score, 0.76)
        self.assertGreater(reads, 0)

    def test_slot_order_anchor_lattice_composes_all_unseen_boundaries(self):
        program = self.fact_program()
        cases = {
            "酸素は気体に分類される": ("酸素", "気体"),
            "歴史上の鎌倉幕府は政権の仲間に数えられる": ("鎌倉幕府", "政権"),
            "正方形というものは図形である": ("正方形", "図形"),
            "銅を分類すると金属だった": ("銅", "金属"),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                bindings, score, reads = LongTemporalNarrativeLearner._schema_bind(program, text)
                self.assertEqual(bindings, expected)
                self.assertGreaterEqual(score, 0.80)
                self.assertGreater(reads, 0)

    def test_reversed_surface_order_keeps_semantic_roles(self):
        program = self.fact_program()
        bindings, score, _reads = LongTemporalNarrativeLearner._schema_bind(
            program, "金属の仲間に数えられるものが銅だ"
        )
        self.assertEqual(bindings, ("銅", "金属"))
        self.assertGreaterEqual(score, 0.80)

    def test_handles_interleaved_observations_by_latent_state_key(self):
        learner = self.make_learner()
        text = (
            "箱Aには2個ある。試料Aの温度は10度である。"
            "箱Aに3個加える。誰かが窓を開けた。箱Aには5個ある。"
            "試料Aの温度を5度上げる。外では雨が降った。試料Aの温度は15度である。"
        )
        result = learner.learn_long_chronological_document(text, "I")
        self.assertEqual(result.transitions_found, 2)
        self.assertEqual(len(learner.programs), 2)

    def test_rejects_ambiguous_two_event_explanation(self):
        learner = self.make_learner()
        text = "箱Aには2個ある。箱Aに3個加える。箱Aを3増やす。箱Aには5個ある。"
        result = learner.learn_long_chronological_document(text, "A")
        self.assertEqual(result.transitions_found, 0)
        self.assertEqual(result.ambiguous_transitions, 1)
        self.assertEqual(len(learner.programs), 0)

    def test_transfers_delayed_program_after_serialization(self):
        learner = self.make_learner()
        learner.learn_long_chronological_documents(long_corpus())
        restored = LongTemporalNarrativeLearner.from_bytes(learner.to_bytes())
        before = restored.observe_world(["箱Zには9個ある"]).world
        result = restored.apply("箱Zに3個加える", before)
        self.assertTrue(result.accepted)
        self.assertIn(12, result.world.number_map().values())


if __name__ == "__main__":
    unittest.main()
