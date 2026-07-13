from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .cap_sem_002_raw_japanese_bridge import run_gate as run_bridge_gate
from .cap_sem_002_raw_japanese_grounding import (
    fit_raw_semantic_model,
    run_gate as run_grounding_gate,
)

CAPABILITY_ID = "CAP-SEM-002"
CANONICAL_IMPLEMENTATION = "cap_sem_002_raw_japanese_bridge"
EXPERIMENTAL_IMPLEMENTATION = "cap_sem_002_raw_japanese_grounding"


def experimental_refits_semantic_runtime() -> bool:
    """Detect the disqualifying semantic refit in the experimental candidate.

    CAP-SEM-002 is defined as a surface learner connected to the already learned
    CAP-SEM-001 runtime. Calling learn_meaning from the CAP-SEM-002 fitting path
    violates that dependency even when held-out accuracy is perfect.
    """

    return "learn_meaning" in fit_raw_semantic_model.__code__.co_names


def run_gate() -> dict[str, object]:
    canonical = run_bridge_gate()
    experimental = run_grounding_gate()
    refits_semantics = experimental_refits_semantic_runtime()

    checks = {
        "canonical_gate_passes": canonical["passed"] is True,
        "canonical_semantic_runtime_is_frozen": canonical["checks"][
            "semantic_runtime_is_frozen"
        ]
        is True,
        "canonical_reaches_perfect_heldout_accuracy": (
            canonical["heldout_accuracy"] == 1.0
            and canonical["heldout_coverage"] == 1.0
        ),
        "experimental_candidate_is_measured": experimental["passed"] is True,
        "experimental_semantic_refit_is_detected": refits_semantics,
        "experimental_is_not_promoted_despite_score": refits_semantics,
        "canonical_does_not_overclaim": (
            canonical["unrestricted_japanese_understanding"] is False
            and canonical["high_school_intelligence"] is False
            and canonical["general_llm_parity"] is False
        ),
    }

    return {
        "capability_id": CAPABILITY_ID,
        "decision": "canonical_selected",
        "canonical_implementation": CANONICAL_IMPLEMENTATION,
        "experimental_implementation": EXPERIMENTAL_IMPLEMENTATION,
        "selection_reason": (
            "The canonical bridge alone preserves the byte-identical frozen "
            "CAP-SEM-001 semantic runtime. The experimental candidate obtains "
            "strong surface results but calls learn_meaning during CAP-SEM-002 "
            "fitting, so it is retained only as a parser-search ablation."
        ),
        "canonical": {
            "passed": canonical["passed"],
            "heldout_accuracy": canonical["heldout_accuracy"],
            "heldout_coverage": canonical["heldout_coverage"],
            "learned_bridge_payload_bytes": canonical[
                "learned_bridge_payload_bytes"
            ],
            "average_semantic_inference_operations": canonical[
                "average_semantic_inference_operations"
            ],
            "semantic_runtime_is_frozen": canonical["checks"][
                "semantic_runtime_is_frozen"
            ],
        },
        "experimental": {
            "passed_as_standalone_gate": experimental["passed"],
            "heldout_accuracy": experimental["heldout_accuracy"],
            "heldout_coverage": experimental["heldout_coverage"],
            "training_operations": experimental["training_operations"],
            "average_inference_operations": experimental[
                "average_inference_operations"
            ],
            "refits_semantic_runtime": refits_semantics,
            "promotion_status": "rejected_as_canonical",
        },
        "checks": checks,
        "passed": all(checks.values()),
        "next_capability": "CAP-SEM-003 open relation-expression grounding",
        "unrestricted_japanese_understanding": False,
        "high_school_intelligence": False,
        "general_llm_parity": False,
    }


def render_markdown(result: Mapping[str, object]) -> str:
    canonical = result["canonical"]
    experimental = result["experimental"]
    lines = [
        "# CAP-SEM-002 implementation selection",
        "",
        f"Selection passed: **{result['passed']}**",
        "",
        f"Canonical: `{result['canonical_implementation']}`",
        f"Experimental ablation: `{result['experimental_implementation']}`",
        "",
        "## Decision",
        "",
        str(result["selection_reason"]),
        "",
        "## Canonical result",
        "",
        f"- Held-out accuracy: **{canonical['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{canonical['heldout_coverage']:.3f}**",
        (
            "- Frozen semantic runtime: "
            f"**{canonical['semantic_runtime_is_frozen']}**"
        ),
        (
            "- Learned bridge payload: "
            f"**{canonical['learned_bridge_payload_bytes']} bytes**"
        ),
        "",
        "## Experimental ablation",
        "",
        f"- Held-out accuracy: **{experimental['heldout_accuracy']:.3f}**",
        f"- Held-out coverage: **{experimental['heldout_coverage']:.3f}**",
        (
            "- Refits semantic runtime: "
            f"**{experimental['refits_semantic_runtime']}**"
        ),
        f"- Promotion: **{experimental['promotion_status']}**",
        "",
        "## Checks",
        "",
    ]
    for name, value in result["checks"].items():
        lines.append(f"- {name}: **{value}**")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This selects a controlled-Japanese surface bridge, not unrestricted Japanese understanding. CAP-SEM-003 must learn unseen relation expressions without adding a relation-specific solver.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = run_gate()
    root = Path(__file__).resolve().parents[2]
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "cap_sem_002_selection.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "cap_sem_002_selection.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
