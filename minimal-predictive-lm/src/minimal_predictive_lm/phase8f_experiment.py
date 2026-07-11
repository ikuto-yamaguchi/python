from __future__ import annotations

import json
import math
import random
from fractions import Fraction
from pathlib import Path
from typing import Mapping

from .probabilistic_effects import (
    BinarySensor,
    EffectBelief,
    TemporalFactLedger,
    choose_probe,
    minimum_risk_decision,
    posterior_probability,
    sample_sensor,
)


RELATIONS: tuple[str, ...] = ("location", "owner", "status")
GROUND_TRUTH: Mapping[str, tuple[Fraction, Mapping[int, Fraction]]] = {
    "location": (
        Fraction(9, 10),
        {2: Fraction(7, 10), 4: Fraction(3, 10)},
    ),
    "owner": (
        Fraction(3, 4),
        {1: Fraction(1, 2), 3: Fraction(1, 2)},
    ),
    "status": (
        Fraction(3, 5),
        {5: Fraction(2, 5), 8: Fraction(3, 5)},
    ),
}
SENSOR = BinarySensor(
    true_positive=Fraction(9, 10),
    false_positive=Fraction(2, 25),
    missing_probability=Fraction(1, 4),
    cost=Fraction(4, 1),
)
ERROR_COST = Fraction(64, 1)


def _sample_lag(
    rng: random.Random,
    distribution: Mapping[int, Fraction],
) -> int:
    draw = rng.random()
    cumulative = 0.0
    for lag, probability in sorted(distribution.items()):
        cumulative += float(probability)
        if draw < cumulative:
            return lag
    return max(distribution)


def _train_beliefs() -> tuple[dict[str, EffectBelief], dict[str, int]]:
    rng = random.Random(7)
    beliefs = {relation: EffectBelief(max_lag=16) for relation in RELATIONS}
    statistics = {
        "episodes": 1_200,
        "missing_outcome": 0,
        "missing_lag": 0,
        "observed_success": 0,
        "observed_failure": 0,
    }
    for index in range(statistics["episodes"]):
        relation = RELATIONS[index % len(RELATIONS)]
        success_probability, lag_distribution = GROUND_TRUTH[relation]
        success = rng.random() < float(success_probability)
        lag = _sample_lag(rng, lag_distribution) if success else None

        if rng.random() < 0.30:
            statistics["missing_outcome"] += 1
            beliefs[relation].observe(None)
            continue

        if success:
            statistics["observed_success"] += 1
            if rng.random() < 0.25:
                statistics["missing_lag"] += 1
                beliefs[relation].observe(True, None)
            else:
                beliefs[relation].observe(True, lag)
        else:
            statistics["observed_failure"] += 1
            beliefs[relation].observe(False)
    return beliefs, statistics


def _heldout_episodes(
    beliefs: Mapping[str, EffectBelief],
) -> list[dict[str, object]]:
    rng = random.Random(99)
    episodes: list[dict[str, object]] = []
    for index in range(3_000):
        relation = RELATIONS[index % len(RELATIONS)]
        success_probability, lag_distribution = GROUND_TRUTH[relation]
        success = rng.random() < float(success_probability)
        lag = _sample_lag(rng, lag_distribution) if success else None
        step = 1 + (index * 7) % 16
        truth = bool(success and lag is not None and lag <= step)
        reading = sample_sensor(rng, truth, SENSOR)
        episodes.append(
            {
                "relation": relation,
                "step": step,
                "truth": truth,
                "reading": reading,
                "prior": beliefs[relation].changed_by(step),
            }
        )
    return episodes


