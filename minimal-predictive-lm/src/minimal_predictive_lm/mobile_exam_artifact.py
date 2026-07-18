from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence
import zlib

from .cic_choice_data import choice_features, parse_choice_question
from .cic_choice_model import _dot
from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact, MobileUnifiedPrediction


@dataclass(frozen=True)
class MobileExamPrediction:
    mode: str
    answer: str
    confidence: float | None
    work: int
    evidence_titles: tuple[str, ...]


def _unit(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return ()
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    scale = variance ** 0.5 or 1.0
    return tuple((value - mean) / scale for value in values)


class MobileExamArtifact:
    """One executable package for dialogue, existing reasoning and curriculum memory."""

    FORMAT = "mobile-exam-artifact-001"

    def __init__(
        self,
        base: MobileUnifiedArtifact,
        curriculum: QuantizedCurriculumMemory,
        *,
        alpha: float,
        memory_confidence_threshold: float,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between zero and one")
        self.base = base
        self.curriculum = curriculum
        self.alpha = alpha
        self.memory_confidence_threshold = memory_confidence_threshold
        self.metadata = dict(metadata or {})

    def _base_choice_scores(self, stem: str, options: Sequence[str]) -> tuple[float, ...]:
        model = self.base.reasoning.choice
        raw = [
            model.scale
            * _dot(
                model.weights,
                choice_features(
                    stem,
                    option,
                    index,
                    dimensions=model.dimensions,
                    hash_replicas=model.hash_replicas,
                    relation_scope=model.relation_scope,
                ),
            )
            for index, option in enumerate(options)
        ]
        return _unit(raw)

    def predict(self, text: str) -> MobileExamPrediction:
        parsed = parse_choice_question(text)
        if parsed is None:
            prediction: MobileUnifiedPrediction = self.base.predict(text)
            return MobileExamPrediction(
                mode=prediction.mode,
                answer=prediction.answer,
                confidence=prediction.confidence,
                work=prediction.work,
                evidence_titles=(),
            )

        stem, options = parsed
        base_scores = self._base_choice_scores(stem, options)
        memory = self.curriculum.score_options(stem, options)
        if memory.confidence >= self.memory_confidence_threshold:
            scores = tuple(
                (1.0 - self.alpha) * base + self.alpha * evidence
                for base, evidence in zip(base_scores, memory.scores)
            )
            mode = "exam_choice_hybrid"
        else:
            scores = base_scores
            mode = "exam_choice_base"
        selected = max(range(len(scores)), key=lambda index: scores[index])
        ordered = sorted(scores, reverse=True)
        confidence = ordered[0] - ordered[1] if len(ordered) > 1 else 0.0
        return MobileExamPrediction(
            mode=mode,
            answer=options[selected],
            confidence=confidence,
            work=len(options) + memory.active_postings,
            evidence_titles=memory.retrieved_documents,
        )

    def planned_complete_package_bytes(self) -> int:
        return (
            self.base.planned_complete_package_bytes()
            + len(self.curriculum.to_bytes())
            + 64 * 1024
        )

    def resource_report(self) -> dict[str, object]:
        base = self.base.resource_report()
        memory = self.curriculum.resource_report()
        complete = self.planned_complete_package_bytes()
        return {
            "base": base,
            "curriculum": memory,
            "planned_complete_package_bytes": complete,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "package_within_limit": complete <= MAX_MODEL_PACKAGE_BYTES,
            "estimated_combined_active_bytes": (
                int(base["recurrent_active_weight_bytes_per_step"])
                + int(memory["estimated_active_bytes"])
            ),
            "transformer_used": False,
            "dense_attention_used": False,
            "mobile_device_gate_passed": False,
            "university_exam_mastery_passed": False,
            "highschool_level_passed": False,
        }

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "base": base64.b64encode(self.base.to_bytes()).decode("ascii"),
            "curriculum": base64.b64encode(self.curriculum.to_bytes()).decode("ascii"),
            "alpha": self.alpha,
            "memory_confidence_threshold": self.memory_confidence_threshold,
            "metadata": self.metadata,
            "planned_complete_package_bytes": self.planned_complete_package_bytes(),
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "MobileExamArtifact":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported mobile exam artifact format")
        artifact = cls(
            MobileUnifiedArtifact.from_bytes(base64.b64decode(payload["base"])),
            QuantizedCurriculumMemory.from_bytes(
                base64.b64decode(payload["curriculum"])
            ),
            alpha=float(payload["alpha"]),
            memory_confidence_threshold=float(
                payload["memory_confidence_threshold"]
            ),
            metadata=dict(payload.get("metadata", {})),
        )
        if artifact.planned_complete_package_bytes() != int(
            payload["planned_complete_package_bytes"]
        ):
            raise ValueError("mobile exam package accounting mismatch")
        return artifact

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "MobileExamArtifact":
        return cls.from_bytes(Path(path).read_bytes())
