from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
from typing import Mapping


@dataclass(frozen=True)
class CausalEvent:
    name: str
    actual: bool
    normal: bool
    time: int = 0

    @property
    def abnormal(self) -> bool:
        return self.actual != self.normal


@dataclass(frozen=True)
class OutcomeRule:
    inputs: tuple[str, ...]
    threshold: int

    def evaluate(self, assignment: Mapping[str, bool]) -> bool:
        return sum(bool(assignment.get(name, False)) for name in self.inputs) >= self.threshold

    @classmethod
    def all_of(cls, *inputs: str) -> "OutcomeRule":
        return cls(tuple(inputs), len(inputs))

    @classmethod
    def any_of(cls, *inputs: str) -> "OutcomeRule":
        return cls(tuple(inputs), 1)


@dataclass(frozen=True)
class CausalScenario:
    events: tuple[CausalEvent, ...]
    rule: OutcomeRule
    query: str
    normative_selection: bool = True


@dataclass(frozen=True)
class IntentEvidence:
    outcome_occurred: bool
    controlled_action: bool
    expected_path: bool
    goal: bool = False
    foresaw_side_effect: bool = False


@dataclass(frozen=True)
class CausalPrediction:
    output: bool | None
    classification: str
    operations: int
    contingency: tuple[str, ...] = ()
    explanation: str = ""


class NormAwareCausalMachine:
    """Small structural causal adjudicator with normality-constrained contingencies.

    The machine separates physical dependence from normative selection. A query
    can be pivotal directly, or become pivotal after other variables are moved
    only toward their declared normal values. For conjunctive outcomes, an
    otherwise normal contributor is suppressed when a co-contributor is
    abnormal; this records responsibility selection separately from mechanics.
    """

    def __init__(self) -> None:
        specification = {
            "physical": "threshold structural equation",
            "intervention": "flip queried event",
            "contingencies": "other events may move only to normal values",
            "selection": "abnormal conjunctive contributor outranks normal cofactor",
            "intent": "controlled expected action and goal-or-foreseen-side-effect",
            "uncertain": "abstain",
        }
        self.description_bits = len(
            json.dumps(specification, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ) * 8

    def judge_cause(self, scenario: CausalScenario) -> CausalPrediction:
        events = {event.name: event for event in scenario.events}
        query = events.get(scenario.query)
        if query is None or scenario.query not in scenario.rule.inputs:
            return CausalPrediction(None, "unsupported", 1, explanation="query is not a modeled input")
        assignment = {name: event.actual for name, event in events.items()}
        operations = 1
        if not scenario.rule.evaluate(assignment) or not query.actual:
            return CausalPrediction(False, "not-actual", operations, explanation="query or outcome did not occur")

        flipped = dict(assignment)
        flipped[query.name] = not query.actual
        operations += 1
        if not scenario.rule.evaluate(flipped):
            if scenario.normative_selection and scenario.rule.threshold == len(scenario.rule.inputs):
                abnormal_others = [
                    events[name]
                    for name in scenario.rule.inputs
                    if name != query.name and events[name].abnormal
                ]
                if abnormal_others and not query.abnormal:
                    return CausalPrediction(
                        False,
                        "normal-conjunct-suppressed",
                        operations,
                        explanation="an abnormal co-contributor is selected over the normal cofactor",
                    )
            return CausalPrediction(True, "but-for", operations, explanation="flipping the query prevents the outcome")

        candidates = [
            events[name]
            for name in scenario.rule.inputs
            if name != query.name and events[name].actual != events[name].normal
        ]
        for size in range(1, len(candidates) + 1):
            for subset in itertools.combinations(candidates, size):
                operations += 1
                contingent = dict(assignment)
                for event in subset:
                    contingent[event.name] = event.normal
                if not scenario.rule.evaluate(contingent):
                    continue
                counterfactual = dict(contingent)
                counterfactual[query.name] = not query.actual
                operations += 1
                if not scenario.rule.evaluate(counterfactual):
                    return CausalPrediction(
                        True,
                        "normality-contingency",
                        operations,
                        tuple(event.name for event in subset),
                        "the query becomes pivotal after only normality-improving changes",
                    )
        return CausalPrediction(
            False,
            "redundant-under-normal-contingencies",
            operations,
            explanation="making the query pivotal would require a less normal contingency",
        )

    def judge_intent(self, evidence: IntentEvidence) -> CausalPrediction:
        operations = 1
        if not evidence.outcome_occurred:
            return CausalPrediction(False, "outcome-absent", operations)
        operations += 1
        if not evidence.controlled_action or not evidence.expected_path:
            return CausalPrediction(
                False,
                "accidental-realization",
                operations,
                explanation="the outcome did not follow a controlled expected path",
            )
        operations += 1
        intentional = evidence.goal or evidence.foresaw_side_effect
        return CausalPrediction(
            intentional,
            "goal" if evidence.goal else "foreseen-side-effect" if intentional else "unforeseen",
            operations,
            explanation="intent includes goals and foreseen side effects on a controlled expected path",
        )
