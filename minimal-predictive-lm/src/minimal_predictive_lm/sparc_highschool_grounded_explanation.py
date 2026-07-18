from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_general import World
from .sparc_highschool_narrative_alignment import NarrativeAlignedLearner, NarrativeAlignmentResult


@dataclass(frozen=True)
class GroundedExplanationResult:
    accepted: bool
    narrative: NarrativeAlignmentResult
    factual_trace: tuple[int, ...]
    counterfactual_trace: tuple[int, ...]
    answer: str
    verified: bool
    mechanism: str


class GroundedExplanationLearner(NarrativeAlignedLearner):
    """Verbalize and independently verify the same shared world rollouts.

    The explainer does not receive a task or domain label.  It replays the paths
    already inferred from ordinary narrative text, records the changing numeric
    state, and verbalizes only values reproduced by the common executor.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grounded_explanations = 0
        self.explanation_abstentions = 0
        self.verification_replays = 0
        self.verification_failures = 0

    @staticmethod
    def _only_value(world: World) -> int | None:
        values = world.number_map()
        if world.facts or len(values) != 1:
            return None
        return next(iter(values.values()))

    def _trace(self, initial: World, actions: tuple[str, ...]) -> tuple[tuple[int, ...], World] | None:
        first = self._only_value(initial)
        if first is None:
            return None
        values = [first]
        world = initial
        for action in actions:
            applied = self.apply(action, world)
            if not applied.accepted:
                return None
            world = applied.world
            value = self._only_value(world)
            if value is None:
                return None
            values.append(value)
        return tuple(values), world

    def explain_counterfactual_narrative(self, text: str) -> GroundedExplanationResult:
        aligned = self.infer_counterfactual_narrative(text)
        if not aligned.accepted or aligned.comparison is None or aligned.intervention_at is None:
            self.explanation_abstentions += 1
            return GroundedExplanationResult(False, aligned, (), (), "", False, "abstain-unresolved-world-alignment")

        factual = self._trace(aligned.initial_world, aligned.factual_actions)
        replacement_actions = (
            aligned.factual_actions[: aligned.intervention_at]
            + aligned.replacement_actions
            + aligned.factual_actions[aligned.intervention_at + 1 :]
        )
        counterfactual = self._trace(aligned.initial_world, replacement_actions)
        self.verification_replays += 2
        if factual is None or counterfactual is None:
            self.verification_failures += 1
            self.explanation_abstentions += 1
            return GroundedExplanationResult(False, aligned, (), (), "", False, "abstain-replay-failed")

        factual_trace, factual_world = factual
        counterfactual_trace, counterfactual_world = counterfactual
        verified = (
            factual_world == aligned.comparison.factual.world
            and counterfactual_world == aligned.comparison.counterfactual.world
        )
        if not verified:
            self.verification_failures += 1
            self.explanation_abstentions += 1
            return GroundedExplanationResult(False, aligned, factual_trace, counterfactual_trace, "", False, "abstain-verification-mismatch")

        actual = factual_trace[-1]
        alternative = counterfactual_trace[-1]
        difference = alternative - actual
        factual_path = "→".join(str(value) for value in factual_trace)
        alternative_path = "→".join(str(value) for value in counterfactual_trace)
        direction = "多い" if difference > 0 else "少ない" if difference < 0 else "同じ"
        magnitude = abs(difference)
        answer = (
            f"同じ初期状態から計算すると、実際の経路は{factual_path}で結果は{actual}です。"
            f"変更した経路は{alternative_path}で結果は{alternative}です。"
            f"したがって変更した場合は実際より{magnitude}{'多い' if direction == '多い' else '少ない' if direction == '少ない' else ''}結果です。"
            "両方の経路を同じ世界遷移で再実行し、観測された実際の結果とも一致することを検算しました。"
        )
        self.grounded_explanations += 1
        return GroundedExplanationResult(True, aligned, factual_trace, counterfactual_trace, answer, True, "shared-replayed-world-trace-verbalization")

    def report(self):
        result = super().report()
        result.update({
            "grounded_trace_explanation": True,
            "verification_uses_shared_executor": True,
            "grounded_explanations": self.grounded_explanations,
            "explanation_abstentions": self.explanation_abstentions,
            "verification_replays": self.verification_replays,
            "verification_failures": self.verification_failures,
        })
        return result
