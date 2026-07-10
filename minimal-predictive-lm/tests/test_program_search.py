import unittest

import numpy as np

from minimal_predictive_lm.program_search import sample_tokens, search_register_programs
from minimal_predictive_lm.registers import RegisterLanguage


class ProgramSearchTests(unittest.TestCase):
    def test_mdl_search_recovers_minimum_register_count_and_address_rule(self) -> None:
        language = RegisterLanguage(4)
        tokens = sample_tokens(language, 30_000, np.random.default_rng(3))
        results = search_register_programs(tokens, maximum_slots=8)
        best = results[0]
        self.assertEqual(best.slots, 4)
        self.assertEqual(best.write_offset, 0)
        self.assertEqual(best.errors, 0)


if __name__ == "__main__":
    unittest.main()
