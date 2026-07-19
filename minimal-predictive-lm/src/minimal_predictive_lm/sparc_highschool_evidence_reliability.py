from __future__ import annotations

from dataclasses import dataclass
import json

from .sparc_highschool_evidence_quality import EvidenceQualityConsensusLearner
from .sparc_highschool_hypothesis_consensus import HypothesisConsensusResult


@dataclass(frozen=True)
class EvidenceReliabilityStats:
    target: str
    winner_state_key: str
    rewarded_lineages: int
    contradicted_lineages: int


class EvidenceReliabilityConsensusLearner(EvidenceQualityConsensusLearner):
    """Learn bounded source reproducibility across independently verified worlds.

    Structural coverage is local to one document. This layer reuses the same
    provenance clusters across unrelated targets and records whether each lineage
    repeatedly agrees with a uniquely supported, replay-verified world. The score
    is learned from cross-target outcomes, not from source names, task/domain labels,
    phrase exceptions, or a hand-authored trust table.
    """

    def __init__(self, max_reliability_score: int = 4, **kwargs):
        super().__init__(**kwargs)
        if max_reliability_score < 1:
            raise ValueError("max_reliability_score must be positive")
        self.max_reliability_score = max_reliability_score
        self._reliability: dict[str, int] = {}
        self._reliability_settled_targets: set[str] = set()
        self.reliability_reads = 0
        self.reliability_writes = 0
        self.reliability_consolidations = 0
        self.last_reliability = EvidenceReliabilityStats("", "", 0, 0)

    def reset_reliability_graph(self) -> None:
        """Reset both bounded graph state and graph-local accounting.

        The reliability graph is evaluated as an independent episode. Keeping
        counters from an earlier episode makes later gate cases depend on test
        order even though their graph state has been cleared. Resetting the
        accounting together with the graph preserves the shared mechanism while
        making resource and consolidation measurements episode-local.
        """
        self.reset_quality_graph()
        self._reliability.clear()
        self._reliability_settled_targets.clear()
        self.reliability_reads = 0
        self.reliability_writes = 0
        self.reliability_consolidations = 0
        self.last_reliability = EvidenceReliabilityStats("", "", 0, 0)

    def _prune_reliability_graph(self) -> None:
        """Keep derived reliability state aligned with bounded parent graphs."""
        active_lineages = set(self._lineages)
        for lineage_id in tuple(self._reliability):
            if lineage_id not in active_lineages:
                self._reliability.pop(lineage_id, None)
        self._reliability_settled_targets.intersection_update(self._hypotheses)

    def _evict_lineage(self) -> None:
        """Evict inherited lineage state and its derived reliability score together."""
        before = set(self._lineages)
        super()._evict_lineage()
        for lineage_id in before.difference(self._lineages):
            self._reliability.pop(lineage_id, None)

    def ingest_reliability_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        result = self.ingest_quality_verified_hypothesis(text)
        self._prune_reliability_graph()
        return result

    def consolidate_verified_target(self, target: str) -> bool:
        """Update lineage reproducibility only after a unique local quality winner.

        A target contributes at most once. At least two competing hypotheses and a
        strict positive margin are required, preventing a single unopposed document
        from bootstrapping its own reputation.
        """
        self._prune_reliability_graph()
        if target in self._reliability_settled_targets:
            return False
        rows = self._hypotheses.get(target, {})
        if len(rows) < 2:
            return False
        ranked: list[tuple[int, str, dict[str, object]]] = []
        for state_key, record in rows.items():
            ranked.append((self._weighted_support(target, state_key), state_key, record))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        if ranked[0][0] <= 0 or ranked[0][0] == ranked[1][0]:
            return False

        winner_key = ranked[0][1]
        rewarded = 0
        contradicted = 0
        for _support, state_key, record in ranked:
            for lineage_id in tuple(record["lineage_ids"]):
                if (lineage_id, target) in self._lineage_conflicts:
                    continue
                delta = 1 if state_key == winner_key else -1
                old = self._reliability.get(lineage_id, 0)
                new = max(-self.max_reliability_score, min(self.max_reliability_score, old + delta))
                self._reliability[lineage_id] = new
                self.reliability_writes += 1
                if delta > 0:
                    rewarded += 1
                else:
                    contradicted += 1
        self._reliability_settled_targets.add(target)
        self.reliability_consolidations += 1
        self.last_reliability = EvidenceReliabilityStats(target, winner_key, rewarded, contradicted)
        return True

    def _reliability_factor(self, lineage_id: str) -> int:
        self.reliability_reads += 1
        return 1 + max(0, self._reliability.get(lineage_id, 0))

    def _reliability_weighted_support(self, target: str, state_key: str) -> int:
        record = self._hypotheses.get(target, {}).get(state_key)
        if record is None:
            return 0
        total = 0
        for lineage_id in record["lineage_ids"]:
            self.quality_reads += 1
            if (lineage_id, target) in self._lineage_conflicts:
                continue
            quality = self._quality.get((lineage_id, target, state_key), 0)
            total += quality * self._reliability_factor(lineage_id)
        return total

    def answer_from_reliability_graph(self, question: str) -> HypothesisConsensusResult:
        entities = tuple(self._hypothesis_order)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unsupported-reliability-target")
        if len(targets) == 1:
            target = targets[0]
        elif len(targets) == 0 and self._hypothesis_focus in self._hypotheses:
            target = self._hypothesis_focus  # type: ignore[assignment]
            reused = True
        else:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-ambiguous-reliability-query")

        rows = self._hypotheses[target]
        self.hypothesis_reads += len(rows)
        ranked = [
            (self._reliability_weighted_support(target, state_key), int(record["last_seen"]), record)
            for state_key, record in rows.items()
        ]
        ranked.sort(key=lambda row: (-row[0], -row[1]))
        if not ranked or ranked[0][0] <= 0:
            return self._h_abstain("abstain-no-verified-reliability-support")
        best = ranked[0][0]
        tied = [row for row in ranked if row[0] == best]
        if len(tied) != 1:
            self.hypothesis_conflict_abstentions += 1
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unresolved-verified-reliability-conflict")
        self._hypothesis_focus = target
        return self._reliability_answer(target, tuple(tied[0][2]["states"]), best, len(ranked), reused)

    @staticmethod
    def _reliability_answer(target: str, states, support: int, alternatives: int, reused: bool) -> HypothesisConsensusResult:
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        answer = (
            f"{target}は{details}です。観測被覆と独立由来に加え、別論点で再現した検算済み履歴を"
            f"有界に合成した支持重みは{support}で、競合仮説{alternatives}件の中で一意に最大です。"
        )
        return HypothesisConsensusResult(
            True,
            target,
            tuple(states),
            answer,
            "shared-bounded-cross-topic-verified-source-reliability-graph",
            support,
            alternatives,
            reused,
        )

    def reliability_graph_bytes(self) -> bytes:
        self._prune_reliability_graph()
        payload = {
            "quality": json.loads(self.quality_graph_bytes().decode("utf-8")),
            "reliability": sorted(self._reliability.items()),
            "settled_targets": sorted(self._reliability_settled_targets),
            "max_reliability_score": self.max_reliability_score,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")