from __future__ import annotations

import unittest

from minimal_predictive_lm.continuous_stream_induction import (
    event_precision_recall,
    infer_continuous_stream,
    split_continuous_stream,
)
from minimal_predictive_lm.phase11e_experiment import run


class ContinuousStreamInductionTests(unittest.TestCase):
    def test_splits_continuous_text_without_record_objects(self) -> None:
        rows = split_continuous_stream(
            "alpha became ALPHA success. beta became BETA success; noise only."
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].text, "alpha became ALPHA success")
        self.assertEqual(rows[1].text, "beta became BETA success")

    def test_infers_roles_and_ignores_single_character_distractor(self) -> None:
        inference = infer_continuous_stream(
            "if retry quartz to QUARTZ failed evidence run7. "
            "unrelated x changed to y."
        )
        self.assertEqual(len(inference.events), 1)
        event = inference.events[0]
        self.assertEqual(event.source, "quartz")
        self.assertEqual(event.target, "QUARTZ")
        self.assertEqual(event.result, "failure")
        self.assertTrue(event.has_condition)
        self.assertEqual(event.provenance, "run7")

    def test_induces_two_shared_primitives_without_channel_metadata(self) -> None:
        inference = infer_continuous_stream(
            "sphinx to SPHINX success source a. "
            "quartz to QUARTZ success source b. "
            "VOW to vow success source c. "
            "ZEBRA to zebra success source d."
        )
        self.assertEqual(len(inference.clusters), 2)
        offsets = {cluster.primitive.offset for cluster in inference.clusters}
        self.assertEqual(offsets, {-32, 32})

    def test_unseen_stream_uses_same_event_representation(self) -> None:
        inference = infer_continuous_stream(
            "feature changed into FEATURE passed source repo. "
            "if recovery MOTOR to motor success evidence sensor."
        )
        expected = {
            ("feature", "FEATURE", "success", False, "repo"),
            ("MOTOR", "motor", "success", True, "sensor"),
        }
        precision, recall = event_precision_recall(inference.events, expected)
        self.assertEqual(precision, 1.0)
        self.assertEqual(recall, 1.0)

    def test_phase11e_reports_success_without_general_parity_claim(self) -> None:
        payload = run()
        self.assertTrue(payload["verdict"]["phase11e_success"])
        self.assertFalse(payload["verdict"]["open_ended_stream_grounding_achieved"])
        self.assertFalse(payload["comparison_readiness"]["multi_domain_llm_parity_ready"])
        self.assertFalse(payload["comparison_readiness"]["stage_c_score_changed"])


if __name__ == "__main__":
    unittest.main()
