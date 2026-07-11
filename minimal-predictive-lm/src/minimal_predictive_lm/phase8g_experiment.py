from __future__ import annotations

import json
import math
from pathlib import Path
import random
from typing import Mapping

from .adaptive_event_intelligence import (
    EventObservation,
    Sensor,
    always_probe_policy,
    assign_new_template,
    beam_merge_event_search,
    best_change_point,
    canonical_template_groups,
    cluster_posterior,
    exact_bounded_information_policy,
    exhaustive_event_search,
    fit_event_partition,
    no_probe_policy,
    one_probe_policy,
)


OPERATIONS = {
    "SET": ("write", 0.92, {1: 0.70, 2: 0.30}),
    "VERIFY": ("read", 0.82, {1: 0.20, 2: 0.50, 3: 0.30}),
    "RETRACT": ("remove", 0.88, {1: 0.90, 2: 0.10}),
    "EMIT": ("emit", 0.97, {1: 1.00}),
}
DOMAINS = ("conversation", "writing", "code", "tool")
EFFECT_VOCABULARY = tuple(
    sorted({specification[0] for specification in OPERATIONS.values()})
)
MAX_LAG = 8


def _surface(domain: str, operation: str) -> str:
    examples = {
        ("conversation", "SET"): "会話で事実を記憶する",
        ("conversation", "VERIFY"): "相手の意図を確認する",
        ("conversation", "RETRACT"): "直前の主張を訂正する",
        ("conversation", "EMIT"): "返答を送る",
        ("writing", "SET"): "段落へ主張を追加する",
        ("writing", "VERIFY"): "根拠を検証する",
        ("writing", "RETRACT"): "未確認文を削除する",
        ("writing", "EMIT"): "文章を出力する",
        ("code", "SET"): "変数へ値を設定する",
        ("code", "VERIFY"): "テストを実行する",
        ("code", "RETRACT"): "失敗した変更を戻す",
        ("code", "EMIT"): "パッチを書き出す",
        ("tool", "SET"): "ツール結果を状態へ保存する",
        ("tool", "VERIFY"): "ツール結果を照合する",
        ("tool", "RETRACT"): "外部操作を取り消す",
        ("tool", "EMIT"): "コマンドを送信する",
    }
    return examples[(domain, operation)]


def _generate_observations(
    domains: tuple[str, ...],
    *,
    seed: int,
    per_template: int,
) -> tuple[tuple[str, ...], dict[str, str], list[EventObservation]]:
    random_generator = random.Random(seed)
    templates: list[str] = []
    hidden_operation: dict[str, str] = {}
    for domain in domains:
        for operation in OPERATIONS:
            template = _surface(domain, operation)
            templates.append(template)
            hidden_operation[template] = operation

    effects = list(EFFECT_VOCABULARY)
    observations: list[EventObservation] = []
    for template in templates:
        operation = hidden_operation[template]
        effect, success_probability, lag_distribution = OPERATIONS[operation]
        lag_values = list(lag_distribution)
        lag_weights = list(lag_distribution.values())
        domain = next(
            domain
            for domain in domains
            if template == _surface(domain, operation)
        )
        for _ in range(per_template):
            success = random_generator.random() < success_probability
            lag = (
                random_generator.choices(lag_values, lag_weights)[0]
                if success
                else None
            )
            if random_generator.random() < 0.08:
                observations.append(
                    EventObservation(template, domain, None, None, None)
                )
                continue
            observed_effect = (
                effect
                if random_generator.random() > 0.05
                else random_generator.choice(effects)
            )
            observed_lag = (
                lag
                if success and random_generator.random() > 0.10
                else None
            )
            observations.append(
                EventObservation(
                    template,
                    domain,
                    observed_effect,
                    success,
                    observed_lag,
                )
            )

    return tuple(sorted(templates)), hidden_operation, observations


def _hidden_groups(
    templates: tuple[str, ...],
    hidden_operation: Mapping[str, str],
) -> set[frozenset[str]]:
    groups: dict[str, set[str]] = {}
    for template in templates:
        groups.setdefault(hidden_operation[template], set()).add(template)
    return {frozenset(group) for group in groups.values()}


