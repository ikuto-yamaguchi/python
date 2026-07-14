from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil, log2
from random import Random
from typing import Mapping, Sequence

from .cap_gen_002_loop_microprogram_induction import (
    DEFAULT_PROGRAM_LIBRARY,
    LoopProgram,
    discover_loop_interchange_model,
)
from .cap_gen_002_raw_interchange_induction import DiscoveryConfig, HiddenEpisode


TemplatePair = tuple[bytes, bytes]
Boundary = tuple[int, int]


@dataclass(frozen=True)
class ContextDiscoveryConfig:
    context_length: int = 3
    minimum_source_length: int = 4
    maximum_source_length: int = 6
    maximum_target_length: int = 12
    minimum_relation_delay: int = 6
    maximum_relation_delay: int = 15
    fit_fraction: float = 2.0 / 3.0
    minimum_anchor_support: int = 2
    minimum_fit_support: int = 8
    minimum_calibration_support: int = 4

    def validate(self) -> None:
        if self.context_length < 1:
            raise ValueError("context length must be positive")
        if self.minimum_source_length < 1:
            raise ValueError("source length must be positive")
        if self.maximum_source_length < self.minimum_source_length:
            raise ValueError("invalid source length interval")
        if self.maximum_target_length < self.minimum_source_length:
            raise ValueError("target limit is too small")
        if self.minimum_relation_delay < 0:
            raise ValueError("relation delay must be non-negative")
        if self.maximum_relation_delay < self.minimum_relation_delay:
            raise ValueError("invalid relation delay interval")
        if not 0.5 < self.fit_fraction < 0.9:
            raise ValueError("fit fraction must leave chronological calibration data")
        if min(
            self.minimum_anchor_support,
            self.minimum_fit_support,
            self.minimum_calibration_support,
        ) < 1:
            raise ValueError("support thresholds must be positive")


@dataclass(frozen=True)
class SpanProgramMatch:
    program_library_index: int
    source_boundary: Boundary
    target_boundary: Boundary
    source_left: bytes
    source_right: bytes
    target_left: bytes
    target_right: bytes
    source_value: bytes
    target_value: bytes

    @property
    def source_context_pair(self) -> TemplatePair:
        return (self.source_left, self.source_right)

    @property
    def target_context_pair(self) -> TemplatePair:
        return (self.target_left, self.target_right)


@dataclass(frozen=True)
class ContextRole:
    program_index: int
    source_left_class: frozenset[bytes]
    source_right_class: frozenset[bytes]
    target_left_class: frozenset[bytes]
    target_right_class: frozenset[bytes]
    fit_support: int
    calibration_support: int
    gain_bits: int
    confirmed_source_boundaries: tuple[Boundary, ...]
    confirmed_target_boundaries: tuple[Boundary, ...]
    seen_source_pairs: frozenset[TemplatePair]
    seen_target_pairs: frozenset[TemplatePair]


@dataclass(frozen=True)
class ContextDiscoveryStats:
    raw_bytes: int
    split_position: int
    target_span_index_entries: int
    source_spans_examined: int
    program_candidates_executed: int
    exact_program_matches: int
    program_groups_examined: int
    calibration_bytes_checked: int
    peak_context_class_entries: int


@dataclass(frozen=True)
class FactorizedContextModel:
    programs: tuple[LoopProgram, ...]
    roles: tuple[ContextRole, ...]
    config: ContextDiscoveryConfig
    stats: ContextDiscoveryStats

    @property
    def learned_payload_bits(self) -> int:
        program_bits = sum(program.description_bits for program in self.programs)
        anchor_bits = sum(
            8 * sum(len(anchor) for anchor in anchor_class)
            for role in self.roles
            for anchor_class in (
                role.source_left_class,
                role.source_right_class,
                role.target_left_class,
                role.target_right_class,
            )
        )
        # Direction-independent role framing, one program reference, and four set tags.
        role_metadata_bits = 20 * len(self.roles)
        return program_bits + anchor_bits + role_metadata_bits

    @property
    def exact_cross_product_template_bits(self) -> int:
        """Bits for explicitly storing every left/right combination covered by classes."""

        total = 0
        for role in self.roles:
            total += sum(
                (len(left) + len(right)) * 8
                for left in role.source_left_class
                for right in role.source_right_class
            )
            total += sum(
                (len(left) + len(right)) * 8
                for left in role.target_left_class
                for right in role.target_right_class
            )
        return total


