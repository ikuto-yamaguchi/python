from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

from .sparc_discourse import SPARCHS9Model, _normalise
from .sparc_role_induction_v2 import (
    InducedDiscourseGraphV2,
    SPARCHS10ModelV2,
)


class SPARCHS10ModelV3(SPARCHS10ModelV2):
    """Competition-gated HS10 model that cannot hijack older capabilities."""

    def reply(self, text: str):
        compact = _normalise(text)
        owns_query = any(
            title and title in compact
            for title in self.learned_discourse.exact_titles
        )
        if owns_query:
            learned = self.learned_discourse.answer(text)
            if learned is not None and learned.confidence >= 0.35:
                return learned
        return self.base.reply(text)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS10ModelV3":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS9Model.from_bytes(base64.b85decode(payload["base"])))
        model.learned_discourse = InducedDiscourseGraphV2.from_bytes(
            base64.b85decode(payload["learned"])
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS10ModelV3":
        return cls.from_bytes(Path(path).read_bytes())
