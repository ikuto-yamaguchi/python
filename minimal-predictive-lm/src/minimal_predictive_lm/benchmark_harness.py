from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import unicodedata
from typing import Iterable, Mapping, Sequence


ABSTAIN_TOKEN = "__ABSTAIN__"


@dataclass(frozen=True)
class BenchmarkExample:
    example_id: str
    axis: str
    prompt: str
    target: str
    answer_type: str = "exact"

    def model_view(self) -> dict[str, str]:
        """Return the only fields a compared model is allowed to observe."""
        return {
            "id": self.example_id,
            "axis": self.axis,
            "prompt": self.prompt,
        }


@dataclass(frozen=True)
class BenchmarkManifest:
    name: str
    split: str
    source: str
    license_id: str
    public: bool
    sha256: str
    examples: tuple[BenchmarkExample, ...]


@dataclass(frozen=True)
class RunPolicy:
    max_output_chars: int = 128
    stop_sequences: tuple[str, ...] = ("\n\n",)
    tools_allowed: tuple[str, ...] = ()
    temperature: float = 0.0
    seed: int = 0


@dataclass(frozen=True)
class PredictionRecord:
    example_id: str
    text: str
    operations: int = 0
    reads: int = 0
    writes: int = 0


@dataclass(frozen=True)
class ResourceUsage:
    model_bytes: int
    peak_rss_bytes: int
    wall_ns: int
    cpu_ns: int
    operations: int
    reads: int
    writes: int
    energy_joules: float | None = None


@dataclass(frozen=True)
class RunReport:
    model_id: str
    manifest_name: str
    manifest_sha256: str
    public_benchmark: bool
    policy: RunPolicy
    predictions: tuple[PredictionRecord, ...]
    resources: ResourceUsage
    execution_mode: str
    instrumentation_version: str = "mpm-bench-v1"


@dataclass(frozen=True)
class ScoreSummary:
    examples: int
    answered: int
    correct: int
    overall_accuracy: float
    selective_accuracy: float
    coverage: float


@dataclass(frozen=True)
class ComparisonSummary:
    candidate: ScoreSummary
    baseline: ScoreSummary
    fairness_violations: tuple[str, ...]
    parity_claim_allowed: bool
    pareto_claim_allowed: bool
    strictly_better_resources: tuple[str, ...]


def _canonical_example_line(example: BenchmarkExample) -> bytes:
    payload = {
        "id": example.example_id,
        "axis": example.axis,
        "prompt": example.prompt,
        "target": example.target,
        "answer_type": example.answer_type,
    }
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def benchmark_sha256(examples: Iterable[BenchmarkExample]) -> str:
    digest = hashlib.sha256()
    for example in examples:
        digest.update(_canonical_example_line(example))
    return digest.hexdigest()


