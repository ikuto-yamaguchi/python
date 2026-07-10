from __future__ import annotations

import unittest

from minimal_predictive_lm.phase6_experiment import (
    chain_case,
    parity_case,
    repeated_query_case,
)


class Phase6ScalingTests(unittest.TestCase):
    def test_factorized_chain_meets_state_lower_bound(self) -> None:
        result = chain_case(256)
        self.assertEqual(
            result["factorized_runtime_state_bits"],
            result["state_lower_bound_bits"],
        )
        self.assertGreater(result["program_compression_ratio"], 100.0)
        self.assertEqual(result["required_steps"], 256)

    def test_parity_separates_description_state_and_reads(self) -> None:
        result = parity_case(20)
        self.assertEqual(result["parity_runtime_state_bits"], 1)
        self.assertEqual(result["required_input_reads"], 20)
        self.assertGreater(result["description_compression_ratio"], 10_000.0)

    def test_workload_specific_memo_beats_generic_alternatives(self) -> None:
        result = repeated_query_case(64, 100)
        self.assertLess(
            result["single_query_memo_total_bit_accesses"],
            result["on_demand_total_bit_accesses"],
        )
        self.assertLess(
            result["single_query_memo_total_bit_accesses"],
            result["full_closure_total_bit_accesses"],
        )

    def test_invalid_sizes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            chain_case(0)
        with self.assertRaises(ValueError):
            parity_case(0)
        with self.assertRaises(ValueError):
            repeated_query_case(1, 0)


if __name__ == "__main__":
    unittest.main()
