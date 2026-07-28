#!/usr/bin/env python3
from __future__ import annotations

import unittest

from audit_r02_gaddy_klein_fidelity import audit


class R02GaddyKleinFidelityAuditTests(unittest.TestCase):
    @staticmethod
    def rows(*, entity: bool = False, language: bool = False) -> list[dict]:
        rows: list[dict] = []
        for seed in (1, 7, 19):
            for split in ("train", "test"):
                for action in (0, 1, 2):
                    is_test = split == "test"
                    rows.append(
                        {
                            "instance_id": f"{split}-{seed}-{action}",
                            "episode_id": f"{split}-{seed}-{action}",
                            "seed": seed,
                            "split": split,
                            "domain": "rtfm_s1",
                            "state_before": [0.0, 1.0],
                            "state_after": [1.0, 0.0],
                            "text_tokens": [seed, action] if split == "train" else [99, seed, action],
                            "action": action,
                            "reward": 1.0 if is_test and action == 0 else 0.0,
                            "done": is_test and action == 0,
                            "dynamics_holdout": is_test,
                            "entity_holdout": is_test and entity,
                            "language_holdout": is_test and language,
                        }
                    )
        return rows

    @staticmethod
    def metadata(**transfer_support: str) -> dict:
        return {
            "state_schema": [
                {"name": "x", "type": "continuous", "start": 0, "end": 1},
                {"name": "flag", "type": "binary", "start": 1, "end": 2},
            ],
            "transfer_support": transfer_support,
        }

    def test_conditional_entity_and_language_holdouts_may_be_unsupported(self) -> None:
        result = audit(
            self.rows(),
            self.metadata(
                dynamics_holdout="supported",
                entity_holdout="unsupported",
                language_holdout="unsupported",
            ),
        )
        self.assertEqual("eligible", result["status"])
        self.assertEqual(
            "unsupported",
            result["transfer_support"]["entity_holdout"]["effective_status"],
        )
        self.assertEqual(
            "unsupported",
            result["transfer_support"]["language_holdout"]["effective_status"],
        )

    def test_required_dynamics_holdout_cannot_be_omitted(self) -> None:
        rows = self.rows()
        for row in rows:
            row["dynamics_holdout"] = False
        result = audit(rows, self.metadata(dynamics_holdout="supported"))
        self.assertEqual("blocked", result["status"])
        self.assertTrue(
            any("required dynamics_holdout" in error for error in result["errors"]),
            result["errors"],
        )

    def test_supported_conditional_holdout_requires_real_examples(self) -> None:
        result = audit(
            self.rows(),
            self.metadata(
                dynamics_holdout="supported",
                entity_holdout="supported",
                language_holdout="unsupported",
            ),
        )
        self.assertEqual("blocked", result["status"])
        self.assertTrue(
            any("entity_holdout is declared supported" in error for error in result["errors"]),
            result["errors"],
        )

    def test_examples_cannot_be_declared_unsupported(self) -> None:
        result = audit(
            self.rows(entity=True),
            self.metadata(
                dynamics_holdout="supported",
                entity_holdout="unsupported",
                language_holdout="unsupported",
            ),
        )
        self.assertEqual("blocked", result["status"])
        self.assertTrue(
            any("entity_holdout has test examples" in error for error in result["errors"]),
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
