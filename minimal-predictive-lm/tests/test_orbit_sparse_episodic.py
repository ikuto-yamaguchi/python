from __future__ import annotations

import unittest

from minimal_predictive_lm.orbit_sparse_episodic import (
    Binding,
    Memory,
    SparseEpisodicOrbit,
    apply,
    evaluate,
    induce,
)


class SparseEpisodicOrbitTest(unittest.TestCase):
    def test_induce_and_apply(self) -> None:
        before = "赤箱にはりんごが8個あります。青箱にはりんごが8個あります。"
        after = "赤箱にはりんごが6個あります。青箱にはりんごが10個あります。"
        binding = induce(before, after)
        self.assertEqual(binding, Binding("赤箱", "青箱", "りんご", 2))
        assert binding is not None
        self.assertEqual(apply(before, binding), after)

    def test_sparse_readout_is_capacity_bounded(self) -> None:
        model = SparseEpisodicOrbit(3)
        model.memories = [Memory(Binding("赤箱", "青箱", "りんご", 1), step) for step in range(5)]
        state = "赤箱にはりんごが8個あります。青箱にはりんごが8個あります。"
        model.predict("直前と同じ操作を1個続けた。", state)
        self.assertLessEqual(model.readouts, 3)

    def test_heldout_paraphrase_failure_is_reproducible(self) -> None:
        result = evaluate(seed=0, ntrain=96, ntest=50)
        self.assertGreater(float(result["accuracy"]), 0.45)
        self.assertLess(float(result["accuracy"]), 0.90)
        self.assertLess(int(result["model_bytes"]), 100_000)


if __name__ == "__main__":
    unittest.main()
