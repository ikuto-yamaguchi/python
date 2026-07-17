from __future__ import annotations

import unittest

from minimal_predictive_lm.sparc_relational_world import ACTUAL, FactKey, RelationalWorldLearner, parse_training_document
from minimal_predictive_lm.sparc_relational_world_gate import BASE_FAMILIES, NOVEL_FAMILIES, dialogue_probe, generate_documents


class RelationalWorldTest(unittest.TestCase):
    def setUp(self) -> None:
        self.items = ("鍵", "本", "地図", "箱")
        self.places = ("机", "棚", "教室", "図書館")
        self.people = ("太郎", "花子", "健")

    def test_raw_document_recovers_graph_transition(self) -> None:
        document = generate_documents(
            {"hidden_move": BASE_FAMILIES["hidden_move"]},
            1,
            self.items,
            self.places,
            self.people,
            per_template=1,
        )[0]
        before, event, after = parse_training_document(document)
        self.assertTrue(before)
        self.assertTrue(after)
        self.assertNotEqual(before, after)
        self.assertIsInstance(event, str)

    def test_false_belief_and_correction(self) -> None:
        model = RelationalWorldLearner()
        model.learn_documents(
            generate_documents(BASE_FAMILIES, 2, self.items, self.places, self.people, per_template=3),
            reset=True,
        )
        probe = dialogue_probe(model)
        self.assertEqual(probe["mismatch_answer"], "一致していません。")
        self.assertEqual(probe["comparison_answer"], "実際は棚、花子の認識は机です。")
        self.assertEqual(probe["corrected_answer"], "一致しています。")

    def test_continual_program_growth_without_reset(self) -> None:
        model = RelationalWorldLearner()
        self.assertEqual(
            model.learn_documents(
                generate_documents(BASE_FAMILIES, 3, self.items, self.places, self.people, per_template=3),
                reset=True,
            ),
            6,
        )
        self.assertEqual(
            model.learn_documents(
                generate_documents(NOVEL_FAMILIES, 4, self.items, self.places, self.people, per_template=3)
            ),
            8,
        )
        self.assertEqual(len(model.program_vectors), 8)

    def test_unknown_event_preserves_state_and_restore(self) -> None:
        model = RelationalWorldLearner()
        model.learn_documents(
            generate_documents(BASE_FAMILIES, 5, self.items, self.places, self.people, per_template=3),
            reset=True,
        )
        model.process("実際には鍵の位置は机だった。花子の認識では鍵の位置は机だった。")
        before = dict(model.state)
        result = model.process("鍵は量子霧へ瞬間変換された")
        self.assertEqual(result.status, "abstained")
        self.assertEqual(model.state, before)
        restored = RelationalWorldLearner.from_bytes(model.to_bytes())
        self.assertEqual(restored.state[FactKey(ACTUAL, "位置", "鍵")], "机")


if __name__ == "__main__":
    unittest.main()
