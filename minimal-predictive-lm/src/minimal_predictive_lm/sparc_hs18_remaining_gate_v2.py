from __future__ import annotations

import json
from pathlib import Path

from . import sparc_hs17_reference_gate as source
from . import sparc_hs18_remaining_gate as gate
from .benchmark_harness import BenchmarkExample, build_manifest


HIGHEST_INDIVIDUAL_TARGET_INSPECTED = 141


def build_individually_uninspected_tail() -> tuple[object, int]:
    payload = source.download_verified_git_blob(
        f"{source.BBH_BASE_URL}/causal_judgement.json", gate.CAUSAL_BLOB_SHA1
    )
    rows = json.loads(payload.decode("utf-8")).get("examples")
    if not isinstance(rows, list) or len(rows) < gate.FINAL_COUNT:
        raise ValueError("causal source is unexpectedly small")
    start = len(rows) - gate.FINAL_COUNT
    if start <= HIGHEST_INDIVIDUAL_TARGET_INSPECTED:
        raise ValueError("causal tail overlaps individually inspected targets")
    examples = tuple(
        BenchmarkExample(
            f"bbh_causal_tail_{index:03d}",
            "causal_judgement_final_holdout",
            str(item["input"]),
            str(item["target"]),
            "exact",
        )
        for index, item in enumerate(rows[start:], start=start)
    )
    return (
        build_manifest(
            name="sparc-hs18-causal-individually-uninspected-tail",
            split=f"verified-tail-{start}-{len(rows)-1}",
            source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
            license_id="MIT",
            public=True,
            examples=examples,
        ),
        start,
    )


def run_gate() -> dict[str, object]:
    gate.build_final_causal_holdout = build_individually_uninspected_tail
    result = gate.run_gate()
    protocol = result["protocol"]
    protocol["development_public_causal_target_labels_inspected_at_least"] = 52
    protocol["highest_individual_target_index_inspected"] = HIGHEST_INDIVIDUAL_TARGET_INSPECTED
    protocol["final_individual_target_labels_inspected_before_freeze"] = 0
    protocol["aggregate_score_leakage_from_prior_120_159_run"] = True
    protocol["strict_unseen_holdout_claim_allowed"] = False
    result["claim_boundary"] = (
        "Tail labels are individually uninspected and begin after the highest inspected "
        "failure label. However, an earlier aggregate score included part of the tail, so "
        "this is not called a strict unseen holdout. A prospective external holdout is still "
        "required before a general causal claim. High-school and phone claims remain false."
    )
    return result


def main() -> None:
    result = run_gate()
    output = Path("results")
    output.mkdir(exist_ok=True)
    (output / "sparc_hs18_remaining_gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "sparc_hs18_remaining_gate.md").write_text(
        gate.render_markdown(result), encoding="utf-8"
    )
    print(gate.render_markdown(result), end="")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