@dataclass(frozen=True)
class PredictedSpanPair:
    role_index: int
    source_boundary: Boundary
    target_boundary: Boundary
    prediction: bytes
    observed: bytes

    @property
    def exact(self) -> bool:
        return self.prediction == self.observed


@dataclass(frozen=True)
class FactorizedEvaluation:
    source_candidates: int
    target_candidates: int
    paired_predictions: tuple[PredictedSpanPair, ...]
    context_scan_operations: int
    program_operations: int

    @property
    def paired(self) -> int:
        return len(self.paired_predictions)

    @property
    def exact(self) -> int:
        return sum(row.exact for row in self.paired_predictions)

    @property
    def exact_accuracy(self) -> float:
        return self.exact / self.paired if self.paired else 0.0


@dataclass(frozen=True)
class HiddenContextRole:
    source_left_class: tuple[bytes, ...]
    source_right_class: tuple[bytes, ...]
    target_left_class: tuple[bytes, ...]
    target_right_class: tuple[bytes, ...]
    program: LoopProgram


@dataclass(frozen=True)
class HiddenContextEpisode:
    role_index: int
    source_boundary: Boundary
    target_boundary: Boundary
    source_context_pair: TemplatePair
    target_context_pair: TemplatePair


def _positive_limit_bits(limit: int) -> int:
    return max(1, ceil(log2(limit + 1)))


def _enumerate_program_matches(
    stream: bytes,
    config: ContextDiscoveryConfig,
    program_library: Sequence[LoopProgram],
) -> tuple[tuple[SpanProgramMatch, ...], Mapping[str, int]]:
    """Search every raw source span and retain minimum-code exact program matches."""

    context = config.context_length
    target_index: dict[tuple[int, bytes], list[int]] = defaultdict(list)
    target_entries = 0
    for target_length in range(
        config.minimum_source_length,
        config.maximum_target_length + 1,
    ):
        final_start = len(stream) - target_length - context
        for start in range(context, final_start + 1):
            target_index[(target_length, stream[start : start + target_length])].append(start)
            target_entries += 1

    best: dict[tuple[Boundary, Boundary], SpanProgramMatch] = {}
    source_spans = program_executions = 0
    for source_length in range(
        config.minimum_source_length,
        config.maximum_source_length + 1,
    ):
        final_start = len(stream) - source_length - context
        for source_start in range(context, final_start + 1):
            source_spans += 1
            source_end = source_start + source_length
            source = stream[source_start:source_end]
            minimum_target_start = source_end + config.minimum_relation_delay
            maximum_target_start = source_end + config.maximum_relation_delay
            for program_index, program in enumerate(program_library):
                program_executions += 1
                target = program.apply(source)
                positions = target_index.get((len(target), target))
                if not positions:
                    continue
                left = bisect_left(positions, minimum_target_start)
                right = bisect_right(positions, maximum_target_start)
                for target_start in positions[left:right]:
                    target_end = target_start + len(target)
                    key = (
                        (source_start, source_end),
                        (target_start, target_end),
                    )
                    candidate = SpanProgramMatch(
                        program_index,
                        key[0],
                        key[1],
                        stream[source_start - context : source_start],
                        stream[source_end : source_end + context],
                        stream[target_start - context : target_start],
                        stream[target_end : target_end + context],
                        source,
                        target,
                    )
                    incumbent = best.get(key)
                    if incumbent is None or (
                        program.description_bits,
                        program.reverse,
                        program.body,
                    ) < (
                        program_library[incumbent.program_library_index].description_bits,
                        program_library[incumbent.program_library_index].reverse,
                        program_library[incumbent.program_library_index].body,
                    ):
                        best[key] = candidate

    matches = tuple(
        sorted(
            best.values(),
            key=lambda row: (
                row.source_boundary,
                row.target_boundary,
                row.program_library_index,
            ),
        )
    )
    return matches, {
        "target_span_index_entries": target_entries,
        "source_spans_examined": source_spans,
        "program_candidates_executed": program_executions,
        "exact_program_matches": len(matches),
    }


