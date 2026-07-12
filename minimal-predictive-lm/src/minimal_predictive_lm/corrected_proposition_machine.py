from __future__ import annotations

import re

from .generic_proposition_machine import (
    BoolExpr,
    GenericPropositionMachine,
    any_of,
    neg,
)


class CorrectedPropositionMachine(GenericPropositionMachine):
    """Phase 16c normalization correction for explicit none-of disjunctions."""

    def _expr(self, text: str) -> BoolExpr:
        cleaned = self._clean(text)
        match = re.fullmatch(
            r"none of (?:this|these):\s*(.+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match:
            members = self._split_top(match.group(1), "or")
            if len(members) > 1:
                return neg(any_of(*(self._expr(member) for member in members)))
        return super()._expr(text)
