from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_temporal_state import GenericTemporalMachine
from minimal_predictive_lm.phase15d_experiment import cross_domain_temporal_examples


class Phase15dGenericTemporalStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.machine = GenericTemporalMachine()
        cls.examples = {row.example_id: row for row in cross_domain_temporal_examples()}

    def test_cross_domain_temporal_examples(self) -> None:
        for row in self.examples.values():
            with self.subTest(row=row.example_id):
                self.assertEqual(self.machine.predict(row.prompt).output, row.target)

    def test_named_direct_date_and_calendar_boundary(self) -> None:
        prompt = (
            "Today is Apr 10, 1985. What is the date one week ago from today in MM/DD/YYYY?\n"
            "Options:\n(A) 04/03/1985\n(B) 04/17/1985\n(C) 03/10/1985"
        )
        prediction = self.machine.predict(prompt)
        self.assertEqual(prediction.output, "(A)")
        self.assertEqual(prediction.anchor_reason, "direct-today")

    def test_numeric_tomorrow_anchor(self) -> None:
        prompt = (
            "The meeting is tomorrow, 10/16/1924. "
            "What is the date one week from today in MM/DD/YYYY?\n"
            "Options:\n(A) 10/22/1924\n(B) 10/23/1924\n(C) 10/08/1924"
        )
        self.assertEqual(self.machine.predict(prompt).output, "(A)")

    def test_elapsed_days_and_month_shift(self) -> None:
        prompt = (
            "Mira started on Mar 20, 2020. 176 days have passed since then. "
            "What is the date a month ago in MM/DD/YYYY?\n"
            "Options:\n(A) 08/12/2020\n(B) 08/13/2020\n(C) 09/12/2020"
        )
        self.assertEqual(self.machine.predict(prompt).output, "(A)")

    def test_palindrome_date_is_derived_without_option_search(self) -> None:
        prompt = (
            "Today is the palindrome day of 2020, because MMDDYYYY reads the same backwards. "
            "What is the date tomorrow in MM/DD/YYYY?\n"
            "Options:\n(A) 02/03/2020\n(B) 01/03/2020\n(C) 03/02/2020"
        )
        self.assertEqual(self.machine.predict(prompt).output, "(A)")

    def test_missing_time_of_day_for_36_hours_abstains(self) -> None:
        prompt = (
            "2030 is coming in 36 hours. What is the date today in MM/DD/YYYY?\n"
            "Options:\n(A) 12/29/2029\n(B) 12/30/2029\n(C) 12/31/2029"
        )
        prediction = self.machine.predict(prompt)
        self.assertIsNone(prediction.output)
        self.assertEqual(prediction.anchor_reason, "time-of-day-ambiguous")

    def test_non_temporal_prompt_abstains(self) -> None:
        self.assertIsNone(self.machine.predict("Sort these values: c a b").output)
        self.assertEqual(self.machine.benchmark_task_name_branches, 0)
        self.assertGreater(self.machine.description_bits, 0)


if __name__ == "__main__":
    unittest.main()
