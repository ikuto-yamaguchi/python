from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .sparc_highschool_causal_provenance import (
    CausalProvenanceLearner,
    CausalProvenanceResult,
)


@dataclass(frozen=True)
class InterventionLatticeResult:
    accepted: bool
    provenance: CausalProvenanceResult
    contributions: tuple[int, ...]
    pairwise_interactions: tuple[tuple[int, int, int], ...]
    answer: str
    verified: bool
    mechanism: str


class InterventionLatticeLearner(CausalProvenanceLearner):
    """Decompose outcomes with one task-blind sparse intervention lattice.

    Instead of replaying every omission set from the initial world, the learner
    expands one shared prefix graph. States with the same processed prefix and
    omitted-index set are computed once and reused by every downstream single or
    pair intervention. The mechanism is shared by calculation, causal comparison,
    planning and explanation; no task/domain label or causal vocabulary is used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.intervention_lattices = 0
        self.intervention_lattice_abstentions = 0
        self.intervention_rollouts = 0
        self.intervention_transition_expansions = 0
        self.intervention_prefix_reuses = 0
        self.single_contributions_measured = 0
        self.pairwise_interactions_measured = 0
        self.intervention_verification_failures = 0

    def _numeric_rollout(self, initial, actions: tuple[str, ...]):
        rollout = self.rollout(initial, actions)
        self.intervention_rollouts += 1
        if not rollout.accepted:
            return None
        value = self._only_value(rollout.world)
        if value is None:
            return None
        return value, rollout.world

    def _shared_omission_lattice(self, initial, actions: tuple[str, ...]):
        """Return terminal worlds for every omission set of size at most two.

        The graph key is only (processed position, omitted indices). A transition
        that keeps the next action executes exactly one learned event from the
        cached prefix world; an omission transition reuses that world directly.
        Sparse transition expansions are measured separately from inherited
        counterfactual branch rollouts so the resource report remains interpretable.
        """
        frontier: dict[frozenset[int], object] = {frozenset(): initial}
        for index, action in enumerate(actions):
            next_frontier: dict[frozenset[int], object] = {}
            for omitted, world in frontier.items():
                kept = self.apply(action, world)
                self.intervention_transition_expansions += 1
                if not kept.accepted:
                    return None
                if omitted in next_frontier:
                    self.intervention_prefix_reuses += 1
                next_frontier[omitted] = kept.world
                if len(omitted) < 2:
                    omitted_next = frozenset((*omitted, index))
                    if omitted_next in next_frontier:
                        self.intervention_prefix_reuses += 1
                    next_frontier[omitted_next] = world
            frontier = next_frontier
        return frontier

    def _abstain(self, provenance, mechanism: str):
        self.intervention_lattice_abstentions += 1
        return InterventionLatticeResult(False, provenance, (), (), "", False, mechanism)

    def explain_interaction_narrative(self, text: str) -> InterventionLatticeResult:
        provenance = self.explain_causal_narrative(text)
        if not provenance.accepted or not provenance.verified:
            return self._abstain(provenance, "abstain-unverified-causal-provenance")

        narrative = provenance.grounded.narrative
        actions = tuple(narrative.factual_actions)
        if len(actions) < 2 or narrative.comparison is None:
            return self._abstain(provenance, "abstain-insufficient-shared-actions")

        worlds = self._shared_omission_lattice(narrative.initial_world, actions)
        if worlds is None:
            return self._abstain(provenance, "abstain-shared-lattice-expansion-failed")

        factual_world = worlds.get(frozenset())
        if factual_world is None or factual_world != narrative.comparison.factual.world:
            self.intervention_verification_failures += 1
            return self._abstain(provenance, "abstain-factual-world-mismatch")
        factual_value = self._only_value(factual_world)
        if factual_value is None:
            return self._abstain(provenance, "abstain-nonnumeric-factual-world")

        omitted_values: dict[frozenset[int], int] = {}
        required = [frozenset((i,)) for i in range(len(actions))]
        required += [frozenset((i, j)) for i, j in combinations(range(len(actions)), 2)]
        for omitted in required:
            world = worlds.get(omitted)
            value = None if world is None else self._only_value(world)
            if value is None:
                return self._abstain(provenance, "abstain-incomplete-shared-lattice")
            omitted_values[omitted] = value

        contributions = tuple(
            factual_value - omitted_values[frozenset((index,))]
            for index in range(len(actions))
        )
        self.single_contributions_measured += len(contributions)

        pairwise = tuple(
            (
                left,
                right,
                factual_value
                - omitted_values[frozenset((left,))]
                - omitted_values[frozenset((right,))]
                + omitted_values[frozenset((left, right))],
            )
            for left, right in combinations(range(len(actions)), 2)
        )
        self.pairwise_interactions_measured += len(pairwise)

        strongest_index = max(
            range(len(contributions)), key=lambda index: (abs(contributions[index]), -index)
        )
        nonzero = [row for row in pairwise if row[2] != 0]
        if nonzero:
            left, right, interaction = max(
                nonzero, key=lambda row: (abs(row[2]), -row[0], -row[1])
            )
            relation = "増幅" if interaction > 0 else "抑制"
            interaction_text = (
                f"操作{left + 1}と操作{right + 1}には{abs(interaction)}の{relation}相互作用があります。"
            )
        else:
            interaction_text = "操作間の非加算的な相互作用は確認されませんでした。"

        answer = (
            f"同じ初期状態から共有介入格子で計算すると、単独寄与は{contributions}です。"
            f"最大の単独寄与は操作{strongest_index + 1}の{abs(contributions[strongest_index])}です。"
            f"{interaction_text}"
            f"共通接頭状態を再利用し、事実世界の結果{factual_value}と一致することを検算しました。"
        )
        self.intervention_lattices += 1
        return InterventionLatticeResult(
            True,
            provenance,
            contributions,
            pairwise,
            answer,
            True,
            "shared-sparse-prefix-intervention-lattice",
        )

    def report(self):
        result = super().report()
        result.update(
            {
                "shared_intervention_lattice": True,
                "shared_sparse_prefix_lattice": True,
                "causal_vocabulary_supplied": False,
                "intervention_lattices": self.intervention_lattices,
                "intervention_lattice_abstentions": self.intervention_lattice_abstentions,
                "intervention_rollouts": self.intervention_rollouts,
                "intervention_transition_expansions": self.intervention_transition_expansions,
                "intervention_prefix_reuses": self.intervention_prefix_reuses,
                "single_contributions_measured": self.single_contributions_measured,
                "pairwise_interactions_measured": self.pairwise_interactions_measured,
                "intervention_verification_failures": self.intervention_verification_failures,
            }
        )
        return result
