import unittest

from minimal_predictive_lm.mobile_hard_gate import (
    DeviceBenchmark,
    evaluate_device_benchmark,
    run_gate,
)
from minimal_predictive_lm.mobile_sparse_core import (
    CI_MOBILE_PROFILE,
    MAX_MODEL_PACKAGE_BYTES,
    MOBILE_1GB_PROFILE,
    MobilePagedSparseCore,
)


class MobileSparseCoreTests(unittest.TestCase):
    def test_serious_profile_hard_caps(self):
        gate = MOBILE_1GB_PROFILE.static_gate()
        self.assertTrue(gate["passed"])
        self.assertLessEqual(gate["package_bytes"], MAX_MODEL_PACKAGE_BYTES)
        self.assertGreater(gate["package_bytes"], 800_000_000)
        self.assertLessEqual(gate["active_weight_bytes_per_step"], 4_000_000)
        self.assertLessEqual(gate["macs_per_byte_step"], 2_000_000)

    def test_active_compute_is_below_one_percent_of_total_blocks(self):
        active = (
            MOBILE_1GB_PROFILE.active_groups
            * MOBILE_1GB_PROFILE.active_blocks_per_group
        )
        self.assertLess(active, MOBILE_1GB_PROFILE.total_blocks // 100)

    def test_learning_reduces_mixed_japanese_loss(self):
        core = MobilePagedSparseCore(CI_MOBILE_PROFILE, seed=3)
        texts = (
            "質問: 水は何度で凍る？ 答え: 標準気圧では0度。",
            "質問: 2x+3=9を解け。 答え: x=3。",
            "質問: 鎌倉幕府を開いた人物は？ 答え: 源頼朝。",
            "質問: Pythonで長さを得るには？ 答え: lenを使う。",
        )
        report = core.fit_texts(texts, epochs=5)
        self.assertLess(report.nll_after, report.nll_before)

    def test_chat_path_can_recall_taught_response(self):
        core = MobilePagedSparseCore(CI_MOBILE_PROFILE, seed=1)
        core.remember("こんにちは", "こんにちは。今日は何を考えましょうか？")
        self.assertEqual(
            core.generate("こんにちは"),
            "こんにちは。今日は何を考えましょうか？",
        )

    def test_report_never_claims_highschool_or_phone_pass(self):
        core = MobilePagedSparseCore(CI_MOBILE_PROFILE)
        report = core.report()
        self.assertFalse(report["highschool_level_passed"])
        self.assertFalse(report["mobile_device_gate_passed"])

    def test_reference_runtime_is_executable(self):
        core = MobilePagedSparseCore(CI_MOBILE_PROFILE)
        result = core.host_reference_benchmark(steps=20)
        self.assertGreater(result["byte_steps_per_second"], 0)

    def test_missing_real_phone_result_never_passes(self):
        result = run_gate()
        self.assertTrue(result["mechanism_passed"])
        self.assertFalse(result["mobile_device_gate_passed"])
        self.assertFalse(result["highschool_level_passed"])

    def test_actual_weak_android_result_must_meet_every_limit(self):
        passing = DeviceBenchmark(
            device_class="weak-android-phone",
            os_name="Android 14",
            architecture="arm64-v8a",
            physical_ram_bytes=3_000_000_000,
            model_package_bytes=905_003_008,
            peak_rss_bytes=310_000_000,
            first_byte_latency_ms=240.0,
            sustained_byte_steps_per_second=72.0,
            p95_step_latency_ms=16.0,
        )
        self.assertTrue(evaluate_device_benchmark(passing)["passed"])
        failing = DeviceBenchmark(
            **{**passing.__dict__, "peak_rss_bytes": 500_000_000}
        )
        self.assertFalse(evaluate_device_benchmark(failing)["passed"])


if __name__ == "__main__":
    unittest.main()
