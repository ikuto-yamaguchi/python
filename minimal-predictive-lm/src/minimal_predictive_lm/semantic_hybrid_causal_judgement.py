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
        return self.symbolic.description_bits + learned + 8 * 384

    def _eligible(self, prompt: str) -> bool:
        split = self.symbolic._split(prompt)
        if split is None:
            return False
        _story, question = split
        return any(
            marker in question
            for marker in (
                " cause ",
                " caused ",
                " because ",
                " intentionally ",
                " intend ",
                " intended ",
            )
        ) or question.startswith(("did ", "was ")) and any(
            marker in question for marker in ("cause", "intentional", "because")
        )

    def answer(self, prompt: str) -> SemanticHybridPrediction:
        symbolic = self.symbolic.answer(prompt)
        if self.ranker is None or not self._eligible(prompt):
            return SemanticHybridPrediction(symbolic.output, symbolic.operations, symbolic.evidence)
        output = combine_semantic_prediction(self.ranker, prompt, symbolic.output)
        return SemanticHybridPrediction(
            output,
            symbolic.operations + len(prompt),
            symbolic.evidence + 96,
        )
