from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
import json
from math import exp, perm
from pathlib import Path
import unicodedata
from typing import Iterable, Mapping, Sequence

from .phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    LinearFactorizationModel,
    induce_linear_factorization,
)


AnonymousState = tuple[int, ...]
FrameTemplate = str

ENTITY_LEXEMES = ("アキ", "ボブ", "チカ", "ダイ")
ACTION_LEXEMES = ("渡す", "受ける", "写す", "移す")
ACTION_BITS = {"渡す": True, "受ける": False, "写す": True, "移す": False}
FRAME_SPECS = {
    0: ("{left}が{right}に{action}", False),
    1: ("{left}から{right}へ{action}", False),
    2: ("{left}に{right}が{action}", True),
    3: ("{left}へ{right}から{action}", True),
}
IDENTIFYING_PAIRS = (
    ("渡す", 0),
    ("渡す", 1),
    ("渡す", 2),
    ("渡す", 3),
    ("受ける", 0),
    ("受ける", 1),
    ("写す", 0),
    ("写す", 1),
    ("移す", 0),
    ("移す", 1),
)
REPETITIONS = 25
FLIPS_PER_GROUP = 2
MAX_LEXEME_CHARACTERS = 6
MIN_BOUNDARY_VARIANTS = 2

_PUNCTUATION = "。、，,！？!?「」『』（）()【】"


class NonIdentifiableContinuousJapaneseError(ValueError):
    pass


@dataclass(frozen=True)
class ContinuousJapaneseObservation:
    sentence: str
    before: AnonymousState
    after: AnonymousState

    @classmethod
    def build(
        cls,
        sentence: str,
        before: Sequence[int],
        after: Sequence[int],
    ) -> "ContinuousJapaneseObservation":
        before_row = tuple(int(value) for value in before)
        after_row = tuple(int(value) for value in after)
        if len(before_row) < 2 or len(before_row) != len(after_row):
            raise ValueError("anonymous states must have equal length >= 2")
        if not normalize_continuous(sentence):
            raise ValueError("sentence must contain visible Japanese characters")
        return cls(sentence, before_row, after_row)

    @property
    def text(self) -> str:
        return normalize_continuous(self.sentence)


@dataclass(frozen=True)
class TransitionRoles:
    source: int
    destination: int


@dataclass(frozen=True)
class SpanCandidate:
    text: str
    observations: int
    occurrences: int
    left_contexts: int
    right_contexts: int


@dataclass(frozen=True)
class GroundingSearchResult:
    best_mappings: tuple[tuple[tuple[str, int], ...], ...]
    best_cost: int
    second_best_cost: int | None
    candidate_lexemes: int
    theoretical_assignments: int
    complete_assignments_evaluated: int
    branch_nodes: int

    @property
    def margin(self) -> int | None:
        if self.second_best_cost is None:
            return None
        return self.second_best_cost - self.best_cost


@dataclass(frozen=True)
class SegmentedFactor:
    action: str
    frame: FrameTemplate
    effective_forward: bool


@dataclass(frozen=True)
class ActionLexiconSearchResult:
    exact_cover_lexicons: int
    cycle_consistent_connected_models: int
    best_models: int
    candidate_action_lexemes: int
    best_training_errors: int
    best_description_units: int


