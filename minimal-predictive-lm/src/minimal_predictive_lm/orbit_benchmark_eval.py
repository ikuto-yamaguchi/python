from __future__ import annotations

from dataclasses import dataclass
import random

from .orbit_benchmark_data import MECHANISMS, apply_named, build_training, transition
from .orbit_delta_baseline import ExactDeltaBaseline
from .orbit_learner import OrbitLearner
from .orbit_operator import TransitionEpisode, ordered_roles, parse_control


@dataclass(frozen=True)
class ScaleResult:
    examples_per_surface: int
    training_episodes: int
    orbit_count: int
    orbit_bytes: int
    reuse_ratio: float
    heldout_accuracy: float
    heldout_coverage: float
    one_shot_grounding_accuracy: float
    depth2_accuracy: float
    depth4_accuracy: float
    depth8_accuracy: float
    depth16_accuracy: float
    counterfactual_selectivity: float
    baseline_accuracy: float
    residual_rate: float


def evaluate_scale(
    examples_per_surface: int,
    seed: int,
    noise_rate: float = 0.0,
) -> ScaleResult:
    training = build_training(examples_per_surface, seed, noise_rate)
    learner = OrbitLearner(
        minimum_support=max(2, examples_per_surface // 3),
        minimum_fraction=0.7,
    )
    learner.fit(training)
    baseline = ExactDeltaBaseline()
    for row in training:
        baseline.observe(row)

    rng = random.Random(seed + 1)
    grounded = 0
    for mechanism, specification in MECHANISMS.items():
        demo = transition(
            mechanism,
            str(specification["heldout"]),
            rng,
            100_000 + grounded,
            noise_entities=7,
        )
        grounded += int(learner.ground_surface_once(demo) is not None)
        baseline.observe(demo)

    correct = answered = selective = baseline_correct = total = 0
    for mechanism, specification in MECHANISMS.items():
        for _index in range(96):
            row = transition(
                mechanism,
                str(specification["heldout"]),
                rng,
                200_000 + total,
                noise_entities=11,
            )
            prediction = learner.predict(row.text, row.before)
            answered += int(prediction.after is not None)
            correct += int(prediction.after == dict(row.after))
            baseline_correct += int(
                baseline.predict(row.text, row.before) == dict(row.after)
            )
            selective += int(_matching_orbits(learner, row) == 1)
            total += 1

    support = sum(orbit.support for orbit in learner.orbits.values())
    residuals = sum(orbit.residuals for orbit in learner.orbits.values())
    return ScaleResult(
        examples_per_surface,
        len(training),
        len(learner.orbits),
        len(learner.to_bytes()),
        1.0 - len(learner.orbits) / len(training),
        correct / total,
        answered / total,
        grounded / len(MECHANISMS),
        _composition(learner, 2, rng),
        _composition(learner, 4, rng),
        _composition(learner, 8, rng),
        _composition(learner, 16, rng),
        selective / total,
        baseline_correct / total,
        residuals / max(1, support + residuals),
    )


def _composition(learner: OrbitLearner, depth: int, rng: random.Random) -> float:
    correct = 0
    for episode in range(48):
        a, b = f"C{episode}甲", f"C{episode}乙"
        expected = {a: rng.randint(200, 800), b: rng.randint(200, 800)}
        predicted = dict(expected)
        solved = True
        for step in range(depth):
            mechanism = tuple(MECHANISMS)[(episode + step) % len(MECHANISMS)]
            control = rng.randint(2, 31)
            text = str(MECHANISMS[mechanism]["heldout"]).format(
                a=a,
                b=b,
                c=control,
            )
            expected = apply_named(mechanism, expected, a, b, control)
            result = learner.predict(text, predicted)
            if result.after is None:
                solved = False
                break
            predicted = result.after
        correct += int(solved and predicted == expected)
    return correct / 48


def _matching_orbits(learner: OrbitLearner, row: TransitionEpisode) -> int:
    roles = ordered_roles(row.text, row.before, row.after)
    values = tuple(row.before[role] for role in roles)
    targets = tuple(row.after[role] for role in roles)
    control = parse_control(row.text, row.before)
    matches = 0
    for orbit in learner.orbits.values():
        if orbit.operator.arity != len(roles):
            continue
        variants = [orbit.operator]
        if orbit.operator.arity == 2:
            variants.append(orbit.operator.permute((1, 0)))
        matches += int(
            any(operator.apply_values(values, control) == targets for operator in variants)
        )
    return matches
