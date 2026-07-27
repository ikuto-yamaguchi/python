#!/usr/bin/env python3
import copy
import unittest

import evaluation_contract as contract


def row(instance_id, seed, split, utterance):
    return {
        "instance_id": instance_id,
        "domain": "rtfm",
        "seed": seed,
        "split": split,
        "condition": "in_distribution",
        "utterance": utterance,
        "state_before": {"x": seed},
        "gold_action": 0,
        "gold_state_after": {"x": seed + 1},
    }


class CanonicalInstanceIdentityCoreTest(unittest.TestCase):
    def test_unicode_width_alias_is_rejected(self):
        rows = []
        for seed in sorted(contract.CANONICAL_SEEDS):
            rows.append(row(f"train-{seed}", seed, "train", f"train utterance {seed}"))
            rows.append(row(f"Episode-{seed}", seed, "test", f"test utterance {seed}"))
        rows.append(row("ＥＰＩＳＯＤＥ－１", 1, "test", "another test utterance"))
        audit = contract.validate_dataset(rows)
        self.assertFalse(audit["valid"])
        self.assertTrue(audit["canonical_instance_identity_required"])
        self.assertTrue(audit["instance_id_collisions"])
        self.assertTrue(any("duplicate canonical instance_id" in error for error in audit["errors"]))

    def test_whitespace_format_only_id_is_rejected(self):
        rows = [row("\u200b \t", seed, "train" if seed == 1 else "test", f"u-{seed}") for seed in sorted(contract.CANONICAL_SEEDS)]
        audit = contract.validate_dataset(rows)
        self.assertFalse(audit["valid"])
        self.assertTrue(any("non-empty after canonicalization" in error for error in audit["errors"]))

    def test_prediction_alias_is_not_bound_to_dataset_instance(self):
        rows = []
        for seed in sorted(contract.CANONICAL_SEEDS):
            rows.append(row(f"train-{seed}", seed, "train", f"train utterance {seed}"))
            rows.append(row(f"Episode-{seed}", seed, "test", f"test utterance {seed}"))
        target = next(item for item in rows if item["instance_id"] == "Episode-1")
        prediction = {
            "instance_id": "ＥＰＩＳＯＤＥ－１",
            "method": "correct",
            "instance_fingerprint": contract.instance_fingerprint(target),
            "pred_action": target["gold_action"],
            "pred_state_after": copy.deepcopy(target["gold_state_after"]),
        }
        result = contract.score(rows, [prediction])
        self.assertFalse(result["valid"])
        self.assertFalse(result["statistics_emitted"])
        self.assertTrue(result["exact_prediction_instance_id_required"])
        self.assertTrue(any("non-exact instance_id alias" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
