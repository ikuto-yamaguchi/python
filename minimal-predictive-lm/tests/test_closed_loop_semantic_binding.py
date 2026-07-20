import unittest

from minimal_predictive_lm.closed_loop_semantic_binding import (
    ClosedLoopSemanticBinding,
    Episode,
    trajectory_signature,
)


class ClosedLoopSemanticBindingTests(unittest.TestCase):
    def test_full_trajectory_distinguishes_same_immediate_effect(self):
        model = ClosedLoopSemanticBinding()
        color = Episode("色を教えて", (0, 0, 0), (0, 0, 0), (1, 0, 0), (1, 1, 0))
        decoy = Episode("今日の天気は", (0, 0, 0), (0, 0, 0), (0, 0, 1), (1, 0, 1))
        color_id = model.observe(color)
        self.assertNotEqual(trajectory_signature(color), trajectory_signature(decoy))
        self.assertIsNone(model.infer_from_trajectory(decoy))
        self.assertEqual(model.infer_from_trajectory(color), color_id)

    def test_one_grounded_episode_enables_later_form_recall(self):
        model = ClosedLoopSemanticBinding()
        known = Episode("色を教えて", (1, 2, 3), (1, 2, 3), (2, 2, 3), (2, 3, 3))
        unseen = Episode("何色なの", (4, 0, 1), (4, 0, 1), (5, 0, 1), (5, 1, 1))
        operation = model.observe(known)
        self.assertEqual(model.infer_from_trajectory(unseen), operation)
        model.observe(unseen)
        self.assertEqual(model.infer_known("何色なの"), operation)

    def test_unknown_language_without_trajectory_remains_unknown(self):
        model = ClosedLoopSemanticBinding()
        model.observe(Episode("場所はどこ", (0, 0, 0), (0, 0, 0), (0, 0, 1), (1, 0, 1)))
        self.assertIsNone(model.infer_known("所在地はどちらですか"))


if __name__ == "__main__":
    unittest.main()