def _anchor_classes(
    rows: Sequence[SpanProgramMatch],
    minimum_support: int,
) -> dict[str, frozenset[bytes]]:
    attributes = (
        "source_left",
        "source_right",
        "target_left",
        "target_right",
    )
    output: dict[str, frozenset[bytes]] = {}
    for attribute in attributes:
        counts = Counter(getattr(row, attribute) for row in rows)
        output[attribute] = frozenset(
            anchor for anchor, support in counts.items() if support >= minimum_support
        )
    return output


def _inside_classes(
    row: SpanProgramMatch,
    classes: Mapping[str, frozenset[bytes]],
) -> bool:
    return all(getattr(row, attribute) in anchors for attribute, anchors in classes.items())


def _role_gain_bits(
    program: LoopProgram,
    classes: Mapping[str, frozenset[bytes]],
    confirmed: Sequence[SpanProgramMatch],
    stream_length: int,
) -> int:
    literal_bits = 8 * sum(len(row.target_value) for row in confirmed)
    anchor_bits = 8 * sum(
        len(anchor)
        for anchor_class in classes.values()
        for anchor in anchor_class
    )
    pointer_bits = 2 * _positive_limit_bits(stream_length) * len(confirmed)
    encoded_bits = program.description_bits + anchor_bits + pointer_bits + 20
    return literal_bits - encoded_bits


