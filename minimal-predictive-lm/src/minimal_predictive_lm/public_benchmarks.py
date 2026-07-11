from __future__ import annotations

import hashlib
import json
from urllib.request import Request, urlopen

from .benchmark_harness import BenchmarkExample, BenchmarkManifest, build_manifest


GSM8K_TEST_URL = (
    "https://raw.githubusercontent.com/openai/grade-school-math/"
    "master/grade_school_math/data/test.jsonl"
)
GSM8K_TEST_GIT_BLOB_SHA1 = "e4c2ff4942b9a78bd74f04141224c11e28d12dc9"
GSM8K_TEST_EXAMPLES = 1319

BIGBENCH_ARITHMETIC_BASE_URL = (
    "https://raw.githubusercontent.com/google/BIG-bench/main/"
    "bigbench/benchmark_tasks/arithmetic"
)
BIGBENCH_ARITHMETIC_TASKS = tuple(
    f"{digits}_digit_{operation}"
    for digits in range(1, 6)
    for operation in ("addition", "subtraction", "multiplication", "division")
)
BIGBENCH_ARITHMETIC_SUBSET_SHA256 = (
    "cfd8bd98c597f5482df9724eb2750d293a443a1c6526630d4b0510a30723626d"
)


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _download(url: str, *, timeout_seconds: float = 30.0) -> bytes:
    request = Request(url, headers={"User-Agent": "minimal-predictive-lm/0.1"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def download_verified_git_blob(
    url: str,
    expected_blob_sha1: str,
    *,
    timeout_seconds: float = 30.0,
) -> bytes:
    payload = _download(url, timeout_seconds=timeout_seconds)
    observed = git_blob_sha1(payload)
    if observed != expected_blob_sha1:
        raise ValueError(
            f"public benchmark blob mismatch: expected {expected_blob_sha1}, got {observed}"
        )
    return payload


def _final_gsm8k_answer(answer: str) -> str:
    if "####" not in answer:
        raise ValueError("GSM8K answer does not contain the final-answer delimiter")
    return answer.rsplit("####", 1)[1].strip().replace(",", "")


def parse_gsm8k_test(payload: bytes, *, limit: int | None = None) -> tuple[BenchmarkExample, ...]:
    examples: list[BenchmarkExample] = []
    for index, raw_line in enumerate(payload.decode("utf-8").splitlines()):
        if not raw_line.strip():
            continue
        item = json.loads(raw_line)
        examples.append(
            BenchmarkExample(
                f"gsm8k_test_{index:04d}",
                "mathematics",
                str(item["question"]),
                _final_gsm8k_answer(str(item["answer"])),
                "numeric",
            )
        )
        if limit is not None and len(examples) >= limit:
            break
    if limit is None and len(examples) != GSM8K_TEST_EXAMPLES:
        raise ValueError(
            f"unexpected GSM8K test size: expected {GSM8K_TEST_EXAMPLES}, got {len(examples)}"
        )
    return tuple(examples)


def load_gsm8k_test(*, limit: int | None = None) -> BenchmarkManifest:
    payload = download_verified_git_blob(GSM8K_TEST_URL, GSM8K_TEST_GIT_BLOB_SHA1)
    return build_manifest(
        name="gsm8k",
        split="test" if limit is None else f"test-first-{limit}",
        source=GSM8K_TEST_URL,
        license_id="MIT",
        public=True,
        examples=parse_gsm8k_test(payload, limit=limit),
    )


def parse_bigbench_arithmetic_task(
    payload: bytes,
    *,
    task_name: str,
    limit: int,
) -> tuple[BenchmarkExample, ...]:
    document = json.loads(payload.decode("utf-8"))
    if str(document.get("name")) != task_name:
        raise ValueError(
            f"BIG-bench task name mismatch: expected {task_name!r}, got {document.get('name')!r}"
        )
    raw_examples = document.get("examples")
    if not isinstance(raw_examples, list) or len(raw_examples) < limit:
        raise ValueError(f"BIG-bench task {task_name!r} has fewer than {limit} examples")
    return tuple(
        BenchmarkExample(
            f"bigbench_{task_name}_{index:03d}",
            "mathematics",
            str(item["input"]),
            str(item["target"]),
            "numeric",
        )
        for index, item in enumerate(raw_examples[:limit])
    )


def load_bigbench_arithmetic_subset(
    *,
    examples_per_task: int = 10,
    expected_manifest_sha256: str | None = BIGBENCH_ARITHMETIC_SUBSET_SHA256,
) -> BenchmarkManifest:
    examples: list[BenchmarkExample] = []
    for task_name in BIGBENCH_ARITHMETIC_TASKS:
        url = f"{BIGBENCH_ARITHMETIC_BASE_URL}/{task_name}/task.json"
        examples.extend(
            parse_bigbench_arithmetic_task(
                _download(url),
                task_name=task_name,
                limit=examples_per_task,
            )
        )
    manifest = build_manifest(
        name="bigbench-arithmetic",
        split=f"first-{examples_per_task}-per-subtask",
        source=(
            "https://github.com/google/BIG-bench/tree/main/"
            "bigbench/benchmark_tasks/arithmetic"
        ),
        license_id="Apache-2.0",
        public=True,
        examples=examples,
    )
    if expected_manifest_sha256 is not None and manifest.sha256 != expected_manifest_sha256:
        raise ValueError(
            "BIG-bench arithmetic manifest mismatch: "
            f"expected {expected_manifest_sha256}, got {manifest.sha256}"
        )
    return manifest
