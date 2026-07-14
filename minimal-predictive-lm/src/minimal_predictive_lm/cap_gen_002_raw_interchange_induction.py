from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil, log2
from random import Random
from typing import Iterable, Sequence


TemplateKey = tuple[bytes, bytes]


@dataclass(frozen=True)
class DiscoveryConfig:
    anchor_lengths: tuple[int, ...] = (2, 3, 4)
    minimum_gap: int = 4
    maximum_gap: int = 7
    minimum_slot_support: int = 8
    maximum_relation_distance: int = 32
    minimum_relation_support: int = 8
    validation_fraction: float = 0.25

    def validate(self) -> None:
        if not self.anchor_lengths or min(self.anchor_lengths) < 1:
            raise ValueError("anchor lengths must be positive")
        if self.minimum_gap < 1 or self.maximum_gap < self.minimum_gap:
            raise ValueError("invalid gap interval")
        if self.minimum_slot_support < 2 or self.minimum_relation_support < 3:
            raise ValueError("support is too small for discovery plus validation")
        if self.maximum_relation_distance < 0:
            raise ValueError("relation distance must be non-negative")
        if not 0.0 < self.validation_fraction < 0.5:
            raise ValueError("validation fraction must lie in (0, 0.5)")


@dataclass(frozen=True)
class GapOccurrence:
    template: TemplateKey
    start: int
    gap_start: int
    gap_end: int
    end: int
    value: bytes

    @property
    def boundary(self) -> tuple[int, int]:
        return (self.gap_start, self.gap_end)


@dataclass(frozen=True)
class SlotTemplate:
    left: bytes
    right: bytes
    occurrences: tuple[GapOccurrence, ...]

    @property
    def key(self) -> TemplateKey:
        return (self.left, self.right)


@dataclass(frozen=True)
class ByteAffineProgram:
    """Tiny generic byte transducer used only for the first falsification trial.

    The input may be read left-to-right or right-to-left. Every byte is mapped by
    y = scale*x + shift (mod 256). This is not claimed to be a universal language of
    thought; it isolates whether raw span boundaries and delayed operator links can be
    discovered jointly before attempting a universal microprogram substrate.
    """

    reverse: bool
    scale: int
    shift: int

    def __post_init__(self) -> None:
        if not 1 <= self.scale <= 255 or not 0 <= self.shift <= 255:
            raise ValueError("invalid byte-affine parameters")

    @property
    def signature(self) -> tuple[bool, int, int]:
        return (self.reverse, self.scale, self.shift)

    @property
    def description_bits(self) -> int:
        return 17

    def apply(self, source: bytes) -> bytes:
        values = reversed(source) if self.reverse else source
        return bytes((self.scale * value + self.shift) & 0xFF for value in values)


@dataclass(frozen=True)
class RelationLink:
    source: TemplateKey
    target: TemplateKey
    program_index: int
    train_support: int
    validation_support: int
    gain_bits: int
    source_boundaries: tuple[tuple[int, int], ...]
    target_boundaries: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class DiscoveryStats:
    raw_bytes: int
    slot_windows_examined: int
    slot_templates_retained: int
    relation_links_examined: int
    paired_examples_examined: int
    program_candidates_examined: int
    validation_bytes_checked: int
    peak_occurrence_entries: int


@dataclass(frozen=True)
class InterchangeModel:
    programs: tuple[ByteAffineProgram, ...]
    links: tuple[RelationLink, ...]
    config: DiscoveryConfig
    stats: DiscoveryStats

    @property
    def learned_payload_bits(self) -> int:
        program_index_bits = 0 if len(self.programs) <= 1 else ceil(log2(len(self.programs)))
        program_bits = sum(program.description_bits for program in self.programs)
        link_bits = 0
        for link in self.links:
            link_bits += 8 * sum(len(part) for part in link.source + link.target)
            link_bits += program_index_bits
            link_bits += 2 * ceil(log2(self.config.maximum_gap + 1))
            link_bits += ceil(log2(self.config.maximum_relation_distance + 1))
        return program_bits + link_bits


