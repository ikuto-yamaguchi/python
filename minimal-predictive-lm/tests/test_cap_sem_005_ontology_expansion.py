import pytest

from minimal_predictive_lm.cap_sem_001_relational_meaning import (
    build_heldout_records,
    build_training_records,
    learn_meaning,
    predict,
)
from minimal_predictive_lm.cap_sem_002_raw_japanese_bridge import (
    build_raw_training_records,
    learn_surface_bridge,
)
from minimal_predictive_lm.cap_sem_005_ontology_expansion import (
    NEW_QUERY_GROUPS,
    NEW_STATEMENT_GROUPS,
    _renamed_groups,
    build_new_relation_heldout,
    build_ontology_calibration,
    evaluate_dynamic,
    extend_semantic_model,
    learn_ontology_extension,
    predict_dynamic,
    run_gate,
)


def _dependencies():
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    return semantic, bridge


def test_complete_capability_gate_passes():
    result = run_gate()
    assert result["passed"] is True
    assert result["new_relation_pairs"] == 1
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["high_school_intelligence"] is False


def test_new_pair_extends_without_colliding_with_old_codes():
    semantic, bridge = _dependencies()
    extension = learn_ontology_extension(
        build_ontology_calibration(semantic), bridge, semantic
    )
    assert extension.new_relation_pairs == 1
    assert len(extension.marker_codes) == 8
    assert not (set(extension.inverse_codes) & set(semantic.inverse_codes))
    combined = extend_semantic_model(semantic, extension)
    assert len(combined.inverse_codes) == len(semantic.inverse_codes) + 2


def test_generic_runtime_preserves_all_old_predictions():
    semantic, _ = _dependencies()
    records = build_heldout_records(seed=20260717, size=128)
    expected = tuple(predict(semantic, row)[0] for row in records)
    observed = tuple(predict_dynamic(semantic, row)[0] for row in records)
    assert observed == expected


def test_new_pair_handles_multihop_chains():
    semantic, bridge = _dependencies()
    extension = learn_ontology_extension(
        build_ontology_calibration(semantic), bridge, semantic
    )
    model = extend_semantic_model(semantic, extension)
    evaluation = evaluate_dynamic(model, build_new_relation_heldout())
    assert evaluation.correct == evaluation.total == 128


def test_duplicate_existing_relation_does_not_expand_ontology():
    semantic, bridge = _dependencies()
    extension = learn_ontology_extension(
        build_ontology_calibration(
            semantic,
            statement_groups=_renamed_groups(NEW_STATEMENT_GROUPS, "既"),
            query_groups=_renamed_groups(NEW_QUERY_GROUPS, "既"),
            duplicate_existing_pair=True,
        ),
        bridge,
        semantic,
    )
    assert extension.new_relation_pairs == 0
    assert extension.mapped_to_existing == 8


def test_incomplete_inverse_pair_is_rejected():
    semantic, bridge = _dependencies()
    calibration = build_ontology_calibration(semantic)
    incomplete = tuple(
        row
        for row in calibration
        if not any(marker in row.text for marker in NEW_QUERY_GROUPS[1])
    )
    with pytest.raises(ValueError):
        learn_ontology_extension(incomplete, bridge, semantic)


def test_contradictory_behavior_is_rejected():
    semantic, bridge = _dependencies()
    calibration = build_ontology_calibration(semantic)
    contradictory = calibration + (
        type(calibration[-1])(
            calibration[-1].text, not calibration[-1].answer
        ),
    )
    with pytest.raises(ValueError):
        learn_ontology_extension(contradictory, bridge, semantic)
