from __future__ import annotations

import json
from pathlib import Path


TASKS = 64
AFFINE_TASKS = 56
EXCEPTION_TASKS = TASKS - AFFINE_TASKS
ENTRY_BITS = 16
SCHEMA_BITS = 24
PARAM_BITS_PER_AFFINE_TASK = 10
SHARED_SCHEMA_DISCOVERY_COST = 1_400
DUPLICATED_PROGRAM_DISCOVERY_COST = 512
MIGRATION_READ_BITS = TASKS * 2 * ENTRY_BITS
MIGRATION_WRITE_BITS = AFFINE_TASKS * PARAM_BITS_PER_AFFINE_TASK + EXCEPTION_TASKS * 4 * ENTRY_BITS
HORIZONS = (2, 4, 8, 16, 32, 64)


def exact_cache_cost(queries_per_task: int) -> int:
    return TASKS * queries_per_task * ENTRY_BITS


def duplicated_program_cost(queries_per_task: int) -> int:
    return (
        DUPLICATED_PROGRAM_DISCOVERY_COST
        + AFFINE_TASKS * (SCHEMA_BITS + PARAM_BITS_PER_AFFINE_TASK)
        + EXCEPTION_TASKS * queries_per_task * ENTRY_BITS
    )


def shared_hybrid_cost(queries_per_task: int) -> int:
    return (
        SHARED_SCHEMA_DISCOVERY_COST
        + SCHEMA_BITS
        + AFFINE_TASKS * PARAM_BITS_PER_AFFINE_TASK
        + EXCEPTION_TASKS * queries_per_task * ENTRY_BITS
    )


def local_commit_cost(actual_queries_per_task: int) -> int:
    """A myopic policy commits to exact caches after seeing only two examples."""

    assert exact_cache_cost(2) < shared_hybrid_cost(2)
    return exact_cache_cost(actual_queries_per_task)


def rolling_reoptimization_cost(actual_queries_per_task: int) -> int:
    """Start myopically, then migrate once repetition makes sharing visible."""

    return (
        shared_hybrid_cost(actual_queries_per_task)
        + MIGRATION_READ_BITS
        + MIGRATION_WRITE_BITS
    )


def heldout_generalization_cost(heldout_affine_tasks: int, queries_per_task: int) -> dict[str, int]:
    return {
        "exact_cache": heldout_affine_tasks * queries_per_task * ENTRY_BITS,
        "shared_schema": heldout_affine_tasks * PARAM_BITS_PER_AFFINE_TASK,
    }


def run() -> dict[str, object]:
    frontier = []
    for horizon in HORIZONS:
        candidates = {
            "exact_cache": exact_cache_cost(horizon),
            "duplicated_program": duplicated_program_cost(horizon),
            "shared_hybrid": shared_hybrid_cost(horizon),
        }
        winner = min(candidates, key=candidates.get)
        frontier.append(
            {
                "queries_per_task": horizon,
                "costs": candidates,
                "winner": winner,
            }
        )

    actual_horizon = 16
    policies = {
        "local_commit": local_commit_cost(actual_horizon),
        "rolling_reoptimization": rolling_reoptimization_cost(actual_horizon),
        "global_lifetime_selection": shared_hybrid_cost(actual_horizon),
    }

    heldout = heldout_generalization_cost(32, actual_horizon)

    return {
        "workload": {
            "tasks": TASKS,
            "affine_tasks": AFFINE_TASKS,
            "exception_tasks": EXCEPTION_TASKS,
            "entry_bits": ENTRY_BITS,
            "schema_bits": SCHEMA_BITS,
            "parameter_bits_per_affine_task": PARAM_BITS_PER_AFFINE_TASK,
        },
        "horizon_frontier": frontier,
        "actual_horizon": actual_horizon,
        "policy_lifetime_costs": policies,
        "global_vs_local_ratio": policies["local_commit"] / policies["global_lifetime_selection"],
        "heldout_affine_tasks": 32,
        "heldout_costs": heldout,
        "heldout_ratio": heldout["exact_cache"] / heldout["shared_schema"],
        "principle": (
            "Choose representation and policy over the task distribution and deployment lifetime; "
            "permit local compilation only when it lowers the global constrained objective."
        ),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Phase 6c results: local optimum versus lifetime global optimum",
        "",
        "The experiment compares four ideas that are often conflated:",
        "",
        "- memorize exact cases",
        "- duplicate a small program per task",
        "- synthesize one shared rule plus exact exceptions",
        "- begin locally and migrate later",
        "",
        "All reported costs include stored representation and the declared discovery or migration costs.",
        "",
        "## Horizon-dependent winner",
        "",
        "| queries per task | exact cache | duplicated program | shared hybrid | winner |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in payload["horizon_frontier"]:
        costs = row["costs"]
        lines.append(
            f"| {row['queries_per_task']} | {costs['exact_cache']:,} | "
            f"{costs['duplicated_program']:,} | {costs['shared_hybrid']:,} | "
            f"{row['winner']} |"
        )

    policies = payload["policy_lifetime_costs"]
    heldout = payload["heldout_costs"]
    lines.extend(
        [
            "",
            "## Sixteen-query deployment",
            "",
            f"- myopic commit to exact caches: **{policies['local_commit']:,} cost units**",
            f"- re-optimize after committing: **{policies['rolling_reoptimization']:,}**",
            f"- select over the whole deployment distribution: **{policies['global_lifetime_selection']:,}**",
            f"- local/global ratio: **{payload['global_vs_local_ratio']:.3f}x**",
            "",
            "The rolling policy recovers the better representation but pays to read and rewrite the old cache.",
            "Reversible early choices reduce this tax; irreversible local compilation increases it.",
            "",
            "## Held-out tasks",
            "",
            f"For 32 unseen affine tasks with 16 queries each, exact caching costs **{heldout['exact_cache']:,} bits**,",
            f"while reusing the shared schema requires **{heldout['shared_schema']:,} bits** of new task parameters.",
            f"The ratio is **{payload['heldout_ratio']:.1f}x**.",
            "",
            "## Interpretation",
            "",
            "The globally selected machine is not a single universal representation chosen forever.",
            "At two queries per task, exact caching is cheapest because rule discovery has not paid back.",
            "At four or more queries, the shared rule plus exceptions wins. Therefore the optimizer must",
            "select over workload, horizon, uncertainty, migration cost, and held-out transfer—not merely",
            "minimize the cost of the current episode.",
            "",
            "A local optimization is admissible only when it is either reversible or certified not to",
            "increase the best known lower-bounded lifetime objective.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase6c.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "phase6c.md").write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
