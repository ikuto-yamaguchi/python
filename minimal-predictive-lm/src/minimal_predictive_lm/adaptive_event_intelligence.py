from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class EventObservation:
    """One surface event and the observable consequence used for induction."""

    template: str
    domain: str
    effect: str | None
    success: bool | None
    lag: int | None


@dataclass(frozen=True)
class EventPartitionModel:
    partition: tuple[tuple[int, ...], ...]
    templates: tuple[str, ...]
    objective: float
    description_bits: int
    nll_bits: float


@dataclass(frozen=True)
class EventSearchResult:
    selected: EventPartitionModel
    evaluated_partitions: int


@dataclass(frozen=True)
class Sensor:
    name: str
    true_positive: float
    false_positive: float
    missing: float
    cost: float


@dataclass(frozen=True)
class DecisionValue:
    total_cost: float
    error_probability: float
    expected_probes: float
    action: str


def canonical_partition(
    partition: Sequence[Sequence[int]],
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        sorted(
            (tuple(sorted(block)) for block in partition),
            key=lambda block: block[0],
        )
    )


def enumerate_partitions(count: int):
    """Enumerate set partitions. Only for oracle-sized experiments."""

    def recurse(items: tuple[int, ...]):
        if not items:
            yield tuple()
            return
        first = items[0]
        for rest in recurse(items[1:]):
            yield ((first,),) + rest
            for index in range(len(rest)):
                merged = tuple(sorted(rest[index] + (first,)))
                candidate = rest[:index] + (merged,) + rest[index + 1 :]
                yield canonical_partition(candidate)

    seen: set[tuple[tuple[int, ...], ...]] = set()
    for partition in recurse(tuple(range(count))):
        normalized = canonical_partition(partition)
        if normalized in seen:
            continue
        seen.add(normalized)
        yield normalized


def _dirichlet_nll(counts: Sequence[int], categories: int) -> float:
    total = sum(counts)
    log_probability = (
        math.lgamma(categories)
        - math.lgamma(total + categories)
        + sum(math.lgamma(count + 1) for count in counts)
    )
    return -log_probability / math.log(2.0)


def _cluster_nll(
    block: Sequence[int],
    templates: tuple[str, ...],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
) -> float:
    selected_templates = {templates[index] for index in block}
    selected = [
        observation
        for observation in observations
        if observation.template in selected_templates
    ]
    successes = sum(observation.success is True for observation in selected)
    failures = sum(observation.success is False for observation in selected)
    nll = _dirichlet_nll((successes, failures), 2)

    effect_counts = Counter(
        observation.effect
        for observation in selected
        if observation.effect is not None
    )
    nll += _dirichlet_nll(
        tuple(effect_counts[effect] for effect in effect_vocabulary),
        len(effect_vocabulary),
    )

    lag_counts = Counter(
        observation.lag
        for observation in selected
        if observation.success is True and observation.lag is not None
    )
    nll += _dirichlet_nll(
        tuple(lag_counts[lag] for lag in range(1, max_lag + 1)),
        max_lag,
    )
    return nll


def fit_event_partition(
    partition: Sequence[Sequence[int]],
    templates: tuple[str, ...],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
    *,
    cluster_description_bits: int = 48,
) -> EventPartitionModel:
    normalized = canonical_partition(partition)
    cluster_count = len(normalized)
    assignment_bits = len(templates) * max(
        1,
        math.ceil(math.log2(cluster_count)),
    )
    description_bits = (
        cluster_count * cluster_description_bits + assignment_bits
    )
    nll_bits = sum(
        _cluster_nll(
            block,
            templates,
            observations,
            effect_vocabulary,
            max_lag,
        )
        for block in normalized
    )
    return EventPartitionModel(
        normalized,
        templates,
        description_bits + nll_bits,
        description_bits,
        nll_bits,
    )


def exhaustive_event_search(
    templates: tuple[str, ...],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
) -> EventSearchResult:
    models = [
        fit_event_partition(
            partition,
            templates,
            observations,
            effect_vocabulary,
            max_lag,
        )
        for partition in enumerate_partitions(len(templates))
    ]
    selected = min(models, key=lambda model: model.objective)
    return EventSearchResult(selected, len(models))


