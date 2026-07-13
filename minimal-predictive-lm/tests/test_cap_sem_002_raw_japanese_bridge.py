import pytest

from minimal_predictive_lm.cap_sem_001_relational_meaning import (
    build_training_records,
    learn_meaning,
)
from minimal_predictive_lm.cap_sem_002_raw_japanese_bridge import (
    RawExample,
    build_raw_training_records,
    evaluate_raw,
    learn_surface_bridge,
    parse_raw_example,
    render_raw_heldout,
    run_gate,
)


def _bridge():
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    return semantic, bridge


def test_complete_capability_gate_passes():
    result = run_gate()
    assert result["passed"] is True
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["high_school_intelligence"] is False


def test_raw_parser_recovers_unseen_multihop_records():
    semantic, bridge = _bridge()
    evaluation = evaluate_raw(bridge, semantic, render_raw_heldout())
    assert evaluation.correct == evaluation.total == 128
    assert evaluation.coverage == 128


def test_unknown_relation_marker_is_rejected():
    _, bridge = _bridge()
    example = RawExample(
        "未知00は未知01より謎。未知00は未知01より以前？", True
    )
    with pytest.raises(ValueError):
        parse_raw_example(bridge, example)


def test_malformed_clause_and_query_terminator_are_rejected():
    _, bridge = _bridge()
    with pytest.raises(ValueError):
        parse_raw_example(bridge, RawExample("甲は乙よりさき？", True))
    with pytest.raises(ValueError):
        parse_raw_example(
            bridge, RawExample("甲は乙よりさき。甲は乙より以前。", True)
        )


def test_alternate_punctuation_is_relearned_not_hardcoded():
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(
        build_raw_training_records(
            statement_separator="；", query_terminator="！"
        ),
        semantic,
    )
    evaluation = evaluate_raw(
        bridge,
        semantic,
        render_raw_heldout(
            template_variant=2,
            statement_separator="；",
            query_terminator="！",
        ),
    )
    assert bridge.statement_separator == "；"
    assert bridge.query_terminator == "！"
    assert evaluation.correct == evaluation.total == 128


def test_surface_bridge_keeps_frozen_semantic_runtime():
    semantic = learn_meaning(build_training_records())
    before = semantic.payload()
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    evaluate_raw(bridge, semantic, render_raw_heldout(template_variant=1))
    assert semantic.payload() == before
    assert bridge.behavioral_classes == 1
    assert bridge.orientation_assignments_evaluated == 64
