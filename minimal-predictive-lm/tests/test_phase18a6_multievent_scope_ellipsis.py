from __future__ import annotations
import unittest
from minimal_predictive_lm import phase18a6_multievent_scope_ellipsis as phase


class Phase18a6DiscourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model, cls.fit = phase.induce(phase.training())
        cls.heldout = phase.heldout()

    def test_campaign_passes_all_gates(self) -> None:
        payload = phase.run()
        failed = [name for name, passed in payload["theorem_checks"].items() if not passed]
        self.assertEqual(failed, [])
        self.assertTrue(payload["all_theorem_checks_pass"])

    def test_connector_and_ellipsis_rules_are_recovered(self) -> None:
        self.assertEqual(dict(self.model.connectors), phase.TRUE_C)
        self.assertEqual(phase.emap(self.model.ellipsis), phase.TRUE_E)

    def test_unseen_joint_compositions_transfer(self) -> None:
        self.assertEqual(phase.score(self.model, self.heldout), (1.0, 1.0))

    def test_commuting_data_cannot_identify_order(self) -> None:
        self.assertTrue(phase.commuting_nonid())

    def test_causal_interventions(self) -> None:
        self.assertEqual(phase.interventions(self.model), (True, True, True))

    def test_unknown_connector_and_ellipsis_abstain(self) -> None:
        self.assertEqual(phase.unknowns(self.model), (True, True))


if __name__ == "__main__":
    unittest.main()
