from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_reference_machine import (
    ReferenceCandidate,
    ReferenceSituation,
)
from minimal_predictive_lm.phase16g_experiment import (
    build_reference_machine,
    calibration_observations,
    heldout_situations,
)


class Phase16gGenericReferenceMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.machine = build_reference_machine()

    def test_calibration_and_structured_heldout_are_exact(self) -> None:
        for observation in calibration_observations():
            with self.subTest(expected=observation.expected):
                self.assertEqual(
                    self.machine.predict(observation.situation).output,
                    observation.expected,
                )
        for name, situation, expected in heldout_situations():
            with self.subTest(case=name):
                self.assertEqual(self.machine.predict(situation).output, expected)

    def test_structural_control_outweighs_semantics_and_semantics_recency(self) -> None:
        weights = self.machine.weight_map()
        self.assertGreater(weights["object_control"], weights["semantic_fit"])
        self.assertGreater(weights["subject_control"], weights["semantic_fit"])
        self.assertGreater(weights["semantic_fit"], weights["recency"])
        self.assertEqual(weights["semantic_fit"], weights["possessive_link"])
        self.assertEqual(weights["subject_continuity"], weights["possessive_link"])

    def test_agreement_is_a_hard_filter(self) -> None:
        situation = ReferenceSituation(
            (
                ReferenceCandidate.build(
                    "incompatible",
                    compatible=False,
                    object_control=1,
                    semantic_fit=1,
                ),
                ReferenceCandidate.build("compatible", recency=1),
            )
        )
        prediction = self.machine.predict(situation)
        self.assertEqual(prediction.output, "compatible")
        self.assertEqual(dict(prediction.scores)["incompatible"], None)

    def test_tie_and_nonpositive_evidence_are_ambiguous(self) -> None:
        tie = ReferenceSituation(
            (
                ReferenceCandidate.build("left", semantic_fit=1),
                ReferenceCandidate.build("right", possessive_link=1),
            )
        )
        neutral = ReferenceSituation(
            (
                ReferenceCandidate.build("left"),
                ReferenceCandidate.build("right"),
            )
        )
        self.assertIsNone(self.machine.predict(tie).output)
        self.assertIsNone(self.machine.predict(neutral).output)
        self.assertTrue(self.machine.predict(tie).ambiguous)
        self.assertTrue(self.machine.predict(neutral).ambiguous)

    def test_incompatible_irrelevant_candidate_does_not_change_resolution(self) -> None:
        base = ReferenceSituation(
            (
                ReferenceCandidate.build("controller", object_control=1),
                ReferenceCandidate.build("other", semantic_fit=1),
            )
        )
        augmented = ReferenceSituation(
            base.candidates
            + (
                ReferenceCandidate.build(
                    "irrelevant",
                    compatible=False,
                    object_control=1,
                    semantic_fit=1,
                ),
            )
        )
        self.assertEqual(self.machine.predict(base).output, "controller")
        self.assertEqual(self.machine.predict(augmented).output, "controller")

    def test_evidence_ablation_restores_ambiguity(self) -> None:
        resolved = ReferenceSituation(
            (
                ReferenceCandidate.build("controller", object_control=1),
                ReferenceCandidate.build("other"),
            )
        )
        ablated = ReferenceSituation(
            (
                ReferenceCandidate.build("controller"),
                ReferenceCandidate.build("other"),
            )
        )
        self.assertEqual(self.machine.predict(resolved).output, "controller")
        self.assertIsNone(self.machine.predict(ablated).output)

    def test_machine_has_no_task_name_or_domain_handler(self) -> None:
        self.assertEqual(self.machine.benchmark_task_name_branches, 0)
        self.assertEqual(self.machine.domain_specific_handlers, 0)
        self.assertGreater(self.machine.description_bits, 0)
        self.assertEqual(self.machine.calibration_examples, 17)


if __name__ == "__main__":
    unittest.main()
