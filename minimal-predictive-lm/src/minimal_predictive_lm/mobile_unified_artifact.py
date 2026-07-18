from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
import zlib

from .cic_mixed_artifact import MixedCICArtifact
from .mobile_dialogue_ranker import QuantizedDialogueRanker
from .mobile_sparse_core import (
    MAX_MODEL_PACKAGE_BYTES,
    MOBILE_1GB_PROFILE,
    MobileSparseProfile,
)


@dataclass(frozen=True)
class MobileUnifiedPrediction:
    mode: str
    answer: str
    work: int
    confidence: float | None


class MobileUnifiedArtifact:
    """One deployable manifest for sparse recurrent, public reasoning and dialogue.

    The large recurrent block store is represented by its exact deployment profile in
    this Python artifact; production packaging appends the mmap-backed int8 block file.
    Package accounting always includes that full planned block store, so the small
    manifest cannot be misreported as the complete model size.
    """

    FORMAT = "mobile-unified-artifact-001"

    def __init__(
        self,
        reasoning: MixedCICArtifact,
        dialogue: QuantizedDialogueRanker,
        *,
        profile: MobileSparseProfile = MOBILE_1GB_PROFILE,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.reasoning = reasoning
        self.dialogue = dialogue
        self.profile = profile
        self.metadata = dict(metadata or {})

    def predict(self, text: str) -> MobileUnifiedPrediction:
        reasoning = self.reasoning.predict(text)
        if reasoning.mode != "unknown":
            return MobileUnifiedPrediction(
                mode=reasoning.mode,
                answer=reasoning.answer,
                work=reasoning.work,
                confidence=None,
            )
        dialogue = self.dialogue.predict(text)
        if dialogue.response is not None:
            return MobileUnifiedPrediction(
                mode="dialogue",
                answer=dialogue.response,
                work=dialogue.candidates_scored,
                confidence=dialogue.confidence,
            )
        return MobileUnifiedPrediction(
            mode="abstain",
            answer="まだこの質問へ十分な根拠を持って答えられません。",
            work=dialogue.candidates_scored,
            confidence=dialogue.confidence,
        )

    def component_payload_bytes(self) -> int:
        return len(self.reasoning.to_bytes()) + len(self.dialogue.to_bytes())

    def planned_complete_package_bytes(self) -> int:
        manifest_overhead = 128 * 1024
        return (
            self.profile.package_bytes()
            + self.component_payload_bytes()
            + manifest_overhead
        )

    def resource_report(self) -> dict[str, object]:
        reasoning_bytes = len(self.reasoning.to_bytes())
        dialogue_report = self.dialogue.resource_report()
        complete = self.planned_complete_package_bytes()
        return {
            "recurrent_profile_bytes": self.profile.package_bytes(),
            "reasoning_artifact_bytes": reasoning_bytes,
            "dialogue_artifact_bytes": int(dialogue_report["serialized_bytes"]),
            "planned_complete_package_bytes": complete,
            "decimal_1gb_limit": MAX_MODEL_PACKAGE_BYTES,
            "package_within_limit": complete <= MAX_MODEL_PACKAGE_BYTES,
            "recurrent_active_weight_bytes_per_step": (
                self.profile.active_weight_bytes_per_step()
            ),
            "recurrent_macs_per_byte_step": self.profile.macs_per_byte_step(),
            "dialogue_estimated_active_weight_bytes": int(
                dialogue_report["estimated_active_weight_bytes"]
            ),
            "transformer_used": False,
            "dense_attention_used": False,
            "task_name_input_used": False,
            "mobile_device_gate_passed": False,
            "highschool_level_passed": False,
        }

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "profile": {
                key: value
                for key, value in self.profile.__dict__.items()
            },
            "metadata": self.metadata,
            "reasoning": base64.b64encode(self.reasoning.to_bytes()).decode("ascii"),
            "dialogue": base64.b64encode(self.dialogue.to_bytes()).decode("ascii"),
            "planned_complete_package_bytes": self.planned_complete_package_bytes(),
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "MobileUnifiedArtifact":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported mobile unified artifact format")
        profile = MobileSparseProfile(**payload["profile"])
        artifact = cls(
            MixedCICArtifact.from_bytes(base64.b64decode(payload["reasoning"])),
            QuantizedDialogueRanker.from_bytes(base64.b64decode(payload["dialogue"])),
            profile=profile,
            metadata=dict(payload.get("metadata", {})),
        )
        recorded = int(payload["planned_complete_package_bytes"])
        if artifact.planned_complete_package_bytes() != recorded:
            raise ValueError("mobile unified package accounting mismatch")
        return artifact

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "MobileUnifiedArtifact":
        return cls.from_bytes(Path(path).read_bytes())
