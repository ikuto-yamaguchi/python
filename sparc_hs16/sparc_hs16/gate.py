from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .model import SparcHS16


REQUIRED_DOMAINS = (
    "japanese_modern",
    "japanese_classical",
    "mathematics",
    "english_reading",
    "english_writing",
    "physics",
    "chemistry",
    "biology",
    "earth_science",
    "world_history",
    "japanese_history",
    "geography",
    "civics",
    "information",
    "essay",
    "oral_interview",
    "long_conversation",
)


@dataclass(frozen=True)
class GateCase:
    domain: str
    prompt: str
    expected: str


@dataclass
class GateReport:
    total: int
    correct: int
    accuracy: float
    domain_accuracy: dict[str, float]
    p95_latency_ms: float
    artifact_bytes: int
    all_required_domains_present: bool
    university_exam_mastery_passed: bool
    mobile_device_gate_passed: bool
    communication_gate_passed: bool
    highschool_level_passed: bool
    failures: list[dict]


class UniversityExamGate:
    """Fail-closed gate for the complete target."""

    def __init__(self, max_bytes: int = 1_000_000_000, max_p95_ms: float = 100.0) -> None:
        self.max_bytes = max_bytes
        self.max_p95_ms = max_p95_ms

    def evaluate(self, model: SparcHS16, cases: Iterable[GateCase]) -> GateReport:
        rows = list(cases)
        correct = 0
        by_domain: dict[str, list[bool]] = {}
        latencies: list[float] = []
        failures: list[dict] = []
        for case in rows:
            result = model.solve(case.prompt)
            ok = result.answer.strip() == case.expected.strip()
            correct += int(ok)
            by_domain.setdefault(case.domain, []).append(ok)
            latencies.append(result.elapsed_ms)
            if not ok:
                failures.append({
                    "domain": case.domain,
                    "prompt": case.prompt,
                    "expected": case.expected,
                    "actual": result.answer,
                    "mechanism": result.mechanism,
                })
        domain_accuracy = {name: sum(values) / len(values) for name, values in by_domain.items()}
        required_present = set(REQUIRED_DOMAINS).issubset(domain_accuracy)
        p95 = self._p95(latencies)
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "model.json"
            model.save(artifact)
            artifact_bytes = artifact.stat().st_size
        exact_all = bool(rows) and correct == len(rows)
        communication = all(
            domain_accuracy.get(name, 0.0) == 1.0
            for name in ("essay", "oral_interview", "long_conversation")
        )
        university = required_present and exact_all
        mobile = artifact_bytes <= self.max_bytes and p95 <= self.max_p95_ms
        highschool = university and mobile and communication
        return GateReport(
            total=len(rows),
            correct=correct,
            accuracy=correct / len(rows) if rows else 0.0,
            domain_accuracy=domain_accuracy,
            p95_latency_ms=p95,
            artifact_bytes=artifact_bytes,
            all_required_domains_present=required_present,
            university_exam_mastery_passed=university,
            mobile_device_gate_passed=mobile,
            communication_gate_passed=communication,
            highschool_level_passed=highschool,
            failures=failures,
        )

    @staticmethod
    def _p95(values: list[float]) -> float:
        if not values:
            return float("inf")
        ordered = sorted(values)
        index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * 0.95)))
        return ordered[index]


def load_jsonl(path: str | Path) -> list[GateCase]:
    cases: list[GateCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cases.append(GateCase(str(row["domain"]), str(row["prompt"]), str(row["expected"])))
    return cases


def save_report(report: GateReport, path: str | Path) -> None:
    Path(path).write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
