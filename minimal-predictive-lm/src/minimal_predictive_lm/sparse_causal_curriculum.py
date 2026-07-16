from __future__ import annotations

import random
import string

from .sparse_causal_induction import CausalTrainingExample


def _name(rng: random.Random, prefix: str) -> str:
    return prefix + "".join(rng.choice(string.ascii_lowercase) for _ in range(7))


def build_sparse_causal_curriculum(
    *, seed: int = 1810, variants_per_pattern: int = 160
) -> tuple[CausalTrainingExample, ...]:
    rng = random.Random(seed)
    rows: list[CausalTrainingExample] = []

    for _ in range(variants_per_pattern):
        agent = _name(rng, "agent")
        target = _name(rng, "target")
        rows.extend(
            (
                CausalTrainingExample(
                    f"{agent} realized that acting would definitely harm {target}. "
                    f"{agent} did not care and decided to act. The harm occurred. "
                    f"Did {agent} intentionally harm {target}?",
                    "intent-foreseen",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"{agent} wanted to win but lost balance. The tool slipped out of "
                    f"the agent's hand and accidentally hit {target}. Did {agent} "
                    f"intentionally hit {target}?",
                    "intent-accident",
                    "No",
                ),
                CausalTrainingExample(
                    f"A committee was told that a program would increase profit but "
                    f"would also damage {target}. The committee decided to implement "
                    f"the program and the damage occurred. Did the committee "
                    f"intentionally damage {target}?",
                    "intent-foreseen",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"{agent} deliberately performed an action for another goal. The "
                    f"action unexpectedly made {target} move, and the effect had not "
                    f"been foreseen. Did {agent} intentionally move {target}?",
                    "intent-unforeseen",
                    "No",
                ),
            )
        )

    for _ in range(variants_per_pattern):
        worker = _name(rng, "worker")
        machine = _name(rng, "machine")
        rows.extend(
            (
                CausalTrainingExample(
                    f"{worker} is responsible for maintaining {machine}. {worker} "
                    f"noticed that oil was missing but did not add it. {machine} broke. "
                    f"Did {machine} break because {worker} did not add oil?",
                    "omission-duty",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"{worker} was not responsible for maintaining {machine} and did "
                    f"not notice that oil was missing. {machine} broke. Did {machine} "
                    f"break because {worker} did not add oil?",
                    "omission-passive",
                    "No",
                ),
                CausalTrainingExample(
                    f"A service sends a reward when a client is subscribed. The client "
                    f"was already subscribed and did not change the status. The reward "
                    f"arrived. Did the reward arrive because the client did not change "
                    f"the subscription status?",
                    "omission-passive-state",
                    "No",
                ),
                CausalTrainingExample(
                    f"{worker} checked an enabled switch, saw that it was on, and left "
                    f"it on. The enabled switch powered {machine}. Did {machine} run "
                    f"because {worker} did not turn the switch off?",
                    "omission-maintenance",
                    "Yes",
                ),
            )
        )

    for _ in range(variants_per_pattern):
        violator = _name(rng, "violator")
        normal = _name(rng, "normal")
        outcome = _name(rng, "outcome")
        rows.extend(
            (
                CausalTrainingExample(
                    f"{outcome} occurs if both {violator} and {normal} enter. "
                    f"{violator} is not supposed to enter and deliberately ignores the "
                    f"rule. {normal} is supposed to enter and follows the rule. Both "
                    f"enter and {outcome} occurs. Did {violator} cause {outcome}?",
                    "conjunct-abnormal",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"{outcome} occurs if both {violator} and {normal} enter. "
                    f"{violator} is not supposed to enter and deliberately ignores the "
                    f"rule. {normal} is supposed to enter and follows the rule. Both "
                    f"enter and {outcome} occurs. Did {normal} cause {outcome}?",
                    "conjunct-normal",
                    "No",
                ),
                CausalTrainingExample(
                    f"A result requires both a rare roll and an ordinary coin result. "
                    f"The rare roll amazingly occurs and the coin has its normal result. "
                    f"Did the ordinary coin result cause the outcome?",
                    "conjunct-normal",
                    "No",
                ),
                CausalTrainingExample(
                    f"A result requires both a rare roll and an ordinary coin result. "
                    f"The rare roll amazingly occurs and the coin has its normal result. "
                    f"Did the rare roll cause the outcome?",
                    "conjunct-abnormal",
                    "Yes",
                ),
            )
        )

    for _ in range(variants_per_pattern):
        actor = _name(rng, "actor")
        outcome = _name(rng, "outcome")
        rows.extend(
            (
                CausalTrainingExample(
                    f"{outcome} occurs if either switch A is active or switch B is "
                    f"active. Switch A was already active. {actor} later changed switch "
                    f"B to active and {outcome} occurred. Did {outcome} occur because "
                    f"{actor} changed switch B?",
                    "disjunct-redundant-addition",
                    "No",
                ),
                CausalTrainingExample(
                    f"A shop profits if anyone orders. As usual, {actor} ordered and "
                    f"two other regular customers also ordered. Did {actor} ordering "
                    f"cause the shop to profit?",
                    "disjunct-equal-normal",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"A shop profits if anyone orders. Unexpectedly, {actor} ordered, "
                    f"while two usual customers also ordered. Did {actor} ordering "
                    f"cause the shop to profit?",
                    "disjunct-abnormal-redundant",
                    "No",
                ),
                CausalTrainingExample(
                    f"A vehicle needs at least one battery. {actor} and another person "
                    f"independently obtained equal batteries and installed both. Did "
                    f"{actor} cause the vehicle to become able to start?",
                    "disjunct-equal-contributor",
                    "Yes",
                ),
            )
        )

    for _ in range(variants_per_pattern):
        first = _name(rng, "first")
        later = _name(rng, "later")
        outcome = _name(rng, "outcome")
        rows.extend(
            (
                CausalTrainingExample(
                    f"Either {first} or {later} is sufficient for {outcome}. {first} "
                    f"occurred right at the beginning, and {later} occurred at the end. "
                    f"Did {later} cause {outcome}?",
                    "preemption-late",
                    "No",
                ),
                CausalTrainingExample(
                    f"Either {first} or {later} is sufficient for {outcome}. {first} "
                    f"occurred right at the beginning, and {later} occurred at the end. "
                    f"Did {first} cause {outcome}?",
                    "preemption-early",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"A person chose meal B instead of meal A. Both of these meals "
                    f"contained the same allergen and either choice would cause the "
                    f"reaction. Did the person's choice of meal cause the reaction?",
                    "choice-invariant",
                    "No",
                ),
                CausalTrainingExample(
                    f"A direct intervention immediately produced {outcome}. A remote "
                    f"background condition existed years earlier. Did the direct "
                    f"intervention cause {outcome}?",
                    "path-direct",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"A direct intervention immediately produced {outcome}. A remote "
                    f"background condition existed years earlier. Did the remote "
                    f"background condition cause {outcome}?",
                    "path-background",
                    "No",
                ),
            )
        )

    for _ in range(variants_per_pattern):
        query = _name(rng, "query")
        outcome = _name(rng, "outcome")
        rows.extend(
            (
                CausalTrainingExample(
                    f"A detector activates if two people enter. Exactly two entered, "
                    f"including {query}, who was prohibited from entering. Did {query} "
                    f"cause the detector to activate?",
                    "threshold-abnormal-member",
                    "Yes",
                ),
                CausalTrainingExample(
                    f"A breaker fails if two people activate devices. Four people "
                    f"activated devices, including {query}. Did {query} cause the "
                    f"breaker to fail?",
                    "threshold-overdetermined",
                    "No",
                ),
                CausalTrainingExample(
                    f"A box is empty because an allowed person and a prohibited person "
                    f"both took the final items. Did the allowed person cause the "
                    f"problem?",
                    "depletion-normal-contributor",
                    "No",
                ),
                CausalTrainingExample(
                    f"A box is empty because an allowed person and a prohibited person "
                    f"both took the final items. Did the prohibited person cause the "
                    f"problem?",
                    "depletion-abnormal-contributor",
                    "Yes",
                ),
            )
        )

    rng.shuffle(rows)
    return tuple(rows)
