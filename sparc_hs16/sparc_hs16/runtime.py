from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from .conversation import ConsistentConversationEngine, ConversationReply, ConversationState
from .induction import NumericDemonstration, NumericMechanismBank
from .model import SolveResult, SparseMemory, SparcHS16
from .reading import JapaneseReadingReasoner


class AdaptiveSparcRuntime:
    """Integrated sparse runtime with acquired executable mechanisms.

    The runtime combines bounded dialogue state, fact memory, verified symbolic
    mechanisms, programs induced from demonstrations, and a proof-producing
    Japanese passage reasoner behind one serialized artifact.
    """

    def __init__(
        self,
        base: SparcHS16 | None = None,
        numeric_bank: NumericMechanismBank | None = None,
        reading_reasoner: JapaneseReadingReasoner | None = None,
        conversation: ConsistentConversationEngine | None = None,
    ) -> None:
        self.base = base or SparcHS16()
        self.numeric_bank = numeric_bank or NumericMechanismBank(self.base.memory)
        self.numeric_bank.memory = self.base.memory
        self.reading_reasoner = reading_reasoner or JapaneseReadingReasoner()
        self.conversation = conversation or ConsistentConversationEngine()

    @property
    def memory(self) -> SparseMemory:
        return self.base.memory

    def teach_numeric_mechanism(
        self,
        name: str,
        demonstrations: Iterable[NumericDemonstration],
    ):
        return self.numeric_bank.learn(name, demonstrations)

    def chat(self, text: str) -> ConversationReply:
        reply = self.conversation.respond(text)
        if reply is not None:
            return reply
        solved = self.solve(text)
        self.conversation.state.append("user", text)
        self.conversation.state.append("assistant", solved.answer)
        return ConversationReply(solved.answer, solved.mechanism, solved.confidence)

    def solve(self, text: str) -> SolveResult:
        started = time.perf_counter()

        if self.reading_reasoner.can_handle(text):
            reading = self.reading_reasoner.solve(text)
            if reading is not None:
                elapsed = (time.perf_counter() - started) * 1000
                return SolveResult(
                    answer=reading.answer,
                    mechanism="proof-japanese-reading:" + "|".join(reading.proof),
                    confidence=reading.confidence,
                    elapsed_ms=elapsed,
                )

        learned = self.numeric_bank.solve(text)
        if learned is not None:
            value, program, route_score = learned
            elapsed = (time.perf_counter() - started) * 1000
            return SolveResult(
                answer=f"{value}です。",
                mechanism=f"induced-program:{program.expression}",
                confidence=min(1.0, 0.7 + route_score),
                elapsed_ms=elapsed,
            )
        return self.base.solve(text)

    def to_dict(self) -> dict:
        return {
            "format": "adaptive-sparc-hs16-v3",
            "memory": self.base.memory.to_dict(),
            "numeric_mechanisms": self.numeric_bank.to_dict(),
            "conversation": self.conversation.state.to_dict(),
            "capabilities": {
                "proof_japanese_reading": True,
                "relation_transitive_closure": True,
                "causal_proof": True,
                "bounded_conversation_state": True,
                "explicit_correction_semantics": True,
                "preference_contradiction_resolution": True,
            },
            "architecture": {
                "transformer_used": False,
                "softmax_attention_used": False,
                "growing_kv_cache_used": False,
                "dense_vocabulary_projection_used": False,
            },
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveSparcRuntime":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") not in {
            "adaptive-sparc-hs16-v1",
            "adaptive-sparc-hs16-v2",
            "adaptive-sparc-hs16-v3",
        }:
            raise ValueError("unsupported adaptive runtime artifact")
        memory = SparseMemory.from_dict(data["memory"])
        base = SparcHS16(memory)
        bank = NumericMechanismBank.from_dict(memory, data.get("numeric_mechanisms", {}))
        conversation = ConsistentConversationEngine(
            ConversationState.from_dict(data.get("conversation", {}))
        )
        return cls(base=base, numeric_bank=bank, conversation=conversation)

    def serialized_bytes(self) -> int:
        return len(
            json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
