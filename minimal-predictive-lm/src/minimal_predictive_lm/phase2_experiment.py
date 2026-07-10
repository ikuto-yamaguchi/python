from __future__ import annotations

import json
from pathlib import Path

from .registers import RegisterLanguage, register_cost


def run() -> list[dict[str, int | float]]:
    rows: list[dict[str, int | float]] = []
    for key_count in (1, 2, 4, 8, 16, 32):
        cost = register_cost(RegisterLanguage(key_count))
        rows.append(
            {
                "key_count": cost.key_count,
                "memory_lower_bound_bits": cost.predictive_memory_lower_bound_bits,
                "factored_data_memory_bits": cost.factored_data_memory_bits,
                "factored_total_runtime_bits": cost.factored_total_runtime_bits,
                "flat_ready_states": cost.flat_ready_states,
                "flat_enumerated_states": cost.flat_enumerated_states,
                "flat_sparse_edges": cost.flat_sparse_edges,
                "flat_sparse_table_bytes": cost.flat_sparse_table_bytes,
                "factored_parameter_bytes": cost.factored_parameter_bytes,
                "data_reads_bits_per_token": cost.expected_data_bit_reads_per_token,
                "data_writes_bits_per_token": cost.expected_data_bit_writes_per_token,
                "dense_fp32_state_write_bits_per_token": cost.dense_fp32_state_write_bits_per_token,
                "write_traffic_reduction": cost.write_traffic_reduction,
            }
        )
    return rows


def render_markdown(rows: list[dict[str, int | float]]) -> str:
    lines = [
        "# Phase 2 results: factor the transition law, not only the state",
        "",
        "A K-bit key-value memory has 2^K predictively distinguishable assignments.",
        "Any exact predictor therefore needs at least K runtime bits. A flat causal-state",
        "implementation meets that runtime-state bound with a state ID, but its transition",
        "program still grows exponentially. The factored register machine stores K bits",
        "and uses indexed read/write rules whose description length is constant in 2^K.",
        "",
        "| K | lower bound bits | factored data bits | total runtime bits | flat ready states | flat sparse table bytes | factored parameter bytes | dense/factored write traffic |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {key_count} | {memory_lower_bound_bits} | {factored_data_memory_bits} | "
            "{factored_total_runtime_bits} | {flat_ready_states} | {flat_sparse_table_bytes} | "
            "{factored_parameter_bytes} | {write_traffic_reduction:.0f}x |".format(**row)
        )
    lines.extend(
        [
            "",
            "With write/query/filler probabilities 0.4/0.4/0.2, the factored machine",
            "touches only 0.153846 data bits per token for writes and the same for reads.",
            "A dense FP32 K-dimensional recurrent state writes 32K bits every token.",
            "",
            "## Lower-bound argument",
            "",
            "For any two different memory assignments m and m', there is a key j where",
            "their bits differ. The observed suffix `QUERY KEY_j` makes the next token",
            "deterministically BIT_0 under one history and BIT_1 under the other. Therefore",
            "the histories are in different predictive equivalence classes. There are 2^K",
            "classes, so at least log2(2^K)=K state bits are required. The register machine",
            "uses exactly K data bits and reaches this lower bound.",
            "",
            "## Consequence",
            "",
            "Minimizing causal-state count or Hankel rank alone is insufficient. The objective",
            "must also penalize the description length of the transition law and dynamic memory",
            "traffic. Compositional addressable memory can be exponentially smaller than a flat",
            "table even when both have the same information-theoretic runtime-state requirement.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    rows = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase2.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (output / "phase2.md").write_text(render_markdown(rows), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
