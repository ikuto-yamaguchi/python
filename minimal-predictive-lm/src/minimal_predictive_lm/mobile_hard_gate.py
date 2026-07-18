from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import platform
from typing import Mapping

from .mobile_sparse_core import (
    CI_MOBILE_PROFILE,
    MOBILE_1GB_PROFILE,
    MobileHardLimits,
    MobilePagedSparseCore,
)


@dataclass(frozen=True)
class DeviceBenchmark:
    device_class: str
    os_name: str
    architecture: str
    physical_ram_bytes: int
    model_package_bytes: int
    peak_rss_bytes: int
    first_byte_latency_ms: float
    sustained_byte_steps_per_second: float
    p95_step_latency_ms: float


def evaluate_device_benchmark(
    benchmark: DeviceBenchmark,
    limits: MobileHardLimits = MobileHardLimits(),
) -> dict[str, object]:
    checks = {
        "declared_weak_phone": benchmark.device_class == "weak-android-phone",
        "actual_android": "android" in benchmark.os_name.lower(),
        "actual_arm64": benchmark.architecture.lower()
        in {"aarch64", "arm64-v8a", "arm64"},
        "physical_ram_at_most_4gb": benchmark.physical_ram_bytes <= 4_000_000_000,
        "model_at_most_1gb": benchmark.model_package_bytes
        <= limits.model_package_bytes_max,
        "peak_rss_within_limit": benchmark.peak_rss_bytes <= limits.peak_rss_bytes_max,
        "first_byte_fast_enough": benchmark.first_byte_latency_ms
        <= limits.first_byte_latency_ms_max,
        "sustained_speed_fast_enough": benchmark.sustained_byte_steps_per_second
        >= limits.sustained_byte_steps_per_second_min,
        "p95_step_fast_enough": benchmark.p95_step_latency_ms <= 20.0,
    }
    return {
        "benchmark": asdict(benchmark),
        "limits": asdict(limits),
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_gate(device_benchmark: DeviceBenchmark | None = None) -> dict[str, object]:
    static = MOBILE_1GB_PROFILE.static_gate()
    core = MobilePagedSparseCore(CI_MOBILE_PROFILE, seed=7)
    texts = (
        "質問: 2x+3=9を解け。 答え: x=3。",
        "質問: 水は標準気圧で何度で凍る？ 答え: 0度。",
        "質問: 鎌倉幕府を開いた人物は？ 答え: 源頼朝。",
        "質問: Pythonのリストの長さはどう得る？ 答え: lenを使う。",
        "質問: 慣性とは何か。 答え: 外力がなければ運動状態を保つ性質。",
    )
    training = core.fit_texts(texts, epochs=5)
    core.remember(
        "こんにちは",
        "こんにちは。まだ研究中ですが、会話経路は動作しています。",
    )
    chat_sample = core.generate("こんにちは")
    host = core.host_reference_benchmark(steps=500)
    device = (
        evaluate_device_benchmark(device_benchmark)
        if device_benchmark is not None
        else {
            "passed": False,
            "reason": (
                "No real weak Android phone result was supplied. Host speed and "
                "operation counts cannot substitute for the mandatory device gate."
            ),
        }
    )
    checks = {
        "serious_profile_static_gate": bool(static["passed"]),
        "strict_decimal_1gb_cap": static["package_bytes"] <= 1_000_000_000,
        "training_mechanics_improve": training.nll_after < training.nll_before,
        "chat_path_executable": bool(chat_sample),
        "native_kernel_required": True,
        "real_phone_gate_not_faked": (
            device_benchmark is not None or not bool(device["passed"])
        ),
    }
    return {
        "capability_id": "CAP-GEN-002-MOBILE-HARD-001",
        "static_profile": static,
        "training": asdict(training),
        "host_reference": {
            **host,
            "host_os": platform.platform(),
            "claim_boundary": "Reference only; this is not a phone benchmark.",
        },
        "chat_sample": chat_sample,
        "device_gate": device,
        "checks": checks,
        "mechanism_passed": all(checks.values()),
        "mobile_device_gate_passed": bool(device["passed"]),
        "cap_gen_002_passed": False,
        "highschool_level_passed": False,
        "claim_boundary": (
            "The 1 GB and sparse-compute architecture constraints are executable. "
            "Japanese high-school intelligence and weak-phone speed remain false "
            "until the same trained checkpoint passes broad frozen capability gates "
            "and a real low-end Android ARM64 benchmark."
        ),
    }


def render_markdown(result: Mapping[str, object]) -> str:
    static = result["static_profile"]
    training = result["training"]
    host = result["host_reference"]
    return "\n".join(
        [
            "# CAP-GEN-002 mobile hard gate",
            "",
            f"- Static mobile architecture passed: **{static['passed']}**",
            f"- Model package: **{static['package_bytes']:,} bytes**",
            f"- Active weights/byte step: **{static['active_weight_bytes_per_step']:,} bytes**",
            f"- MACs/byte step: **{static['macs_per_byte_step']:,}**",
            f"- Training NLL: **{training['nll_before']:.4f} -> {training['nll_after']:.4f}**",
            f"- Host reference speed: **{host['byte_steps_per_second']:.1f} byte steps/s**",
            f"- Real weak-phone gate passed: **{result['mobile_device_gate_passed']}**",
            f"- High-school level passed: **{result['highschool_level_passed']}**",
            "",
            "## Claim boundary",
            "",
            str(result["claim_boundary"]),
            "",
        ]
    )


def main() -> None:
    result = run_gate()
    output = Path("results")
    output.mkdir(exist_ok=True)
    (output / "cap_gen_002_mobile_hard.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "cap_gen_002_mobile_hard.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(render_markdown(result), end="")
    if not result["mechanism_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