def beam_merge_event_search(
    templates: tuple[str, ...],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
    *,
    beam_width: int = 64,
) -> EventSearchResult:
    """Merge-only beam search from surface-specific clusters.

    Any partition is reachable by merges, but finite beam width is not a proof
    that the global optimum is retained.
    """

    start = tuple((index,) for index in range(len(templates)))
    first = fit_event_partition(
        start,
        templates,
        observations,
        effect_vocabulary,
        max_lag,
    )
    beam = [first]
    best = first
    seen = {start}
    evaluated = 1

    while beam and len(beam[0].partition) > 1:
        candidates: list[EventPartitionModel] = []
        for model in beam:
            partition = model.partition
            for left in range(len(partition)):
                for right in range(left + 1, len(partition)):
                    blocks = tuple(
                        block
                        for index, block in enumerate(partition)
                        if index not in (left, right)
                    )
                    merged = canonical_partition(
                        blocks
                        + (
                            tuple(
                                sorted(
                                    partition[left] + partition[right]
                                )
                            ),
                        )
                    )
                    if merged in seen:
                        continue
                    seen.add(merged)
                    candidates.append(
                        fit_event_partition(
                            merged,
                            templates,
                            observations,
                            effect_vocabulary,
                            max_lag,
                        )
                    )
                    evaluated += 1
        if not candidates:
            break
        candidates.sort(key=lambda model: model.objective)
        beam = candidates[:beam_width]
        if beam[0].objective < best.objective:
            best = beam[0]

    return EventSearchResult(best, evaluated)


def canonical_template_groups(
    model: EventPartitionModel,
) -> set[frozenset[str]]:
    return {
        frozenset(model.templates[index] for index in block)
        for block in model.partition
    }


def cluster_posterior(
    block: Sequence[int],
    templates: tuple[str, ...],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
) -> tuple[float, str, int]:
    selected_templates = {templates[index] for index in block}
    selected = [
        observation
        for observation in observations
        if observation.template in selected_templates
    ]
    successes = sum(observation.success is True for observation in selected)
    failures = sum(observation.success is False for observation in selected)
    success_probability = (successes + 1) / (successes + failures + 2)

    effect_counts = Counter(
        observation.effect
        for observation in selected
        if observation.effect is not None
    )
    effect = max(effect_vocabulary, key=lambda item: effect_counts[item])

    lag_counts = Counter(
        observation.lag
        for observation in selected
        if observation.success is True and observation.lag is not None
    )
    lag = max(range(1, max_lag + 1), key=lambda item: lag_counts[item])
    return success_probability, effect, lag


def assign_new_template(
    model: EventPartitionModel,
    calibration: Sequence[EventObservation],
    observations: Sequence[EventObservation],
    effect_vocabulary: tuple[str, ...],
    max_lag: int,
) -> int:
    if not calibration:
        raise ValueError("calibration must not be empty")
    new_template = calibration[0].template
    if any(item.template != new_template for item in calibration):
        raise ValueError("calibration must contain one surface template")

    costs: list[tuple[float, int]] = []
    extended_templates = model.templates + (new_template,)
    extended_observations = list(observations) + list(calibration)
    new_index = len(model.templates)
    for cluster_index, block in enumerate(model.partition):
        before = _cluster_nll(
            block,
            model.templates,
            observations,
            effect_vocabulary,
            max_lag,
        )
        after = _cluster_nll(
            tuple(block) + (new_index,),
            extended_templates,
            extended_observations,
            effect_vocabulary,
            max_lag,
        )
        costs.append((after - before, cluster_index))
    return min(costs)[1]


def beta_bernoulli_nll(outcomes: Sequence[bool]) -> float:
    successes = sum(outcomes)
    failures = len(outcomes) - successes
    return _dirichlet_nll((successes, failures), 2)


def best_change_point(
    outcomes: Sequence[bool],
    *,
    min_segment: int = 30,
    split_description_bits: float = 10.0,
) -> tuple[int | None, float]:
    """Return the best single split and its MDL gain."""

    if len(outcomes) < min_segment * 2:
        return None, 0.0
    unsplit = beta_bernoulli_nll(outcomes)
    best_split: int | None = None
    best_gain = 0.0
    for split in range(min_segment, len(outcomes) - min_segment + 1):
        split_cost = (
            beta_bernoulli_nll(outcomes[:split])
            + beta_bernoulli_nll(outcomes[split:])
            + split_description_bits
        )
        gain = unsplit - split_cost
        if gain > best_gain:
            best_gain = gain
            best_split = split
    return best_split, best_gain


