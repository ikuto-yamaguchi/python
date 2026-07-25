import json
import tempfile
import unittest
from pathlib import Path

from audit_r02_holdout_assignments import audit, load_jsonl


class HoldoutAssignmentAuditTest(unittest.TestCase):
    def write_rows(self, rows):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "data.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return directory, path

    def valid_rows(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({
                "instance_id": f"train-{seed}", "seed": seed, "split": "train",
                "entity_signature": f"train-e-{seed}",
                "dynamics_signature": f"train-d-{seed}",
                "language_form_signature": f"train-l-{seed}",
            })
            for condition, field, prefix in (
                ("entity_holdout", "entity_signature", "held-e"),
                ("dynamics_holdout", "dynamics_signature", "held-d"),
                ("language_holdout", "language_form_signature", "held-l"),
            ):
                row = {
                    "instance_id": f"{condition}-{seed}", "seed": seed, "split": "test",
                    "entity_holdout": False, "dynamics_holdout": False, "language_holdout": False,
                    "entity_signature": f"test-e-{seed}",
                    "dynamics_signature": f"test-d-{seed}",
                    "language_form_signature": f"test-l-{seed}",
                }
                row[condition] = True
                row[field] = f"{prefix}-{seed}"
                rows.append(row)
        return rows

    def test_valid_three_seed_holdouts_pass(self):
        directory, path = self.write_rows(self.valid_rows())
        self.addCleanup(directory.cleanup)
        self.assertEqual(audit(load_jsonl(path), path)["status"], "pass")

    def test_current_placeholder_pattern_fails(self):
        rows = []
        for seed in (1, 7, 19):
            rows.append({"seed": seed, "split": "train"})
            rows.append({
                "seed": seed, "split": "test", "entity_holdout": False,
                "dynamics_holdout": False, "language_holdout": True,
            })
        directory, path = self.write_rows(rows)
        self.addCleanup(directory.cleanup)
        result = audit(load_jsonl(path), path)
        self.assertEqual(result["status"], "initial_reproduction_failure")
        self.assertTrue(any("placeholder entity" in item for item in result["failures"]))
        self.assertTrue(any("wholesale" in item for item in result["failures"]))

    def test_signature_overlap_fails(self):
        rows = self.valid_rows()
        train_signature = next(row["entity_signature"] for row in rows if row["split"] == "train")
        target = next(row for row in rows if row.get("entity_holdout"))
        target["entity_signature"] = train_signature
        directory, path = self.write_rows(rows)
        self.addCleanup(directory.cleanup)
        result = audit(load_jsonl(path), path)
        self.assertEqual(result["status"], "initial_reproduction_failure")
        self.assertGreater(result["cells"]["entity_holdout"]["train_overlap_count"], 0)


if __name__ == "__main__":
    unittest.main()
