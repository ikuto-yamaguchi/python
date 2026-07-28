import unittest

from audit_episode_cluster_statistics import audit
from evaluation_contract import instance_fingerprint


METHODS = ["correct", "random", "language_blind", "state_only", "target_label_shuffle", "outcome_shuffle"]


def dataset(with_episode=True):
    rows = []
    for seed in (1, 7, 19):
        for episode in range(2):
            for step in range(3):
                row = {
                    "instance_id": f"{seed}-{episode}-{step}",
                    "domain": "rtfm",
                    "seed": seed,
                    "split": "test",
                    "condition": "in_distribution",
                    "utterance": [seed, episode],
                    "state_before": [step],
                    "gold_action": 1,
                    "gold_state_after": [step + 1],
                }
                if with_episode:
                    row["episode_id"] = f"{seed}-{episode}"
                rows.append(row)
    return rows


def predictions(rows):
    result = []
    for row in rows:
        for method in METHODS:
            correct = method == "correct"
            result.append({
                "instance_id": row["instance_id"],
                "method": method,
                "instance_fingerprint": instance_fingerprint(row),
                "pred_action": 1 if correct else 0,
                "pred_state_after": row["gold_state_after"] if correct else [-1],
            })
    return result


class EpisodeClusterStatisticsTest(unittest.TestCase):
    def test_valid_complete_bundle(self):
        rows = dataset()
        result = audit(rows, predictions(rows))
        self.assertTrue(result["valid"], result["errors"])
        action = result["comparisons_vs_correct"]["random"]["action"]
        self.assertEqual(action["paired_episodes"], 6)
        self.assertEqual(action["paired_steps"], 18)
        self.assertGreater(action["episode_cluster_bootstrap_ci95_low"], 0)

    def test_missing_episode_id_fails(self):
        rows = dataset(with_episode=False)
        result = audit(rows, predictions(rows))
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "initial_reproduction_failure")
        self.assertTrue(any("missing episode_id" in error for error in result["errors"]))

    def test_incomplete_control_coverage_fails(self):
        rows = dataset()
        preds = [row for row in predictions(rows) if not (row["method"] == "state_only" and row["instance_id"] == "19-1-2")]
        result = audit(rows, preds)
        self.assertFalse(result["valid"])
        self.assertTrue(any("state_only" in error and "incomplete coverage" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
