from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from .induction import NumericDemonstration, NumericMechanismBank
from .model import SolveResult, SparseMemory, SparcHS16


class AdaptiveSparcRuntime:
    """Integrated sparse runtime with learned executable mechanisms.

    The base model keeps dialogue, facts and verified hand-independent solvers.
    The mechanism bank can acquire compact programs from demonstrations without
    changing runtime source code. Both parts are serialized as one artifact.
    """

    def __init__(
        self,
        base: SparcHS16 | None = None,
        numeric_bank: NumericMechanismBank | None = None,
    ) -> None:
        self.base = base or SparcHS16()
        self.numeric_bank = numeric_bank or NumericMechanismBank(self.base.memory)
        self.numeric_bank.memory = self.base.memory

    @property
    def memory(self) -> SparseMemory:
        return self.base.memory

    def teach_numeric_mechanism(
        self,
        name: str,
        demonstrations: Iterable[NumericDemonstration],
    ):
        return self.numeric_bank.learn(name, demonstrations)

    def solve(self, text: str) -> SolveResult:
        started = time.perf_counter()
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
            "format": "adaptive-sparc-hs16-v1",
            "memory": self.base.memory.to_dict(),
            "numeric_mechanisms": self.numeric_bank.to_dict(),
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
        if data.get("format") != "adaptive-sparc-hs16-v1":
            raise ValueError("unsupported adaptive runtime artifact")
        memory = SparseMemory.from_dict(data["memory"])
        base = SparcHS16(memory)
        bank = NumericMechanismBank.from_dict(memory, data.get("numeric_mechanisms", {}))
        return cls(base=base, numeric_bank=bank)

    def serialized_bytes(self) -> int:
        return len(
            json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
