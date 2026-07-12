from __future__ import annotations

from .benchmark_harness import BenchmarkManifest, build_manifest
from .public_benchmarks import (
    BBH_BASE_URL,
    download_verified_git_blob,
    parse_bbh_task,
)


PHASE15A_TASKS = {
    "date_understanding": {
        "blob_sha1": "a577c0c4335aeda00997df7438f133a448d7562e",
        "axis": "date_understanding",
        "answer_type": "exact",
    },
    "logical_deduction_three_objects": {
        "blob_sha1": "8de29eba01188e46784a4b1ec63ade9b50a4548c",
        "axis": "logical_ordering",
        "answer_type": "exact",
    },
    "tracking_shuffled_objects_three_objects": {
        "blob_sha1": "116054a16e2f7148365a2ff6ee5e00e9206d2c52",
        "axis": "state_permutation_tracking",
        "answer_type": "exact",
    },
    "navigate": {
        "blob_sha1": "b806905501d90c4fc17f9305bd146e0666c0eb67",
        "axis": "spatial_navigation",
        "answer_type": "exact",
    },
    "dyck_languages": {
        "blob_sha1": "2a507b4d952dd18e6af54e9e38509584b47f08cf",
        "axis": "stack_completion",
        "answer_type": "exact",
    },
}


def load_phase15a_public_transfer_suite(
    *,
    examples_per_task: int = 40,
    expected_manifest_sha256: str | None = None,
) -> BenchmarkManifest:
    examples = []
    for task_name, config in PHASE15A_TASKS.items():
        url = f"{BBH_BASE_URL}/{task_name}.json"
        payload = download_verified_git_blob(url, str(config["blob_sha1"]))
        examples.extend(
            parse_bbh_task(
                payload,
                task_name=task_name,
                axis=str(config["axis"]),
                answer_type=str(config["answer_type"]),
                limit=examples_per_task,
            )
        )
    manifest = build_manifest(
        name="phase15a-frozen-unseen-public-capabilities",
        split=f"first-{examples_per_task}-per-task",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )
    if expected_manifest_sha256 is not None and manifest.sha256 != expected_manifest_sha256:
        raise ValueError(
            "Phase 15a manifest mismatch: "
            f"expected {expected_manifest_sha256}, got {manifest.sha256}"
        )
    return manifest