def discover_factorized_context_model(
    stream: bytes,
    config: ContextDiscoveryConfig = ContextDiscoveryConfig(),
    program_library: Sequence[LoopProgram] = DEFAULT_PROGRAM_LIBRARY,
) -> FactorizedContextModel:
    """Learn left/right context classes and transformations from one raw byte stream.

    Full context pairs need not repeat.  Individual left and right contexts are retained
    when repeated high-confidence transformation matches support them.  A later raw
    suffix calibrates the cross-product classes.  No token, record, event, role, task,
    domain, aligned example, or hidden boundary is passed to this function.
    """

    config.validate()
    if not program_library:
        raise ValueError("program library must not be empty")
    matches, counters = _enumerate_program_matches(stream, config, program_library)
    split = int(len(stream) * config.fit_fraction)

    raw_roles: list[tuple[LoopProgram, dict[str, frozenset[bytes]], tuple[SpanProgramMatch, ...], int, int, int]] = []
    calibration_bytes = 0
    peak_class_entries = 0
    program_groups = 0
    for library_index in sorted({row.program_library_index for row in matches}):
        program_groups += 1
        program = program_library[library_index]
        fit_rows = tuple(
            row
            for row in matches
            if row.program_library_index == library_index
            and row.target_boundary[1] <= split
        )
        calibration_rows = tuple(
            row
            for row in matches
            if row.program_library_index == library_index
            and row.source_boundary[0] >= split
        )
        candidate_classes = _anchor_classes(fit_rows, config.minimum_anchor_support)
        if any(not anchors for anchors in candidate_classes.values()):
            continue

        calibration_confirmed = tuple(
            row for row in calibration_rows if _inside_classes(row, candidate_classes)
        )
        calibration_bytes += sum(len(row.target_value) for row in calibration_confirmed)
        if len(calibration_confirmed) < config.minimum_calibration_support:
            continue

        # Calibration retains only context variants that independently recur in the
        # held-out chronological suffix.  Exact left/right pair combinations are not
        # required to have appeared in the fit prefix.
        final_classes = {
            attribute: frozenset(getattr(row, attribute) for row in calibration_confirmed)
            for attribute in candidate_classes
        }
        peak_class_entries = max(
            peak_class_entries,
            sum(len(anchors) for anchors in final_classes.values()),
        )
        fit_confirmed = tuple(
            row for row in fit_rows if _inside_classes(row, final_classes)
        )
        if len(fit_confirmed) < config.minimum_fit_support:
            continue
        confirmed = tuple(
            row
            for row in matches
            if row.program_library_index == library_index
            and _inside_classes(row, final_classes)
        )
        gain = _role_gain_bits(program, final_classes, confirmed, len(stream))
        if gain <= 0:
            continue
        raw_roles.append(
            (
                program,
                final_classes,
                confirmed,
                len(fit_confirmed),
                len(calibration_confirmed),
                gain,
            )
        )

    programs: list[LoopProgram] = []
    program_indices: dict[tuple[bool, tuple[str, ...]], int] = {}
    roles: list[ContextRole] = []
    for program, classes, confirmed, fit_support, calibration_support, gain in raw_roles:
        signature = (program.reverse, program.body)
        program_index = program_indices.get(signature)
        if program_index is None:
            program_index = len(programs)
            program_indices[signature] = program_index
            programs.append(program)
        roles.append(
            ContextRole(
                program_index,
                classes["source_left"],
                classes["source_right"],
                classes["target_left"],
                classes["target_right"],
                fit_support,
                calibration_support,
                gain,
                tuple(row.source_boundary for row in confirmed),
                tuple(row.target_boundary for row in confirmed),
                frozenset(row.source_context_pair for row in confirmed),
                frozenset(row.target_context_pair for row in confirmed),
            )
        )

    return FactorizedContextModel(
        tuple(programs),
        tuple(roles),
        config,
        ContextDiscoveryStats(
            len(stream),
            split,
            int(counters["target_span_index_entries"]),
            int(counters["source_spans_examined"]),
            int(counters["program_candidates_executed"]),
            int(counters["exact_program_matches"]),
            program_groups,
            calibration_bytes,
            peak_class_entries,
        ),
    )


def _find_factorized_spans(
    stream: bytes,
    left_class: frozenset[bytes],
    right_class: frozenset[bytes],
    *,
    context_length: int,
    minimum_length: int,
    maximum_length: int,
) -> tuple[tuple[Boundary, bytes], ...]:
    output: list[tuple[Boundary, bytes]] = []
    final_start = len(stream) - context_length - minimum_length
    for start in range(context_length, final_start + 1):
        if stream[start - context_length : start] not in left_class:
            continue
        for length in range(minimum_length, maximum_length + 1):
            end = start + length
            if end + context_length > len(stream):
                break
            if stream[end : end + context_length] in right_class:
                output.append(((start, end), stream[start:end]))
    return tuple(output)


