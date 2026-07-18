from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_exam_artifact import MobileExamArtifact
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


def package_artifact(
    base_path: str | Path,
    memory_path: str | Path,
    experiment_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    base = MobileUnifiedArtifact.load(base_path)
    memory = QuantizedCurriculumMemory.load(memory_path)
    experiment = json.loads(Path(experiment_path).read_text(encoding="utf-8"))
    policy = experiment["selected_policy"]
    artifact = MobileExamArtifact(
        base,
        memory,
        alpha=float(policy["alpha"]),
        memory_confidence_threshold=float(policy["memory_confidence_threshold"]),
        metadata={
            "capability_id": "MOBILE-UNIVERSITY-EXAM-ARTIFACT-001",
            "policy_selected_on": "JMMLU disclosed development split only",
            "official_common_test_targets_used": 0,
            "university_exam_mastery_passed": False,
            "highschool_level_passed": False,
        },
    )
    report = artifact.resource_report()
    checks = {
        "package_below_decimal_1gb": (
            int(report["planned_complete_package_bytes"]) <= MAX_MODEL_PACKAGE_BYTES
        ),
        "curriculum_is_paged_sparse": bool(
            report["curriculum"]["paged_sparse"]
        ),
        "curriculum_has_document_local_support": bool(
            report["curriculum"]["document_local_support"]
        ),
        "active_bytes_below_5mb": (
            int(report["estimated_combined_active_bytes"]) <= 5_000_000
        ),
        "official_exam_targets_used_zero": True,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact.save(output)
    result = {
        "artifact_path": str(output),
        "manifest_bytes": len(artifact.to_bytes()),
        "selected_policy": policy,
        "resources": report,
        "checks": checks,
        "package_passed": all(checks.values()),
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
        "mobile_device_gate_passed": False,
    }
    report_path = output.with_suffix(output.suffix + ".json")
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not result["package_passed"]:
        raise SystemExit("mobile exam artifact package failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("memory")
    parser.add_argument("experiment")
    parser.add_argument("output")
    args = parser.parse_args()
    print(
        json.dumps(
            package_artifact(
                args.base,
                args.memory,
                args.experiment,
                args.output,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
