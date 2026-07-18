import unittest

from minimal_predictive_lm.sparc_highschool_evidence_quality import EvidenceQualityConsensusLearner


def weak(target: str, initial: int, add: int, note: str) -> str:
    return (
        f"{target}に{add}個加える。{note}。{target}には{initial + add}個ある。"
        f"{target}を2倍にする。{target}について不足する状態を根拠付きで説明してください。"
    )


def strong(target: str, initial: int, add: int, note: str) -> str:
    final = (initial + add) * 2
    return (
        f"{target}には{initial}個ある。{target}に{add}個加える。"
        f"{target}を2倍にする。{target}には{final}個ある。{note}。"
        f"{target}について不足する状態を根拠付きで説明してください。"
    )


class EvidenceQualityConsensusTest(unittest.TestCase):
    def learner(self):
        return EvidenceQualityConsensusLearner(
            max_evidence_components=4,
            max_hypotheses_per_target=3,
            max_lineages=10,
            lineage_similarity_threshold=0.50,
            max_quality_weight=3,
        )

    def test_fewer_well_anchored_lineages_beat_many_weak_reconstructions(self):
        learner = self.learner()
        target = "品質論点A"
        for note in ("北側の伝聞記録", "西側の間接記録", "旧帳簿の再構成"):
            learner.ingest_quality_verified_hypothesis(weak(target, 7, 3, note))
        for note in ("独立測定系列一", "独立測定系列二"):
            learner.ingest_quality_verified_hypothesis(strong(target, 12, 3, note))
        result = learner.answer_from_quality_graph(f"{target}の現在の結論を説明してください。")
        self.assertTrue(result.accepted)
        self.assertEqual(4, result.support)
        self.assertIn((target, "NDR0", 0, 12), result.selected_states)
        self.assertNotIn((target, "NDR0", 0, 7), result.selected_states)

    def test_equal_verified_coverage_abstains(self):
        learner = self.learner()
        target = "品質論点B"
        learner.ingest_quality_verified_hypothesis(strong(target, 5, 2, "独立測定甲"))
        learner.ingest_quality_verified_hypothesis(strong(target, 9, 2, "独立測定乙"))
        result = learner.answer_from_quality_graph(f"{target}の結論を説明してください。")
        self.assertFalse(result.accepted)
        self.assertEqual("abstain-unresolved-verified-quality-conflict", result.mechanism)

    def test_duplicate_lineage_does_not_add_quality(self):
        learner = self.learner()
        target = "品質論点C"
        text = strong(target, 8, 4, "共同測定の記録をそのまま転記した")
        learner.ingest_quality_verified_hypothesis(text)
        learner.ingest_quality_verified_hypothesis(text)
        result = learner.answer_from_quality_graph(f"{target}の結論を説明してください。")
        self.assertTrue(result.accepted)
        self.assertEqual(2, result.support)

    def test_graph_is_bounded_and_serializable(self):
        learner = self.learner()
        for index in range(6):
            learner.ingest_quality_verified_hypothesis(
                strong(f"品質保存{index}", index + 3, 2, f"独立測定{index}")
            )
        payload = learner.quality_graph_bytes()
        self.assertLessEqual(len(payload), 32768)
        self.assertGreater(learner.quality_writes, 0)


if __name__ == "__main__":
    unittest.main()