def _evaluate_policy(
    episodes: list[dict[str, object]],
    mode: str,
) -> dict[str, int | float]:
    errors = 0
    probes = 0
    missing_probes = 0
    total_objective = Fraction(0, 1)
    for episode in episodes:
        prior = episode["prior"]
        assert isinstance(prior, Fraction)
        truth = bool(episode["truth"])
        reading = episode["reading"]
        assert reading is None or isinstance(reading, bool)

        choice = choose_probe(prior, SENSOR, ERROR_COST)
        should_probe = mode == "always" or (mode == "voi" and choice.should_probe)
        posterior = prior
        if should_probe:
            probes += 1
            total_objective += SENSOR.cost
            if reading is None:
                missing_probes += 1
            posterior = posterior_probability(prior, SENSOR, reading)
        prediction = minimum_risk_decision(posterior)
        if prediction != truth:
            errors += 1
            total_objective += ERROR_COST

    total = len(episodes)
    return {
        "errors": errors,
        "accuracy": (total - errors) / total,
        "probes": probes,
        "probe_rate": probes / total,
        "missing_probes": missing_probes,
        "total_objective": float(total_objective),
    }


def _brier_score(episodes: list[dict[str, object]], *, uniform: bool) -> float:
    total = 0.0
    for episode in episodes:
        probability = Fraction(1, 2) if uniform else episode["prior"]
        assert isinstance(probability, Fraction)
        target = 1.0 if episode["truth"] else 0.0
        total += (float(probability) - target) ** 2
    return total / len(episodes)


