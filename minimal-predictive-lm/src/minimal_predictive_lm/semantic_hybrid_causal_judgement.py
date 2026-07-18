from __future__ import annotations

from dataclasses import dataclass
import os

from .generic_causal_judgement_v3 import GenericCausalJudgementV3
from .semantic_causal_ranker import (
    QuantizedSemanticCausalRanker,
    combine_semantic_prediction,
)


@dataclass(frozen=True)
class SemanticHybridPrediction:
    output: str | None
    operations: int
    evidence: int


class SemanticHybridCausalJudgement:
    def __init__(self, ranker: QuantizedSemanticCausalRanker | None = None) -> None:
        self.symbolic = GenericCausalJudgementV3()
        self.ranker = ranker

    @classmethod
    def from_environment(cls) -> "SemanticHybridCausalJudgement":
        path = os.environ.get("MPM_SEMANTIC_CAUSAL_RANKER")
        return cls(QuantizedSemanticCausalRanker.load(path) if path else None)

    @property
    def description_bits(self) -> int:
        learned = self.ranker.description_bits if self.ranker else 0
        return self.symbolic.description_bits + learned + 8 * 256

    def answer(self, prompt: str) -> SemanticHybridPrediction:
        symbolic = self.symbolic.answer(prompt)
        if self.ranker is None or "\nOptions:" not in prompt:
            return SemanticHybridPrediction(symbolic.output, symbolic.operations, symbolic.evidence)
        output = combine_semantic_prediction(self.ranker, prompt, symbolic.output)
        return SemanticHybridPrediction(
            output,
            symbolic.operations + len(prompt),
            symbolic.evidence + 96,
        )