def build_manifest(
    *,
    name: str,
    split: str,
    source: str,
    license_id: str,
    public: bool,
    examples: Iterable[BenchmarkExample],
) -> BenchmarkManifest:
    items = tuple(examples)
    if not items:
        raise ValueError("benchmark must contain at least one example")
    identifiers = [item.example_id for item in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("benchmark example ids must be unique")
    for item in items:
        if not item.prompt.strip() or not item.target.strip():
            raise ValueError(f"empty benchmark field in {item.example_id!r}")
        if item.answer_type not in {"exact", "numeric"}:
            raise ValueError(f"unsupported answer type {item.answer_type!r}")
    return BenchmarkManifest(
        name,
        split,
        source,
        license_id,
        public,
        benchmark_sha256(items),
        items,
    )


def load_jsonl_manifest(
    path: str | Path,
    *,
    name: str,
    split: str,
    source: str,
    license_id: str,
    public: bool,
    expected_sha256: str | None = None,
) -> BenchmarkManifest:
    items: list[BenchmarkExample] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        try:
            items.append(
                BenchmarkExample(
                    str(payload["id"]),
                    str(payload["axis"]),
                    str(payload["prompt"]),
                    str(payload["target"]),
                    str(payload.get("answer_type", "exact")),
                )
            )
        except KeyError as exc:
            raise ValueError(f"missing field at line {line_number}: {exc}") from exc
    manifest = build_manifest(
        name=name,
        split=split,
        source=source,
        license_id=license_id,
        public=public,
        examples=items,
    )
    if expected_sha256 is not None and manifest.sha256 != expected_sha256:
        raise ValueError(
            f"benchmark checksum mismatch: expected {expected_sha256}, got {manifest.sha256}"
        )
    return manifest


def model_request(manifest: BenchmarkManifest, policy: RunPolicy) -> dict[str, object]:
    """Build a target-free request for an external model process."""
    return {
        "manifest": {
            "name": manifest.name,
            "split": manifest.split,
            "sha256": manifest.sha256,
        },
        "policy": asdict(policy),
        "examples": [example.model_view() for example in manifest.examples],
    }


def _rss_bytes(value: int) -> int:
    # Linux reports KiB; macOS reports bytes.
    return value if sys.platform == "darwin" else value * 1024


def run_command_adapter(
    manifest: BenchmarkManifest,
    policy: RunPolicy,
    *,
    model_id: str,
    command: Sequence[str],
    timeout_seconds: float = 120.0,
) -> RunReport:
    request = model_request(manifest, policy)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter_ns()
    completed = subprocess.run(
        list(command),
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    wall_ns = time.perf_counter_ns() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if completed.returncode != 0:
        raise RuntimeError(
            f"model command failed with {completed.returncode}: {completed.stderr[-2000:]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"model command returned invalid JSON: {completed.stdout[-1000:]}") from exc

    raw_predictions = payload.get("predictions")
    if not isinstance(raw_predictions, list):
        raise ValueError("model response must contain a predictions list")
    predictions = tuple(
        PredictionRecord(
            str(item["id"]),
            str(item.get("text", ""))[: policy.max_output_chars],
            int(item.get("operations", 0)),
            int(item.get("reads", 0)),
            int(item.get("writes", 0)),
        )
        for item in raw_predictions
    )
    expected_ids = tuple(example.example_id for example in manifest.examples)
    observed_ids = tuple(item.example_id for item in predictions)
    if observed_ids != expected_ids:
        raise ValueError(
            f"prediction ids or order differ from benchmark: {observed_ids!r} != {expected_ids!r}"
        )

    cpu_seconds = (
        after.ru_utime
        + after.ru_stime
        - before.ru_utime
        - before.ru_stime
    )
    reported_rss = int(payload.get("peak_rss_bytes", 0))
    peak_rss = reported_rss or _rss_bytes(int(after.ru_maxrss))
    energy = payload.get("energy_joules")
    resources = ResourceUsage(
        model_bytes=int(payload.get("model_bytes", 0)),
        peak_rss_bytes=peak_rss,
        wall_ns=wall_ns,
        cpu_ns=max(0, int(cpu_seconds * 1_000_000_000)),
        operations=sum(item.operations for item in predictions),
        reads=sum(item.reads for item in predictions),
        writes=sum(item.writes for item in predictions),
        energy_joules=None if energy is None else float(energy),
    )
    return RunReport(
        model_id,
        manifest.name,
        manifest.sha256,
        manifest.public,
        policy,
        predictions,
        resources,
        "fresh_subprocess",
    )


def _normal_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).lower().strip()
    return re.sub(r"\s+", " ", text)


def _last_fraction(value: str) -> Fraction | None:
    tokens = re.findall(r"[-+]?\d+(?:/\d+|\.\d+)?", unicodedata.normalize("NFKC", value))
    if not tokens:
        return None
    try:
        return Fraction(tokens[-1])
    except (ValueError, ZeroDivisionError):
        return None


def answer_is_correct(example: BenchmarkExample, prediction: str) -> bool:
    if prediction.strip() == ABSTAIN_TOKEN:
        return False
    if example.answer_type == "numeric":
        predicted = _last_fraction(prediction)
        target = _last_fraction(example.target)
        return predicted is not None and target is not None and predicted == target
    return _normal_text(prediction) == _normal_text(example.target)


def score_report(manifest: BenchmarkManifest, report: RunReport) -> ScoreSummary:
    if report.manifest_sha256 != manifest.sha256:
        raise ValueError("report was produced for a different benchmark checksum")
    mapping = {item.example_id: item for item in report.predictions}
    answered = 0
    correct = 0
    for example in manifest.examples:
        prediction = mapping.get(example.example_id)
        if prediction is None:
            continue
        text = prediction.text.strip()
        if not text or text == ABSTAIN_TOKEN:
            continue
        answered += 1
        correct += int(answer_is_correct(example, text))
    total = len(manifest.examples)
    return ScoreSummary(
        total,
        answered,
        correct,
        correct / total,
        correct / answered if answered else 0.0,
        answered / total,
    )


def fairness_violations(
    manifest: BenchmarkManifest,
    candidate: RunReport,
    baseline: RunReport,
) -> tuple[str, ...]:
    violations: list[str] = []
    if not manifest.public:
        violations.append("benchmark_not_public")
    if candidate.manifest_sha256 != baseline.manifest_sha256 or candidate.manifest_sha256 != manifest.sha256:
        violations.append("benchmark_checksum_mismatch")
    if candidate.policy != baseline.policy:
        violations.append("run_policy_mismatch")
    if candidate.execution_mode != "fresh_subprocess" or baseline.execution_mode != "fresh_subprocess":
        violations.append("fresh_process_required")
    if candidate.instrumentation_version != baseline.instrumentation_version:
        violations.append("instrumentation_version_mismatch")
    for label, report in (("candidate", candidate), ("baseline", baseline)):
        if report.resources.model_bytes <= 0:
            violations.append(f"{label}_model_bytes_missing")
        if report.resources.peak_rss_bytes <= 0:
            violations.append(f"{label}_peak_rss_missing")
        if report.resources.wall_ns <= 0:
            violations.append(f"{label}_wall_time_missing")
    return tuple(sorted(set(violations)))


def compare_reports(
    manifest: BenchmarkManifest,
    candidate: RunReport,
    baseline: RunReport,
) -> ComparisonSummary:
    candidate_score = score_report(manifest, candidate)
    baseline_score = score_report(manifest, baseline)
    violations = fairness_violations(manifest, candidate, baseline)
    parity = not violations and candidate_score.overall_accuracy >= baseline_score.overall_accuracy

    candidate_resources = candidate.resources
    baseline_resources = baseline.resources
    resource_pairs = {
        "model_bytes": (candidate_resources.model_bytes, baseline_resources.model_bytes),
        "peak_rss_bytes": (candidate_resources.peak_rss_bytes, baseline_resources.peak_rss_bytes),
        "wall_ns": (candidate_resources.wall_ns, baseline_resources.wall_ns),
        "cpu_ns": (candidate_resources.cpu_ns, baseline_resources.cpu_ns),
    }
    no_worse = all(left <= right for left, right in resource_pairs.values())
    strictly_better = tuple(
        name for name, (left, right) in resource_pairs.items() if left < right
    )
    pareto = parity and no_worse and bool(strictly_better)
    return ComparisonSummary(
        candidate_score,
        baseline_score,
        violations,
        parity,
        pareto,
        strictly_better,
    )


def report_to_dict(report: RunReport) -> dict[str, object]:
    return asdict(report)


def report_from_dict(payload: Mapping[str, object]) -> RunReport:
    policy_payload = payload["policy"]
    resource_payload = payload["resources"]
    return RunReport(
        str(payload["model_id"]),
        str(payload["manifest_name"]),
        str(payload["manifest_sha256"]),
        bool(payload["public_benchmark"]),
        RunPolicy(
            int(policy_payload["max_output_chars"]),
            tuple(policy_payload["stop_sequences"]),
            tuple(policy_payload["tools_allowed"]),
            float(policy_payload["temperature"]),
            int(policy_payload["seed"]),
        ),
        tuple(
            PredictionRecord(
                str(item["example_id"]),
                str(item["text"]),
                int(item.get("operations", 0)),
                int(item.get("reads", 0)),
                int(item.get("writes", 0)),
            )
            for item in payload["predictions"]
        ),
        ResourceUsage(
            int(resource_payload["model_bytes"]),
            int(resource_payload["peak_rss_bytes"]),
            int(resource_payload["wall_ns"]),
            int(resource_payload["cpu_ns"]),
            int(resource_payload["operations"]),
            int(resource_payload["reads"]),
            int(resource_payload["writes"]),
            None
            if resource_payload.get("energy_joules") is None
            else float(resource_payload["energy_joules"]),
        ),
        str(payload["execution_mode"]),
        str(payload.get("instrumentation_version", "mpm-bench-v1")),
    )
