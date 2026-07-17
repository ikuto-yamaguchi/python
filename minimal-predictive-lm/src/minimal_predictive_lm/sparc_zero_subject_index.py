"""Sparse learned index for Japanese zero-subject template recovery.

The baseline scans every learned relation surface whenever a subject is omitted.
This extension derives a compact suffix index from those same learned templates.
No relation names, morphology, parser, or hand-written ellipsis surfaces are added.
"""
from __future__ import annotations

from collections import defaultdict

from .sparc_open_textbook_learner import _clean
from .sparc_zero_subject import ZeroSubjectLearner


class IndexedZeroSubjectLearner(ZeroSubjectLearner):
    """Zero-subject learner with a learned, bounded suffix-to-template index."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zero_subject_suffix_index: dict[str, tuple[tuple[str, str], ...]] = {}
        self.zero_subject_index_build_reads = 0
        self.zero_subject_index_lookups = 0
        self.zero_subject_index_bucket_max = 0

    def _rebuild_zero_subject_index(self) -> None:
        buckets: dict[str, set[tuple[str, str]]] = defaultdict(set)
        reads = 0
        for patterns in self.relation_patterns.values():
            for pattern in patterns:
                reads += len(pattern)
                if not pattern.startswith("<A>") or "<B>" not in pattern:
                    continue
                b_index = pattern.index("<B>")
                bridge = pattern[len("<A>"):b_index]
                visible_template = pattern[b_index:]
                literal_tail = visible_template[len("<B>"):]
                if not literal_tail:
                    continue
                key = literal_tail[-min(4, len(literal_tail)):]
                buckets[key].add((bridge, visible_template))
        self.zero_subject_suffix_index = {
            key: tuple(sorted(values)) for key, values in sorted(buckets.items())
        }
        self.zero_subject_index_build_reads += reads
        self.zero_subject_index_bucket_max = max(
            (len(values) for values in self.zero_subject_suffix_index.values()),
            default=0,
        )

    def learn_paragraphs(self, records):
        result = super().learn_paragraphs(records)
        self._rebuild_zero_subject_index()
        return result

    def _template_completions(self, text: str) -> list[str]:
        normalized = _clean(text)
        candidates: set[tuple[str, str]] = set()
        for width in range(1, min(4, len(normalized)) + 1):
            key = normalized[-width:]
            bucket = self.zero_subject_suffix_index.get(key, ())
            self.zero_subject_index_lookups += 1
            candidates.update(bucket)
        completions = set()
        for bridge, visible_template in candidates:
            self.zero_subject_template_reads += len(visible_template)
            if self._compile_template(visible_template).fullmatch(normalized):
                completions.add(self.discourse_subject + bridge + text)
        return sorted(completions)

    def report(self):
        result = super().report()
        result.update({
            "zero_subject_suffix_index_keys": len(self.zero_subject_suffix_index),
            "zero_subject_suffix_index_entries": sum(
                len(values) for values in self.zero_subject_suffix_index.values()
            ),
            "zero_subject_index_build_reads": self.zero_subject_index_build_reads,
            "zero_subject_index_lookups": self.zero_subject_index_lookups,
            "zero_subject_index_bucket_max": self.zero_subject_index_bucket_max,
            "handwritten_suffixes_used": False,
            "state_slots_added": 0,
        })
        return result
