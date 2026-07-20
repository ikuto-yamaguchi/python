import unittest

from minimal_predictive_lm.exchange_binding_closure import (
    Episode,
    ExchangeBindingClosure,
    experiment,
    split_change,
)


class ExchangeBindingClosureTests(unittest.TestCase):
    def test_split_change_finds_replaced_span(self):
        left, right, prefix, suffix = split_change("葵が鍵を持つ", "蓮が鍵を持つ")
        self.assertEqual((left, right, prefix, suffix), ("葵", "蓮", "", "が鍵を持つ"))

    def test_model_is_bounded(self):
        model = ExchangeBindingClosure(max_rules=4, max_reads=2)
        episodes = [
            Episode("葵が鍵を持つ", "葵が鍵を持つ状態です"),
            Episode("蓮が鍵を持つ", "蓮が鍵を持つ状態です"),
            Episode("凛が鍵を持つ", "凛が鍵を持つ状態です"),
        ]
        model.fit(episodes)
        model.generate("湊が鍵を持つ")
        self.assertLessEqual(len(model.rules), 4)
        self.assertLessEqual(model.last_reads, 2)

    def test_decoy_and_integrated_gate_are_reported(self):
        report = experiment()
        self.assertFalse(report["highschool_level_passed"])
        self.assertFalse(report["native_japanese_communication_passed"])
        self.assertIn("max_decoy_rules", report["aggregate"])
        self.assertEqual(len(report["results"]), 9)
        self.assertTrue(all(result["candidate_count"] == 1 for result in report["results"]))


if __name__ == "__main__":
    unittest.main()
