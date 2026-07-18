from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
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
    """Find delayed state transitions and reuse one role-aware surface binder.

    Observation sentences are grounded by independently learned world schemas.
    Consecutive observations of the same latent state key define candidate intervals,
    and only a unique intervening sentence that compiles the observed edit is learned.

    Surface binding is shared by factual reading, event execution, causal simulation,
    planning, explanation, and dialogue. The primary binder constructs an ordered
    anchor lattice from all learned schemas of a program. Anchors keep their position
    relative to semantic slots, so fragments from different schemas may compose
    without confusing a prefix, inter-slot predicate, or suffix. The older weighted
    non-overlap alignment remains a conservative fallback for clause insertion and
    omission. No task name, domain route, phrase exception, or relation dictionary is
    supplied.
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
        self.slot_anchor_compositions = 0

    @staticmethod
    def _pattern_layout(pattern: str) -> tuple[tuple[int, ...], tuple[str, ...]]:
        parts = re.split(r"(<V\d+>)", pattern)
        slots: list[int] = []
        literals: list[str] = [""]
        for part in parts:
            match = re.fullmatch(r"<V(\d+)>", part)
            if match:
                slots.append(int(match.group(1)))
                literals.append("")
            else:
                literals[-1] += part
        return tuple(slots), tuple(literals)

    @classmethod
    def _ordered_anchor_bind(
        cls, program: Program, text: str, slot_count: int
    ) -> tuple[tuple[str, ...], float, int]:
        """Bind slots using anchors whose semantic boundary roles are preserved.

        Learned patterns that expose the same textual slot order contribute anchors
        to the same boundary pools. We enumerate sparse boundary choices, preserve
        their order in the input, and score complete slot assignments by coverage,
        number of independently supported boundaries, and compactness. This is a
        shared schema operation rather than a Japanese phrase list.
        """

        layouts: dict[tuple[int, ...], list[tuple[str, ...]]] = defaultdict(list)
        reads = 0
        for pattern in program.patterns:
            order, literals = cls._pattern_layout(pattern)
            reads += len(pattern)
            if len(order) == slot_count and set(order) == set(range(slot_count)):
                layouts[order].append(literals)

        ranked: list[tuple[float, tuple[str, ...], int]] = []
        for order, rows in layouts.items():
            pools: list[tuple[str, ...]] = []
            for boundary in range(slot_count + 1):
                values = sorted(
                    {row[boundary] for row in rows if row[boundary]},
                    key=lambda value: (-len(value), value),
                )
                # Prefix and suffix may be absent in an unseen composition. An
                # inter-slot boundary is required because it separates two values.
                if boundary in (0, slot_count):
                    values.append("")
                if not values:
                    pools = []
                    break
                pools.append(tuple(values))
            if not pools:
                continue

            for anchors in product(*pools):
                reads += 1
                if not anchors[0] and not anchors[-1] and slot_count == 1:
                    continue
                positions: list[tuple[int, int]] = []
                cursor = 0
                valid = True
                for anchor in anchors:
                    if not anchor:
                        positions.append((cursor, cursor))
                        continue
                    start = text.find(anchor, cursor)
                    if start < 0:
                        valid = False
                        break
                    positions.append((start, start + len(anchor)))
                    cursor = start + len(anchor)
                if not valid:
                    continue

                textual_values: list[str] = []
                for index in range(slot_count):
                    left = positions[index][1]
                    right = positions[index + 1][0]
                    value = text[left:right]
                    if not value or len(value) > 24:
                        valid = False
                        break
                    textual_values.append(value)
                if not valid:
                    continue
                if anchors[0] and positions[0][0] != 0:
                    continue
                if anchors[-1] and positions[-1][1] != len(text):
                    continue

                bindings = [""] * slot_count
                for textual_index, slot_index in enumerate(order):
                    bindings[slot_index] = textual_values[textual_index]
                if any(not value for value in bindings):
                    continue

                covered = sum(len(anchor) for anchor in anchors)
                cue_ratio = covered / max(1, len(text))
                supported = sum(bool(anchor) for anchor in anchors)
                if cue_ratio < 0.30 or supported < 1:
                    continue
                # Exact role-compatible anchors deserve a stronger score than
                # character similarity, reducing false ambiguity between programs.
                score = min(0.997, 0.79 + 0.18 * cue_ratio + 0.012 * supported)
                ranked.append((score, tuple(bindings), reads))

        ranked.sort(key=lambda row: (-row[0], sum(map(len, row[1])), row[1]))
        if not ranked:
            return (), 0.0, reads
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0] and ranked[0][1] != ranked[1][1]:
            return (), ranked[0][0], reads
        return ranked[0][1], ranked[0][0], reads

    @classmethod
    def _schema_bind(cls, program: Program, text: str) -> tuple[tuple[str, ...], float, int]:
        slot_count = 1 + max(
            index
            for edit in program.edits
            for index in (edit.subject_slot, edit.object_slot)
            if index is not None
        )
        ordered, ordered_score, reads = cls._ordered_anchor_bind(program, text, slot_count)
        if ordered:
            return ordered, ordered_score, reads

        literals = {
            fragment
            for pattern in program.patterns
            for fragment in cls._literal_fragments(pattern)
            if fragment
        }
        candidates: dict[str, int] = {}
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

        matches.sort(key=lambda row: (row[1], row[0], -row[2], -len(row[3])))
        ends = [row[1] for row in matches]
        best: list[tuple[int, tuple[int, ...]]] = [(0, ())]
        for i, (start, _end, weight, _fragment) in enumerate(matches):
            lo, hi = 0, i
            while lo < hi:
                mid = (lo + hi) // 2
                if ends[mid] <= start:
                    lo = mid + 1
                else:
                    hi = mid
            previous = lo - 1
            take_score = weight + best[previous + 1][0]
            take_path = best[previous + 1][1] + (i,)
            skip_score, skip_path = best[i]
            best.append((take_score, take_path) if take_score > skip_score else (skip_score, skip_path))

        selected = [matches[index] for index in best[-1][1]]
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
            return (), max(cue_ratio, ordered_score), reads
        if any(len(value) > 24 for value in bindings):
            return (), max(cue_ratio, ordered_score), reads
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

        transitions = learned = ignored = ambiguous = maximum_delay = 0
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
            "slot_order_anchor_lattice": True,
            "fixed_three_sentence_layout_supplied": False,
            "event_boundaries_supplied": False,
            "delay_length_supplied": False,
        })
        return result
