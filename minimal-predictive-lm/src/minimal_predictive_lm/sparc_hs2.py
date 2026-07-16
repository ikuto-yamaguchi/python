from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Iterable

from .sparc_language import ReplyResult, SPARCLanguageModel
from .sparc_reasoning import ReasoningResult, SparseRelationalCortex


class SPARCHS2Model:
    """Interactive sparse conversation model with a bounded relational cortex."""

    def __init__(self, language_profile: str = "ci", reasoning_profile: str = "ci") -> None:
        self.language = SPARCLanguageModel(language_profile)
        self.reasoning = SparseRelationalCortex(reasoning_profile)

    def fit_dialogues(self, records: Iterable[tuple[str, str]]) -> "SPARCHS2Model":
        self.language.fit(records)
        return self

    def learn(self, user_text: str, assistant_text: str | None = None) -> str:
        facts = self.reasoning.learn_text(user_text)
        if facts:
            return f"{len(facts)}件の関係を学習しました。"
        if assistant_text is not None:
            self.language.learn(user_text, assistant_text)
            return "会話例を学習しました。"
        return "関係として解釈できませんでした。質問と回答の組を教えてください。"

    def reply(self, text: str) -> ReasoningResult | ReplyResult:
        reasoning = self.reasoning.answer(text)
        if reasoning is not None:
            return reasoning
        facts = self.reasoning.learn_text(text)
        if facts:
            return ReplyResult(
                text=f"分かりました。{len(facts)}件の関係を覚えました。",
                confidence=1.0,
                mechanism="online-relational-learning",
                candidates_inspected=0,
                active_bits=0,
                estimated_sparse_operations=len(facts),
            )
        return self.language.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs2-combined",
            "language": base64.b85encode(self.language.to_bytes()).decode("ascii"),
            "reasoning": base64.b85encode(self.reasoning.to_bytes()).decode("ascii"),
        }
        return zlib.compress(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS2Model":
        payload = json.loads(zlib.decompress(data))
        model = cls()
        model.language = SPARCLanguageModel.from_bytes(base64.b85decode(payload["language"]))
        model.reasoning = SparseRelationalCortex.from_bytes(base64.b85decode(payload["reasoning"]))
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS2Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "language": self.language.report(),
            "reasoning": self.reasoning.report(),
            "combined_serialized_bytes": len(self.to_bytes()),
            "interactive_chat": True,
            "online_relational_learning": True,
            "bounded_multihop_reasoning": True,
        }
