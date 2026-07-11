from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import ceil, log2
from random import Random
from typing import Mapping


def counter_bits(value: int) -> int:
    """Bits needed by a non-negative integer counter, including zero."""

    if value < 0:
        raise ValueError("counter must be non-negative")
    return max(1, ceil(log2(value + 1)))


@dataclass
class EffectBelief:
    """Conjugate sufficient statistics for success and delayed completion.

    A Beta(1, 1) prior is used for whether an effect eventually happens.  A
    symmetric Dirichlet(1, ..., 1) prior is used for the lag conditional on a
    successful effect.  The active state grows with the number of lag bins, not
    with the number of historical episodes.
    """

    max_lag: int = 16
    successes: int = 0
    failures: int = 0
    lag_counts: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_lag <= 0:
            raise ValueError("max_lag must be positive")
        if not self.lag_counts:
            self.lag_counts = [0] * self.max_lag
        if len(self.lag_counts) != self.max_lag:
            raise ValueError("lag_counts must match max_lag")
        if self.successes < 0 or self.failures < 0:
            raise ValueError("counts must be non-negative")
        if any(value < 0 for value in self.lag_counts):
            raise ValueError("lag counts must be non-negative")

    @property
    def success_probability(self) -> Fraction:
        return Fraction(self.successes + 1, self.successes + self.failures + 2)

    def lag_probability(self, lag: int) -> Fraction:
        if not 1 <= lag <= self.max_lag:
            raise ValueError("lag outside supported range")
        total = sum(self.lag_counts) + self.max_lag
        return Fraction(self.lag_counts[lag - 1] + 1, total)

    def lag_cdf(self, step: int) -> Fraction:
        bounded = max(0, min(step, self.max_lag))
        total = sum(self.lag_counts) + self.max_lag
        observed = sum(value + 1 for value in self.lag_counts[:bounded])
        return Fraction(observed, total)

    def changed_by(self, step: int) -> Fraction:
        return self.success_probability * self.lag_cdf(step)

    def observe(self, success: bool | None, lag: int | None = None) -> None:
        """Update only statistics actually observed.

        ``success=None`` is a censored/missing outcome and therefore adds no
        fictitious failure.  A successful outcome with unknown lag updates the
        Bernoulli statistic but not the lag statistic.
        """

        if success is None:
            return
        if success:
            self.successes += 1
            if lag is not None:
                if not 1 <= lag <= self.max_lag:
                    raise ValueError("lag outside supported range")
                self.lag_counts[lag - 1] += 1
        else:
            if lag is not None:
                raise ValueError("failed effect cannot have a completion lag")
            self.failures += 1

    def sufficient_stat_bits(self) -> int:
        return sum(
            counter_bits(value)
            for value in (self.successes, self.failures, *self.lag_counts)
        )