def evaluate_factorized_context_model(
    model: FactorizedContextModel,
    stream: bytes,
) -> FactorizedEvaluation:
    predictions: list[PredictedSpanPair] = []
    source_candidate_total = target_candidate_total = 0
    scan_operations = program_operations = 0
    context = model.config.context_length

    for role_index, role in enumerate(model.roles):
        sources = _find_factorized_spans(
            stream,
            role.source_left_class,
            role.source_right_class,
            context_length=context,
            minimum_length=model.config.minimum_source_length,
            maximum_length=model.config.maximum_source_length,
        )
        targets = _find_factorized_spans(
            stream,
            role.target_left_class,
            role.target_right_class,
            context_length=context,
            minimum_length=model.config.minimum_source_length,
            maximum_length=model.config.maximum_target_length,
        )
        source_candidate_total += len(sources)
        target_candidate_total += len(targets)
        scan_operations += 2 * max(0, len(stream) - 2 * context)
        scan_operations += len(sources) * (
            model.config.maximum_source_length - model.config.minimum_source_length + 1
        )
        scan_operations += len(targets) * (
            model.config.maximum_target_length - model.config.minimum_source_length + 1
        )

        targets_by_start: dict[int, list[tuple[Boundary, bytes]]] = defaultdict(list)
        for row in targets:
            targets_by_start[row[0][0]].append(row)
        starts = sorted(targets_by_start)
        used_targets: set[Boundary] = set()
        program = model.programs[role.program_index]

        for source_boundary, source_value in sources:
            prediction = program.apply(source_value)
            program_operations += len(source_value) * program.operations_per_input_byte
            minimum_start = source_boundary[1] + model.config.minimum_relation_delay
            maximum_start = source_boundary[1] + model.config.maximum_relation_delay
            index = bisect_left(starts, minimum_start)
            selected: tuple[Boundary, bytes] | None = None
            while index < len(starts) and starts[index] <= maximum_start:
                for candidate in targets_by_start[starts[index]]:
                    if candidate[0] in used_targets:
                        continue
                    if len(candidate[1]) != len(prediction):
                        continue
                    selected = candidate
                    break
                if selected is not None:
                    break
                index += 1
            if selected is None:
                continue
            used_targets.add(selected[0])
            predictions.append(
                PredictedSpanPair(
                    role_index,
                    source_boundary,
                    selected[0],
                    prediction,
                    selected[1],
                )
            )

    return FactorizedEvaluation(
        source_candidate_total,
        target_candidate_total,
        tuple(predictions),
        scan_operations,
        program_operations,
    )


def evaluate_exact_pair_baseline(
    model: FactorizedContextModel,
    stream: bytes,
) -> FactorizedEvaluation:
    """Ablation: store seen full left/right pairs instead of factorized classes."""

    context = model.config.context_length
    predictions: list[PredictedSpanPair] = []
    source_total = target_total = scan_operations = program_operations = 0
    for role_index, role in enumerate(model.roles):
        source_rows: list[tuple[Boundary, bytes]] = []
        target_rows: list[tuple[Boundary, bytes]] = []
        final_start = len(stream) - context - model.config.minimum_source_length
        for start in range(context, final_start + 1):
            left = stream[start - context : start]
            scan_operations += 1
            for length in range(
                model.config.minimum_source_length,
                model.config.maximum_target_length + 1,
            ):
                end = start + length
                if end + context > len(stream):
                    break
                pair = (left, stream[end : end + context])
                if length <= model.config.maximum_source_length and pair in role.seen_source_pairs:
                    source_rows.append(((start, end), stream[start:end]))
                if pair in role.seen_target_pairs:
                    target_rows.append(((start, end), stream[start:end]))
        source_total += len(source_rows)
        target_total += len(target_rows)
        targets_by_start: dict[int, list[tuple[Boundary, bytes]]] = defaultdict(list)
        for row in target_rows:
            targets_by_start[row[0][0]].append(row)
        starts = sorted(targets_by_start)
        program = model.programs[role.program_index]
        for source_boundary, source_value in source_rows:
            prediction = program.apply(source_value)
            program_operations += len(source_value) * program.operations_per_input_byte
            index = bisect_left(
                starts,
                source_boundary[1] + model.config.minimum_relation_delay,
            )
            while index < len(starts) and starts[index] <= (
                source_boundary[1] + model.config.maximum_relation_delay
            ):
                selected = next(
                    (
                        row
                        for row in targets_by_start[starts[index]]
                        if len(row[1]) == len(prediction)
                    ),
                    None,
                )
                if selected is not None:
                    predictions.append(
                        PredictedSpanPair(
                            role_index,
                            source_boundary,
                            selected[0],
                            prediction,
                            selected[1],
                        )
                    )
                    break
                index += 1

    return FactorizedEvaluation(
        source_total,
        target_total,
        tuple(predictions),
        scan_operations,
        program_operations,
    )


