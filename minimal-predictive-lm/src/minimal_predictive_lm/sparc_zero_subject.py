"""Sparse Japanese zero-subject recovery from learned relation templates.

No relation names, parser, tokenizer, or lexical ellipsis list is added.  An
omitted subject and its following bridge are reconstructed from already learned
two-argument templates only when one completion is uniquely supported.
"""
from __future__ import annotations

from .sparc_discourse_focus import DiscourseFocusLearner
from .sparc_open_textbook_learner import _clean


class ZeroSubjectLearner(DiscourseFocusLearner):
    """Two-slot discourse learner with template-gated subject ellipsis recovery."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zero_subject_resolutions = 0
        self.zero_subject_abstentions = 0
        self.zero_subject_template_reads = 0

    @staticmethod
    def _unique_top(rows) -> bool:
        if not rows:
            return False
        if len(rows) == 1:
            return True
        return not (rows[0][0] == rows[1][0] and rows[0][1:4] != rows[1][1:4])

    def _template_completions(self, text: str) -> list[str]:
        """Recover the material between omitted <A> and the visible <B> fragment."""
        normalized = _clean(text)
        completions = set()
        for patterns in self.relation_patterns.values():
            for pattern in patterns:
                self.zero_subject_template_reads += len(pattern)
                if not pattern.startswith("<A>") or "<B>" not in pattern:
                    continue
                b_index = pattern.index("<B>")
                bridge = pattern[len("<A>"):b_index]
                visible_template = pattern[b_index:]
                if self._compile_template(visible_template).fullmatch(normalized):
                    completions.add(self.discourse_subject + bridge + text)
        return sorted(completions)

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
        supported = []
        for completed in self._template_completions(text):
            rows = self._match_sentence(completed)
            if self._unique_top(rows):
                supported.append((completed, rows[0][1:4]))
        if len(supported) != 1:
            self.zero_subject_abstentions += 1
            return text, "explicit"
        self.zero_subject_resolutions += 1
        return supported[0][0], "zero-subject-focus"

    def report(self):
        result = super().report()
        result.update({
            "zero_subject_resolutions": self.zero_subject_resolutions,
            "zero_subject_abstentions": self.zero_subject_abstentions,
            "zero_subject_template_reads": self.zero_subject_template_reads,
            "zero_subject_state_slots_added": 0,
            "ellipsis_lexicon_used": False,
            "parser_used": False,
        })
        return result