@dataclass(frozen=True)
class BinarySensor:
    true_positive: Fraction
    false_positive: Fraction
    missing_probability: Fraction
    cost: Fraction

    def __post_init__(self) -> None:
        for name, value in (
            ("true_positive", self.true_positive),
            ("false_positive", self.false_positive),
            ("missing_probability", self.missing_probability),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be a probability")
        if self.cost < 0:
            raise ValueError("sensor cost must be non-negative")


@dataclass(frozen=True)
class ProbeChoice:
    should_probe: bool
    value_of_information: Fraction
    current_risk: Fraction
    expected_risk_after_probe: Fraction
    total_probe_risk: Fraction


def bayes_error_risk(probability_true: Fraction, error_cost: Fraction) -> Fraction:
    if not 0 <= probability_true <= 1:
        raise ValueError("probability must be in [0, 1]")
    if error_cost < 0:
        raise ValueError("error cost must be non-negative")
    return min(probability_true, 1 - probability_true) * error_cost


def posterior_probability(
    prior: Fraction,
    sensor: BinarySensor,
    reading: bool | None,
) -> Fraction:
    """Exact Bayes update for a positive, negative, or missing reading."""

    if not 0 <= prior <= 1:
        raise ValueError("prior must be in [0, 1]")
    if reading is None:
        return prior
    if reading:
        denominator = (
            prior * sensor.true_positive
            + (1 - prior) * sensor.false_positive
        )
        if denominator == 0:
            return prior
        return prior * sensor.true_positive / denominator
    denominator = (
        prior * (1 - sensor.true_positive)
        + (1 - prior) * (1 - sensor.false_positive)
    )
    if denominator == 0:
        return prior
    return prior * (1 - sensor.true_positive) / denominator


def expected_risk_after_probe(
    prior: Fraction,
    sensor: BinarySensor,
    error_cost: Fraction,
) -> Fraction:
    """Enumerate all three probe outcomes exactly."""

    missing = sensor.missing_probability
    observed = 1 - missing
    positive_probability = observed * (
        prior * sensor.true_positive
        + (1 - prior) * sensor.false_positive
    )
    negative_probability = observed * (
        prior * (1 - sensor.true_positive)
        + (1 - prior) * (1 - sensor.false_positive)
    )
    return (
        missing * bayes_error_risk(prior, error_cost)
        + positive_probability
        * bayes_error_risk(
            posterior_probability(prior, sensor, True),
            error_cost,
        )
        + negative_probability
        * bayes_error_risk(
            posterior_probability(prior, sensor, False),
            error_cost,
        )
    )


def choose_probe(
    prior: Fraction,
    sensor: BinarySensor,
    error_cost: Fraction,
) -> ProbeChoice:
    """Bayes-optimal choice among ACT-NOW and PROBE-THEN-ACT.

    The action set is finite and every probe outcome is enumerated.  Therefore
    this decision is exact for the one-probe problem rather than a heuristic.
    """

    current = bayes_error_risk(prior, error_cost)
    after = expected_risk_after_probe(prior, sensor, error_cost)
    total = after + sensor.cost
    value = current - total
    return ProbeChoice(value > 0, value, current, after, total)


def minimum_risk_decision(probability_true: Fraction) -> bool:
    return probability_true >= Fraction(1, 2)


def sample_sensor(
    rng: Random,
    truth: bool,
    sensor: BinarySensor,
) -> bool | None:
    if rng.random() < float(sensor.missing_probability):
        return None
    positive_probability = sensor.true_positive if truth else sensor.false_positive
    return rng.random() < float(positive_probability)


@dataclass(frozen=True)
class Claim:
    claim_id: int
    key: str
    value: str
    timestamp: int
    confidence_milli: int


class TemporalFactLedger:
    """Append-only provenance with a minimal active view.

    Retraction can reveal an older still-active claim.  Once a time horizon is
    finalized, ``snapshot`` is the sufficient runtime state and the full ledger
    may be archived outside the active decision loop.
    """

    def __init__(self) -> None:
        self._claims: dict[int, Claim] = {}
        self._retracted: set[int] = set()
        self._next_id = 0

    @property
    def claim_count(self) -> int:
        return len(self._claims)

    def add(
        self,
        key: str,
        value: str,
        timestamp: int,
        confidence: Fraction = Fraction(1, 1),
    ) -> int:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
        claim_id = self._next_id
        self._next_id += 1
        self._claims[claim_id] = Claim(
            claim_id,
            key,
            value,
            timestamp,
            int(confidence * 1000),
        )
        return claim_id

    def retract(self, claim_id: int) -> None:
        if claim_id not in self._claims:
            raise KeyError(claim_id)
        self._retracted.add(claim_id)

    def resolve_claim(self, key: str) -> Claim | None:
        active = [
            claim
            for claim_id, claim in self._claims.items()
            if claim_id not in self._retracted and claim.key == key
        ]
        if not active:
            return None
        return max(
            active,
            key=lambda claim: (
                claim.timestamp,
                claim.confidence_milli,
                claim.claim_id,
            ),
        )

    def resolve(self, key: str) -> str | None:
        claim = self.resolve_claim(key)
        return None if claim is None else claim.value

    def snapshot(self) -> dict[str, str]:
        keys = sorted({claim.key for claim in self._claims.values()})
        return {
            key: value
            for key in keys
            if (value := self.resolve(key)) is not None
        }

    def contradiction_count(self) -> int:
        active_values: dict[str, set[str]] = {}
        for claim_id, claim in self._claims.items():
            if claim_id in self._retracted:
                continue
            active_values.setdefault(claim.key, set()).add(claim.value)
        return sum(max(0, len(values) - 1) for values in active_values.values())

    def ledger_bits(self) -> int:
        """Simple explicit code length for the active provenance ledger."""

        claim_bits = sum(
            32
            + 32
            + 10
            + 8 * len(claim.key.encode("utf-8"))
            + 8 * len(claim.value.encode("utf-8"))
            for claim in self._claims.values()
        )
        return claim_bits + len(self._claims)

    def finalized_snapshot_bits(self) -> int:
        return sum(
            8 * len(key.encode("utf-8"))
            + 8 * len(value.encode("utf-8"))
            for key, value in self.snapshot().items()
        )


def snapshot_matches(
    ledger: TemporalFactLedger,
    expected: Mapping[str, str],
) -> bool:
    return ledger.snapshot() == dict(expected)
