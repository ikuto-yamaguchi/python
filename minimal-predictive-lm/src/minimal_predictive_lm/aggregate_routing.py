from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


_KEY_VALUE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_.-]*\s*=\s*[^\s,]+")
_NUMBER = re.compile(r"[-+]?\d+(?:/\d+|\.\d+)?")


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    reason: str
    number_count: int
    character_count: int


def phase12_prompt_eligibility(prompt: str) -> EligibilityDecision:
    """Guard the compact Phase 12 learner from sparse numbers in arbitrary prose.

    Phase 12 was calibrated on explicit key/value records and compact arithmetic
    questions. A lone year, product number, version, or model identifier inside a
    long document is not sufficient evidence that a Phase 12 numeric program applies.
    """

    normalized = unicodedata.normalize("NFKC", prompt).strip()
    numbers = tuple(_NUMBER.findall(normalized))
    if _KEY_VALUE.search(normalized):
        return EligibilityDecision(True, "explicit_key_value_record", len(numbers), len(normalized))
    if "\n" in normalized:
        return EligibilityDecision(False, "multiline_unstructured_text", len(numbers), len(normalized))
    if len(normalized) > 160:
        return EligibilityDecision(False, "long_unstructured_text", len(numbers), len(normalized))
    if len(numbers) < 2:
        return EligibilityDecision(False, "insufficient_numeric_arguments", len(numbers), len(normalized))
    return EligibilityDecision(True, "compact_multi_argument_text", len(numbers), len(normalized))
