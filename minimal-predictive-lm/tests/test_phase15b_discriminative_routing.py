from __future__ import annotations

import unittest

from minimal_predictive_lm.phase15b_experiment import build_guarded_algebra_model


NAVIGATION_PROMPT = (
    "If you follow these instructions, do you return to the starting point? "
    "Always face forward. Take 1 step left. Take 1 step right.\n"
    "Options:\n- Yes\n- No"
)


class Phase15bDiscriminativeRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = build_guarded_algebra_model()

    def test_minimal_discriminative_cue_drops_broad_these_feature(self) -> None:
        self.assertNotIn("these", self.model.ordering.required_cues)
        self.assertEqual(self.model.ordering.required_cues, ("sort",))
        self.assertGreater(self.model.ordering.candidate_cue_sets, 0)

    def test_unseen_ordering_still_transfers(self) -> None:
        prediction = self.model.predict(
            "Sort these API names alphabetically: render apply emit"
        )
        self.assertEqual(prediction.output, "apply emit render")

    def test_navigation_options_do_not_trigger_ordering(self) -> None:
        self.assertIsNone(self.model.predict(NAVIGATION_PROMPT).output)

    def test_non_ordering_colon_prompts_do_not_trigger(self) -> None:
        prompts = (
            "Process these records: gamma alpha beta",
            "Compare these values: 7 3 9",
            "Copy these labels: rollback apply verify",
            "Follow these steps: open inspect close",
        )
        self.assertTrue(all(self.model.predict(prompt).output is None for prompt in prompts))

    def test_expression_algebra_is_unchanged(self) -> None:
        self.assertEqual(self.model.predict("2 * -3 =").output, -6)
        self.assertIs(self.model.predict("not False or False is").output, True)
        self.assertEqual(self.model.domain_specific_handlers, 0)


if __name__ == "__main__":
    unittest.main()
