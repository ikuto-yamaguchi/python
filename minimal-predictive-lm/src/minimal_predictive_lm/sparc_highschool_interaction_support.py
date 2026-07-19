from __future__ import annotations

import json

from .sparc_highschool_evidence_factor_interaction import (
    EvidenceFactorInteractionConsensusLearner,
)


class EvidenceFactorInteractionSupportLearner(EvidenceFactorInteractionConsensusLearner):
    """Prevent a one-episode conjunction from overriding shared evidence.

    Pair reliability is useful for conditional effects, but a single resolved target can
    create a high-dimensional accidental conjunction.  This layer tracks how many
    independently resolved targets supported each pair.  Only repeatedly reproduced
    interactions may override the marginal factor graph; weak interactions remain stored
    for continual learning but cannot yet steer an answer.
    """

    def __init__(
        self,
        min_interaction_targets: int = 2,
        max_interaction_support: int = 15,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if min_interaction_targets < 2:
            raise ValueError("interaction transfer needs at least two resolved targets")
        if max_interaction_support < min_interaction_targets:
            raise ValueError("interaction support bound is too small")
        self.min_interaction_targets = min_interaction_targets
        self.max_interaction_support = max_interaction_support
        self._interaction_support: dict[tuple[int, int], int] = {}
        self.interaction_support_reads = 0
        self.interaction_support_writes = 0
        self.low_support_interactions_ignored = 0

    def reset_factor_interaction_graph(self) -> None:
        super().reset_factor_interaction_graph()
        self._interaction_support.clear()
        self.interaction_support_reads = 0
        self.interaction_support_writes = 0
        self.low_support_interactions_ignored = 0

    def _prune_interaction_graph(self) -> None:
        super()._prune_interaction_graph()
        if not hasattr(self, "_interaction_support"):
            return
        for pair in tuple(self._interaction_support):
            if pair not in self._factor_interactions:
                self._interaction_support.pop(pair, None)
        if len(self._interaction_support) > self.max_interaction_entries:
            ranked = sorted(
                self._interaction_support,
                key=lambda pair: (
                    self._interaction_support[pair],
                    abs(self._factor_interactions.get(pair, 0)),
                    self._pair_rank(pair),
                    pair,
                ),
            )
            remove = len(self._interaction_support) - self.max_interaction_entries
            for pair in ranked[:remove]:
                self._interaction_support.pop(pair, None)
                self._factor_interactions.pop(pair, None)

    def consolidate_verified_target_interactions(self, target: str) -> bool:
        rows = self._hypotheses.get(target, {})
        candidate_pairs = {
            pair
            for record in rows.values()
            for lineage_id in tuple(record["lineage_ids"])
            if (lineage_id, target) not in self._lineage_conflicts
            for pair in self._interaction_pairs(lineage_id)
        }
        if not super().consolidate_verified_target_interactions(target):
            return False
        for pair in candidate_pairs:
            if pair not in self._factor_interactions:
                continue
            self._interaction_support[pair] = min(
                self.max_interaction_support,
                self._interaction_support.get(pair, 0) + 1,
            )
            self.interaction_support_writes += 1
        self._prune_interaction_graph()
        return True

    def _interaction_signal(self, lineage_id: str) -> tuple[int, bool, int]:
        pairs = self._interaction_pairs(lineage_id)
        self.interaction_reads += len(pairs)
        active_scores: list[int] = []
        for pair in pairs:
            score = self._factor_interactions.get(pair, 0)
            if score == 0:
                continue
            support = self._interaction_support.get(pair, 0)
            self.interaction_support_reads += 1
            if support < self.min_interaction_targets:
                self.low_support_interactions_ignored += 1
                continue
            active_scores.append(score)
        if not active_scores:
            return 0, False, 0
        positive_mass = sum(score for score in active_scores if score > 0)
        negative_mass = sum(-score for score in active_scores if score < 0)
        if positive_mass and negative_mass:
            minority = min(positive_mass, negative_mass)
            majority = max(positive_mass, negative_mass)
            if minority * 2 >= majority:
                return 0, True, len(active_scores)
        adjustment = int(sum(active_scores) / len(active_scores))
        return (
            max(-self.max_interaction_score, min(self.max_interaction_score, adjustment)),
            False,
            len(active_scores),
        )

    def factor_interaction_support_graph_bytes(self) -> bytes:
        self._prune_interaction_graph()
        payload = {
            "interaction_graph": json.loads(
                self.factor_interaction_graph_bytes().decode("utf-8")
            ),
            "interaction_support": [
                [left, right, support]
                for (left, right), support in sorted(self._interaction_support.items())
            ],
            "min_interaction_targets": self.min_interaction_targets,
            "max_interaction_support": self.max_interaction_support,
            "repeated_verified_target_support_required": True,
            "single_episode_interaction_cannot_override_marginals": True,
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
