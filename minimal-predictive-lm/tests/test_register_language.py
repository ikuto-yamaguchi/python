import unittest

import numpy as np

from minimal_predictive_lm.registers import (
    BIT_ONE,
    BIT_ZERO,
    KEY_BASE,
    QUERY,
    Phase,
    RegisterLanguage,
    RegisterState,
    register_cost,
)


class RegisterLanguageTests(unittest.TestCase):
    def test_distributions_are_normalized(self) -> None:
        language = RegisterLanguage(4)
        states = [
            RegisterState(0, Phase.READY),
            RegisterState(0, Phase.WRITE_KEY),
            RegisterState(0, Phase.WRITE_VALUE, 2),
            RegisterState(5, Phase.QUERY_KEY),
            RegisterState(5, Phase.QUERY_VALUE, 2),
        ]
        for state in states:
            self.assertTrue(np.isclose(language.next_distribution(state).sum(), 1.0))

    def test_write_then_query_is_exact(self) -> None:
        language = RegisterLanguage(8)
        state = language.initial_state
        values = (1, 0, 1, 1, 0, 0, 1, 0)
        for key, value in enumerate(values):
            state = language.write(state, key, value)
        for key, value in enumerate(values):
            tokens = language.query_tokens(state, key)
            self.assertEqual(tokens, (QUERY, KEY_BASE + key, BIT_ONE if value else BIT_ZERO))
            state = language.query(state, key)

    def test_all_memory_assignments_are_predictively_distinguishable(self) -> None:
        language = RegisterLanguage(4)
        for first in range(1 << language.key_count):
            for second in range(first + 1, 1 << language.key_count):
                difference = first ^ second
                key = (difference & -difference).bit_length() - 1
                first_query = RegisterState(first, Phase.QUERY_VALUE, key)
                second_query = RegisterState(second, Phase.QUERY_VALUE, key)
                self.assertFalse(
                    np.array_equal(
                        language.next_distribution(first_query),
                        language.next_distribution(second_query),
                    )
                )

    def test_factored_memory_meets_information_lower_bound(self) -> None:
        for key_count in (1, 2, 4, 8, 16, 32):
            cost = register_cost(RegisterLanguage(key_count))
            self.assertEqual(cost.predictive_memory_lower_bound_bits, key_count)
            self.assertEqual(cost.factored_data_memory_bits, key_count)
            self.assertEqual(cost.flat_ready_states, 1 << key_count)


if __name__ == "__main__":
    unittest.main()
