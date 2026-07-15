from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass
from pathlib import Path

from .cic_artifact import CICArtifact
from .cic_choice_data import parse_choice_question
from .cic_choice_model import QuantizedChoiceMechanism


@dataclass(frozen=True)
class MixedPrediction:
    mode: str
    answer: str
    mechanism: str
    work: int


@dataclass
class MixedCICArtifact:
    arithmetic: CICArtifact
    choice: QuantizedChoiceMechanism
    metadata: dict[str, object]

    def predict(self, text: str) -> MixedPrediction:
        parsed = parse_choice_question(text)
        if parsed is not None:
            stem, options = parsed
            index, checked = self.choice.predict(stem, options)
            return MixedPrediction(
                "choice",
                options[index],
                "choose_option",
                checked,
            )
        value, mechanism, checked = self.arithmetic.predict(text)
        if value is None:
            return MixedPrediction(
                "unknown",
                "まだこの質問を実行できる機構を獲得していません。",
                "none",
                checked,
            )
        return MixedPrediction(
            "arithmetic",
            str(value),
            mechanism or "arithmetic",
            checked,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "cic-mixed-001",
            "metadata": self.metadata,
            "arithmetic": base64.b64encode(self.arithmetic.to_bytes()).decode("ascii"),
            "choice": {
                "dimensions": self.choice.dimensions,
                "scale": self.choice.scale,
                "weights": {
                    str(index): value for index, value in self.choice.weights.items()
                },
            },
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "MixedCICArtifact":
        payload = json.loads(zlib.decompress(data))
        choice = payload["choice"]
        return cls(
            CICArtifact.from_bytes(base64.b64decode(payload["arithmetic"])),
            QuantizedChoiceMechanism(
                int(choice["dimensions"]),
                float(choice["scale"]),
                {int(index): int(value) for index, value in choice["weights"].items()},
            ),
            dict(payload.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "MixedCICArtifact":
        return cls.from_bytes(Path(path).read_bytes())
