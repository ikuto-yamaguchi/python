from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import json

from .sparc_highschool_evidence_factor_reliability import (
    EvidenceFactorReliabilityConsensusLearner,
)
from .sparc_highschool_hypothesis_consensus import HypothesisConsensusResult


@dataclass(frozen=True)
class EvidenceFactorInteractionStats:
    target: str
    rewarded_interactions: int
    contradicted_interactions: int


class EvidenceFactorInteractionConsensusLearner(EvidenceFactorReliabilityConsensusLearner):
    """Learn bounded context-dependent reliability from sparse source-factor pairs.

    A scalar reliability value per factor cannot represent conditional evidence: the
    same instrument, operator, or environment can be reliable in one combination and
    unreliable in another. Marginal scores then cancel and the previous learner must
    abstain everywhere. This layer retains a bounded sketch of co-occurring factor pairs
    and lets repeated verified conjunctions override unresolved marginal attribution.
    It adds no source dictionary, task/domain label, phrase exception, or dense routing.
    """

    def __init__(
        self,
        max_interaction_score: int = 4,
        max_interaction_entries: int = 4096,
        max_interaction_features: int = 64,
        max_pairs_per_lineage: int = 512,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if max_interaction_score < 1 or max_interaction_entries < 16:
            raise ValueError("interaction reliability bounds must be positive")
        if max_interaction_features < 2 or max_pairs_per_lineage < 1:
            raise ValueError("interaction sketch bounds must be positive")
        self.max_interaction_score = max_interaction_score
        self.max_interaction_entries = max_interaction_entries
        self.max_interaction_features = max_interaction_features
        self.max_pairs_per_lineage = max_pairs_per_lineage
        self._factor_interactions: dict[tuple[int, int], int] = {}
        self.interaction_reads = 0
        self.interaction_writes = 0
        self.interaction_consolidations = 0
        self.interaction_conflict_abstentions = 0
        self.last_factor_interaction = EvidenceFactorInteractionStats("", 0, 0)

    def reset_factor_interaction_graph(self) -> None:
        self.reset_factor_reliability_graph()
        self._factor_interactions.clear()
        self.interaction_reads = 0
        self.interaction_writes = 0
        self.interaction_consolidations = 0
        self.interaction_conflict_abstentions = 0
        self.last_factor_interaction = EvidenceFactorInteractionStats("", 0, 0)

    @staticmethod
    def _feature_rank(feature: int) -> int:
        return ((feature * 2654435761) ^ (feature << 13) ^ (feature >> 7)) & 0xFFFFFFFF

    @staticmethod
    def _pair_rank(pair: tuple[int, int]) -> int:
        left, right = pair
        return (
            (left * 2246822519)
            ^ (right * 3266489917)
            ^ ((left + right) * 668265263)
        ) & 0xFFFFFFFF

    def _interaction_pairs(self, lineage_id: str) -> tuple[tuple[int, int], ...]:
        features = tuple({int(value) for value in self._lineages.get(lineage_id, {}).get("features", ())})
        if len(features) < 2:
            return ()
        selected = sorted(
            sorted(features, key=lambda value: (self._feature_rank(value), value))[
                : self.max_interaction_features
            ]
        )
        pairs = list(combinations(selected, 2))
        pairs.sort(key=lambda pair: (self._pair_rank(pair), pair))
        return tuple(pairs[: self.max_pairs_per_lineage])

    def _prune_interaction_graph(self) -> None:
        active_features = {
            int(feature)
            for row in self._lineages.values()
            for feature in row.get("features", ())
        }
        for pair in tuple(self._factor_interactions):
            if pair[0] not in active_features or pair[1] not in active_features:
                self._factor_interactions.pop(pair, None)
        if len(self._factor_interactions) > self.max_interaction_entries:
            ranked = sorted(
                self._factor_interactions,
                key=lambda pair: (
                    abs(self._factor_interactions[pair]),
                    self._pair_rank(pair),
                    pair,
                ),
            )
            remove = len(self._factor_interactions) - self.max_interaction_entries
            for pair in ranked[:remove]:
                self._factor_interactions.pop(pair, None)

    def _evict_lineage(self) -> None:
        super()._evict_lineage()
        if hasattr(self, "_factor_interactions"):
            self._prune_interaction_graph()

    def ingest_interaction_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        result = self.ingest_factor_verified_hypothesis(text)
        self._prune_interaction_graph()
        return result

    def consolidate_verified_target_interactions(self, target: str) -> bool:
        """Consolidate pair signs only after the shared verifier resolves a target."""
        rows = self._hypotheses.get(target, {})
        if len(rows) < 2 or target in self._reliability_settled_targets:
            return False
        ranked = [
            (self._weighted_support(target, state_key), state_key, record)
            for state_key, record in rows.items()
        ]
        ranked.sort(key=lambda row: (-row[0], row[1]))
        if ranked[0][0] <= 0 or ranked[0][0] == ranked[1][0]:
            return False
        winner = ranked[0][1]
        if not super().consolidate_verified_target_factors(target):
            return False

        rewarded = 0
        contradicted = 0
        for _support, state_key, record in ranked:
            delta = 1 if state_key == winner else -1
            for lineage_id in tuple(record["lineage_ids"]):
                if (lineage_id, target) in self._lineage_conflicts:
                    continue
                for pair in self._interaction_pairs(lineage_id):
                    old = self._factor_interactions.get(pair, 0)
                    new = max(
                        -self.max_interaction_score,
                        min(self.max_interaction_score, old + delta),
                    )
                    self._factor_interactions[pair] = new
                    self.interaction_writes += 1
                    if delta > 0:
                        rewarded += 1
                    else:
                        contradicted += 1
        self.interaction_consolidations += 1
        self._prune_interaction_graph()
        self.last_factor_interaction = EvidenceFactorInteractionStats(
            target,
            rewarded,
            contradicted,
        )
        return True

    def _interaction_signal(self, lineage_id: str) -> tuple[int, bool, int]:
        pairs = self._interaction_pairs(lineage_id)
        self.interaction_reads += len(pairs)
        active = [
            self._factor_interactions.get(pair, 0)
            for pair in pairs
            if self._factor_interactions.get(pair, 0) != 0
        ]
        if not active:
            return 0, False, 0
        positive_mass = sum(score for score in active if score > 0)
        negative_mass = sum(-score for score in active if score < 0)
        if positive_mass and negative_mass:
            minority = min(positive_mass, negative_mass)
            majority = max(positive_mass, negative_mass)
            if minority * 2 >= majority:
                return 0, True, len(active)
        adjustment = int(sum(active) / len(active))
        return (
            max(-self.max_interaction_score, min(self.max_interaction_score, adjustment)),
            False,
            len(active),
        )

    def _factor_signal(self, lineage_id: str) -> tuple[int, bool]:
        marginal_adjustment, marginal_conflict = super()._factor_signal(lineage_id)
        interaction_adjustment, interaction_conflict, active = self._interaction_signal(lineage_id)
        if interaction_conflict:
            self.interaction_conflict_abstentions += 1
            return 0, True
        if active:
            return interaction_adjustment, False
        return marginal_adjustment, marginal_conflict

    def factor_interaction_graph_bytes(self) -> bytes:
        self._prune_interaction_graph()
        payload = {
            "factor_graph": json.loads(self.factor_reliability_graph_bytes().decode("utf-8")),
            "factor_interactions": [
                [left, right, score]
                for (left, right), score in sorted(self._factor_interactions.items())
            ],
            "max_interaction_score": self.max_interaction_score,
            "max_interaction_entries": self.max_interaction_entries,
            "max_interaction_features": self.max_interaction_features,
            "max_pairs_per_lineage": self.max_pairs_per_lineage,
            "conditional_factor_pair_consensus": True,
            "marginal_conflict_can_be_resolved_by_verified_context": True,
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
