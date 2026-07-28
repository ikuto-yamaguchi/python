#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest import mock

import audit_score_dataset_contract_binding as audit


class ScoreDatasetContractBindingTests(unittest.TestCase):
    def test_valid_binding_passes(self) -> None:
        dataset_report = {"valid": True, "errors": []}
        score_report = {
            "valid": True,
            "classification": "qualified",
            "dataset_contract_binding": True,
            "dataset_contract_valid": True,
            "cells": [{"method": "correct"}],
            "summary": {"correct": {"action": 1.0}},
            "paired_gaps_vs_correct": {},
        }
        with mock.patch.object(audit.contract, "validate_dataset", return_value=dataset_report), mock.patch.object(
            audit.contract, "score", return_value=score_report
        ):
            report = audit.audit_score_dataset_contract_binding([], [])
        self.assertTrue(report["valid"])

    def test_invalid_dataset_must_not_emit_statistics(self) -> None:
        dataset_report = {"valid": False, "errors": ["duplicate instance_id=x"]}
        score_report = {
            "valid": False,
            "classification": "initial_reproduction_failure",
            "dataset_contract_binding": True,
            "dataset_contract_valid": False,
            "cells": [{"method": "correct"}],
            "summary": {"correct": {"action": 1.0}},
            "paired_gaps_vs_correct": {"random": {"action": {"mean_gap": 1.0}}},
        }
        with mock.patch.object(audit.contract, "validate_dataset", return_value=dataset_report), mock.patch.object(
            audit.contract, "score", return_value=score_report
        ):
            report = audit.audit_score_dataset_contract_binding([], [])
        self.assertFalse(report["valid"])
        self.assertEqual(report["classification"], "initial_reproduction_failure")
        self.assertIn("cells", report["errors"][0])

    def test_missing_binding_declaration_fails(self) -> None:
        dataset_report = {"valid": True, "errors": []}
        score_report = {
            "valid": True,
            "classification": "qualified",
            "dataset_contract_valid": True,
            "cells": [],
            "summary": {},
            "paired_gaps_vs_correct": {},
        }
        with mock.patch.object(audit.contract, "validate_dataset", return_value=dataset_report), mock.patch.object(
            audit.contract, "score", return_value=score_report
        ):
            report = audit.audit_score_dataset_contract_binding([], [])
        self.assertFalse(report["valid"])
        self.assertIn(
            "score artifact does not declare dataset_contract_binding=true",
            report["errors"],
        )

    def test_binding_validity_mismatch_fails(self) -> None:
        dataset_report = {"valid": False, "errors": ["seed topology invalid"]}
        score_report = {
            "valid": False,
            "classification": "initial_reproduction_failure",
            "dataset_contract_binding": True,
            "dataset_contract_valid": True,
            "cells": [],
            "summary": {},
            "paired_gaps_vs_correct": {},
        }
        with mock.patch.object(audit.contract, "validate_dataset", return_value=dataset_report), mock.patch.object(
            audit.contract, "score", return_value=score_report
        ):
            report = audit.audit_score_dataset_contract_binding([], [])
        self.assertFalse(report["valid"])
        self.assertIn("does not match", report["errors"][-1])


if __name__ == "__main__":
    unittest.main()
