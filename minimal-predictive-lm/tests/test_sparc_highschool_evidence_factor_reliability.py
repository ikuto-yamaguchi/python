from minimal_predictive_lm.sparc_highschool_document_stream_gate import _corpus
from minimal_predictive_lm.sparc_highschool_evidence_factor_reliability import (
    EvidenceFactorReliabilityConsensusLearner,
)
from minimal_predictive_lm.sparc_highschool_long_temporal_gate import _long_corpus
from minimal_predictive_lm.sparc_highschool_numeric_stream_gate import _numeric_corpus


def _strong(target: str, initial: int, note: str) -> str:
    return (
        f"{target}には{initial}個ある。{target}に3個加える。{target}を2倍にする。"
        f"{target}には{(initial + 3) * 2}個ある。{note}。"
        f"{target}について不足する状態を根拠付きで説明してください。"
    )


def _weak(target: str, initial: int, note: str) -> str:
    return (
        f"{target}に3個加える。{note}。{target}には{initial + 3}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def _learner() -> EvidenceFactorReliabilityConsensusLearner:
    learner = EvidenceFactorReliabilityConsensusLearner(
        max_evidence_components=10,
        max_hypotheses_per_target=3,
        max_lineages=16,
        lineage_similarity_threshold=0.50,
        max_quality_weight=3,
        max_reliability_score=4,
        max_factor_score=4,
        max_factor_entries=2048,
    )
    learner.learn_independent_documents(_corpus(), min_support=4)
    learner.learn_independent_numeric_documents(_numeric_corpus())
    learner.learn_long_chronological_documents(_long_corpus())
    return learner


def test_shared_factor_reliability_transfers_across_distinct_lineages():
    learner = _learner()
    reliable_core = "校正済み光学標準器による直接測定"
    unreliable_core = "未校正推定装置による間接算出"
    for index in range(4):
        target = f"要素校正{index}"
        truth = 10 + index
        learner.ingest_factor_verified_hypothesis(
            _strong(target, truth + 5, f"旧倉庫記録群{index}の異なる長文背景と{unreliable_core}")
        )
        learner.ingest_factor_verified_hypothesis(
            _strong(target, truth, f"山岳観測班{index}の独立した長文背景と{reliable_core}")
        )
        learner.ingest_factor_verified_hypothesis(
            _strong(target, truth, f"第三者監査機関{index}による完全独立再測定")
        )
        assert learner.consolidate_verified_target_factors(target)

    target = "未知要素論点"
    learner.ingest_factor_verified_hypothesis(
        _weak(target, 17, f"沿岸調査班の新規背景と{reliable_core}")
    )
    learner.ingest_factor_verified_hypothesis(
        _strong(target, 22, f"都市集計班の新規背景と{unreliable_core}")
    )
    result = learner.answer_from_factor_reliability_graph(f"{target}の結論を説明してください。")
    assert result.accepted
    assert (target, "NDR0", 0, 17) in result.selected_states
    assert result.mechanism == "shared-bounded-verified-source-factor-reliability-graph"


def test_factor_graph_is_bounded_and_resettable():
    learner = _learner()
    learner._factor_reliability.update({index: 1 for index in range(3000)})
    learner._prune_factor_graph()
    assert len(learner._factor_reliability) <= learner.max_factor_entries
    learner.reset_factor_reliability_graph()
    assert learner._factor_reliability == {}
    assert learner.factor_reads == 0
    assert learner.factor_writes == 0
    assert learner.factor_consolidations == 0
