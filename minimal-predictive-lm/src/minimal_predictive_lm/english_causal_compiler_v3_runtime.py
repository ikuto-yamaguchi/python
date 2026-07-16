from __future__ import annotations

import re

from .english_causal_compiler import CausalAnswer
from .english_causal_compiler_v3 import CausalEvidence, EnglishCausalResolverV3


class EnglishCausalResolverV3Runtime(EnglishCausalResolverV3):
    """Final V3 runtime with participant-class-independent conjunctions."""

    def _judge_normality_and_redundancy(
        self, low: str, q: str, evidence: CausalEvidence
    ) -> CausalAnswer | None:
        generic_two_member_conjunction = bool(
            re.search(
                r"\bif\s+(?:both\b|two\s+[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,3}\b)",
                low,
            )
        )
        if generic_two_member_conjunction:
            if evidence.queried_normal and evidence.alternative_abnormal:
                return CausalAnswer(
                    "No", len(low), "lattice:normal-generic-conjunct-suppressed", 4
                )
            if evidence.queried_abnormal:
                return CausalAnswer(
                    "Yes", len(low), "lattice:abnormal-generic-conjunct", 4
                )
        return super()._judge_normality_and_redundancy(low, q, evidence)
