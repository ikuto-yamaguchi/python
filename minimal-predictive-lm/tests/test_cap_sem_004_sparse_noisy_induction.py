import pytest

from minimal_predictive_lm.cap_sem_001_relational_meaning import (
    build_training_records,
    learn_meaning,
)
from minimal_predictive_lm.cap_sem_002_raw_japanese_bridge import (
    build_raw_training_records,
    learn_surface_bridge,
)
from minimal_predictive_lm.cap_sem_004_sparse_noisy_induction import (
    ALTERNATE_DEFINITION_TEMPLATES,
    _renamed_groups,
    build_sparse_evidence_corpus,
    learn_sparse_lexicon,
    run_gate,
)
from minimal_predictive_lm.cap_sem_003_open_relation_grounding import (
    NOVEL_QUERY_GROUPS,
    NOVEL_STATEMENT_GROUPS,
)


def _frozen_dependencies():
    semantic = learn_meaning(build_training_records())
    bridge = learn_surface_bridge(build_raw_training_records(), semantic)
    return semantic, bridge


def test_complete_capability_gate_passes():
    result = run_gate()
    assert result["passed"] is True
    assert result["heldout_accuracy"] == 1.0
    assert result["heldout_coverage"] == 1.0
    assert result["intentionally_corrupted_documents"] == 16
    assert result["new_relation_concept_creation"] is False


def test_sparse_noisy_corpus_grounds_all_sixteen_markers():
    semantic, bridge = _frozen_dependencies()
    corpus = build_sparse_evidence_corpus(semantic)
    lexicon = learn_sparse_lexicon(corpus, bridge, semantic)
    assert len(lexicon.statement_codes) == 8
    assert len(lexicon.query_codes) == 8
    assert lexicon.accepted_corruptions >= 16
    assert len(lexicon.connector_deltas) == 4


def test_insufficient_usage_is_rejected():
    semantic, bridge = _frozen_dependencies()
    corpus = build_sparse_evidence_corpus(semantic, usage_limit=2)
    with pytest.raises(ValueError):
        learn_sparse_lexicon(corpus, bridge, semantic)


def test_excess_noise_is_rejected():
    semantic, bridge = _frozen_dependencies()
    corpus = build_sparse_evidence_corpus(semantic, noise_per_marker=3)
    with pytest.raises(ValueError):
        learn_sparse_lexicon(corpus, bridge, semantic)


def test_aliases_and_definition_connectors_can_be_replaced():
    semantic, bridge = _frozen_dependencies()
    statement_groups = _renamed_groups(NOVEL_STATEMENT_GROUPS, "別")
    query_groups = _renamed_groups(NOVEL_QUERY_GROUPS, "別")
    corpus = build_sparse_evidence_corpus(
        semantic,
        statement_groups=statement_groups,
        query_groups=query_groups,
        definition_templates=ALTERNATE_DEFINITION_TEMPLATES,
    )
    lexicon = learn_sparse_lexicon(corpus, bridge, semantic)
    assert set(lexicon.statement_codes) == {
        marker for group in statement_groups for marker in group
    }
    assert set(lexicon.query_codes) == {
        marker for group in query_groups for marker in group
    }


def test_connector_semantics_are_learned_not_named():
    semantic, bridge = _frozen_dependencies()
    corpus = build_sparse_evidence_corpus(
        semantic, definition_templates=ALTERNATE_DEFINITION_TEMPLATES
    )
    lexicon = learn_sparse_lexicon(corpus, bridge, semantic)
    assert set(lexicon.connector_deltas.values()) == {0, 1}
    assert all("同じ向き" not in key for key in lexicon.connector_deltas)
