"""Minimal discourse-focus extension for the boundary-free SPARC learner.

The extension keeps only the last accepted subject and object.  It resolves a
small, explicit class of Japanese textbook anaphora before the already learned
relation templates are applied.  No tokenizer, parser, language model, or
relation-specific rule is added.
"""
from __future__ import annotations

from .sparc_open_textbook_learner import OpenTextbookLearner, _split_sentences


class DiscourseFocusLearner(OpenTextbookLearner):
    """OpenTextbookLearner with two-slot paragraph-local discourse memory."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.discourse_subject: str | None = None
        self.discourse_object: str | None = None
        self.discourse_resolutions = 0
        self.discourse_abstentions = 0

    def reset_discourse(self) -> None:
        self.discourse_subject = None
        self.discourse_object = None

    def _resolve_discourse(self, sentence: str) -> tuple[str | None, str]:
        text = sentence.strip()
        for pronoun in ("これ", "それ"):
            if text.startswith(pronoun + "は"):
                if self.discourse_subject is None:
                    return None, "abstain-unbound-subject-anaphora"
                return self.discourse_subject + text[len(pronoun):], "subject-focus"
        for phrase in ("その対象", "この対象"):
            if text.startswith(phrase + "は"):
                if self.discourse_object is None:
                    return None, "abstain-unbound-object-anaphora"
                return self.discourse_object + text[len(phrase):], "object-focus"
        return text, "explicit"

    def read_discourse_sentence(self, sentence: str, source_id: str):
        resolved, mechanism = self._resolve_discourse(sentence)
        if resolved is None:
            self.discourse_abstentions += 1
            return False, mechanism
        rows = self._match_sentence(resolved)
        accepted, relation = self.read_sentence(resolved, source_id)
        if not accepted:
            return False, relation
        if rows:
            _, _, subject, obj, _ = rows[0]
            self.discourse_subject = subject
            self.discourse_object = obj
        if mechanism != "explicit":
            self.discourse_resolutions += 1
        return True, relation

    def read_passage(self, passage: str, source_id: str):
        results = []
        self.reset_discourse()
        for index, sentence in enumerate(_split_sentences(passage), 1):
            results.append(self.read_discourse_sentence(sentence, f"{source_id}:{index}"))
        return results

    def report(self):
        result = super().report()
        result.update({
            "discourse_state_slots": 2,
            "discourse_resolutions": self.discourse_resolutions,
            "discourse_abstentions": self.discourse_abstentions,
            "parser_used": False,
            "language_model_used": False,
        })
        return result
