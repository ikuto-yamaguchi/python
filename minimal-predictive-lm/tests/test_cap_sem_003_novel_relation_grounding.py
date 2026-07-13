import pytest

from minimal_predictive_lm.cap_sem_001_relational_meaning import (
    build_training_records,
    learn_meaning,
)
from minimal_predictive_lm.cap_sem_002_raw_japanese_bridge import (
    build_raw_training_records,
    learn_surface_bridge,
)
from minimal_predictive_lm.cap_sem_003_novel_relation_grounding import (
    RawExample,
    build_ambiguous_calibration,
    build_lexical_training_records,
    build_novel_alias_heldout,
    evaluate_novel_aliases,
    extend_semantic_model,
    learn_lexical_extension,
    run_gate,
)


def _models():
    base = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), base)
    training, aliases = build_lexical_training_records()
    extension = learn_lexical_extension(training, bridge, base)
    return base, bridge, training, aliases, extension


def test_complete_capability_gate_passes():
    result = run_gate()
    assert result["passed"] is True
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["new_relation_concept_creation"] is False


def test_eight_novel_aliases_transfer_to_multihop_records():
    base, bridge, _, aliases, extension = _models()
    model = extend_semantic_model(base, extension)
    evaluation = evaluate_novel_aliases(
        build_novel_alias_heldout(aliases), bridge, model
    )
    assert len(extension.marker_codes) == 8
    assert evaluation.correct == evaluation.total == 128


def test_alias_renaming_is_relearned_from_usage():
    base = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), base)
    training, aliases = build_lexical_training_records(alias_prefix="別")
    extension = learn_lexical_extension(training, bridge, base)
    evaluation = evaluate_novel_aliases(
        build_novel_alias_heldout(aliases, template_variant=2),
        bridge,
        extend_semantic_model(base, extension),
    )
    assert evaluation.correct == evaluation.total == 128


def test_ambiguous_evidence_is_rejected():
    base = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), base)
    with pytest.raises(ValueError):
        learn_lexical_extension(build_ambiguous_calibration(), bridge, base)


def test_contradictory_evidence_is_rejected():
    base, bridge, training, _, _ = _models()
    contradictory = training[:1] + (
        RawExample(training[0].text, not training[0].answer),
    )
    with pytest.raises(ValueError):
        learn_lexical_extension(contradictory, bridge, base)


def test_unregistered_marker_does_not_silently_map():
    base, bridge, _, aliases, extension = _models()
    model = extend_semantic_model(base, extension)
    row = build_novel_alias_heldout(aliases)[0]
    known_alias = next(iter(extension.marker_codes))
    unknown = RawExample(
        row.text.replace(known_alias, "未登録関係"), row.answer
    )
    evaluation = evaluate_novel_aliases((unknown,), bridge, model)
    assert evaluation.coverage == 0