def _sensor_branches(
    probability: float,
    sensor: Sensor,
) -> tuple[dict[str, float], dict[str, float]]:
    observed = 1.0 - sensor.missing
    positive_likelihood = (
        probability * sensor.true_positive
        + (1.0 - probability) * sensor.false_positive
    )
    negative_likelihood = (
        probability * (1.0 - sensor.true_positive)
        + (1.0 - probability) * (1.0 - sensor.false_positive)
    )
    branch_probability = {
        "positive": observed * positive_likelihood,
        "negative": observed * negative_likelihood,
        "missing": sensor.missing,
    }
    positive_posterior = (
        probability * sensor.true_positive / positive_likelihood
        if positive_likelihood > 0.0
        else probability
    )
    negative_posterior = (
        probability * (1.0 - sensor.true_positive) / negative_likelihood
        if negative_likelihood > 0.0
        else probability
    )
    posterior = {
        "positive": positive_posterior,
        "negative": negative_posterior,
        "missing": probability,
    }
    return branch_probability, posterior


def exact_bounded_information_policy(
    probability: float,
    sensors: Sequence[Sensor],
    *,
    wrong_decision_cost: float = 64.0,
) -> tuple[DecisionValue, int]:
    """Solve the finite binary POMDP exactly for the supplied probes."""

    cache: dict[tuple[float, tuple[int, ...]], DecisionValue] = {}

    def solve(
        belief: float,
        remaining: tuple[int, ...],
    ) -> DecisionValue:
        key = (round(belief, 12), remaining)
        if key in cache:
            return cache[key]

        immediate_error = min(belief, 1.0 - belief)
        best = DecisionValue(
            immediate_error * wrong_decision_cost,
            immediate_error,
            0.0,
            "act",
        )
        for sensor_index in remaining:
            sensor = sensors[sensor_index]
            probabilities, posteriors = _sensor_branches(belief, sensor)
            next_remaining = tuple(
                index for index in remaining if index != sensor_index
            )
            total_cost = sensor.cost
            error_probability = 0.0
            expected_probes = 1.0
            for outcome, outcome_probability in probabilities.items():
                child = solve(posteriors[outcome], next_remaining)
                total_cost += outcome_probability * child.total_cost
                error_probability += (
                    outcome_probability * child.error_probability
                )
                expected_probes += outcome_probability * child.expected_probes
            candidate = DecisionValue(
                total_cost,
                error_probability,
                expected_probes,
                f"probe:{sensor.name}",
            )
            if candidate.total_cost < best.total_cost - 1e-12:
                best = candidate

        cache[key] = best
        return best

    value = solve(probability, tuple(range(len(sensors))))
    return value, len(cache)


def no_probe_policy(
    probability: float,
    *,
    wrong_decision_cost: float = 64.0,
) -> DecisionValue:
    error = min(probability, 1.0 - probability)
    return DecisionValue(error * wrong_decision_cost, error, 0.0, "act")


def one_probe_policy(
    probability: float,
    sensors: Sequence[Sensor],
    *,
    wrong_decision_cost: float = 64.0,
) -> DecisionValue:
    best = no_probe_policy(
        probability,
        wrong_decision_cost=wrong_decision_cost,
    )
    for sensor in sensors:
        probabilities, posteriors = _sensor_branches(probability, sensor)
        error = sum(
            probabilities[outcome]
            * min(posteriors[outcome], 1.0 - posteriors[outcome])
            for outcome in probabilities
        )
        candidate = DecisionValue(
            sensor.cost + error * wrong_decision_cost,
            error,
            1.0,
            f"probe:{sensor.name}",
        )
        if candidate.total_cost < best.total_cost:
            best = candidate
    return best


def always_probe_policy(
    probability: float,
    sensors: Sequence[Sensor],
    *,
    wrong_decision_cost: float = 64.0,
) -> DecisionValue:
    def evaluate(belief: float, index: int) -> DecisionValue:
        if index == len(sensors):
            return no_probe_policy(
                belief,
                wrong_decision_cost=wrong_decision_cost,
            )
        sensor = sensors[index]
        probabilities, posteriors = _sensor_branches(belief, sensor)
        total_cost = sensor.cost
        error_probability = 0.0
        expected_probes = 1.0
        for outcome, outcome_probability in probabilities.items():
            child = evaluate(posteriors[outcome], index + 1)
            total_cost += outcome_probability * child.total_cost
            error_probability += (
                outcome_probability * child.error_probability
            )
            expected_probes += outcome_probability * child.expected_probes
        return DecisionValue(
            total_cost,
            error_probability,
            expected_probes,
            f"probe:{sensor.name}",
        )

    return evaluate(probability, 0)
