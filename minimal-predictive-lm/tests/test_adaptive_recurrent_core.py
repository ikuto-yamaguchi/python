import unittest

import numpy as np

from minimal_predictive_lm.adaptive_recurrent_core import (
    AdaptiveMultiScaleRecurrentCore,
)


class AdaptiveRecurrentCoreTests(unittest.TestCase):
    def test_joint_training_changes_shared_representation_and_reduces_loss(self):
        model = AdaptiveMultiScaleRecurrentCore(seed=11)
        texts = [
            "速度は距離を時間で割って求める。",
            "DNAには遺伝情報が保存される。",
            "関数の変化をグラフから読み取る。",
            "歴史上の出来事には原因と結果がある。",
        ] * 2
        embedding_before = model.embeddings.copy()
        input_before = model.input_projection.copy()
        recurrent_before = model.recurrent_left.copy()
        report = model.fit_texts(
            texts,
            epochs=8,
            learning_rate=0.04,
            feature_learning_rate=0.002,
        )
        self.assertLess(report.nll_after, report.nll_before * 0.75)
        self.assertFalse(np.array_equal(model.embeddings, embedding_before))
        self.assertFalse(np.array_equal(model.input_projection, input_before))
        self.assertFalse(np.array_equal(model.recurrent_left, recurrent_before))

    def test_joint_model_keeps_high_school_claim_false(self):
        model = AdaptiveMultiScaleRecurrentCore(seed=3)
        self.assertFalse(model.resource_report()["highschool_level_passed"])


if __name__ == "__main__":
    unittest.main()
