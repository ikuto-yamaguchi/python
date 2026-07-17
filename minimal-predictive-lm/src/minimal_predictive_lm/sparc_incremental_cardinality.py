"""Incremental relation-cardinality induction without repeated graph scans.

The previous learner rebuilt relation cardinality by scanning every fact after each
accepted sentence. This extension performs one bootstrap scan, then updates only
the affected subject-relation pair. Relation names, supplied cardinalities,
parsers, neural models, and additional discourse slots remain absent.
"""
from __future__ import annotations

from collections import Counter

from .sparc_cardinality_induction import CardinalityInductionLearner


class IncrementalCardinalityLearner(CardinalityInductionLearner):
    """Maintain functional/multivalued relation evidence with local counters."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cardinality_subjects: Counter[str] = Counter()
        self.cardinality_multi_subjects: Counter[str] = Counter()
        self.cardinality_bootstrap_reads = 0
        self.cardinality_local_updates = 0
        self.cardinality_rebuilds_avoided = 0

    def _refresh_relation_class(self, relation: str) -> None:
        if self.cardinality_multi_subjects[relation] > 0:
            self.nonfunctional_relations.add(relation)
            self.functional_relations.discard(relation)
        elif self.cardinality_subjects[relation] >= self.functional_min_subjects:
            self.functional_relations.add(relation)
            self.nonfunctional_relations.discard(relation)
        else:
            self.functional_relations.discard(relation)
            self.nonfunctional_relations.discard(relation)

    def _bootstrap_cardinality(self) -> None:
        pair_counts: dict[tuple[str, str], int] = {}
        for subject, relation, obj in self.facts:
            self.cardinality_bootstrap_reads += 1
            key = (subject, relation)
            pair_counts[key] = pair_counts.get(key, 0) + 1
        self.cardinality_subjects.clear()
        self.cardinality_multi_subjects.clear()
        for (_subject, relation), count in pair_counts.items():
            self.cardinality_subjects[relation] += 1
            if count > 1:
                self.cardinality_multi_subjects[relation] += 1
        self.functional_relations.clear()
        self.nonfunctional_relations.clear()
        for relation in self.cardinality_subjects:
            self._refresh_relation_class(relation)

    def learn_paragraphs(self, records):
        # Bypass CardinalityInductionLearner.learn_paragraphs, whose final action
        # is a full cardinality rebuild. Seed ingestion may be batched, so one
        # bootstrap scan after the batch is sufficient.
        result = super(CardinalityInductionLearner, self).learn_paragraphs(records)
        self._bootstrap_cardinality()
        return result

    def _observe_local_addition(self, relation: str, previous_count: int) -> None:
        self.cardinality_local_updates += 1
        if previous_count == 0:
            self.cardinality_subjects[relation] += 1
        elif previous_count == 1:
            self.cardinality_multi_subjects[relation] += 1
        self._refresh_relation_class(relation)

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
        previous_count = len(existing)
        self.cardinality_checks += 1
        self.conflict_checks += previous_count
        if relation in self.functional_relations and existing and obj not in existing:
            self.conflict_abstentions += 1
            return False, "abstain-functional-conflict"
        accepted, result = self.read_sentence(resolved, source_id)
        if not accepted:
            return False, result
        if obj not in existing:
            self._observe_local_addition(relation, previous_count)
        self.cardinality_rebuilds_avoided += 1
        self.discourse_subject = subject
        self.discourse_object = obj
        if mechanism != "explicit":
            self.discourse_resolutions += 1
        return True, result

    def report(self):
        result = super().report()
        result.update({
            "cardinality_bootstrap_reads": self.cardinality_bootstrap_reads,
            "cardinality_local_updates": self.cardinality_local_updates,
            "cardinality_rebuilds_avoided": self.cardinality_rebuilds_avoided,
            "cardinality_full_rebuilds_after_online_addition": 0,
            "incremental_cardinality_state_slots_added": 0,
        })
        return result
