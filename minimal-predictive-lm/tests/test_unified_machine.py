from __future__ import annotations

import unittest

from minimal_predictive_lm.phase5_experiment import run


class UnifiedMachineTests(unittest.TestCase):
    def test_one_substrate_solves_three_task_families(self) -> None:
        result = run()
        self.assertEqual(
            result["core_primitives"],
            ["MATCH", "DELETE", "ADD", "EMIT", "CHOOSE_MIN"],
        )

        coding = result["tasks"]["coding"]
        self.assertEqual(coding["output"], ["def f(x): return 3 * x + 1"])
        self.assertEqual(coding["trace"], ["patch:a=3,b=1"])

        writing = result["tasks"]["writing"]
        self.assertEqual(len(writing["output"]), 3)
        self.assertEqual(
            writing["trace"],
            ["write:intro-concise", "write:method", "write:caveat"],
        )

        agent = result["tasks"]["agent"]
        self.assertEqual(
            agent["trace"],
            ["move:lab->hall", "move:hall->vault", "pickup:key"],
        )

    def test_state_ids_remain_compact(self) -> None:
        result = run()
        self.assertLessEqual(result["runtime_bits_per_symbol"], 8)


if __name__ == "__main__":
    unittest.main()
