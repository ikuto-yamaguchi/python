import tempfile
import unittest
from pathlib import Path

from minimal_predictive_lm.event_ledger_closure import EventLedger, Episode, run, training_episodes


class EventLedgerClosureTests(unittest.TestCase):
    def test_does_not_store_complete_answers(self):
        model = EventLedger()
        episode = Episode(("文脈",), "鍵は机にある。", "鍵を棚へ移した。", "鍵は棚にある。", "秘密の完成回答")
        model.observe(episode)
        model.observe(episode)
        model.consolidate()
        payload = str(model.events)
        self.assertNotIn("秘密の完成回答", payload)

    def test_capacity_bounds_readout(self):
        model = EventLedger(capacity=7)
        for episode in training_episodes(128, 1):
            model.observe(episode)
        model.consolidate(minimum_support=1)
        model.reset()
        model.step(("文脈",), "未知発話")
        self.assertLessEqual(model.reads, 7)

    def test_report_claim_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run(Path(tmp))
        self.assertFalse(report["highschool_level_passed"])
        self.assertFalse(report["native_japanese_communication_passed"])
        self.assertTrue(report["under_1gb"])
        self.assertEqual(report["largest_scale"]["candidate_count"], 1)
        self.assertEqual(len(report["results"]), 12)


if __name__ == "__main__":
    unittest.main()