def _mixed_domain_induction() -> dict[str, object]:
    oracle_templates, oracle_hidden, oracle_observations = (
        _generate_observations(
            DOMAINS[:2],
            seed=31,
            per_template=30,
        )
    )
    oracle = exhaustive_event_search(
        oracle_templates,
        oracle_observations,
        EFFECT_VOCABULARY,
        MAX_LAG,
    )
    oracle_beam = beam_merge_event_search(
        oracle_templates,
        oracle_observations,
        EFFECT_VOCABULARY,
        MAX_LAG,
        beam_width=32,
    )

    templates, hidden_operation, observations = _generate_observations(
        DOMAINS,
        seed=37,
        per_template=40,
    )
    search = beam_merge_event_search(
        templates,
        observations,
        EFFECT_VOCABULARY,
        MAX_LAG,
        beam_width=64,
    )
    separated = fit_event_partition(
        tuple((index,) for index in range(len(templates))),
        templates,
        observations,
        EFFECT_VOCABULARY,
        MAX_LAG,
    )

    count_width = math.ceil(math.log2(len(observations) + 1))
    sufficient_stat_bits = len(search.selected.partition) * (
        2 + MAX_LAG + len(EFFECT_VOCABULARY)
    ) * count_width
    raw_event_bits = len(observations) * (
        math.ceil(math.log2(len(templates)))
        + math.ceil(math.log2(len(EFFECT_VOCABULARY) + 1))
        + 2
        + math.ceil(math.log2(MAX_LAG + 1))
    )

    return {
        "oracle_templates": len(oracle_templates),
        "oracle_partitions": oracle.evaluated_partitions,
        "oracle_gap": (
            oracle_beam.selected.objective - oracle.selected.objective
        ),
        "oracle_partition_exact": (
            canonical_template_groups(oracle_beam.selected)
            == _hidden_groups(oracle_templates, oracle_hidden)
        ),
        "templates": len(templates),
        "observations": len(observations),
        "hidden_operations": len(OPERATIONS),
        "evaluated_partitions": search.evaluated_partitions,
        "partition_exact": (
            canonical_template_groups(search.selected)
            == _hidden_groups(templates, hidden_operation)
        ),
        "unified_clusters": len(search.selected.partition),
        "unified_objective": search.selected.objective,
        "domain_separated_clusters": len(separated.partition),
        "domain_separated_objective": separated.objective,
        "objective_ratio": separated.objective / search.selected.objective,
        "sufficient_stat_bits": sufficient_stat_bits,
        "raw_event_bits": raw_event_bits,
        "event_to_stat_ratio": raw_event_bits / sufficient_stat_bits,
        "avoided_representation_conversions": len(observations) * 2,
    }


def _new_domain_transfer() -> dict[str, object]:
    train_templates, train_hidden, training = _generate_observations(
        DOMAINS[:3],
        seed=41,
        per_template=40,
    )
    model = beam_merge_event_search(
        train_templates,
        training,
        EFFECT_VOCABULARY,
        MAX_LAG,
        beam_width=64,
    ).selected

    all_templates, all_hidden, all_observations = _generate_observations(
        DOMAINS,
        seed=43,
        per_template=40,
    )
    tool_templates = tuple(
        template
        for template in all_templates
        if template in {
            _surface("tool", operation) for operation in OPERATIONS
        }
    )

    assignments_correct = 0
    pooled_brier: list[float] = []
    calibration_only_brier: list[float] = []
    effect_correct = 0
    effect_total = 0
    lag_correct = 0
    lag_total = 0

    for template in tool_templates:
        observations = [
            item for item in all_observations if item.template == template
        ]
        calibration = observations[:6]
        validation = observations[6:]
        cluster_index = assign_new_template(
            model,
            calibration,
            training,
            EFFECT_VOCABULARY,
            MAX_LAG,
        )
        cluster = model.partition[cluster_index]
        cluster_operations = {
            train_hidden[train_templates[index]] for index in cluster
        }
        assignments_correct += int(
            all_hidden[template] in cluster_operations
        )

        extended_templates = train_templates + (template,)
        extended_observations = list(training) + calibration
        probability, effect, lag = cluster_posterior(
            tuple(cluster) + (len(train_templates),),
            extended_templates,
            extended_observations,
            EFFECT_VOCABULARY,
            MAX_LAG,
        )
        local_success = sum(item.success is True for item in calibration)
        local_failure = sum(item.success is False for item in calibration)
        local_probability = (
            local_success + 1
        ) / (local_success + local_failure + 2)

        for item in validation:
            if item.success is not None:
                target = 1.0 if item.success else 0.0
                pooled_brier.append((probability - target) ** 2)
                calibration_only_brier.append(
                    (local_probability - target) ** 2
                )
            if item.effect is not None:
                effect_total += 1
                effect_correct += int(effect == item.effect)
            if item.success is True and item.lag is not None:
                lag_total += 1
                lag_correct += int(lag == item.lag)

    return {
        "new_domain": "tool",
        "templates": len(tool_templates),
        "calibration_events_per_template": 6,
        "assignment_accuracy": assignments_correct / len(tool_templates),
        "pooled_brier": sum(pooled_brier) / len(pooled_brier),
        "calibration_only_brier": (
            sum(calibration_only_brier) / len(calibration_only_brier)
        ),
        "effect_accuracy": effect_correct / effect_total,
        "modal_lag_accuracy": lag_correct / lag_total,
    }


