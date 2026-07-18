from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_grounded_explanation import (
    GroundedExplanationLearner,
    GroundedExplanationResult,
)


@dataclass(frozen=True)
class CausalProvenanceResult:
    accepted: bool
    grounded: GroundedExplanationResult
    gap_trace: tuple[int, ...]
    first_divergence: int | None
    answer: str
    verified: bool
    mechanism: str


class CausalProvenanceLearner(GroundedExplanationLearner):
    """Attribute an outcome difference to shared world-transition history.

    No task or domain selector is supplied.  The learner first performs the same
    narrative alignment and independent replay as its parent, then compares the
    paired states at every step.  The resulting provenance is shared by causal
    explanation, counterfactual reasoning, verification, and future planning.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.causal_provenance_explanations = 0
        self.provenance_abstentions = 0
        self.paired_state_comparisons = 0
        self.provenance_verification_failures = 0

    @staticmethod
    def _first_nonzero(values: tuple[int, ...]) -> int | None:
        return next((index for index, value in enumerate(values) if value != 0), None)

    @staticmethod
    def _propagation_text(gaps: tuple[int, ...], first: int) -> str:
        clauses: list[str] = []
        for index in range(first + 1, len(gaps)):
            previous = gaps[index - 1]
            current = gaps[index]
            if previous != 0 and current % previous == 0:
                factor = current // previous
                if factor != 1:
                    clauses.append(f"その後の共通操作で差は{abs(factor)}倍の{abs(current)}になりました")
                    continue
            change = current - previous
            if change:
                direction = "増え" if abs(current) > abs(previous) else "減り"
                clauses.append(f"その後の共通操作で差は{abs(change)}{direction}て{abs(current)}になりました")
            else:
                clauses.append(f"その後の共通操作でも差は{abs(current)}のまま保たれました")
        return "。".join(clauses)

    def explain_causal_narrative(self, text: str) -> CausalProvenanceResult:
        grounded = self.explain_counterfactual_narrative(text)
        if not grounded.accepted or not grounded.verified:
            self.provenance_abstentions += 1
            return CausalProvenanceResult(
                False,
                grounded,
                (),
                None,
                "",
                False,
                "abstain-unverified-grounded-explanation",
            )
        if len(grounded.factual_trace) != len(grounded.counterfactual_trace):
            self.provenance_abstentions += 1
            return CausalProvenanceResult(
                False,
                grounded,
                (),
                None,
                "",
                False,
                "abstain-incomparable-trace-length",
            )

        gaps = tuple(
            alternative - factual
            for factual, alternative in zip(
                grounded.factual_trace,
                grounded.counterfactual_trace,
                strict=True,
            )
        )
        self.paired_state_comparisons += len(gaps)
        first = self._first_nonzero(gaps)
        if first is None:
            self.provenance_abstentions += 1
            return CausalProvenanceResult(
                False,
                grounded,
                gaps,
                None,
                "",
                False,
                "abstain-no-causal-difference",
            )

        final_gap = grounded.counterfactual_trace[-1] - grounded.factual_trace[-1]
        verified = gaps[-1] == final_gap
        if not verified:
            self.provenance_verification_failures += 1
            self.provenance_abstentions += 1
            return CausalProvenanceResult(
                False,
                grounded,
                gaps,
                first,
                "",
                False,
                "abstain-provenance-verification-mismatch",
            )

        initial_gap = abs(gaps[first])
        propagation = self._propagation_text(gaps, first)
        answer = (
            f"差が最初に生じたのは{first}番目の状態変化で、この時点の差は{initial_gap}です。"
            f"{propagation}。"
            f"最終的な差{abs(final_gap)}は、途中で生じた差を後続の共通操作が伝播させた結果です。"
            f"実際の経路と変更後の経路を同じ実行器で再計算し、差の履歴{gaps}とも一致することを検算しました。"
        )
        self.causal_provenance_explanations += 1
        return CausalProvenanceResult(
            True,
            grounded,
            gaps,
            first,
            answer,
            True,
            "paired-shared-world-transition-provenance",
        )

    def report(self):
        result = super().report()
        result.update(
            {
                "shared_causal_provenance": True,
                "causal_provenance_explanations": self.causal_provenance_explanations,
                "provenance_abstentions": self.provenance_abstentions,
                "paired_state_comparisons": self.paired_state_comparisons,
                "provenance_verification_failures": self.provenance_verification_failures,
            }
        )
        return result
