"""Sparse contradiction guard for continual Japanese textbook learning.

The guard reuses the learned relation graph. A new sentence is rejected before
mutation when it would give one subject two different objects for the same
latent relation. No truth labels, relation names, parser, or extra memory slots
are introduced.
"""
from __future__ import annotations

from .sparc_zero_subject_index import IndexedZeroSubjectLearner


class ConflictGuardLearner(IndexedZeroSubjectLearner):
    """Reject locally contradictory facts while preserving ordinary learning."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conflict_abstentions = 0
        self.conflict_checks = 0

    def read_discourse_sentence(self, sentence: str, source_id: str):
        resolved, mechanism = self._resolve_discourse(sentence)
        if resolved is None:
            self.discourse_abstentions += 1
            return False, mechanism
        rows = self._match_sentence(resolved)
        if not rows:
            return False, "abstain-unknown-surface"
        top = rows[0]
        if len(rows) > 1 and top[:4] != rows[1][:4] and top[0] == rows[1][0]:
            return False, "abstain-ambiguous-surface"
        _, relation, subject, obj, _ = top
        existing = self.out_index.get(subject, {}).get(relation, set())
        self.conflict_checks += len(existing)
        if existing and obj not in existing:
            self.conflict_abstentions += 1
            return False, "abstain-conflicting-fact"
        accepted, result = self.read_sentence(resolved, source_id)
        if not accepted:
            return False, result
        self.discourse_subject = subject
        self.discourse_object = obj
        if mechanism != "explicit":
            self.discourse_resolutions += 1
        return True, result

    def report(self):
        result = super().report()
        result.update({
            "conflict_abstentions": self.conflict_abstentions,
            "conflict_checks": self.conflict_checks,
            "conflict_state_slots_added": 0,
            "truth_labels_supplied": False,
            "relation_names_supplied_for_conflicts": False,
        })
        return result