def predicted_boundary_scores(
    evaluation: FactorizedEvaluation,
    episodes: Sequence[HiddenContextEpisode],
) -> dict[str, float | int]:
    expected_pairs = {
        (episode.source_boundary, episode.target_boundary) for episode in episodes
    }
    predicted_pairs = {
        (row.source_boundary, row.target_boundary) for row in evaluation.paired_predictions
    }
    overlap = len(expected_pairs & predicted_pairs)
    return {
        "expected_pairs": len(expected_pairs),
        "predicted_pairs": len(predicted_pairs),
        "correct_pairs": overlap,
        "precision": overlap / len(predicted_pairs) if predicted_pairs else 0.0,
        "recall": overlap / len(expected_pairs) if expected_pairs else 0.0,
    }


def training_boundary_scores(
    model: FactorizedContextModel,
    episodes: Sequence[HiddenContextEpisode],
) -> dict[str, float | int]:
    expected_source = {episode.source_boundary for episode in episodes}
    expected_target = {episode.target_boundary for episode in episodes}
    predicted_source = {
        boundary for role in model.roles for boundary in role.confirmed_source_boundaries
    }
    predicted_target = {
        boundary for role in model.roles for boundary in role.confirmed_target_boundaries
    }
    correct = len(expected_source & predicted_source) + len(expected_target & predicted_target)
    predicted = len(predicted_source) + len(predicted_target)
    expected = len(expected_source) + len(expected_target)
    return {
        "expected_boundaries": expected,
        "predicted_boundaries": predicted,
        "correct_boundaries": correct,
        "precision": correct / predicted if predicted else 0.0,
        "recall": correct / expected if expected else 0.0,
    }


