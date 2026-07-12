from __future__ import annotations

import unittest

from minimal_predictive_lm.generic_state_machine import GenericStateMachine
from minimal_predictive_lm.generic_temporal_state import GenericTemporalMachine
from minimal_predictive_lm.phase16a_experiment import frozen_phase15d_fingerprint
from minimal_predictive_lm.phase16a_public_benchmarks import PHASE16A_TASKS


class Phase16aFrozenThirdSliceTests(unittest.TestCase):
    def test_third_slice_has_five_distinct_tasks_and_axes(self) -> None:
        self.assertEqual(len(PHASE16A_TASKS), 5)
        axes = {str(config["axis"]) for config in PHASE16A_TASKS.values()}
        self.assertEqual(len(axes), 5)
        for task, config in PHASE16A_TASKS.items():
            self.assertTrue(task)
            self.assertRegex(str(config["blob_sha1"]), r"^[0-9a-f]{40}$")
            self.assertEqual(config["answer_type"], "exact")

    def test_frozen_phase15d_fingerprint_is_deterministic(self) -> None:
        self.assertEqual(frozen_phase15d_fingerprint(), frozen_phase15d_fingerprint())

    def test_existing_state_and_temporal_machines_have_no_task_name_branches(self) -> None:
        self.assertEqual(GenericStateMachine().benchmark_task_name_branches, 0)
        self.assertEqual(GenericTemporalMachine().benchmark_task_name_branches, 0)


if __name__ == "__main__":
    unittest.main()
