from __future__ import annotations

import re

from .english_causal_compiler_v2 import EnglishCausalResolverV2


class EnglishCausalResolverV2Fixed(EnglishCausalResolverV2):
    """V2 with determiner-safe omission-actor extraction."""

    @staticmethod
    def _omission_actor(q: str) -> str:
        because = re.search(
            r"because\s+(?:the\s+)?([a-z][a-z'-]*)\s+(?:did not|didn't|not)",
            q,
        )
        if because:
            return because.group(1)
        direct = re.search(
            r"did\s+(?:the\s+)?([a-z][a-z'-]*)\s+"
            r"(?:not putting|not put|did not put)",
            q,
        )
        if direct:
            return direct.group(1)
        generic = re.search(
            r"\b(?:the\s+)?([a-z][a-z'-]*)\s+not putting oil",
            q,
        )
        return generic.group(1) if generic else ""