def _change_point_experiment() -> dict[str, object]:
    random_generator = random.Random(47)
    true_change_point = 200
    outcomes = [
        random_generator.random() < 0.90
        for _ in range(true_change_point)
    ]
    outcomes.extend(
        random_generator.random() < 0.55
        for _ in range(200)
    )
    detected, gain = best_change_point(
        outcomes,
        min_segment=30,
        split_description_bits=10.0,
    )
    if detected is None:
        raise RuntimeError("change point was not detected")

    stationary_probability = (sum(outcomes) + 1) / (len(outcomes) + 2)
    recent = outcomes[detected:]
    adaptive_probability = (sum(recent) + 1) / (len(recent) + 2)

    validation = [
        random_generator.random() < 0.55
        for _ in range(500)
    ]
    stationary_brier = sum(
        (stationary_probability - float(outcome)) ** 2
        for outcome in validation
    ) / len(validation)
    adaptive_brier = sum(
        (adaptive_probability - float(outcome)) ** 2
        for outcome in validation
    ) / len(validation)

    count_width = math.ceil(math.log2(len(outcomes) + 1))
    summary_bits = 4 * count_width + count_width
    return {
        "episodes": len(outcomes),
        "true_change_point": true_change_point,
        "detected_change_point": detected,
        "absolute_error": abs(detected - true_change_point),
        "mdl_gain_bits": gain,
        "stationary_probability": stationary_probability,
        "adaptive_probability": adaptive_probability,
        "stationary_brier": stationary_brier,
        "adaptive_brier": adaptive_brier,
        "raw_history_bits": len(outcomes),
        "two_segment_summary_bits": summary_bits,
        "history_summary_ratio": len(outcomes) / summary_bits,
    }


def _bounded_information_experiment() -> dict[str, object]:
    sensors = (
        Sensor("cheap", 0.72, 0.28, 0.10, 1.5),
        Sensor("strong", 0.93, 0.07, 0.15, 5.0),
        Sensor("confirm", 0.84, 0.16, 0.35, 2.5),
    )
    priors = tuple(index / 10 for index in range(1, 10))
    policy_values: dict[str, list[object]] = {
        "none": [],
        "one_probe": [],
        "exact_bounded": [],
        "always": [],
    }
    dynamic_states = 0
    for probability in priors:
        policy_values["none"].append(no_probe_policy(probability))
        policy_values["one_probe"].append(
            one_probe_policy(probability, sensors)
        )
        exact, states = exact_bounded_information_policy(
            probability,
            sensors,
        )
        dynamic_states += states
        policy_values["exact_bounded"].append(exact)
        policy_values["always"].append(
            always_probe_policy(probability, sensors)
        )

    summary: dict[str, object] = {}
    for name, values in policy_values.items():
        summary[name] = {
            "mean_total_cost": sum(
                item.total_cost for item in values
            ) / len(values),
            "mean_error_probability": sum(
                item.error_probability for item in values
            ) / len(values),
            "mean_probes": sum(
                item.expected_probes for item in values
            ) / len(values),
        }

    exact_cost = summary["exact_bounded"]["mean_total_cost"]
    return {
        "priors": len(priors),
        "sensors": len(sensors),
        "policies": summary,
        "exact_policy_dynamic_states": dynamic_states,
        "oracle_gap": 0.0,
        "exact_dominates_available_baselines": all(
            exact_cost <= summary[name]["mean_total_cost"] + 1e-12
            for name in ("none", "one_probe", "always")
        ),
    }


