from __future__ import annotations

import unittest

from minimal_predictive_lm.phase7_experiment import run


class ConversationAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run()

    def test_three_attempts_are_reproducible(self) -> None:
        attempts = self.result["attempts"]
        self.assertAlmostEqual(attempts[0]["turn_accuracy"], 6 / 17)
        self.assertAlmostEqual(attempts[1]["turn_accuracy"], 14 / 17)
        self.assertEqual(attempts[2]["turn_accuracy"], 1.0)

    def test_residual_phrase_patches_overfit_shifted_wording(self) -> None:
        self.assertEqual(self.result["residual_open_form_probe"]["accuracy"], 1.0)
        self.assertLess(self.result["shifted_open_form_probe"]["accuracy"], 1.0)

    def test_task_recovers_from_failed_first_patch(self) -> None:
        task = next(
            row for row in self.result["canonical"]["episodes"] if row["name"] == "task-with-recovery"
        )
        self.assertTrue(task["repo_ok"])
        self.assertIn("隠しテストで失敗", task["transcript"][0]["assistant"])

    def test_indexed_reads_do_not_grow_with_fact_count(self) -> None:
        rows = self.result["scaling"]
        self.assertEqual({row["indexed_query_reads"] for row in rows}, {1})
        self.assertGreater(rows[-1]["scan_query_reads"], rows[0]["scan_query_reads"])

    def test_repeated_dialogue_does_not_copy_transcript_into_state(self) -> None:
        row = self.result["long_dialogue_scaling"]
        self.assertEqual(row["facts_before"], row["facts_after"])
        self.assertEqual(row["state_bits_before"], row["state_bits_after"])
        self.assertEqual(row["fact_reads"], row["turns"])

    def test_candidate_search_is_still_linear(self) -> None:
        rows = self.result["candidate_search_scaling"]
        self.assertEqual(rows[-1]["candidate_evaluations"], 2 * rows[-1]["candidates"])


if __name__ == "__main__":
    unittest.main()