@dataclass(frozen=True)
class ContinuousJapaneseModel:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    frame_index: tuple[tuple[FrameTemplate, int], ...]
    factorization: LinearFactorizationModel
    training_rows: int

    def entity_map(self) -> dict[str, int]:
        return dict(self.entity_lexicon)

    def frame_map(self) -> dict[FrameTemplate, int]:
        return dict(self.frame_index)

    @property
    def description_bits(self) -> int:
        payload = {
            "entity_lexicon": [list(row) for row in self.entity_lexicon],
            "action_lexicon": list(self.action_lexicon),
            "frame_index": [list(row) for row in self.frame_index],
            "factorization": self.factorization.render(),
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8

    def predict(
        self,
        sentence: str,
        before: Sequence[int],
    ) -> AnonymousState | None:
        before_row = tuple(int(value) for value in before)
        try:
            factor, surface_coordinates = extract_segmented_factor(
                ContinuousJapaneseObservation.build(sentence, before_row, before_row),
                entity_grounding=self.entity_lexicon,
                action_lexicon=self.action_lexicon,
                require_transition=False,
            )
        except ValueError:
            return None

        frame_id = self.frame_map().get(factor.frame)
        if frame_id is None:
            return None
        direction = self.factorization.effective_forward(factor.action, frame_id)
        if direction is None:
            return None
        left_coordinate, right_coordinate = surface_coordinates
        if max(left_coordinate, right_coordinate) >= len(before_row):
            return None
        source, destination = (
            (left_coordinate, right_coordinate)
            if direction
            else (right_coordinate, left_coordinate)
        )
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


def normalize_continuous(sentence: str) -> str:
    text = unicodedata.normalize("NFKC", sentence)
    for mark in _PUNCTUATION:
        text = text.replace(mark, "")
    return "".join(text.split())


def infer_transition_roles(
    observation: ContinuousJapaneseObservation,
) -> TransitionRoles:
    changed = [
        index
        for index, (before, after) in enumerate(
            zip(observation.before, observation.after)
        )
        if before != after
    ]
    if len(changed) != 1:
        raise ValueError("copy intervention must change exactly one coordinate")
    destination = changed[0]
    source_candidates = [
        index
        for index, value in enumerate(observation.before)
        if index != destination and value == observation.after[destination]
    ]
    if len(source_candidates) != 1:
        raise ValueError("transition must identify one unique source coordinate")
    return TransitionRoles(source_candidates[0], destination)


def occurrence_spans(text: str, lexeme: str) -> tuple[tuple[int, int], ...]:
    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        index = text.find(lexeme, start)
        if index < 0:
            return tuple(spans)
        spans.append((index, index + len(lexeme)))
        start = index + 1


def boundary_contexts(
    observations: Sequence[ContinuousJapaneseObservation],
    lexeme: str,
) -> tuple[set[str], set[str], int]:
    left: set[str] = set()
    right: set[str] = set()
    occurrences = 0
    for observation in observations:
        text = observation.text
        for start, end in occurrence_spans(text, lexeme):
            occurrences += 1
            left.add(text[start - 1] if start else "<BOS>")
            right.add(text[end] if end < len(text) else "<EOS>")
    return left, right, occurrences


def substring_candidates(
    observations: Iterable[ContinuousJapaneseObservation],
    *,
    require_boundary_diversity: bool = True,
    max_characters: int = MAX_LEXEME_CHARACTERS,
    minimum_observations: int = 2,
) -> tuple[SpanCandidate, ...]:
    rows = tuple(observations)
    substrings: set[str] = set()
    for observation in rows:
        text = observation.text
        for start in range(len(text)):
            for length in range(1, min(max_characters, len(text) - start) + 1):
                substrings.add(text[start : start + length])

    candidates: list[SpanCandidate] = []
    for lexeme in substrings:
        observed = sum(lexeme in observation.text for observation in rows)
        if observed < minimum_observations:
            continue
        left, right, occurrences = boundary_contexts(rows, lexeme)
        if require_boundary_diversity and (
            len(left) < MIN_BOUNDARY_VARIANTS
            or len(right) < MIN_BOUNDARY_VARIANTS
        ):
            continue
        candidates.append(
            SpanCandidate(
                lexeme,
                observed,
                occurrences,
                len(left),
                len(right),
            )
        )
    return tuple(
        sorted(
            candidates,
            key=lambda row: (len(row.text), row.text),
        )
    )


def substring_signature(
    observations: Sequence[ContinuousJapaneseObservation],
    lexeme: str,
) -> tuple[bool, ...]:
    return tuple(lexeme in observation.text for observation in observations)


def coordinate_signatures(
    observations: Sequence[ContinuousJapaneseObservation],
) -> dict[int, tuple[bool, ...]]:
    if not observations:
        return {}
    coordinate_count = len(observations[0].before)
    if any(len(observation.before) != coordinate_count for observation in observations):
        raise ValueError("all observations must share one coordinate universe")
    roles = tuple(infer_transition_roles(observation) for observation in observations)
    return {
        coordinate: tuple(
            coordinate in (role.source, role.destination) for role in roles
        )
        for coordinate in range(coordinate_count)
    }


def hamming_distance(
    left: Sequence[bool],
    right: Sequence[bool],
) -> int:
    if len(left) != len(right):
        raise ValueError("signatures must have equal length")
    return sum(a != b for a, b in zip(left, right))


def robust_entity_span_search(
    observations: Iterable[ContinuousJapaneseObservation],
    *,
    require_boundary_diversity: bool = True,
) -> GroundingSearchResult:
    """Find the exact best injective substring-to-coordinate assignment.

    Branch-and-bound prunes only with an admissible lower bound, so the best and
    second-best objective values are exact over the declared finite substring
    universe.
    """

    rows = tuple(observations)
    candidates = substring_candidates(
        rows,
        require_boundary_diversity=require_boundary_diversity,
    )
    lexemes = tuple(candidate.text for candidate in candidates)
    coordinate_rows = coordinate_signatures(rows)
    coordinates = tuple(sorted(coordinate_rows))
    if len(lexemes) < len(coordinates):
        return GroundingSearchResult(
            tuple(),
            0,
            None,
            len(lexemes),
            0,
            0,
            0,
        )

    signatures = {
        lexeme: substring_signature(rows, lexeme) for lexeme in lexemes
    }
    costs = {
        coordinate: {
            lexeme: hamming_distance(coordinate_rows[coordinate], signatures[lexeme])
            for lexeme in lexemes
        }
        for coordinate in coordinates
    }
    sorted_lexemes = {
        coordinate: tuple(
            sorted(lexemes, key=lambda lexeme: (costs[coordinate][lexeme], lexeme))
        )
        for coordinate in coordinates
    }
    coordinate_order = tuple(
        sorted(
            coordinates,
            key=lambda coordinate: (
                costs[coordinate][sorted_lexemes[coordinate][1]]
                - costs[coordinate][sorted_lexemes[coordinate][0]]
                if len(sorted_lexemes[coordinate]) > 1
                else 10**9
            ),
            reverse=True,
        )
    )

    best_cost: int | None = None
    second_best_cost: int | None = None
    best_mappings: list[tuple[tuple[str, int], ...]] = []
    complete_assignments = 0
    branch_nodes = 0

    def lower_bound(
        remaining: Sequence[int],
        used: set[str],
    ) -> int:
        return sum(
            min(
                costs[coordinate][lexeme]
                for lexeme in lexemes
                if lexeme not in used
            )
            for coordinate in remaining
        )

    def search(
        depth: int,
        used: set[str],
        running_cost: int,
        selected: dict[int, str],
    ) -> None:
        nonlocal best_cost, second_best_cost, complete_assignments, branch_nodes
        branch_nodes += 1
        if depth == len(coordinate_order):
            complete_assignments += 1
            mapping = tuple(
                sorted((lexeme, coordinate) for coordinate, lexeme in selected.items())
            )
            if best_cost is None or running_cost < best_cost:
                second_best_cost = best_cost
                best_cost = running_cost
                best_mappings.clear()
                best_mappings.append(mapping)
            elif running_cost == best_cost:
                best_mappings.append(mapping)
            elif second_best_cost is None or running_cost < second_best_cost:
                second_best_cost = running_cost
            return

        coordinate = coordinate_order[depth]
        for lexeme in sorted_lexemes[coordinate]:
            if lexeme in used:
                continue
            next_used = {*used, lexeme}
            next_cost = running_cost + costs[coordinate][lexeme]
            bound = next_cost + lower_bound(
                coordinate_order[depth + 1 :],
                next_used,
            )
            if second_best_cost is not None and bound > second_best_cost:
                continue
            selected[coordinate] = lexeme
            search(depth + 1, next_used, next_cost, selected)
            del selected[coordinate]

    search(0, set(), 0, {})
    return GroundingSearchResult(
        tuple(sorted(set(best_mappings))),
        int(best_cost if best_cost is not None else 0),
        second_best_cost,
        len(lexemes),
        perm(len(lexemes), len(coordinates)),
        complete_assignments,
        branch_nodes,
    )


def induce_entity_grounding(
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[tuple[tuple[str, int], ...], GroundingSearchResult]:
    result = robust_entity_span_search(observations)
    if len(result.best_mappings) != 1:
        raise NonIdentifiableContinuousJapaneseError(
            f"continuous entity grounding has {len(result.best_mappings)} optima"
        )
    if result.margin is not None and result.margin < 1:
        raise NonIdentifiableContinuousJapaneseError(
            "continuous entity grounding lacks a positive objective margin"
        )
    return result.best_mappings[0], result


def non_overlapping_occurrences(
    text: str,
    lexeme: str,
    blocked_spans: Sequence[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (start, end)
        for start, end in occurrence_spans(text, lexeme)
        if all(
            end <= blocked_start or start >= blocked_end
            for blocked_start, blocked_end in blocked_spans
        )
    )


def entity_spans(
    observation: ContinuousJapaneseObservation,
    entity_grounding: Sequence[tuple[str, int]],
) -> tuple[tuple[int, int, str, int], ...]:
    rows: list[tuple[int, int, str, int]] = []
    for lexeme, coordinate in entity_grounding:
        spans = occurrence_spans(observation.text, lexeme)
        if len(spans) == 1:
            start, end = spans[0]
            rows.append((start, end, lexeme, coordinate))
        elif len(spans) > 1:
            raise ValueError("an entity lexeme occurs more than once")
    return tuple(sorted(rows))


def replace_semantic_spans(
    text: str,
    spans: Sequence[tuple[int, int, str]],
) -> str:
    if not spans:
        raise ValueError("at least one semantic span is required")
    ordered = tuple(sorted(spans))
    if any(
        left[1] > right[0]
        for left, right in zip(ordered, ordered[1:])
    ):
        raise ValueError("semantic spans overlap")
    cursor = ordered[0][0]
    end_of_core = max(end for _, end, _ in ordered)
    parts: list[str] = []
    for start, end, label in ordered:
        parts.append(text[cursor:start])
        parts.append(label)
        cursor = end
    parts.append(text[cursor:end_of_core])
    return "".join(parts)


def extract_segmented_factor(
    observation: ContinuousJapaneseObservation,
    *,
    entity_grounding: Sequence[tuple[str, int]],
    action_lexicon: Sequence[str],
    require_transition: bool = True,
) -> tuple[SegmentedFactor, tuple[int, int]]:
    text = observation.text
    entities = entity_spans(observation, entity_grounding)
    if len(entities) != 2 or entities[0][2] == entities[1][2]:
        raise ValueError("a factor row must contain two distinct entity lexemes")
    blocked = tuple((start, end) for start, end, _, _ in entities)

    action_occurrences: list[tuple[int, int, str]] = []
    for action in action_lexicon:
        spans = non_overlapping_occurrences(text, action, blocked)
        if len(spans) > 1:
            raise ValueError("an action lexeme occurs more than once")
        if len(spans) == 1:
            action_occurrences.append((*spans[0], action))
    if len(action_occurrences) != 1:
        raise ValueError("a factor row must contain exactly one action lexeme")
    action_start, action_end, action = action_occurrences[0]

    surface_entities = tuple(sorted(entities))
    semantic_spans = [
        (surface_entities[0][0], surface_entities[0][1], "E0"),
        (surface_entities[1][0], surface_entities[1][1], "E1"),
        (action_start, action_end, "A"),
    ]
    frame = replace_semantic_spans(text, semantic_spans)
    coordinates = (surface_entities[0][3], surface_entities[1][3])

    if not require_transition:
        return SegmentedFactor(action, frame, False), coordinates

    roles = infer_transition_roles(observation)
    if roles == TransitionRoles(*coordinates):
        effective_forward = True
    elif roles == TransitionRoles(coordinates[1], coordinates[0]):
        effective_forward = False
    else:
        raise ValueError("surface participants do not explain the transition")
    return SegmentedFactor(action, frame, effective_forward), coordinates


def complete_semantic_rows(
    observations: Iterable[ContinuousJapaneseObservation],
    entity_grounding: Sequence[tuple[str, int]],
) -> tuple[ContinuousJapaneseObservation, ...]:
    rows: list[ContinuousJapaneseObservation] = []
    for observation in observations:
        try:
            entities = entity_spans(observation, entity_grounding)
        except ValueError:
            continue
        if len(entities) == 2 and entities[0][2] != entities[1][2]:
            rows.append(observation)
    return tuple(rows)


def action_candidate_lexemes(
    observations: Sequence[ContinuousJapaneseObservation],
    entity_grounding: Sequence[tuple[str, int]],
) -> tuple[str, ...]:
    candidates = substring_candidates(observations)
    entity_set = {lexeme for lexeme, _ in entity_grounding}
    minimum_coverage = max(2, REPETITIONS // 2)
    selected: list[str] = []
    for candidate in candidates:
        lexeme = candidate.text
        if lexeme in entity_set:
            continue
        coverage = 0
        ambiguous = False
        for observation in observations:
            blocked = tuple(
                (start, end)
                for start, end, _, _ in entity_spans(observation, entity_grounding)
            )
            spans = non_overlapping_occurrences(observation.text, lexeme, blocked)
            if len(spans) > 1:
                ambiguous = True
                break
            coverage += int(len(spans) == 1)
        if not ambiguous and minimum_coverage <= coverage < len(observations):
            selected.append(lexeme)
    return tuple(sorted(selected, key=lambda lexeme: (len(lexeme), lexeme)))


def exact_cover_action_lexicons(
    observations: Sequence[ContinuousJapaneseObservation],
    entity_grounding: Sequence[tuple[str, int]],
    candidates: Sequence[str],
) -> tuple[tuple[str, ...], ...]:
    coverage: dict[str, frozenset[int]] = {}
    row_candidates: dict[int, list[str]] = {
        index: [] for index in range(len(observations))
    }
    for lexeme in candidates:
        covered: set[int] = set()
        for index, observation in enumerate(observations):
            blocked = tuple(
                (start, end)
                for start, end, _, _ in entity_spans(observation, entity_grounding)
            )
            spans = non_overlapping_occurrences(observation.text, lexeme, blocked)
            if len(spans) == 1:
                covered.add(index)
        coverage[lexeme] = frozenset(covered)
        for index in covered:
            row_candidates[index].append(lexeme)

    solutions: set[tuple[str, ...]] = set()

    def search(uncovered: frozenset[int], chosen: tuple[str, ...]) -> None:
        if not uncovered:
            solutions.add(tuple(sorted(chosen)))
            return
        row = min(
            uncovered,
            key=lambda index: sum(
                coverage[lexeme].issubset(uncovered)
                for lexeme in row_candidates[index]
            ),
        )
        for lexeme in row_candidates[row]:
            lexeme_coverage = coverage[lexeme]
            if lexeme_coverage and lexeme_coverage.issubset(uncovered):
                search(
                    uncovered - lexeme_coverage,
                    (*chosen, lexeme),
                )

    search(frozenset(range(len(observations))), tuple())
    return tuple(sorted(solutions))


def fit_action_lexicon(
    observations: Sequence[ContinuousJapaneseObservation],
    entity_grounding: Sequence[tuple[str, int]],
    action_lexicon: Sequence[str],
) -> tuple[
    tuple[tuple[FrameTemplate, int], ...],
    LinearFactorizationModel,
    int,
    int,
] | None:
    grouped: dict[tuple[str, FrameTemplate], Counter[bool]] = defaultdict(Counter)
    for observation in observations:
        try:
            factor, _ = extract_segmented_factor(
                observation,
                entity_grounding=entity_grounding,
                action_lexicon=action_lexicon,
            )
        except ValueError:
            return None
        grouped[(factor.action, factor.frame)][factor.effective_forward] += 1

    labels: dict[tuple[str, FrameTemplate], bool] = {}
    training_errors = 0
    for key, counts in grouped.items():
        if counts[True] == counts[False]:
            return None
        labels[key] = counts[True] > counts[False]
        training_errors += min(counts.values())

    frames = tuple(sorted({frame for _, frame in labels}))
    frame_ids = {frame: index for index, frame in enumerate(frames)}
    edges = tuple(
        LabeledSemanticEdge(action, frame_ids[frame], label)
        for (action, frame), label in sorted(labels.items())
    )
    try:
        factorization = induce_linear_factorization(
            edges,
            verbs=tuple(sorted(action_lexicon)),
            template_positions=tuple(range(len(frames))),
        )
    except InconsistentSemanticsError:
        return None
    if not factorization.identifiable:
        return None

    description_units = (
        sum(len(action) for action in action_lexicon)
        + sum(len(frame) for frame in frames)
        + len(action_lexicon)
        + len(frames)
        + len(edges)
    )
    return (
        tuple((frame, frame_ids[frame]) for frame in frames),
        factorization,
        training_errors,
        description_units,
    )


def induce_continuous_japanese(
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[
    ContinuousJapaneseModel,
    GroundingSearchResult,
    ActionLexiconSearchResult,
    int,
]:
    rows = tuple(observations)
    entity_grounding, grounding_search = induce_entity_grounding(rows)
    semantic_rows = complete_semantic_rows(rows, entity_grounding)
    candidates = action_candidate_lexemes(semantic_rows, entity_grounding)
    covers = exact_cover_action_lexicons(
        semantic_rows,
        entity_grounding,
        candidates,
    )

    valid: list[
        tuple[
            tuple[int, int],
            tuple[str, ...],
            tuple[tuple[FrameTemplate, int], ...],
            LinearFactorizationModel,
        ]
    ] = []
    for action_lexicon in covers:
        fitted = fit_action_lexicon(
            semantic_rows,
            entity_grounding,
            action_lexicon,
        )
        if fitted is None:
            continue
        frame_index, factorization, errors, description_units = fitted
        valid.append(
            (
                (errors, description_units),
                tuple(action_lexicon),
                frame_index,
                factorization,
            )
        )
    if not valid:
        raise NonIdentifiableContinuousJapaneseError(
            "no connected cycle-consistent segmentation model survives"
        )
    best_score = min(row[0] for row in valid)
    best = [row for row in valid if row[0] == best_score]
    if len(best) != 1:
        raise NonIdentifiableContinuousJapaneseError(
            f"continuous action segmentation has {len(best)} equal-cost models"
        )
    _, action_lexicon, frame_index, factorization = best[0]
    search_result = ActionLexiconSearchResult(
        exact_cover_lexicons=len(covers),
        cycle_consistent_connected_models=len(valid),
        best_models=len(best),
        candidate_action_lexemes=len(candidates),
        best_training_errors=best_score[0],
        best_description_units=best_score[1],
    )
    return (
        ContinuousJapaneseModel(
            tuple(entity_grounding),
            action_lexicon,
            frame_index,
            factorization,
            len(rows),
        ),
        grounding_search,
        search_result,
        len(rows) - len(semantic_rows),
    )
