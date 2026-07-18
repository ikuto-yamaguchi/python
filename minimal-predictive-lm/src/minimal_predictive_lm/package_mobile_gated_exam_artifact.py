from __future__ import annotations

import argparse
import json
from pathlib import Path

from .curriculum_memory_gate import QuantizedCurriculumGate
from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_gated_exam_artifact import MobileGatedExamArtifact
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


def package_artifact(
    base_path: str | Path,
    memory_path: str | Path,
    gate_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    artifact = MobileGatedExamArtifact(
        MobileUnifiedArtifact.load(base_path),
        QuantizedCurriculumMemory.load(memory_path),
        QuantizedCurriculumGate.from_bytes(Path(gate_path).read_bytes()),
        metadata={
            "capability_id": "MOBILE-GATED-UNIVERSITY-EXAM-ARTIFACT-001",
            "gate_validation": "five-fold out-of-fold JMMLU development",
            "official_common_test_targets_used": 0,
            "completion_allowed": False,
        },
    )
    report = artifact.resource_report()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact.save(output)
    checks = {
        "package_below_decimal_1gb": int(report["planned_complete_package_bytes"]) <= MAX_MODEL_PACKAGE_BYTES,
        "active_bytes_below_5mb": int(report["estimated_combined_active_bytes"]) <= 5_000_000,
        "gate_below_16kb": int(report["gate_bytes"]) <= 16 * 1024,
        "subject_name_not_used": report["subject_name_input_used"] is False,
        "prompt_text_not_used_by_gate": report["prompt_text_gate_feature_used"] is False,
        "official_common_test_targets_used_zero": report["official_common_test_targets_used"] == 0,
    }
    result = {
        "artifact_path": str(output),
        "manifest_bytes": len(artifact.to_bytes()),
        "resources": report,
        "checks": checks,
        "package_passed": all(checks.values()),
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
        "mobile_device_gate_passed": False,
        "claim_boundary": (
            "The package contains the first cross-validated positive curriculum-memory gate, "
            "but the gain is small and no official exam has been scored yet."
        ),
    }
    report_path = output.with_suffix(output.suffix + ".json")
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not result["package_passed"]:
        raise SystemExit("gated mobile exam package failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("memory")
    parser.add_argument("gate")
    parser.add_argument("output")
    args = parser.parse_args()
    print(
        json.dumps(
            package_artifact(args.base, args.memory, args.gate, args.output),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
