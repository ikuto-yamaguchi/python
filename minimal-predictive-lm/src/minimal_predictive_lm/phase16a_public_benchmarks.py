from __future__ import annotations

from .benchmark_harness import BenchmarkManifest, build_manifest
from .public_benchmarks import BBH_BASE_URL, download_verified_git_blob, parse_bbh_task


PHASE16A_TASKS = {
    "causal_judgement": {
        "blob_sha1": "7b6f3590a0c191244e5704e18d691d46268ac923",
        "axis": "causal_judgement",
        "answer_type": "exact",
    },
    "disambiguation_qa": {
        "blob_sha1": "d896cfe6b83a150d2904164e5424521f85bb0a3b",
        "axis": "reference_resolution",
        "answer_type": "exact",
    },
    "formal_fallacies": {
        "blob_sha1": "f54e739fb41e1e0ad57b21b2cd61653465bb78fd",
        "axis": "formal_validity",
        "answer_type": "exact",
    },
    "hyperbaton": {
        "blob_sha1": "f6667d70447e8cbd205ce713a6a8e9f2c7125dcd",
        "axis": "adjective_order",
        "answer_type": "exact",
    },
    "web_of_lies": {
        "blob_sha1": "ac9fa3b4bb872853a7b1ac7cbbebb1f8b02b8178",
        "axis": "belief_propagation",
        "answer_type": "exact",
    },
}


def load_phase16a_public_transfer_suite(
    *,
    examples_per_task: int = 40,
    expected_manifest_sha256: str | None = None,
) -> BenchmarkManifest:
    examples = []
    for task_name, config in PHASE16A_TASKS.items():
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
        name="phase16a-frozen-third-public-capability-slice",
        split=f"first-{examples_per_task}-per-task",
        source="https://github.com/suzgunmirac/BIG-Bench-Hard/tree/main/bbh",
        license_id="MIT",
        public=True,
        examples=examples,
    )
    if expected_manifest_sha256 is not None and manifest.sha256 != expected_manifest_sha256:
        raise ValueError(
            "Phase 16a manifest mismatch: "
            f"expected {expected_manifest_sha256}, got {manifest.sha256}"
        )
    return manifest