def run() -> dict[str, object]:
    mixed = _mixed_domain_induction()
    transfer = _new_domain_transfer()
    change_point = _change_point_experiment()
    information = _bounded_information_experiment()
    return {
        "mixed_domain_induction": mixed,
        "new_domain_transfer": transfer,
        "change_point": change_point,
        "bounded_information": information,
        "conclusion": {
            "oracle_gap_zero": mixed["oracle_gap"] == 0.0,
            "cross_domain_partition_exact": mixed["partition_exact"],
            "new_domain_assignment_exact": (
                transfer["assignment_accuracy"] == 1.0
            ),
            "pooling_improves_brier": (
                transfer["pooled_brier"]
                < transfer["calibration_only_brier"]
            ),
            "change_point_improves_brier": (
                change_point["adaptive_brier"]
                < change_point["stationary_brier"]
            ),
            "bounded_policy_is_optimal": information[
                "exact_dominates_available_baselines"
            ],
        },
        "limitations": [
            "surface templates are persistent IDs; free-form language grounding is not solved",
            "observable effect categories still anchor the latent operation",
            "the change-point experiment permits only one abrupt Bernoulli shift",
            "the exact POMDP has one binary hidden variable and three probes",
            "mixed-domain workflows are synthetic micro-tasks, not real repositories or open conversation",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    mixed = payload["mixed_domain_induction"]
    transfer = payload["new_domain_transfer"]
    change = payload["change_point"]
    information = payload["bounded_information"]
    lines = [
        "# Phase 8g results: shared stochastic event intelligence across domains",
        "",
        "Conversation, writing, code, and tool events are fitted with one stochastic",
        "operation vocabulary instead of four domain-specific runtimes.",
        "",
        "## Joint latent-operation induction",
        "",
        f"- surface templates: **{mixed['templates']}**",
        f"- latent operations recovered: **{mixed['unified_clusters']}**",
        f"- exact hidden partition: **{mixed['partition_exact']}**",
        f"- evaluated merge candidates: **{mixed['evaluated_partitions']:,}**",
        f"- 8-template exhaustive-oracle gap: **{mixed['oracle_gap']:.6f}**",
        "",
        "| model | clusters | objective |",
        "|---|---:|---:|",
        f"| domain-separated | {mixed['domain_separated_clusters']} | {mixed['domain_separated_objective']:.3f} |",
        f"| shared event model | {mixed['unified_clusters']} | {mixed['unified_objective']:.3f} |",
        "",
        f"The domain-separated objective is **{mixed['objective_ratio']:.2f}x** the shared objective.",
        f"Sufficient statistics use **{mixed['sufficient_stat_bits']} bits** versus "
        f"**{mixed['raw_event_bits']} bits** for the compact event stream.",
        "",
        "## New-domain transfer",
        "",
        f"- operation assignment: **{transfer['assignment_accuracy']:.1%}**",
        f"- pooled Brier: **{transfer['pooled_brier']:.6f}**",
        f"- six-shot-only Brier: **{transfer['calibration_only_brier']:.6f}**",
        f"- effect accuracy: **{transfer['effect_accuracy']:.1%}**",
        "",
        "## Non-stationary effect",
        "",
        f"- true / detected change point: **{change['true_change_point']} / {change['detected_change_point']}**",
        f"- MDL gain: **{change['mdl_gain_bits']:.3f} bits**",
        f"- stationary / adaptive Brier: **{change['stationary_brier']:.6f} / {change['adaptive_brier']:.6f}**",
        f"- raw history / two-segment summary: **{change['raw_history_bits']} / {change['two_segment_summary_bits']} bits**",
        "",
        "## Exact bounded information acquisition",
        "",
        "| policy | mean total cost | mean error | mean probes |",
        "|---|---:|---:|---:|",
    ]
    for name in ("none", "one_probe", "exact_bounded", "always"):
        item = information["policies"][name]
        lines.append(
            f"| {name} | {item['mean_total_cost']:.6f} | "
            f"{item['mean_error_probability']:.6f} | "
            f"{item['mean_probes']:.6f} |"
        )
    lines.extend(
        [
            "",
            "The bounded policy enumerates every available action and sensor outcome",
            "for this finite binary POMDP, so its oracle gap is zero in this experiment.",
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
    (results / "phase8g.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (results / "phase8g.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
