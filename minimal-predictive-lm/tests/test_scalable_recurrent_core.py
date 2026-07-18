import unittest

from minimal_predictive_lm.scalable_recurrent_core import (
    CI_PROFILE,
    LOCAL_4060_PROFILE,
    SCALE_PROFILE,
    MultiScaleRecurrentCore,
)


class ScalableRecurrentCoreTests(unittest.TestCase):
    def test_serious_profiles_are_not_two_kilobyte_toys(self):
        self.assertGreaterEqual(
            LOCAL_4060_PROFILE.persistent_bytes(), 128 * 1024 * 1024
        )
        self.assertGreater(
            SCALE_PROFILE.persistent_bytes(),
            LOCAL_4060_PROFILE.persistent_bytes(),
        )
        self.assertLessEqual(
            LOCAL_4060_PROFILE.training_peak_bytes(), 8 * 1024**3
        )
        self.assertIn("not-a-high-school-candidate", CI_PROFILE.name)

    def test_shared_sequence_training_reduces_mixed_japanese_loss(self):
        model = MultiScaleRecurrentCore(seed=1)
        texts = [
            "日本の高校生は数学を学ぶ。",
            "物体の速度は距離を時間で割る。",
            "鎌倉幕府は歴史上の政権である。",
        ] * 2
        report = model.fit_texts(
            texts, epochs=8, learning_rate=0.04
        )
        self.assertLess(report.nll_after, report.nll_before * 0.75)
        self.assertGreater(report.updates, 0)

    def test_associative_memory_is_shared_and_task_name_free(self):
        model = MultiScaleRecurrentCore(seed=2)
        model.remember("速度はどう求める？", "距離を時間で割る。")
        model.remember("鎌倉幕府とは？", "日本史上の武家政権。")
        self.assertEqual(
            model.answer("速度はどう求める？"),
            "距離を時間で割る。",
        )
        self.assertIsNone(model.answer("DNAの役割は？"))

    def test_resource_report_counts_allocated_arrays_and_refuses_claim(self):
        model = MultiScaleRecurrentCore()
        report = model.resource_report()
        self.assertGreater(report["actual_persistent_bytes"], 2000)
        self.assertFalse(report["transformer_used"])
        self.assertFalse(report["task_names_supplied"])
        self.assertFalse(report["highschool_level_passed"])


if __name__ == "__main__":
    unittest.main()
