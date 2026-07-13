from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .phase19a_general_learning_reality_gate import (
    CorpusFile,
    collect_corpus,
    encode,
    evaluate_model,
    learn_merges,
    nested_training_slice,
    train_ngram,
)

DOMAINS = ("code", "prose", "structured")
FRACTIONS = (0.25, 0.5, 1.0)


def _bytes(rows: Sequence[CorpusFile]) -> int:
    return sum(len(row.data) for row in rows)


def evaluate_transfer(
    train: Sequence[CorpusFile],
    heldout: Sequence[CorpusFile],
    target_domain: str,
) -> Mapping[str, object]:
    if target_domain not in DOMAINS:
        raise ValueError("unknown domain")
    source = tuple(row for row in train if row.domain != target_domain)
    target = tuple(row for row in heldout if row.domain == target_domain)
    if not source or not target:
        raise ValueError("empty source or target")

    scaling: list[Mapping[str, object]] = []
    for fraction in FRACTIONS:
        subset = nested_training_slice(source, fraction)
        merges = learn_merges(subset)
        model = train_ngram(
            [encode(row.data, merges) for row in subset],
            order=3,
            vocabulary_size=256 + len(merges),
        )
        scaling.append(
            {
                "fraction": fraction,
                "training_files": len(subset),
                "training_bytes": _bytes(subset),
                "merges": len(merges),
                **evaluate_model(model, target, merges),
            }
        )

    raw_model = train_ngram(
        [tuple(row.data) for row in source],
        order=3,
        vocabulary_size=256,
    )
    raw_metrics = evaluate_model(raw_model, target, ())
    bpb = [float(row["dictionary_amortized_bits_per_byte"]) for row in scaling]
    full_bpb = bpb[-1]
    raw_bpb = float(raw_metrics["dictionary_amortized_bits_per_byte"])

    return {
        "target_domain": target_domain,
        "source_domains": sorted({row.domain for row in source}),
        "source_files": len(source),
        "target_files": len(target),
        "source_bytes": _bytes(source),
        "target_bytes": _bytes(target),
        "target_paths": [row.path for row in target],
        "source_paths": [row.path for row in source],
        "scaling": scaling,
        "raw_byte_trigram": raw_metrics,
        "full_improvement_bits_per_byte": raw_bpb - full_bpb,
        "checks": {
            "target_domain_excluded_from_source": all(
                row.domain != target_domain for row in source
            ),
            "file_disjoint": not (
                {row.path for row in source} & {row.path for row in target}
            ),
            "enough_target_bytes": _bytes(target) >= 4_096,
            "scaling_improves": full_bpb <= bpb[0] + 0.02,
            "dictionary_beats_raw": full_bpb < raw_bpb,
        },
    }


def run_gate(root: Path) -> Mapping[str, object]:
    train, heldout = collect_corpus(root)
    transfers = [evaluate_transfer(train, heldout, domain) for domain in DOMAINS]
    total_bytes = sum(int(row["target_bytes"]) for row in transfers)
    weighted_full = sum(
        float(row["scaling"][-1]["dictionary_amortized_bits_per_byte"])
        * int(row["target_bytes"])
        for row in transfers
    ) / total_bytes
    weighted_raw = sum(
        float(row["raw_byte_trigram"]["dictionary_amortized_bits_per_byte"])
        * int(row["target_bytes"])
        for row in transfers
    ) / total_bytes
    domain_wins = sum(
        bool(row["checks"]["dictionary_beats_raw"]) for row in transfers
    )
    scaling_wins = sum(bool(row["checks"]["scaling_improves"]) for row in transfers)
    checks = {
        "all_target_domains_fully_excluded": all(
            row["checks"]["target_domain_excluded_from_source"] for row in transfers
        ),
        "all_files_disjoint": all(
            row["checks"]["file_disjoint"] for row in transfers
        ),
        "all_targets_large_enough": all(
            row["checks"]["enough_target_bytes"] for row in transfers
        ),
        "at_least_two_domains_scale": scaling_wins >= 2,
        "at_least_two_domains_beat_raw": domain_wins >= 2,
        "weighted_transfer_beats_raw": weighted_full < weighted_raw,
        "no_task_labels": all(
            set(vars(row)) == {"path", "domain", "data", "rank"} for row in train
        ),
    }
    return {
        "campaign": "phase19b_domain_holdout_transfer_gate",
        "claim": "leave-one-domain-out self-supervised byte prediction only",
        "train_files": len(train),
        "heldout_files": len(heldout),
        "transfers": transfers,
        "weighted_full_bits_per_byte": weighted_full,
        "weighted_raw_bits_per_byte": weighted_raw,
        "domain_wins": domain_wins,
        "scaling_wins": scaling_wins,
        "checks": checks,
        "passed": all(checks.values()),
        "semantic_understanding": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    lines = [
        "# Phase 19b: leave-one-domain-out transfer gate",
        "",
        f"Passed: **{result['passed']}**",
        "",
        "| held-out domain | target bytes | 25% bpb | 50% bpb | 100% bpb | raw trigram | delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for transfer in result["transfers"]:
        scaling = transfer["scaling"]
        lines.append(
            f"| {transfer['target_domain']} | {transfer['target_bytes']} | "
            f"{scaling[0]['dictionary_amortized_bits_per_byte']:.4f} | "
            f"{scaling[1]['dictionary_amortized_bits_per_byte']:.4f} | "
            f"{scaling[2]['dictionary_amortized_bits_per_byte']:.4f} | "
            f"{transfer['raw_byte_trigram']['dictionary_amortized_bits_per_byte']:.4f} | "
            f"{transfer['full_improvement_bits_per_byte']:+.4f} |"
        )
    lines.extend(
        [
            "",
            f"Weighted learned: **{result['weighted_full_bits_per_byte']:.4f} bpb**",
            f"Weighted raw baseline: **{result['weighted_raw_bits_per_byte']:.4f} bpb**",
            "",
            "## Checks",
            "",
        ]
    )
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- The target domain is excluded from all representation and n-gram training.",
            "- Passing shows small cross-domain compression transfer, not semantic understanding.",
            "- No dialogue, question answering, reasoning, or high-school intelligence is demonstrated.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_gate(root)
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "phase19b.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "phase19b.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
