from __future__ import annotations

from dataclasses import dataclass
import json

from .sparc_highschool_evidence_reliability import EvidenceReliabilityConsensusLearner
from .sparc_highschool_hypothesis_consensus import HypothesisConsensusResult


@dataclass(frozen=True)
class EvidenceFactorReliabilityStats:
    target: str
    rewarded_factors: int
    contradicted_factors: int


class EvidenceFactorReliabilityConsensusLearner(EvidenceReliabilityConsensusLearner):
    """Attribute verified cross-topic outcomes to bounded shared source factors.

    Whole-document lineages are too coarse: one operator, instrument, condition, or
    citation component may recur inside otherwise different source descriptions.
    This layer reuses the sparse provenance features already induced by the shared
    lineage mechanism and learns bounded reproducibility per feature. Both verified
    support and verified contradiction participate in later consensus; otherwise a
    repeatedly falsified factor could never suppress a superficially strong source.
    No source-name table, task/domain label, phrase exception, or problem-specific
    router is used.
    """

    def __init__(self, max_factor_score: int = 4, max_factor_entries: int = 2048, **kwargs):
        super().__init__(**kwargs)
        if max_factor_score < 1 or max_factor_entries < 16:
            raise ValueError("factor reliability bounds must be positive")
        self.max_factor_score = max_factor_score
        self.max_factor_entries = max_factor_entries
        self._factor_reliability: dict[int, int] = {}
        self.factor_reads = 0
        self.factor_writes = 0
        self.factor_consolidations = 0
        self.last_factor_reliability = EvidenceFactorReliabilityStats("", 0, 0)

    def reset_factor_reliability_graph(self) -> None:
        self.reset_reliability_graph()
        self._factor_reliability.clear()
        self.factor_reads = 0
        self.factor_writes = 0
        self.factor_consolidations = 0
        self.last_factor_reliability = EvidenceFactorReliabilityStats("", 0, 0)

    def _prune_factor_graph(self) -> None:
        active = {
            int(feature)
            for row in self._lineages.values()
            for feature in row.get("features", ())
        }
        for feature in tuple(self._factor_reliability):
            if feature not in active:
                self._factor_reliability.pop(feature, None)
        if len(self._factor_reliability) > self.max_factor_entries:
            ranked = sorted(
                self._factor_reliability,
                key=lambda feature: (abs(self._factor_reliability[feature]), feature),
            )
            for feature in ranked[: len(self._factor_reliability) - self.max_factor_entries]:
                self._factor_reliability.pop(feature, None)

    def _evict_lineage(self) -> None:
        super()._evict_lineage()
        self._prune_factor_graph()

    def ingest_factor_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        result = self.ingest_reliability_verified_hypothesis(text)
        self._prune_factor_graph()
        return result

    def consolidate_verified_target_factors(self, target: str) -> bool:
        """Learn factors only from a uniquely resolved, competing verified target."""
        self._prune_factor_graph()
        if target in self._reliability_settled_targets:
            return False
        rows = self._hypotheses.get(target, {})
        if len(rows) < 2:
            return False
        ranked = [
            (self._weighted_support(target, state_key), state_key, record)
            for state_key, record in rows.items()
        ]
        ranked.sort(key=lambda row: (-row[0], row[1]))
        if ranked[0][0] <= 0 or ranked[0][0] == ranked[1][0]:
            return False
        winner = ranked[0][1]
        rewarded = 0
        contradicted = 0
        for _support, state_key, record in ranked:
            delta = 1 if state_key == winner else -1
            for lineage_id in tuple(record["lineage_ids"]):
                if (lineage_id, target) in self._lineage_conflicts:
                    continue
                for feature in self._lineages.get(lineage_id, {}).get("features", ()):
                    old = self._factor_reliability.get(int(feature), 0)
                    new = max(-self.max_factor_score, min(self.max_factor_score, old + delta))
                    self._factor_reliability[int(feature)] = new
                    self.factor_writes += 1
                    if delta > 0:
                        rewarded += 1
                    else:
                        contradicted += 1
        self._reliability_settled_targets.add(target)
        self.factor_consolidations += 1
        self._prune_factor_graph()
        self.last_factor_reliability = EvidenceFactorReliabilityStats(target, rewarded, contradicted)
        return True

    def _factor_adjustment(self, lineage_id: str) -> int:
        """Return a bounded signed contrast from verified shared factors.

        Neutral features are excluded from the denominator so ubiquitous Japanese
        fragments cannot wash out a repeatedly verified or falsified source factor.
        The score remains bounded and sparse; no dense attention or extra candidate
        expansion is introduced.
        """
        features = tuple(self._lineages.get(lineage_id, {}).get("features", ()))
        self.factor_reads += len(features)
        scores = [self._factor_reliability.get(int(feature), 0) for feature in features]
        active = [score for score in scores if score != 0]
        if not active:
            return 0
        adjustment = int(sum(active) / len(active))
        return max(-self.max_factor_score, min(self.max_factor_score, adjustment))

    def _factor_multiplier(self, lineage_id: str) -> int:
        """Compatibility view for positive reproducibility used by older reports."""
        return 1 + max(0, self._factor_adjustment(lineage_id))

    def _factor_weighted_support(self, target: str, state_key: str) -> int:
        record = self._hypotheses.get(target, {}).get(state_key)
        if record is None:
            return 0
        total = 0
        for lineage_id in record["lineage_ids"]:
            self.quality_reads += 1
            if (lineage_id, target) in self._lineage_conflicts:
                continue
            quality = self._quality.get((lineage_id, target, state_key), 0)
            adjustment = self._factor_adjustment(lineage_id)
            if adjustment >= 0:
                total += quality * (1 + adjustment)
            else:
                total += max(0, quality + adjustment)
        return total

    def answer_from_factor_reliability_graph(self, question: str) -> HypothesisConsensusResult:
        entities = tuple(self._hypothesis_order)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unsupported-factor-reliability-target")
        if len(targets) == 1:
            target = targets[0]
        elif len(targets) == 0 and self._hypothesis_focus in self._hypotheses:
            target = self._hypothesis_focus  # type: ignore[assignment]
            reused = True
        else:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-ambiguous-factor-reliability-query")
        rows = self._hypotheses[target]
        self.hypothesis_reads += len(rows)
        ranked = [
            (self._factor_weighted_support(target, state_key), int(record["last_seen"]), record)
            for state_key, record in rows.items()
        ]
        ranked.sort(key=lambda row: (-row[0], -row[1]))
        if not ranked or ranked[0][0] <= 0 or sum(row[0] == ranked[0][0] for row in ranked) != 1:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unresolved-factor-reliability-conflict")
        self._hypothesis_focus = target
        states = tuple(ranked[0][2]["states"])
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        focus_note = "直前の検算済み焦点を再利用し、" if reused else ""
        return HypothesisConsensusResult(
            True,
            target,
            states,
            f"{target}は{details}です。{focus_note}複数論点で検算された共有由来特徴の支持と反証を符号付きで有界合成した結果、支持が一意に最大です。",
            "shared-bounded-verified-source-factor-reliability-graph",
            ranked[0][0],
            len(ranked),
            reused,
        )

    def factor_reliability_graph_bytes(self) -> bytes:
        self._prune_factor_graph()
        payload = {
            "reliability": json.loads(self.reliability_graph_bytes().decode("utf-8")),
            "factor_reliability": sorted(self._factor_reliability.items()),
            "max_factor_score": self.max_factor_score,
            "max_factor_entries": self.max_factor_entries,
            "signed_factor_consensus": True,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")