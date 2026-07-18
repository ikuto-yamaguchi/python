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
    """Decompose an outcome through one shared intervention lattice.

    The same task-blind narrative alignment, latent program bank, immutable World,
    binder and executor are reused.  Every factual operation is omitted alone and
    in pairs from the same initial world.  Marginal contributions and non-additive
    interactions therefore come from executable world differences rather than a
    causal vocabulary, domain selector, or problem-specific rule.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.intervention_lattices = 0
        self.intervention_lattice_abstentions = 0
        self.intervention_rollouts = 0
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

    def explain_interaction_narrative(self, text: str) -> InterventionLatticeResult:
        provenance = self.explain_causal_narrative(text)
        if not provenance.accepted or not provenance.verified:
            self.intervention_lattice_abstentions += 1
            return InterventionLatticeResult(
                False,
                provenance,
                (),
                (),
                "",
                False,
                "abstain-unverified-causal-provenance",
            )

        narrative = provenance.grounded.narrative
        actions = tuple(narrative.factual_actions)
        if len(actions) < 2 or narrative.comparison is None:
            self.intervention_lattice_abstentions += 1
            return InterventionLatticeResult(
                False,
                provenance,
                (),
                (),
                "",
                False,
                "abstain-insufficient-shared-actions",
            )

        factual = self._numeric_rollout(narrative.initial_world, actions)
        if factual is None:
            self.intervention_lattice_abstentions += 1
            return InterventionLatticeResult(
                False, provenance, (), (), "", False, "abstain-factual-replay-failed"
            )
        factual_value, factual_world = factual
        if factual_world != narrative.comparison.factual.world:
            self.intervention_verification_failures += 1
            self.intervention_lattice_abstentions += 1
            return InterventionLatticeResult(
                False,
                provenance,
                (),
                (),
                "",
                False,
                "abstain-factual-world-mismatch",
            )

        omitted_values: dict[frozenset[int], int] = {}
        for index in range(len(actions)):
            remaining = actions[:index] + actions[index + 1 :]
            replay = self._numeric_rollout(narrative.initial_world, remaining)
            if replay is None:
                self.intervention_lattice_abstentions += 1
                return InterventionLatticeResult(
                    False,
                    provenance,
                    (),
                    (),
                    "",
                    False,
                    "abstain-single-intervention-failed",
                )
            omitted_values[frozenset((index,))] = replay[0]

        contributions = tuple(
            factual_value - omitted_values[frozenset((index,))]
            for index in range(len(actions))
        )
        self.single_contributions_measured += len(contributions)

        interactions: list[tuple[int, int, int]] = []
        for left, right in combinations(range(len(actions)), 2):
            remaining = tuple(
                action
                for index, action in enumerate(actions)
                if index not in {left, right}
            )
            replay = self._numeric_rollout(narrative.initial_world, remaining)
            if replay is None:
                self.intervention_lattice_abstentions += 1
                return InterventionLatticeResult(
                    False,
                    provenance,
                    (),
                    (),
                    "",
                    False,
                    "abstain-pair-intervention-failed",
                )
            pair_value = replay[0]
            interaction = (
                factual_value
                - omitted_values[frozenset((left,))]
                - omitted_values[frozenset((right,))]
                + pair_value
            )
            interactions.append((left, right, interaction))
        pairwise = tuple(interactions)
        self.pairwise_interactions_measured += len(pairwise)

        strongest_index = max(
            range(len(contributions)), key=lambda index: (abs(contributions[index]), -index)
        )
        nonzero = [row for row in pairwise if row[2] != 0]
        if nonzero:
            strongest_pair = max(nonzero, key=lambda row: (abs(row[2]), -row[0], -row[1]))
            left, right, interaction = strongest_pair
            relation = "増幅" if interaction > 0 else "抑制"
            interaction_text = (
                f"操作{left + 1}と操作{right + 1}には{abs(interaction)}の{relation}相互作用があります。"
            )
        else:
            interaction_text = "操作間の非加算的な相互作用は確認されませんでした。"

        answer = (
            f"同じ初期状態から各操作を一つずつ外して再計算すると、単独寄与は{contributions}です。"
            f"最大の単独寄与は操作{strongest_index + 1}の{abs(contributions[strongest_index])}です。"
            f"{interaction_text}"
            f"全組合せを同じ世界遷移で再実行し、事実世界の結果{factual_value}と一致することを検算しました。"
        )
        self.intervention_lattices += 1
        return InterventionLatticeResult(
            True,
            provenance,
            contributions,
            pairwise,
            answer,
            True,
            "shared-world-intervention-lattice",
        )

    def report(self):
        result = super().report()
        result.update(
            {
                "shared_intervention_lattice": True,
                "causal_vocabulary_supplied": False,
                "intervention_lattices": self.intervention_lattices,
                "intervention_lattice_abstentions": self.intervention_lattice_abstentions,
                "intervention_rollouts": self.intervention_rollouts,
                "single_contributions_measured": self.single_contributions_measured,
                "pairwise_interactions_measured": self.pairwise_interactions_measured,
                "intervention_verification_failures": self.intervention_verification_failures,
            }
        )
        return result