def _anchor_sets() -> tuple[tuple[tuple[bytes, ...], ...], ...]:
    alphabet = b"abcdefghjkmnpqrstuvwxyz23456789"
    base = len(alphabet)
    index = 0
    output: list[tuple[tuple[bytes, ...], ...]] = []
    for _role in range(3):
        positions: list[tuple[bytes, ...]] = []
        for _position in range(4):
            variants: list[bytes] = []
            for _variant in range(4):
                value = index
                index += 1
                variants.append(
                    bytes(
                        (
                            alphabet[(value // (base * base)) % base],
                            alphabet[(value // base) % base],
                            alphabet[value % base],
                        )
                    )
                )
            positions.append(tuple(variants))
        output.append(tuple(positions))
    return tuple(output)


ANCHOR_SETS = _anchor_sets()
HIDDEN_PROGRAMS = (
    LoopProgram(True, ("EMIT",)),
    LoopProgram(False, ("EMIT", "EMIT")),
    LoopProgram(False, ("INC", "INC", "INC", "EMIT")),
)


def _random_bytes(rng: Random, minimum: int, maximum: int) -> bytes:
    alphabet = b"abcdefghjkmnpqrstuvwxyz23456789"
    return bytes(rng.choice(alphabet) for _ in range(rng.randint(minimum, maximum)))


def make_combinatorial_context_stream(
    *,
    seed: int,
    split: str,
    evaluation_repeats: int = 2,
    independent_targets: bool = False,
) -> tuple[bytes, tuple[HiddenContextRole, ...], tuple[HiddenContextEpisode, ...]]:
    """Build one delimiter-free stream whose full context pairs do not repeat.

    Training uses the off-diagonal combinations of four left and four right variants.
    Evaluation uses only diagonal combinations, which were never observed as full pairs.
    Every individual anchor variant is nevertheless identified in training/calibration.
    """

    if split not in {"train", "evaluation"}:
        raise ValueError("split must be train or evaluation")
    rng = Random(seed)
    roles = tuple(
        HiddenContextRole(
            ANCHOR_SETS[index][0],
            ANCHOR_SETS[index][1],
            ANCHOR_SETS[index][2],
            ANCHOR_SETS[index][3],
            HIDDEN_PROGRAMS[index],
        )
        for index in range(3)
    )
    if split == "train":
        combination_blocks = tuple(
            tuple((index, (index + shift) % 4) for index in range(4))
            for shift in (1, 2, 3)
        )
    else:
        combination_blocks = tuple(
            tuple((index, index) for index in range(4))
            for _ in range(evaluation_repeats)
        )

    pieces: list[bytes] = []
    episodes: list[HiddenContextEpisode] = []
    position = 0
    for block_index, combinations in enumerate(combination_blocks):
        for left_index, right_index in combinations:
            for role_index, role in enumerate(roles):
                target_left_index = (left_index + 1) % 4
                target_right_index = (right_index + 2) % 4
                source_value = _random_bytes(rng, 4, 6)
                target_value = (
                    _random_bytes(rng, 4, 12)
                    if independent_targets
                    else role.program.apply(source_value)
                )
                prefix = _random_bytes(rng, 1, 4)
                middle = _random_bytes(rng, 2, 6)
                suffix = _random_bytes(rng, 1, 4)
                source_left = role.source_left_class[left_index]
                source_right = role.source_right_class[right_index]
                target_left = role.target_left_class[target_left_index]
                target_right = role.target_right_class[target_right_index]
                piece = (
                    prefix
                    + source_left
                    + source_value
                    + source_right
                    + middle
                    + target_left
                    + target_value
                    + target_right
                    + suffix
                )
                source_start = position + len(prefix) + len(source_left)
                source_end = source_start + len(source_value)
                target_start = (
                    source_end
                    + len(source_right)
                    + len(middle)
                    + len(target_left)
                )
                target_end = target_start + len(target_value)
                episodes.append(
                    HiddenContextEpisode(
                        role_index,
                        (source_start, source_end),
                        (target_start, target_end),
                        (source_left, source_right),
                        (target_left, target_right),
                    )
                )
                pieces.append(piece)
                position += len(piece)

        # A raw same-alphabet bridge makes the chronological 2/3 split land between
        # fit and calibration blocks without exposing an event delimiter to the learner.
        if split == "train" and block_index == 1:
            bridge = _random_bytes(rng, 48, 48)
            pieces.append(bridge)
            position += len(bridge)

    return b"".join(pieces), roles, tuple(episodes)


def run_experiment() -> dict[str, object]:
    config = ContextDiscoveryConfig()
    training_stream, hidden_roles, training_episodes = make_combinatorial_context_stream(
        seed=7,
        split="train",
    )
    evaluation_stream, _hidden_roles2, evaluation_episodes = make_combinatorial_context_stream(
        seed=97,
        split="evaluation",
        evaluation_repeats=2,
    )
    control_stream, _hidden_roles3, _control_episodes = make_combinatorial_context_stream(
        seed=1701,
        split="train",
        independent_targets=True,
    )

    model = discover_factorized_context_model(training_stream, config)
    evaluation = evaluate_factorized_context_model(model, evaluation_stream)
    exact_pair_baseline = evaluate_exact_pair_baseline(model, evaluation_stream)
    control_model = discover_factorized_context_model(control_stream, config)
    old_exact_anchor_model = discover_loop_interchange_model(
        training_stream,
        DiscoveryConfig(maximum_gap=12),
    )

    training_boundaries = training_boundary_scores(model, training_episodes)
    evaluation_pairs = predicted_boundary_scores(evaluation, evaluation_episodes)
    expected_programs = {
        (role.program.reverse, role.program.body) for role in hidden_roles
    }
    discovered_programs = {
        (program.reverse, program.body) for program in model.programs
    }
    training_source_pairs = {
        episode.source_context_pair for episode in training_episodes
    }
    evaluation_source_pairs = {
        episode.source_context_pair for episode in evaluation_episodes
    }
    training_target_pairs = {
        episode.target_context_pair for episode in training_episodes
    }
    evaluation_target_pairs = {
        episode.target_context_pair for episode in evaluation_episodes
    }

    checks = {
        "one_raw_training_stream": isinstance(training_stream, bytes),
        "no_exact_source_pair_overlap": not (
            training_source_pairs & evaluation_source_pairs
        ),
        "no_exact_target_pair_overlap": not (
            training_target_pairs & evaluation_target_pairs
        ),
        "three_context_roles_discovered": len(model.roles) == 3,
        "three_programs_recovered": discovered_programs == expected_programs,
        "training_boundary_precision": training_boundaries["precision"] == 1.0,
        "training_boundary_recall": training_boundaries["recall"] == 1.0,
        "unseen_combination_pair_precision": evaluation_pairs["precision"] == 1.0,
        "unseen_combination_pair_recall": evaluation_pairs["recall"] == 1.0,
        "frozen_exact_predictions": evaluation.exact_accuracy == 1.0,
        "exact_pair_baseline_has_zero_pairs": exact_pair_baseline.paired == 0,
        "rii_002_exact_anchor_model_has_zero_links": len(old_exact_anchor_model.links) == 0,
        "independent_target_control_rejected": len(control_model.roles) == 0,
        "factorized_context_code_smaller_than_cross_product": (
            model.learned_payload_bits < model.exact_cross_product_template_bits
        ),
        "positive_mdl_gain": all(role.gain_bits > 0 for role in model.roles),
    }
    return {
        "capability_id": "CAP-GEN-002-RII-003",
        "claim": (
            "raw factorized context classes jointly learned with span boundaries and "
            "loop programs, transferring to unseen left/right context combinations"
        ),
        "claim_boundary": (
            "all individual context variants are seen during training; only their exact "
            "combinations are unseen. This is not unseen-vocabulary grounding, natural-language "
            "concept learning, public-axis improvement, or human-level intelligence."
        ),
        "training": {
            "raw_bytes": len(training_stream),
            "hidden_boundaries_visible_to_learner": False,
            "task_ids_visible_to_learner": False,
            "aligned_examples_visible_to_learner": False,
            "exact_source_context_pairs": len(training_source_pairs),
            "exact_target_context_pairs": len(training_target_pairs),
        },
        "model": {
            "context_roles": len(model.roles),
            "shared_programs": len(model.programs),
            "learned_payload_bits": model.learned_payload_bits,
            "exact_cross_product_template_bits": model.exact_cross_product_template_bits,
            "compression_ratio_vs_cross_product": (
                model.exact_cross_product_template_bits / model.learned_payload_bits
            ),
            "minimum_role_gain_bits": min(role.gain_bits for role in model.roles),
        },
        "training_boundary_recovery": training_boundaries,
        "frozen_unseen_combination_evaluation": {
            **evaluation_pairs,
            "exact_accuracy": evaluation.exact_accuracy,
            "source_candidates": evaluation.source_candidates,
            "target_candidates": evaluation.target_candidates,
            "context_scan_operations": evaluation.context_scan_operations,
            "program_operations": evaluation.program_operations,
        },
        "exact_pair_baseline": {
            "paired_predictions": exact_pair_baseline.paired,
            "exact_accuracy": exact_pair_baseline.exact_accuracy,
        },
        "rii_002_exact_anchor_baseline": {
            "surface_links": len(old_exact_anchor_model.links),
        },
        "independent_target_control": {
            "context_roles": len(control_model.roles),
        },
        "discovery_stats": {
            "split_position": model.stats.split_position,
            "target_span_index_entries": model.stats.target_span_index_entries,
            "source_spans_examined": model.stats.source_spans_examined,
            "program_candidates_executed": model.stats.program_candidates_executed,
            "exact_program_matches": model.stats.exact_program_matches,
            "program_groups_examined": model.stats.program_groups_examined,
            "calibration_bytes_checked": model.stats.calibration_bytes_checked,
            "peak_context_class_entries": model.stats.peak_context_class_entries,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