@dataclass(frozen=True)
class FrozenEvaluation:
    target_spans: int
    covered_spans: int
    exact_spans: int
    target_bytes: int
    correct_bytes: int
    inference_operations: int

    @property
    def coverage(self) -> float:
        return self.covered_spans / self.target_spans if self.target_spans else 0.0

    @property
    def exact_accuracy(self) -> float:
        return self.exact_spans / self.target_spans if self.target_spans else 0.0

    @property
    def byte_accuracy(self) -> float:
        return self.correct_bytes / self.target_bytes if self.target_bytes else 0.0


@dataclass(frozen=True)
class HiddenRelation:
    source: TemplateKey
    target: TemplateKey
    program: ByteAffineProgram


@dataclass(frozen=True)
class HiddenEpisode:
    relation_index: int
    source_boundary: tuple[int, int]
    target_boundary: tuple[int, int]


def _bits_for_positive_limit(limit: int) -> int:
    return max(1, ceil(log2(limit + 1)))


def _extract_slot_templates(
    stream: bytes,
    config: DiscoveryConfig,
) -> tuple[tuple[SlotTemplate, ...], int, int]:
    grouped: dict[TemplateKey, list[GapOccurrence]] = defaultdict(list)
    windows = 0
    for anchor_length in config.anchor_lengths:
        minimum_width = 2 * anchor_length + config.minimum_gap
        if len(stream) < minimum_width:
            continue
        for start in range(len(stream) - minimum_width + 1):
            left = stream[start : start + anchor_length]
            for gap_length in range(config.minimum_gap, config.maximum_gap + 1):
                right_start = start + anchor_length + gap_length
                right_end = right_start + anchor_length
                if right_end > len(stream):
                    break
                windows += 1
                right = stream[right_start:right_end]
                grouped[(left, right)].append(
                    GapOccurrence(
                        (left, right),
                        start,
                        start + anchor_length,
                        right_start,
                        right_end,
                        stream[start + anchor_length : right_start],
                    )
                )

    templates: list[SlotTemplate] = []
    peak_entries = 0
    for (left, right), occurrences in grouped.items():
        peak_entries = max(peak_entries, len(occurrences))
        unique_values = {row.value for row in occurrences}
        if len(occurrences) < config.minimum_slot_support:
            continue
        if len(unique_values) < max(3, config.minimum_slot_support // 2):
            continue
        templates.append(SlotTemplate(left, right, tuple(occurrences)))

    templates.sort(
        key=lambda row: (
            -len(row.occurrences),
            len(row.left) + len(row.right),
            row.left,
            row.right,
        )
    )
    return tuple(templates), windows, peak_entries


def _pair_occurrences(
    source: SlotTemplate,
    target: SlotTemplate,
    maximum_distance: int,
) -> tuple[tuple[GapOccurrence, GapOccurrence], ...]:
    target_starts = [row.start for row in target.occurrences]
    pairs: list[tuple[GapOccurrence, GapOccurrence]] = []
    used_targets: set[int] = set()

    for source_row in source.occurrences:
        index = bisect_left(target_starts, source_row.end)
        while index < len(target.occurrences):
            target_row = target.occurrences[index]
            distance = target_row.start - source_row.end
            if distance > maximum_distance:
                break
            if target_row.start not in used_targets:
                pairs.append((source_row, target_row))
                used_targets.add(target_row.start)
                break
            index += 1
    return tuple(pairs)


def _synthesize_program(
    examples: Sequence[tuple[bytes, bytes]],
) -> tuple[ByteAffineProgram | None, int]:
    if not examples or any(len(source) != len(target) or not source for source, target in examples):
        return None, 0

    candidates_examined = 0
    valid: list[ByteAffineProgram] = []
    for reverse in (False, True):
        first_source = examples[0][0][::-1] if reverse else examples[0][0]
        first_target = examples[0][1]
        for scale in range(1, 256):
            candidates_examined += 1
            shift = (first_target[0] - scale * first_source[0]) & 0xFF
            program = ByteAffineProgram(reverse, scale, shift)
            if all(program.apply(source) == target for source, target in examples):
                valid.append(program)

    if not valid:
        return None, candidates_examined
    return min(valid, key=lambda row: row.signature), candidates_examined


def _relation_gain_bits(
    source: SlotTemplate,
    target: SlotTemplate,
    program: ByteAffineProgram,
    pairs: Sequence[tuple[GapOccurrence, GapOccurrence]],
    config: DiscoveryConfig,
) -> int:
    literal_bits = 8 * sum(len(target_row.value) for _source_row, target_row in pairs)
    relation_bits = 8 * sum(len(part) for part in source.key + target.key)
    per_example_bits = (
        _bits_for_positive_limit(config.maximum_relation_distance)
        + _bits_for_positive_limit(config.maximum_gap)
    )
    encoded_bits = program.description_bits + relation_bits + per_example_bits * len(pairs)
    return literal_bits - encoded_bits


def _discover_relation_candidates(
    templates: Sequence[SlotTemplate],
    config: DiscoveryConfig,
) -> tuple[list[tuple[RelationLink, ByteAffineProgram]], tuple[int, int, int, int]]:
    candidates: list[tuple[RelationLink, ByteAffineProgram]] = []
    links_examined = 0
    pairs_examined = 0
    programs_examined = 0
    validation_bytes = 0

    for source in templates:
        for target in templates:
            if source.key == target.key:
                continue
            links_examined += 1
            pairs = _pair_occurrences(source, target, config.maximum_relation_distance)
            pairs_examined += len(pairs)
            if len(pairs) < config.minimum_relation_support:
                continue

            validation_count = max(2, ceil(len(pairs) * config.validation_fraction))
            split = len(pairs) - validation_count
            if split < 2:
                continue
            train_pairs = pairs[:split]
            validation_pairs = pairs[split:]
            program, examined = _synthesize_program(
                [(source_row.value, target_row.value) for source_row, target_row in train_pairs]
            )
            programs_examined += examined
            if program is None:
                continue

            valid = True
            for source_row, target_row in validation_pairs:
                validation_bytes += len(target_row.value)
                if program.apply(source_row.value) != target_row.value:
                    valid = False
                    break
            if not valid:
                continue

            gain_bits = _relation_gain_bits(source, target, program, pairs, config)
            if gain_bits <= 0:
                continue
            candidates.append(
                (
                    RelationLink(
                        source.key,
                        target.key,
                        -1,
                        len(train_pairs),
                        len(validation_pairs),
                        gain_bits,
                        tuple(source_row.boundary for source_row, _target_row in pairs),
                        tuple(target_row.boundary for _source_row, target_row in pairs),
                    ),
                    program,
                )
            )

    return candidates, (links_examined, pairs_examined, programs_examined, validation_bytes)


def _deduplicate_candidates(
    candidates: Iterable[tuple[RelationLink, ByteAffineProgram]],
) -> tuple[tuple[RelationLink, ByteAffineProgram], ...]:
    """Collapse alternate anchor codings of the same raw target boundaries."""

    best: dict[tuple[tuple[int, int], ...], tuple[RelationLink, ByteAffineProgram]] = {}
    for link, program in candidates:
        footprint = link.target_boundaries
        incumbent = best.get(footprint)
        score = (
            link.gain_bits,
            -(sum(len(part) for part in link.source + link.target)),
            link.train_support + link.validation_support,
        )
        if incumbent is None:
            best[footprint] = (link, program)
            continue
        old_link, _old_program = incumbent
        old_score = (
            old_link.gain_bits,
            -(sum(len(part) for part in old_link.source + old_link.target)),
            old_link.train_support + old_link.validation_support,
        )
        if score > old_score:
            best[footprint] = (link, program)
    return tuple(sorted(best.values(), key=lambda row: (-row[0].gain_bits, row[0].target)))


def discover_interchange_model(
    stream: bytes,
    config: DiscoveryConfig = DiscoveryConfig(),
) -> InterchangeModel:
    """Discover byte boundaries, delayed variable links, and shared transformations.

    The only observation is one byte stream. No tokenization, event boundaries, task
    IDs, aligned input/output examples, variable names, relation names, or program labels
    are supplied. Candidate boundaries start at every byte position. A delayed link is
    retained only when one compact program predicts chronologically held-out occurrences
    and lowers total description length.
    """

    config.validate()
    templates, slot_windows, peak_entries = _extract_slot_templates(stream, config)
    raw_candidates, counters = _discover_relation_candidates(templates, config)
    candidates = _deduplicate_candidates(raw_candidates)

    program_index: dict[tuple[bool, int, int], int] = {}
    programs: list[ByteAffineProgram] = []
    links: list[RelationLink] = []
    for link, program in candidates:
        index = program_index.get(program.signature)
        if index is None:
            index = len(programs)
            program_index[program.signature] = index
            programs.append(program)
        links.append(
            RelationLink(
                link.source,
                link.target,
                index,
                link.train_support,
                link.validation_support,
                link.gain_bits,
                link.source_boundaries,
                link.target_boundaries,
            )
        )

    links_examined, pairs_examined, programs_examined, validation_bytes = counters
    return InterchangeModel(
        tuple(programs),
        tuple(links),
        config,
        DiscoveryStats(
            len(stream),
            slot_windows,
            len(templates),
            links_examined,
            pairs_examined,
            programs_examined,
            validation_bytes,
            peak_entries,
        ),
    )


def find_template_occurrences(
    stream: bytes,
    template: TemplateKey,
    *,
    minimum_gap: int,
    maximum_gap: int,
) -> tuple[GapOccurrence, ...]:
    left, right = template
    rows: list[GapOccurrence] = []
    start = 0
    while True:
        left_start = stream.find(left, start)
        if left_start < 0:
            break
        for gap_length in range(minimum_gap, maximum_gap + 1):
            right_start = left_start + len(left) + gap_length
            if stream[right_start : right_start + len(right)] == right:
                rows.append(
                    GapOccurrence(
                        template,
                        left_start,
                        left_start + len(left),
                        right_start,
                        right_start + len(right),
                        stream[left_start + len(left) : right_start],
                    )
                )
                break
        start = left_start + 1
    return tuple(rows)


def evaluate_frozen_model(model: InterchangeModel, stream: bytes) -> FrozenEvaluation:
    target_spans = covered = exact = target_bytes = correct_bytes = operations = 0
    for link in model.links:
        source = SlotTemplate(
            link.source[0],
            link.source[1],
            find_template_occurrences(
                stream,
                link.source,
                minimum_gap=model.config.minimum_gap,
                maximum_gap=model.config.maximum_gap,
            ),
        )
        target = SlotTemplate(
            link.target[0],
            link.target[1],
            find_template_occurrences(
                stream,
                link.target,
                minimum_gap=model.config.minimum_gap,
                maximum_gap=model.config.maximum_gap,
            ),
        )
        target_spans += len(target.occurrences)
        target_bytes += sum(len(row.value) for row in target.occurrences)
        for source_row, target_row in _pair_occurrences(
            source, target, model.config.maximum_relation_distance
        ):
            prediction = model.programs[link.program_index].apply(source_row.value)
            operations += len(source_row.value) + 1
            covered += 1
            exact += int(prediction == target_row.value)
            correct_bytes += sum(
                predicted == observed
                for predicted, observed in zip(prediction, target_row.value)
            )

    return FrozenEvaluation(
        target_spans,
        covered,
        exact,
        target_bytes,
        correct_bytes,
        operations,
    )


def evaluate_literal_template_baseline(
    training_stream: bytes,
    evaluation_stream: bytes,
    model: InterchangeModel,
) -> FrozenEvaluation:
    """Boundary-aware baseline that cannot use a source span or transformation."""

    target_spans = exact = target_bytes = correct_bytes = 0
    for link in model.links:
        train_rows = find_template_occurrences(
            training_stream,
            link.target,
            minimum_gap=model.config.minimum_gap,
            maximum_gap=model.config.maximum_gap,
        )
        counts = Counter(row.value for row in train_rows)
        if not counts:
            continue
        prediction = min(counts, key=lambda value: (-counts[value], len(value), value))
        evaluation_rows = find_template_occurrences(
            evaluation_stream,
            link.target,
            minimum_gap=model.config.minimum_gap,
            maximum_gap=model.config.maximum_gap,
        )
        for row in evaluation_rows:
            target_spans += 1
            target_bytes += len(row.value)
            exact += int(prediction == row.value)
            correct_bytes += sum(
                predicted == observed
                for predicted, observed in zip(prediction, row.value)
            )

    return FrozenEvaluation(
        target_spans,
        target_spans,
        exact,
        target_bytes,
        correct_bytes,
        target_spans,
    )


def _random_value(rng: Random, minimum_length: int = 4, maximum_length: int = 7) -> bytes:
    alphabet = b"abcdefghjkmnpqrstuvwxyz23456789"
    return bytes(rng.choice(alphabet) for _ in range(rng.randint(minimum_length, maximum_length)))


def _noise(rng: Random, minimum_length: int = 1, maximum_length: int = 7) -> bytes:
    alphabet = b"~^;,:/|"
    return bytes(rng.choice(alphabet) for _ in range(rng.randint(minimum_length, maximum_length)))


def make_mixed_raw_stream(
    *,
    seed: int,
    instances_per_relation: int,
    independent_targets: bool = False,
) -> tuple[bytes, tuple[HiddenRelation, ...], tuple[HiddenEpisode, ...]]:
    """Create one delimiter-free stream; hidden metadata is scorer-only."""

    rng = Random(seed)
    hidden_relations = (
        HiddenRelation((b"ab[", b"]cd"), (b"ef{", b"}gh"), ByteAffineProgram(True, 1, 0)),
        HiddenRelation((b"jk<", b">lm"), (b"np(", b")qr"), ByteAffineProgram(True, 1, 0)),
        HiddenRelation((b"st[", b"]uv"), (b"wx{", b"}yz"), ByteAffineProgram(False, 1, 3)),
        HiddenRelation((b"12<", b">34"), (b"56(", b")78"), ByteAffineProgram(False, 1, 3)),
    )
    schedule = [
        relation_index
        for _ in range(instances_per_relation)
        for relation_index in range(len(hidden_relations))
    ]
    rng.shuffle(schedule)

    pieces: list[bytes] = []
    episodes: list[HiddenEpisode] = []
    position = 0
    for relation_index in schedule:
        relation = hidden_relations[relation_index]
        source_value = _random_value(rng)
        target_value = (
            _random_value(rng)
            if independent_targets
            else relation.program.apply(source_value)
        )
        prefix = _noise(rng, 1, 5)
        middle = _noise(rng, 1, 7)
        suffix = _noise(rng, 1, 5)
        piece = (
            prefix
            + relation.source[0]
            + source_value
            + relation.source[1]
            + middle
            + relation.target[0]
            + target_value
            + relation.target[1]
            + suffix
        )
        source_start = position + len(prefix) + len(relation.source[0])
        source_end = source_start + len(source_value)
        target_start = (
            source_end
            + len(relation.source[1])
            + len(middle)
            + len(relation.target[0])
        )
        target_end = target_start + len(target_value)
        episodes.append(
            HiddenEpisode(relation_index, (source_start, source_end), (target_start, target_end))
        )
        pieces.append(piece)
        position += len(piece)

    return b"".join(pieces), hidden_relations, tuple(episodes)


def boundary_scores(
    model: InterchangeModel,
    episodes: Sequence[HiddenEpisode],
) -> dict[str, float | int]:
    expected_source = {row.source_boundary for row in episodes}
    expected_target = {row.target_boundary for row in episodes}
    found_source = {boundary for link in model.links for boundary in link.source_boundaries}
    found_target = {boundary for link in model.links for boundary in link.target_boundaries}

    true_total = len(expected_source & found_source) + len(expected_target & found_target)
    found_total = len(found_source) + len(found_target)
    expected_total = len(expected_source) + len(expected_target)
    return {
        "expected_boundaries": expected_total,
        "found_boundaries": found_total,
        "correct_boundaries": true_total,
        "precision": true_total / found_total if found_total else 0.0,
        "recall": true_total / expected_total if expected_total else 0.0,
    }


def run_experiment() -> dict[str, object]:
    config = DiscoveryConfig()
    training_stream, hidden_relations, training_episodes = make_mixed_raw_stream(
        seed=7,
        instances_per_relation=16,
    )
    evaluation_stream, _relations2, _episodes2 = make_mixed_raw_stream(
        seed=97,
        instances_per_relation=8,
    )
    control_stream, _control_relations, _control_episodes = make_mixed_raw_stream(
        seed=1701,
        instances_per_relation=16,
        independent_targets=True,
    )

    model = discover_interchange_model(training_stream, config)
    frozen = evaluate_frozen_model(model, evaluation_stream)
    literal = evaluate_literal_template_baseline(training_stream, evaluation_stream, model)
    control_model = discover_interchange_model(control_stream, config)
    boundaries = boundary_scores(model, training_episodes)
    expected_programs = {row.program.signature for row in hidden_relations}
    observed_programs = {row.signature for row in model.programs}

    checks = {
        "one_raw_training_stream": isinstance(training_stream, bytes),
        "no_supplied_boundaries_or_task_ids": True,
        "all_hidden_boundaries_recovered": boundaries["recall"] == 1.0,
        "no_false_boundaries": boundaries["precision"] == 1.0,
        "four_surface_links_discovered": len(model.links) == 4,
        "operators_shared_across_surfaces": len(model.programs) < len(model.links),
        "hidden_operator_set_recovered": observed_programs == expected_programs,
        "frozen_exact_generalization": frozen.exact_accuracy == 1.0 and frozen.coverage == 1.0,
        "literal_baseline_fails": literal.exact_accuracy == 0.0,
        "independent_control_rejected": len(control_model.links) == 0,
        "positive_mdl_gain": all(link.gain_bits > 0 for link in model.links),
    }
    return {
        "capability_id": "CAP-GEN-002-RII-001",
        "claim": (
            "controlled evidence for joint raw-byte span-boundary, delayed-variable-link, "
            "and small generic-transducer discovery without supplied event boundaries or aligned examples"
        ),
        "claim_boundary": (
            "synthetic exact byte transformations with repeated surface anchors; not natural-language "
            "concept formation, unrestricted operator invention, public-axis improvement, or human-level intelligence"
        ),
        "training": {
            "raw_bytes": len(training_stream),
            "hidden_metadata_visible_to_learner": False,
            "task_ids_visible_to_learner": False,
            "event_boundaries_visible_to_learner": False,
            "aligned_examples_visible_to_learner": False,
        },
        "model": {
            "programs": [program.signature for program in model.programs],
            "surface_links": len(model.links),
            "shared_programs": len(model.programs),
            "learned_payload_bits": model.learned_payload_bits,
            "minimum_link_gain_bits": min(link.gain_bits for link in model.links),
        },
        "boundary_recovery": boundaries,
        "frozen_evaluation": {
            "target_spans": frozen.target_spans,
            "coverage": frozen.coverage,
            "exact_accuracy": frozen.exact_accuracy,
            "byte_accuracy": frozen.byte_accuracy,
            "inference_operations": frozen.inference_operations,
        },
        "literal_template_baseline": {
            "exact_accuracy": literal.exact_accuracy,
            "byte_accuracy": literal.byte_accuracy,
        },
        "independent_target_control": {"accepted_links": len(control_model.links)},
        "discovery_stats": {
            "slot_windows_examined": model.stats.slot_windows_examined,
            "slot_templates_retained": model.stats.slot_templates_retained,
            "relation_links_examined": model.stats.relation_links_examined,
            "paired_examples_examined": model.stats.paired_examples_examined,
            "program_candidates_examined": model.stats.program_candidates_examined,
            "validation_bytes_checked": model.stats.validation_bytes_checked,
            "peak_occurrence_entries": model.stats.peak_occurrence_entries,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