def _belief_payload(beliefs: Mapping[str, EffectBelief]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for relation, belief in beliefs.items():
        true_success, true_lags = GROUND_TRUTH[relation]
        learned_lags = {
            str(lag): float(belief.lag_probability(lag))
            for lag in range(1, belief.max_lag + 1)
            if belief.lag_counts[lag - 1] > 0
        }
        payload[relation] = {
            "true_success_probability": float(true_success),
            "learned_success_probability": float(belief.success_probability),
            "true_lag_distribution": {
                str(lag): float(probability)
                for lag, probability in true_lags.items()
            },
            "learned_observed_lag_bins": learned_lags,
            "successes": belief.successes,
            "failures": belief.failures,
            "sufficient_stat_bits": belief.sufficient_stat_bits(),
        }
    return payload


def _voi_exactness() -> dict[str, object]:
    checked = 0
    exact = True
    for numerator in range(21):
        prior = Fraction(numerator, 20)
        choice = choose_probe(prior, SENSOR, ERROR_COST)
        brute_force_probe = choice.total_probe_risk < choice.current_risk
        exact &= choice.should_probe == brute_force_probe
        checked += 1
    return {
        "priors_checked": checked,
        "matches_full_two-action_enumeration": exact,
        "probe_outcomes_enumerated": 3,
    }


def _contradiction_experiment() -> dict[str, object]:
    restoration = TemporalFactLedger()
    restoration.add("設計書", "棚A", 1)
    newer = restoration.add("設計書", "保管庫", 2)
    before_retraction = restoration.resolve("設計書")
    restoration.retract(newer)
    after_retraction = restoration.resolve("設計書")

    ledger = TemporalFactLedger()
    for index in range(512):
        key = f"項目{index % 32}"
        value = f"値{(index // 32) % 7}"
        claim_id = ledger.add(key, value, index)
        if index % 11 == 0 and index > 0:
            ledger.retract(claim_id)

    ledger_bits = ledger.ledger_bits()
    snapshot_bits = ledger.finalized_snapshot_bits()
    return {
        "retraction_restores_previous_claim": (
            before_retraction == "保管庫" and after_retraction == "棚A"
        ),
        "before_retraction": before_retraction,
        "after_retraction": after_retraction,
        "claims": ledger.claim_count,
        "resolved_keys": len(ledger.snapshot()),
        "active_contradictions": ledger.contradiction_count(),
        "provenance_ledger_bits": ledger_bits,
        "finalized_snapshot_bits": snapshot_bits,
        "finalized_compaction_ratio": ledger_bits / snapshot_bits,
        "scope": "snapshot compaction is valid only after the retraction horizon is finalized",
    }


def run() -> dict[str, object]:
    beliefs, training = _train_beliefs()
    episodes = _heldout_episodes(beliefs)
    policies = {
        mode: _evaluate_policy(episodes, mode)
        for mode in ("none", "always", "voi")
    }
    sufficient_stat_bits = sum(
        belief.sufficient_stat_bits() for belief in beliefs.values()
    )
    relation_bits = math.ceil(math.log2(len(RELATIONS)))
    raw_event_bits = training["episodes"] * (relation_bits + 2 + 5)

    return {
        "training": {
            **training,
            "beliefs": _belief_payload(beliefs),
            "sufficient_stat_bits": sufficient_stat_bits,
            "compact_raw_event_code_bits": raw_event_bits,
            "history_to_sufficient_stat_ratio": raw_event_bits / sufficient_stat_bits,
        },
        "prediction": {
            "heldout_episodes": len(episodes),
            "learned_brier": _brier_score(episodes, uniform=False),
            "uniform_brier": _brier_score(episodes, uniform=True),
        },
        "policies": policies,
        "voi_exactness": _voi_exactness(),
        "contradiction_and_retraction": _contradiction_experiment(),
        "conclusion": {
            "voi_lower_objective_than_no_probe": (
                policies["voi"]["total_objective"]
                < policies["none"]["total_objective"]
            ),
            "voi_lower_objective_than_always_probe": (
                policies["voi"]["total_objective"]
                < policies["always"]["total_objective"]
            ),
            "voi_matches_always_probe_accuracy": (
                policies["voi"]["accuracy"] == policies["always"]["accuracy"]
            ),
            "voi_uses_fewer_probes": (
                policies["voi"]["probes"] < policies["always"]["probes"]
            ),
        },
        "limitations": [
            "the effect family and relation identity are supplied during this phase",
            "Beta and Dirichlet sufficient statistics assume stationary exchangeable episodes",
            "the VOI theorem is exact only for one optional binary/missing probe and a binary terminal decision",
            "sensor reliability is known rather than jointly induced",
            "snapshot compaction requires a finalized retraction horizon",
            "this is not open-domain conversation, writing, or repository-scale coding",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    training = payload["training"]
    prediction = payload["prediction"]
    policies = payload["policies"]
    contradiction = payload["contradiction_and_retraction"]
    lines = [
        "# Phase 8f results: probabilistic effects, missing sensors, and exact one-probe VOI",
        "",
        "Beta/Dirichlet sufficient statistics replace episode replay. Missing outcomes add no fictitious",
        "failure, and missing lags update success without inventing a completion time.",
        "",
        f"- training episodes: **{training['episodes']:,}**",
        f"- missing outcomes: **{training['missing_outcome']:,}**",
        f"- successful outcomes with missing lag: **{training['missing_lag']:,}**",
        f"- active sufficient statistics: **{training['sufficient_stat_bits']:,} bits**",
        f"- compact raw event code: **{training['compact_raw_event_code_bits']:,} bits**",
        f"- history/stat ratio: **{training['history_to_sufficient_stat_ratio']:.2f}x**",
        f"- learned Brier score: **{prediction['learned_brier']:.6f}**",
        f"- uniform-prior Brier score: **{prediction['uniform_brier']:.6f}**",
        "",
        "## Observation policies",
        "",
        "| policy | accuracy | probes | probe rate | missing probes | total objective |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("none", "always", "voi"):
        item = policies[mode]
        lines.append(
            f"| {mode} | {item['accuracy']:.1%} | {item['probes']:,} | "
            f"{item['probe_rate']:.1%} | {item['missing_probes']:,} | "
            f"{item['total_objective']:,.0f} |"
        )
    lines.extend(
        [
            "",
            "The VOI policy enumerates positive, negative, and missing readings exactly. It therefore",
            "solves the finite ACT-NOW versus PROBE-THEN-ACT problem without search approximation.",
            "",
            "## Contradiction and retraction",
            "",
            f"- retraction restores previous claim: **{contradiction['retraction_restores_previous_claim']}**",
            f"- provenance claims: **{contradiction['claims']:,}**",
            f"- resolved active keys: **{contradiction['resolved_keys']:,}**",
            f"- provenance ledger: **{contradiction['provenance_ledger_bits']:,} bits**",
            f"- finalized active snapshot: **{contradiction['finalized_snapshot_bits']:,} bits**",
            f"- finalized compaction ratio: **{contradiction['finalized_compaction_ratio']:.2f}x**",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    root = Path(__file__).resolve().parents[2]
    results = root / "results"
    results.mkdir(exist_ok=True)
    (results / "phase8f.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results / "phase8f.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
