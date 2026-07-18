from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import curriculum_memory_jmmlu_experiment as baseline
from .mobile_curriculum_memory import QuantizedCurriculumMemory


class _ExpandedMemoryFactory:
    @staticmethod
    def build(documents):
        return QuantizedCurriculumMemory.build(
            documents,
            buckets=524_288,
            max_features_per_document=768,
            max_postings_per_feature=96,
            max_snippet_chars=3_000,
        )


def run_experiment(
    reference_artifact: str | Path,
    curriculum_path: str | Path,
    jmmlu_root: str | Path,
    *,
    output_dir: str | Path = "results",
) -> dict[str, object]:
    previous = baseline.QuantizedCurriculumMemory
    baseline.QuantizedCurriculumMemory = _ExpandedMemoryFactory
    try:
        result = baseline.run_experiment(
            reference_artifact,
            curriculum_path,
            jmmlu_root,
            output_dir=output_dir,
        )
    finally:
        baseline.QuantizedCurriculumMemory = previous
    result["capability_id"] = "CURRICULUM-MEMORY-FULLTEXT-JMMLU-DEVELOPMENT-001"
    result["memory_build"] = {
        "buckets": 524_288,
        "max_features_per_document": 768,
        "max_postings_per_feature": 96,
        "max_snippet_chars": 3_000,
        "full_text_curriculum": True,
    }
    output = Path(output_dir)
    (output / "curriculum_memory_jmmlu.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_artifact")
    parser.add_argument("curriculum")
    parser.add_argument("jmmlu_root")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    print(
        json.dumps(
            run_experiment(
                args.reference_artifact,
                args.curriculum,
                args.jmmlu_root,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
