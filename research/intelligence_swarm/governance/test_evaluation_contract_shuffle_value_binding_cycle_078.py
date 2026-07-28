#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

CORE = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")
spec = importlib.util.spec_from_file_location("evaluation_contract", CORE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def row(iid, action, after):
    return {
        "instance_id": iid,
        "domain": "rtfm",
        "seed": 1,
        "split": "test",
        "condition": "entity_holdout",
        "utterance": iid,
        "state_before": {"x": iid},
        "gold_action": action,
        "gold_state_after": after,
    }


class ShuffleValueBindingTest(unittest.TestCase):
    def setUp(self):
        self.a = row("a", 1, {"s": "A"})
        self.b = row("b", 2, {"s": "B"})
        self.by_id = {"a": self.a, "b": self.b}
        self.eval_ids = {"a", "b"}

    def pred(self, method, iid, donor, action, after):
        return {
            "method": method,
            "instance_id": iid,
            "instance_fingerprint": mod.instance_fingerprint(self.by_id[iid]),
            "pred_action": action,
            "pred_state_after": after,
            "control_source_instance_id": donor,
            "control_source_fingerprint": mod.instance_fingerprint(self.by_id[donor]),
        }

    def test_valid_donor_bound_shuffles_pass(self):
        preds = [
            self.pred("target_label_shuffle", "a", "b", 2, {"free": 1}),
            self.pred("target_label_shuffle", "b", "a", 1, {"free": 2}),
            self.pred("outcome_shuffle", "a", "b", 99, {"s": "B"}),
            self.pred("outcome_shuffle", "b", "a", 98, {"s": "A"}),
        ]
        errors, audit = mod._validate_shuffle_assignments(preds, self.by_id, self.eval_ids)
        self.assertEqual(errors, [])
        self.assertTrue(audit["target_label_shuffle"]["donor_value_binding_required"])
        self.assertTrue(audit["outcome_shuffle"]["donor_value_binding_required"])

    def test_target_label_shuffle_arbitrary_value_fails(self):
        preds = [
            self.pred("target_label_shuffle", "a", "b", 1, {}),
            self.pred("target_label_shuffle", "b", "a", 1, {}),
        ]
        errors, _ = mod._validate_shuffle_assignments(preds, self.by_id, self.eval_ids)
        self.assertTrue(any("pred_action is not bound" in error for error in errors))

    def test_outcome_shuffle_arbitrary_value_fails(self):
        preds = [
            self.pred("outcome_shuffle", "a", "b", 0, {"s": "A"}),
            self.pred("outcome_shuffle", "b", "a", 0, {"s": "A"}),
        ]
        errors, _ = mod._validate_shuffle_assignments(preds, self.by_id, self.eval_ids)
        self.assertTrue(any("pred_state_after is not bound" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
