from __future__ import annotations

from dataclasses import dataclass
import os

from .generic_causal_judgement_v3 import GenericCausalJudgementV3
from .learned_causal_ranker import QuantizedCausalRanker, combine_causal_prediction


@dataclass(frozen=True)
class HybridCausalPrediction:
    output: str | None
    operations: int
    evidence: int


class HybridCausalJudgement:
    """One causal interface combining induced lexical evidence and causal structure."""

    def __init__(self, ranker: QuantizedCausalRanker | None = None) -> None:
        self.symbolic = GenericCausalJudgementV3()
        self.ranker = ranker

    @classmethod
    def from_environment(cls) -> "HybridCausalJudgement":
        path = os.environ.get("MPM_CAUSAL_RANKER")
        return cls(QuantizedCausalRanker.load(path) if path else None)

    @property
    def description_bits(self) -> int:
        learned = self.ranker.description_bits if self.ranker is not None else 0
        return self.symbolic.description_bits + learned + 8 * 256

    def answer(self, prompt: str) -> HybridCausalPrediction:
        symbolic = self.symbolic.answer(prompt)
        if self.ranker is None:
            return HybridCausalPrediction(symbolic.output, symbolic.operations, symbolic.evidence)
        if "\nOptions:" not in prompt or "Yes" not in prompt or "No" not in prompt:
            return HybridCausalPrediction(symbolic.output, symbolic.operations, symbolic.evidence)
        output = combine_causal_prediction(self.ranker, prompt, symbolic.output)
        return HybridCausalPrediction(
            output,
            symbolic.operations + len(prompt),
            symbolic.evidence + len(self.ranker.mechanism.weights),
        )
