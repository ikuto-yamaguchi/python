from __future__ import annotations

import unittest

from minimal_predictive_lm.phase18a7_recursive_conditional_discourse import (
    HELDOUT_PROGRAMS,
    TRUE_CONDITION,
    TRUE_NEGATION,
    TRUE_REFERENCE,
    TRUE_SEQUENCE,
    causal_interventions,
    heldout_observations,
    induce,
    observational_nonidentifiability_controls,
    run,
    score,
    sentence_memorizer_coverage,
    shallow_parser_coverage,
    training_observations,
    tree_memorizer_coverage,
    unknowns_abstain,
)


class Phase18a7RecursiveConditionalDiscourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = training_observations()
        cls.heldout = heldout_observations()
        cls.model, cls.fit = induce(cls.training)

    def test_campaign_passes_every_theorem_gate(self) -> None:
        payload = run()
        failed = [
            name
            for name, passed in payload["theorem_checks"].items()
            if not passed
        ]
        self.assertEqual(failed, [])
        self.assertTrue(payload["all_theorem_checks_pass"])

    def test_all_operator_meanings_are_recovered(self) -> None:
        self.assertEqual(dict(self.model.sequence), TRUE_SEQUENCE)
        self.assertEqual(dict(self.model.condition), TRUE_CONDITION)
        self.assertEqual(dict(self.model.negation), TRUE_NEGATION)
        self.assertEqual(dict(self.model.reference), TRUE_REFERENCE)
        self.assertEqual(self.fit["candidates"], 16)
        self.assertEqual(self.fit["errors"], 8)
        self.assertGreater(self.fit["second"], self.fit["errors"])

    def test_recursive_heldout_transfers_without_memorization(self) -> None:
        self.assertEqual(score(self.model, self.heldout), (1.0, 1.0))
        self.assertEqual(
            sentence_memorizer_coverage(self.training, self.heldout),
            0.0,
        )
        self.assertEqual(
            tree_memorizer_coverage(self.training, self.heldout),
            0.0,
        )
        self.assertEqual(shallow_parser_coverage(self.heldout), 0.0)
        self.assertEqual(len(HELDOUT_PROGRAMS), 6)

    def test_observationally_symmetric_controls_are_non_identifying(self) -> None:
        controls = observational_nonidentifiability_controls()
        self.assertTrue(all(controls.values()), controls)

    def test_internal_operator_interventions_are_causal(self) -> None:
        interventions = causal_interventions(self.model)
        self.assertTrue(all(interventions.values()), interventions)

    def test_unknown_reference_operator_and_malformed_tree_abstain(self) -> None:
        self.assertTrue(unknowns_abstain(self.model))

    def test_claim_boundary_remains_strict(self) -> None:
        payload = run()
        boundary = payload["claim_boundary"]
        self.assertTrue(boundary["controlled_recursive_discourse"])
        self.assertFalse(boundary["unbracketed_general_japanese"])
        self.assertFalse(boundary["reading_comprehension"])
        self.assertFalse(boundary["high_school_intelligence"])


if __name__ == "__main__":
    unittest.main()
