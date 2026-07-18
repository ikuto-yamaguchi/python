from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence
import zlib

from .cic_choice_data import choice_features, parse_choice_question
from .cic_choice_model import _dot
from .curriculum_memory_gate import GateObservation, QuantizedCurriculumGate
from .mobile_curriculum_memory import QuantizedCurriculumMemory
from .mobile_sparse_core import MAX_MODEL_PACKAGE_BYTES
from .mobile_unified_artifact import MobileUnifiedArtifact


@dataclass(frozen=True)
class GatedExamPrediction:
    mode: str
    answer: str
    confidence: float | None
    work: int
    evidence_titles: tuple[str, ...]
    memory_probability: float | None


def _unit(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return ()
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    scale = variance ** 0.5 or 1.0
    return tuple((value - mean) / scale for value in values)


class MobileGatedExamArtifact:
    """Executable non-Transformer package with dialogue, reasoning and gated knowledge."""

    FORMAT = "mobile-gated-university-exam-artifact-001"

    def __init__(
        self,
        base: MobileUnifiedArtifact,
        curriculum: QuantizedCurriculumMemory,
        gate: QuantizedCurriculumGate,
        *,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.base = base
        self.curriculum = curriculum
        self.gate = gate
        self.metadata = dict(metadata or {})

    def _base_scores(self, stem: str, options: Sequence[str]) -> tuple[float, ...]:
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

    def predict(self, text: str) -> GatedExamPrediction:
        parsed = parse_choice_question(text)
        if parsed is None:
            prediction = self.base.predict(text)
            return GatedExamPrediction(
                mode=prediction.mode,
                answer=prediction.answer,
                confidence=prediction.confidence,
                work=prediction.work,
                evidence_titles=(),
                memory_probability=None,
            )

        stem, options = parsed
        base_scores = self._base_scores(stem, options)
        memory = self.curriculum.score_options(stem, options)
        observation = GateObservation(
            example_id="runtime",
            base_scores=base_scores,
            memory_scores=memory.scores,
            active_postings=memory.active_postings,
            stem_length=len(stem),
            option_lengths=tuple(len(option) for option in options),
            answer_index=0,
        )
        probability = self.gate.probability(observation)
        selected = self.gate.choose_index(observation)
        used_memory = selected == observation.memory_index and observation.base_index != observation.memory_index
        chosen_scores = memory.scores if used_memory else base_scores
        ordered = sorted(chosen_scores, reverse=True)
        confidence = ordered[0] - ordered[1] if len(ordered) > 1 else 0.0
        return GatedExamPrediction(
            mode="exam_choice_gated_memory" if used_memory else "exam_choice_base",
            answer=options[selected],
            confidence=confidence,
            work=len(options) + memory.active_postings + len(self.gate.weights),
            evidence_titles=memory.retrieved_documents if used_memory else (),
            memory_probability=probability,
        )

    def planned_complete_package_bytes(self) -> int:
        return (
            self.base.planned_complete_package_bytes()
            + len(self.curriculum.to_bytes())
            + len(self.gate.to_bytes())
            + 64 * 1024
        )

    def resource_report(self) -> dict[str, object]:
        base = self.base.resource_report()
        memory = self.curriculum.resource_report()
        gate_bytes = len(self.gate.to_bytes())
        complete = self.planned_complete_package_bytes()
        return {
            "base": base,
            "curriculum": memory,
            "gate_bytes": gate_bytes,
            "gate_features": len(self.gate.weights),
            "planned_complete_package_bytes": complete,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "package_within_limit": complete <= MAX_MODEL_PACKAGE_BYTES,
            "estimated_combined_active_bytes": (
                int(base["recurrent_active_weight_bytes_per_step"])
                + int(memory["estimated_active_bytes"])
                + gate_bytes
            ),
            "transformer_used": False,
            "dense_attention_used": False,
            "subject_name_input_used": False,
            "prompt_text_gate_feature_used": False,
            "official_common_test_targets_used": 0,
            "mobile_device_gate_passed": False,
            "university_exam_mastery_passed": False,
            "highschool_level_passed": False,
        }

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "base": base64.b64encode(self.base.to_bytes()).decode("ascii"),
            "curriculum": base64.b64encode(self.curriculum.to_bytes()).decode("ascii"),
            "gate": base64.b64encode(self.gate.to_bytes()).decode("ascii"),
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
    def from_bytes(cls, data: bytes) -> "MobileGatedExamArtifact":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported gated exam artifact format")
        artifact = cls(
            MobileUnifiedArtifact.from_bytes(base64.b64decode(payload["base"])),
            QuantizedCurriculumMemory.from_bytes(base64.b64decode(payload["curriculum"])),
            QuantizedCurriculumGate.from_bytes(base64.b64decode(payload["gate"])),
            metadata=dict(payload.get("metadata", {})),
        )
        if artifact.planned_complete_package_bytes() != int(
            payload["planned_complete_package_bytes"]
        ):
            raise ValueError("gated exam package accounting mismatch")
        return artifact

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "MobileGatedExamArtifact":
        return cls.from_bytes(Path(path).read_bytes())
