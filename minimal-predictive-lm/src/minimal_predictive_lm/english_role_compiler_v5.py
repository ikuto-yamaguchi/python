from __future__ import annotations

import re

from . import english_role_compiler_v4 as _v4
from .english_role_compiler_v3 import _option_entity_v3


def _possessor_first_option_entity(option: str, mentions: tuple[str, ...]) -> str | None:
    lower = _v4._normalise(option)
    match = re.search(r"\b(?:the\s+|my\s+)?([a-z][a-z-]*)['’](?:s)?\s+[a-z]", lower)
    if match is not None:
        possessor = match.group(1)
        if possessor in mentions:
            return possessor
    return _option_entity_v3(option, mentions)


# The V4 compiler resolves this global at call time. Replace only candidate
# normalization; all frozen role rules and weights remain unchanged.
_v4._option_entity_v4 = _possessor_first_option_entity
EnglishRoleReferenceResolverV5 = _v4.EnglishRoleReferenceResolverV4
compile_reference_prompt_v5 = _v4.compile_reference_prompt_v4
