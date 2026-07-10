import unittest
from itertools import product

from minimal_predictive_lm.causal import discover_exact_causal_machine
from minimal_predictive_lm.hankel import exact_hankel, numerical_rank, spectral_realization
from minimal_predictive_lm.processes import iid_process, modulo_ones_process


class ExactRecoveryTests(unittest.TestCase):
    def assert_word_probabilities_match(self, process, model, maximum_length: int = 8) -> None:
        for length in range(maximum_length + 1):
            for word in product(process.alphabet, repeat=length):
                self.assertLess(
                    abs(process.probability(word) - model.probability(word)), 1e-10
                )

    def test_iid_has_no_predictive_state_memory(self) -> None:
        process = iid_process()
        _, _, hankel = exact_hankel(process, 4)
        self.assertEqual(numerical_rank(hankel), 1)
        machine = discover_exact_causal_machine(process, history_length=6, future_horizon=3)
        self.assertEqual(machine.state_count, 1)
        self.assertEqual(machine.runtime_state_bits, 0)
        self.assert_word_probabilities_match(process, machine)

    def test_modulo_process_recovers_known_minimum_state(self) -> None:
        for state_count in range(2, 7):
            with self.subTest(state_count=state_count):
                process = modulo_ones_process(state_count)
                hankel_length = max(1, state_count - 1)
                _, _, hankel = exact_hankel(process, hankel_length)
                rank = numerical_rank(hankel)
                self.assertEqual(rank, state_count)

                spectral = spectral_realization(process, hankel_length, rank)
                machine = discover_exact_causal_machine(
                    process,
                    history_length=max(6, state_count),
                    future_horizon=3,
                )
                self.assertEqual(machine.state_count, state_count)
                self.assert_word_probabilities_match(process, spectral)
                self.assert_word_probabilities_match(process, machine)


if __name__ == "__main__":
    unittest.main()
