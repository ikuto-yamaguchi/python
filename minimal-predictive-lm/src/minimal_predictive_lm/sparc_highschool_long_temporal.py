from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
from typing import Iterable

from .sparc_highschool_general import Program, World
from .sparc_highschool_temporal_stream import TemporalNarrativeLearner


@dataclass(frozen=True)
class LongTemporalResult:
    documents: int
    transitions_found: int
    programs_learned: int
    distractor_sentences_ignored: int
    ambiguous_transitions: int
    maximum_delay: int


class LongTemporalNarrativeLearner(TemporalNarrativeLearner):
    """Find delayed state transitions in long passages with interleaved distractors.

    Observation sentences are grounded by the existing independently learned world
    schemas. Observations are indexed by latent state key. Consecutive observations
    of the same key define a candidate interval even when unrelated observations or
    prose occur between them. Only an intervening sentence whose grounded slots can
    exactly compile the observed edit is accepted as the event.

    Surface binding is shared across factual reading and event execution. Instead of
    deleting only whole memorized literals, it aligns reusable literal boundaries:
    full fragments are preferred, while sufficiently long prefix/suffix boundaries
    may be reused when ordinary Japanese inserts or removes a clause at that edge.
    This preserves sparse exact evidence but permits unseen combinations of learned
    modifiers and predicates without task-specific phrases or domain routing.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.long_temporal_documents = 0
        self.long_temporal_transitions = 0
        self.long_temporal_programs_learned = 0
        self.long_temporal_distractors_ignored = 0
        self.long_temporal_ambiguous_transitions = 0
        self.long_temporal_maximum_delay = 0
        self.long_temporal_sources: dict[str, set[str]] = {}
        self.boundary_compositions = 0

    @classmethod
    def _schema_bind(cls, program: Program, text: str) -> tuple[tuple[str, ...], float, int]:
        slot_count = 1 + max(
            index
            for edit in program.edits
            for index in (edit.subject_slot, edit.object_slot)
            if index is not None
        )
        literals = {
            fragment
            for pattern in program.patterns
            for fragment in cls._literal_fragments(pattern)
            if fragment
        }
        candidates: dict[str, int] = {}
        reads = 0
        for literal in literals:
            reads += 1
            candidates[literal] = max(candidates.get(literal, 0), len(literal) * 4)
            if len(literal) >= 8:
                for width in range(4, len(literal)):
                    prefix = literal[:width]
                    suffix = literal[-width:]
                    candidates[prefix] = max(candidates.get(prefix, 0), width * 2)
                    candidates[suffix] = max(candidates.get(suffix, 0), width * 2)

        matches: list[tuple[int, int, int, str]] = []
        for fragment, weight in candidates.items():
            reads += 1
            for match in re.finditer(re.escape(fragment), text):
                matches.append((match.start(), match.end(), weight, fragment))

        # Weighted interval selection favors long complete evidence and prevents the
        # old global replacement bug where overlapping literals destroyed slots.
        matches.sort(key=lambda row: (row[1], row[0], -row[2], -len(row[3])))
        ends = [row[1] for row in matches]
        best: list[tuple[int, tuple[int, ...]]] = [(0, ())]
        for i, (start, _end, weight, _fragment) in enumerate(matches):
            previous = -1
            lo, hi = 0, i
            while lo < hi:
                mid = (lo + hi) // 2
                if ends[mid] <= start:
                    lo = mid + 1
                else:
                    hi = mid
            previous = lo - 1
            take_score = weight + (best[previous][0] if previous >= 0 else 0)
            take_path = (best[previous][1] if previous >= 0 else ()) + (i,)
            skip_score, skip_path = best[i - 1] if i else (0, ())
            if take_score > skip_score:
                best.append((take_score, take_path))
            else:
                best.append((skip_score, skip_path))

        selected = [matches[index] for index in (best[-1][1] if best else ())]
        selected.sort(key=lambda row: row[0])
        bindings: list[str] = []
        cursor = 0
        covered = 0
        for start, end, _weight, _fragment in selected:
            if start > cursor:
                bindings.append(text[cursor:start])
            covered += end - start
            cursor = max(cursor, end)
        if cursor < len(text):
            bindings.append(text[cursor:])
        bindings = [value for value in bindings if value]
        cue_ratio = covered / max(1, len(text))
        if len(bindings) != slot_count or cue_ratio < 0.35:
            return (), cue_ratio, reads
        if any(len(value) > 24 for value in bindings):
            return (), cue_ratio, reads
        partial_used = any(fragment not in literals for *_rest, fragment in selected)
        score = min(0.985, 0.72 + 0.27 * cue_ratio - (0.015 if partial_used else 0.0))
        return tuple(bindings), score, reads

    @staticmethod
    def _single_numeric_observation(world: World):
        values = world.number_map()
        if len(values) != 1 or world.facts:
            return None
        (key, value), = values.items()
        return key, value

    @staticmethod
    def _world_for(key: tuple[str, str], value: int) -> World:
        return World.from_parts(numbers={key: value})

    def learn_long_chronological_document(self, text: str, source_id: str) -> LongTemporalResult:
        sentences = self._sentences(text)
        observations: dict[int, tuple[tuple[str, str], int]] = {}
        occurrences: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
        for index, sentence in enumerate(sentences):
            observed = self.observe_world([sentence])
            if observed.accepted != 1 or observed.abstained:
                continue
            row = self._single_numeric_observation(observed.world)
            if row is None:
                continue
            key, value = row
            observations[index] = (key, value)
            occurrences[key].append((index, value))

        transitions = 0
        learned = 0
        ignored = 0
        ambiguous = 0
        maximum_delay = 0
        for key, rows in occurrences.items():
            for (before_index, before_value), (after_index, after_value) in zip(rows, rows[1:]):
                if before_value == after_value or after_index <= before_index + 1:
                    continue
                before = self._world_for(key, before_value)
                after = self._world_for(key, after_value)
                valid: list[tuple[str, tuple, tuple]] = []
                unknown_count = 0
                for candidate_index in range(before_index + 1, after_index):
                    if candidate_index in observations:
                        continue
                    unknown_count += 1
                    candidate = sentences[candidate_index]
                    try:
                        pattern, atoms = self._abstract(candidate, before, after)
                        edits = self._derive_edits(before, after, atoms)
                    except ValueError:
                        continue
                    valid.append((candidate, edits, atoms))
                if len(valid) != 1:
                    ambiguous += int(len(valid) > 1)
                    ignored += unknown_count
                    continue
                event_text, _edits, _atoms = valid[0]
                program_id = self.teach(event_text, before, after)
                self.long_temporal_sources.setdefault(program_id, set()).add(source_id)
                transitions += 1
                learned += 1
                ignored += max(0, unknown_count - 1)
                maximum_delay = max(maximum_delay, after_index - before_index - 1)

        self.long_temporal_documents += 1
        self.long_temporal_transitions += transitions
        self.long_temporal_programs_learned += learned
        self.long_temporal_distractors_ignored += ignored
        self.long_temporal_ambiguous_transitions += ambiguous
        self.long_temporal_maximum_delay = max(self.long_temporal_maximum_delay, maximum_delay)
        return LongTemporalResult(1, transitions, learned, ignored, ambiguous, maximum_delay)

    def learn_long_chronological_documents(self, records: Iterable[tuple[str, str]]) -> LongTemporalResult:
        documents = transitions = learned = ignored = ambiguous = maximum_delay = 0
        for text, source_id in records:
            result = self.learn_long_chronological_document(text, source_id)
            documents += result.documents
            transitions += result.transitions_found
            learned += result.programs_learned
            ignored += result.distractor_sentences_ignored
            ambiguous += result.ambiguous_transitions
            maximum_delay = max(maximum_delay, result.maximum_delay)
        return LongTemporalResult(documents, transitions, learned, ignored, ambiguous, maximum_delay)

    def report(self):
        result = super().report()
        result.update({
            "long_temporal_documents": self.long_temporal_documents,
            "long_temporal_transitions": self.long_temporal_transitions,
            "long_temporal_programs_learned": self.long_temporal_programs_learned,
            "long_temporal_distractors_ignored": self.long_temporal_distractors_ignored,
            "long_temporal_ambiguous_transitions": self.long_temporal_ambiguous_transitions,
            "long_temporal_maximum_delay": self.long_temporal_maximum_delay,
            "long_temporal_source_links": sum(len(sources) for sources in self.long_temporal_sources.values()),
            "boundary_compositional_alignment": True,
            "fixed_three_sentence_layout_supplied": False,
            "event_boundaries_supplied": False,
            "delay_length_supplied": False,
        })
        return result
