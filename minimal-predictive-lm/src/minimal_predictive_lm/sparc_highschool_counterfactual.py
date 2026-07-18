from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .sparc_highschool_general import World
from .sparc_highschool_long_temporal import LongTemporalNarrativeLearner


@dataclass(frozen=True)
class BranchRollout:
    accepted: bool
    actions: tuple[str, ...]
    world: World
    failed_at: int | None


@dataclass(frozen=True)
class CounterfactualResult:
    accepted: bool
    shared_prefix: tuple[str, ...]
    factual: BranchRollout
    counterfactual: BranchRollout
    changed_facts: frozenset[tuple[str, str, str]]
    changed_numbers: tuple[tuple[str, str, int | None, int | None], ...]


class CounterfactualNarrativeLearner(LongTemporalNarrativeLearner):
    """One task-blind program bank with persistent factual/counterfactual branches.

    Branches are immutable Worlds.  They share the exact same learned programs,
    surface binder, executor, confidence threshold, and abstention path.  No
    causal relation names or benchmark-specific transition functions are added.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.branch_rollouts = 0
        self.counterfactual_comparisons = 0
        self.counterfactual_abstentions = 0
        self.maximum_shared_prefix = 0

    def rollout(self, world: World, actions: Iterable[str]) -> BranchRollout:
        sequence = tuple(actions)
        current = world
        for index, action in enumerate(sequence):
            result = self.apply(action, current)
            if not result.accepted:
                self.counterfactual_abstentions += 1
                return BranchRollout(False, sequence, world, index)
            current = result.world
        self.branch_rollouts += 1
        return BranchRollout(True, sequence, current, None)

    @staticmethod
    def _number_differences(
        factual: World, counterfactual: World
    ) -> tuple[tuple[str, str, int | None, int | None], ...]:
        left = factual.number_map()
        right = counterfactual.number_map()
        return tuple(
            (subject, relation, left.get((subject, relation)), right.get((subject, relation)))
            for subject, relation in sorted(set(left) | set(right))
            if left.get((subject, relation)) != right.get((subject, relation))
        )

    def compare_intervention(
        self,
        world: World,
        factual_actions: Iterable[str],
        *,
        intervention_at: int,
        replacement_actions: Iterable[str],
    ) -> CounterfactualResult:
        factual_sequence = tuple(factual_actions)
        replacements = tuple(replacement_actions)
        if intervention_at < 0 or intervention_at >= len(factual_sequence):
            raise IndexError("intervention_at is outside the factual sequence")

        prefix = factual_sequence[:intervention_at]
        suffix = factual_sequence[intervention_at + 1 :]
        prefix_rollout = self.rollout(world, prefix)
        if not prefix_rollout.accepted:
            failed = BranchRollout(False, factual_sequence, world, prefix_rollout.failed_at)
            return CounterfactualResult(False, prefix, failed, failed, frozenset(), ())

        branch_point = prefix_rollout.world
        factual_tail = self.rollout(branch_point, factual_sequence[intervention_at:])
        counterfactual_tail = self.rollout(branch_point, replacements + suffix)
        accepted = factual_tail.accepted and counterfactual_tail.accepted
        if not accepted:
            self.counterfactual_abstentions += 1
            return CounterfactualResult(False, prefix, factual_tail, counterfactual_tail, frozenset(), ())

        self.counterfactual_comparisons += 1
        self.maximum_shared_prefix = max(self.maximum_shared_prefix, len(prefix))
        changed_facts = factual_tail.world.facts ^ counterfactual_tail.world.facts
        changed_numbers = self._number_differences(factual_tail.world, counterfactual_tail.world)
        return CounterfactualResult(
            True,
            prefix,
            factual_tail,
            counterfactual_tail,
            frozenset(changed_facts),
            changed_numbers,
        )

    def report(self):
        result = super().report()
        result.update(
            {
                "shared_world_branching": True,
                "branch_specific_program_bank": False,
                "counterfactual_relation_labels_supplied": False,
                "branch_rollouts": self.branch_rollouts,
                "counterfactual_comparisons": self.counterfactual_comparisons,
                "counterfactual_abstentions": self.counterfactual_abstentions,
                "maximum_shared_prefix": self.maximum_shared_prefix,
            }
        )
        return result
