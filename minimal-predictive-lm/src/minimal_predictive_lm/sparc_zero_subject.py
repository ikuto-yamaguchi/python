"""Sparse Japanese zero-subject recovery from learned relation templates.

No relation names, parser, tokenizer, or lexical ellipsis list is added.  An
omitted subject is supplied from the existing discourse focus only when that
single completion matches an already learned two-argument sentence template.
"""
from __future__ import annotations

from .sparc_discourse_focus import DiscourseFocusLearner


class ZeroSubjectLearner(DiscourseFocusLearner):
    """Two-slot discourse learner with template-gated subject ellipsis recovery."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zero_subject_resolutions = 0
        self.zero_subject_abstentions = 0

    @staticmethod
    def _unique_top(rows) -> bool:
        if not rows:
            return False
        if len(rows) == 1:
            return True
        return not (rows[0][0] == rows[1][0] and rows[0][1:4] != rows[1][1:4])

    def _resolve_discourse(self, sentence: str) -> tuple[str | None, str]:
        resolved, mechanism = super()._resolve_discourse(sentence)
        if resolved is None or mechanism != "explicit":
            return resolved, mechanism
        text = resolved.strip()
        if self._match_sentence(text):
            return text, "explicit"
        if self.discourse_subject is None:
            self.zero_subject_abstentions += 1
            return text, "explicit"
        completed = self.discourse_subject + text
        rows = self._match_sentence(completed)
        if not self._unique_top(rows):
            self.zero_subject_abstentions += 1
            return text, "explicit"
        self.zero_subject_resolutions += 1
        return completed, "zero-subject-focus"

    def report(self):
        result = super().report()
        result.update({
            "zero_subject_resolutions": self.zero_subject_resolutions,
            "zero_subject_abstentions": self.zero_subject_abstentions,
            "zero_subject_state_slots_added": 0,
            "ellipsis_lexicon_used": False,
            "parser_used": False,
        })
        return result
