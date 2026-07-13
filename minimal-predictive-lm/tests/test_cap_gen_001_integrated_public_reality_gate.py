from minimal_predictive_lm.benchmark_harness import (
    BenchmarkExample,
    build_manifest,
)
from minimal_predictive_lm.cap_gen_001_integrated_public_reality_gate import (
    PUBLIC_AGGREGATE_TARGET,
    PUBLIC_AXIS_TARGET,
    _prefixed_examples,
    readiness_decision,
)


def _axes(*accuracies: float):
    return {
        f"axis_{index}": {
            "accuracy": accuracy,
            "examples": 40,
            "answered": 40,
            "correct": int(40 * accuracy),
            "coverage": 1.0,
        }
        for index, accuracy in enumerate(accuracies)
    }


def test_prefixing_prevents_cross_slice_id_collisions():
    source = build_manifest(
        name="source",
        split="test",
        source="local",
        license_id="test",
        public=True,
        examples=(BenchmarkExample("same", "axis", "q", "a"),),
    )
    first = _prefixed_examples(source, "first")
    second = _prefixed_examples(source, "second")
    assert first[0].example_id != second[0].example_id
    assert first[0].prompt == second[0].prompt == "q"


def test_reality_gate_requires_aggregate_and_every_axis_floor():
    passed = readiness_decision(
        _axes(*([PUBLIC_AXIS_TARGET] * 15)),
        PUBLIC_AGGREGATE_TARGET,
    )
    assert passed["public_reasoning_proxy_passed"] is True
    assert passed["architecture_pivot_required"] is False

    failed_floor = readiness_decision(
        _axes(0.69, *([0.81] * 14)),
        0.80,
    )
    assert failed_floor["public_reasoning_proxy_passed"] is False
    assert failed_floor["architecture_pivot_required"] is True
    assert failed_floor["weak_axes"] == ("axis_0",)


def test_public_proxy_never_authorizes_high_school_or_llm_claim():
    result = readiness_decision(_axes(*([1.0] * 15)), 1.0)
    assert result["public_reasoning_proxy_passed"] is True
    assert result["japanese_high_school_claim_allowed"] is False
    assert result["general_llm_parity_allowed"] is False
