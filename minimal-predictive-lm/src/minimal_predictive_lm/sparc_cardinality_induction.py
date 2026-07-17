"""Infer relation cardinality from observed textbook facts before guarding conflicts.

The previous contradiction guard treated every latent relation as functional.  This
extension reuses the learned sparse graph to distinguish relations consistently
observed with one object per subject from relations observed with several objects.
No relation names, hand-written cardinalities, parser, tokenizer, or extra discourse
slots are supplied.
"""
from __future__ import annotations

from collections import Counter

from .sparc_conflict_guard import ConflictGuardLearner


class CardinalityInductionLearner(ConflictGuardLearner):
    """Guard only relations whose one-object behaviour is supported by data."""

    def __init__(self, *, functional_min_subjects: int = 6, **kwargs):
        super().__init__(**kwargs)
        self.functional_min_subjects = functional_min_subjects
        self.functional_relations: set[str] = set()
        self.nonfunctional_relations: set[str] = set()
        self.cardinality_rebuild_reads = 0
        self.cardinality_checks = 0

    def _rebuild_cardinality(self) -> None:
        objects: dict[tuple[str, str], set[str]] = {}
        subjects: Counter[str] = Counter()
        for subject, relation, obj in self.facts:
            self.cardinality_rebuild_reads += 1
            objects.setdefault((subject, relation), set()).add(obj)
        for subject, relation in objects:
            subjects[relation] += 1
        multi = {relation for (_subject, relation), values in objects.items() if len(values) > 1}
        self.nonfunctional_relations = multi
        self.functional_relations = {
            relation
            for relation, count in subjects.items()
            if count >= self.functional_min_subjects and relation not in multi
        }

    def learn_paragraphs(self, records):
        result = super().learn_paragraphs(records)
        self._rebuild_cardinality()
        return result

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
        self.cardinality_checks += 1
        self.conflict_checks += len(existing)
        if relation in self.functional_relations and existing and obj not in existing:
            self.conflict_abstentions += 1
            return False, "abstain-functional-conflict"
        accepted, result = self.read_sentence(resolved, source_id)
        if not accepted:
            return False, result
        self.discourse_subject = subject
        self.discourse_object = obj
        if mechanism != "explicit":
            self.discourse_resolutions += 1
        self._rebuild_cardinality()
        return True, result

    def report(self):
        result = super().report()
        result.update({
            "functional_relations_induced": len(self.functional_relations),
            "nonfunctional_relations_induced": len(self.nonfunctional_relations),
            "functional_min_subjects": self.functional_min_subjects,
            "cardinality_rebuild_reads": self.cardinality_rebuild_reads,
            "cardinality_checks": self.cardinality_checks,
            "relation_cardinalities_supplied": False,
            "relation_names_supplied_for_cardinality": False,
            "cardinality_state_slots_added": 0,
        })
        return result
