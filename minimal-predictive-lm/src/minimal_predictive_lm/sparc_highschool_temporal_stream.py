from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .sparc_highschool_numeric_stream import IndependentNumericDocumentLearner


_SENTENCE_SPLIT = re.compile(r"(?<=[。！？])")


@dataclass(frozen=True)
class TemporalDocumentResult:
    documents: int
    programs_learned: int
    transitions_found: int
    abstained_documents: int


class TemporalNarrativeLearner(IndependentNumericDocumentLearner):
    """Learn latent state-change programs from chronological Japanese passages.

    The caller supplies complete passages and source IDs only. Observation schemas
    learned from independent streams identify state sentences. An unrecognized
    sentence between two recognized observations is proposed as the event whose
    latent program explains the state difference.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temporal_documents = 0
        self.temporal_transitions = 0
        self.temporal_programs_learned = 0
        self.temporal_abstained_documents = 0
        self.temporal_program_sources: dict[str, set[str]] = {}

    @staticmethod
    def _sentences(text: str) -> tuple[str, ...]:
        rows = tuple(part.strip().rstrip("。！？") for part in _SENTENCE_SPLIT.split(text) if part.strip())
        return rows or (text.strip(),)

    def learn_chronological_document(self, text: str, source_id: str) -> TemporalDocumentResult:
        sentences = self._sentences(text)
        observations = []
        for sentence in sentences:
            observed = self.observe_world([sentence])
            observations.append(observed if observed.accepted == 1 and observed.abstained == 0 else None)

        learned = 0
        transitions = 0
        for index in range(len(sentences) - 2):
            before = observations[index]
            middle = observations[index + 1]
            after = observations[index + 2]
            if before is None or middle is not None or after is None:
                continue
            if before.world == after.world:
                continue
            event_text = sentences[index + 1]
            try:
                program_id = self.teach(event_text, before.world, after.world)
            except ValueError:
                continue
            self.temporal_program_sources.setdefault(program_id, set()).add(source_id)
            learned += 1
            transitions += 1

        self.temporal_documents += 1
        self.temporal_transitions += transitions
        self.temporal_programs_learned += learned
        if transitions == 0:
            self.temporal_abstained_documents += 1
        return TemporalDocumentResult(1, learned, transitions, int(transitions == 0))

    def learn_chronological_documents(self, records: Iterable[tuple[str, str]]) -> TemporalDocumentResult:
        documents = programs = transitions = abstained = 0
        for text, source_id in records:
            result = self.learn_chronological_document(text, source_id)
            documents += result.documents
            programs += result.programs_learned
            transitions += result.transitions_found
            abstained += result.abstained_documents
        return TemporalDocumentResult(documents, programs, transitions, abstained)

    def report(self):
        result = super().report()
        result.update({
            "temporal_documents": self.temporal_documents,
            "temporal_transitions": self.temporal_transitions,
            "temporal_programs_learned": self.temporal_programs_learned,
            "temporal_abstained_documents": self.temporal_abstained_documents,
            "temporal_program_source_links": sum(len(sources) for sources in self.temporal_program_sources.values()),
            "before_after_worlds_supplied": False,
            "event_sentence_labels_supplied": False,
            "chronology_labels_supplied": False,
        })
        return result
