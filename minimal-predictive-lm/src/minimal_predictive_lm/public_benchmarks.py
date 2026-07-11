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


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def download_verified_git_blob(
    url: str,
    expected_blob_sha1: str,
    *,
    timeout_seconds: float = 30.0,
) -> bytes:
    request = Request(url, headers={"User-Agent": "minimal-predictive-lm/0.1"})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read()
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
