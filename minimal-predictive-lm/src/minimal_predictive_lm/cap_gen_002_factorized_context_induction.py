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
from .cap_gen_002_raw_interchange_induction import DiscoveryConfig


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
            raise ValueError("fit fraction must leave calibration data")
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
        return self.source_left, self.source_right

    @property
    def target_context_pair(self) -> TemplatePair:
        return self.target_left, self.target_right


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
        return program_bits + anchor_bits + 20 * len(self.roles)

    @property
    def exact_cross_product_template_bits(self) -> int:
        total = 0
        for role in self.roles:
            total += sum(
                8 * (len(left) + len(right))
                for left in role.source_left_class
                for right in role.source_right_class
            )
            total += sum(
                8 * (len(left) + len(right))
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


def _enumerate_program_matches(
    stream: bytes,
    config: ContextDiscoveryConfig,
    program_library: Sequence[LoopProgram],
) -> tuple[tuple[SpanProgramMatch, ...], dict[str, int]]:
    context = config.context_length
    target_index: dict[tuple[int, bytes], list[int]] = defaultdict(list)
    target_entries = 0
    for length in range(config.minimum_source_length, config.maximum_target_length + 1):
        for start in range(context, len(stream) - length - context + 1):
            target_index[(length, stream[start : start + length])].append(start)
            target_entries += 1

    best: dict[tuple[Boundary, Boundary], SpanProgramMatch] = {}
    source_spans = executions = 0
    for length in range(config.minimum_source_length, config.maximum_source_length + 1):
        for source_start in range(context, len(stream) - length - context + 1):
            source_spans += 1
            source_end = source_start + length
            source = stream[source_start:source_end]
            low = source_end + config.minimum_relation_delay
            high = source_end + config.maximum_relation_delay
            for program_index, program in enumerate(program_library):
                executions += 1
                target = program.apply(source)
                positions = target_index.get((len(target), target))
                if not positions:
                    continue
                left = bisect_left(positions, low)
                right = bisect_right(positions, high)
                for target_start in positions[left:right]:
                    target_end = target_start + len(target)
                    key = ((source_start, source_end), (target_start, target_end))
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
        "program_candidates_executed": executions,
        "exact_program_matches": len(matches),
    }


def _anchor_classes(
    rows: Sequence[SpanProgramMatch], minimum_support: int
) -> dict[str, frozenset[bytes]]:
    output: dict[str, frozenset[bytes]] = {}
    for attribute in (
        "source_left",
        "source_right",
        "target_left",
        "target_right",
    ):
        counts = Counter(getattr(row, attribute) for row in rows)
        output[attribute] = frozenset(
            anchor for anchor, support in counts.items() if support >= minimum_support
        )
    return output


def _inside_classes(
    row: SpanProgramMatch, classes: Mapping[str, frozenset[bytes]]
) -> bool:
    return all(getattr(row, name) in anchors for name, anchors in classes.items())


def _role_gain_bits(
    program: LoopProgram,
    classes: Mapping[str, frozenset[bytes]],
    confirmed: Sequence[SpanProgramMatch],
) -> int:
    """Target literal code minus executable role code.

    Occurrence positions are not stored in the learned artifact: the deterministic
    context scanner recovers them from the raw stream.  Its cost is therefore charged to
    training/inference operations.  Charging per-occurrence pointers here as well would
    count the same location mechanism twice.
    """

    literal_bits = 8 * sum(len(row.target_value) for row in confirmed)
    anchor_bits = 8 * sum(
        len(anchor) for anchors in classes.values() for anchor in anchors
    )
    executable_bits = program.description_bits + anchor_bits + 20
    return literal_bits - executable_bits


def discover_factorized_context_model(
    stream: bytes,
    config: ContextDiscoveryConfig = ContextDiscoveryConfig(),
    program_library: Sequence[LoopProgram] = DEFAULT_PROGRAM_LIBRARY,
) -> FactorizedContextModel:
    """Jointly induce raw span roles, factorized contexts, and loop programs."""

    config.validate()
    if not program_library:
        raise ValueError("program library must not be empty")
    matches, counters = _enumerate_program_matches(stream, config, program_library)
    split = int(len(stream) * config.fit_fraction)

    raw_roles: list[
        tuple[
            LoopProgram,
            dict[str, frozenset[bytes]],
            tuple[SpanProgramMatch, ...],
            int,
            int,
            int,
        ]
    ] = []
    calibration_bytes = peak_entries = program_groups = 0
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
        candidates = _anchor_classes(fit_rows, config.minimum_anchor_support)
        if any(not anchors for anchors in candidates.values()):
            continue
        calibrated = tuple(
            row for row in calibration_rows if _inside_classes(row, candidates)
        )
        calibration_bytes += sum(len(row.target_value) for row in calibrated)
        if len(calibrated) < config.minimum_calibration_support:
            continue

        final_classes = {
            name: frozenset(getattr(row, name) for row in calibrated)
            for name in candidates
        }
        peak_entries = max(
            peak_entries, sum(len(anchors) for anchors in final_classes.values())
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
        gain = _role_gain_bits(program, final_classes, confirmed)
        if gain <= 0:
            continue
        raw_roles.append(
            (
                program,
                final_classes,
                confirmed,
                len(fit_confirmed),
                len(calibrated),
                gain,
            )
        )

    programs: list[LoopProgram] = []
    program_indices: dict[tuple[bool, tuple[str, ...]], int] = {}
    roles: list[ContextRole] = []
    for program, classes, confirmed, fit_support, calibration_support, gain in raw_roles:
        signature = program.reverse, program.body
        index = program_indices.get(signature)
        if index is None:
            index = len(programs)
            program_indices[signature] = index
            programs.append(program)
        roles.append(
            ContextRole(
                index,
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
            counters["target_span_index_entries"],
            counters["source_spans_examined"],
            counters["program_candidates_executed"],
            counters["exact_program_matches"],
            program_groups,
            calibration_bytes,
            peak_entries,
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
    for start in range(
        context_length,
        len(stream) - context_length - minimum_length + 1,
    ):
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
    model: FactorizedContextModel, stream: bytes
) -> FactorizedEvaluation:
    predictions: list[PredictedSpanPair] = []
    source_total = target_total = scan_operations = program_operations = 0
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
        source_total += len(sources)
        target_total += len(targets)
        scan_operations += 2 * max(0, len(stream) - 2 * context)
        scan_operations += len(sources) * (
            model.config.maximum_source_length - model.config.minimum_source_length + 1
        )
        scan_operations += len(targets) * (
            model.config.maximum_target_length - model.config.minimum_source_length + 1
        )

        targets_by_start: dict[int, list[tuple[Boundary, bytes]]] = defaultdict(list)
        for target in targets:
            targets_by_start[target[0][0]].append(target)
        target_starts = sorted(targets_by_start)
        used: set[Boundary] = set()
        program = model.programs[role.program_index]
        for source_boundary, source_value in sources:
            prediction = program.apply(source_value)
            program_operations += len(source_value) * program.operations_per_input_byte
            low = source_boundary[1] + model.config.minimum_relation_delay
            high = source_boundary[1] + model.config.maximum_relation_delay
            position = bisect_left(target_starts, low)
            selected: tuple[Boundary, bytes] | None = None
            while position < len(target_starts) and target_starts[position] <= high:
                selected = next(
                    (
                        target
                        for target in targets_by_start[target_starts[position]]
                        if target[0] not in used
                        and len(target[1]) == len(prediction)
                    ),
                    None,
                )
                if selected is not None:
                    break
                position += 1
            if selected is None:
                continue
            used.add(selected[0])
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
        source_total,
        target_total,
        tuple(predictions),
        scan_operations,
        program_operations,
    )


def evaluate_exact_pair_baseline(
    model: FactorizedContextModel, stream: bytes
) -> FactorizedEvaluation:
    context = model.config.context_length
    predictions: list[PredictedSpanPair] = []
    source_total = target_total = scans = operations = 0
    for role_index, role in enumerate(model.roles):
        sources: list[tuple[Boundary, bytes]] = []
        targets: list[tuple[Boundary, bytes]] = []
        for start in range(
            context,
            len(stream) - context - model.config.minimum_source_length + 1,
        ):
            left = stream[start - context : start]
            scans += 1
            for length in range(
                model.config.minimum_source_length,
                model.config.maximum_target_length + 1,
            ):
                end = start + length
                if end + context > len(stream):
                    break
                pair = left, stream[end : end + context]
                if (
                    length <= model.config.maximum_source_length
                    and pair in role.seen_source_pairs
                ):
                    sources.append(((start, end), stream[start:end]))
                if pair in role.seen_target_pairs:
                    targets.append(((start, end), stream[start:end]))
        source_total += len(sources)
        target_total += len(targets)
        targets_by_start: dict[int, list[tuple[Boundary, bytes]]] = defaultdict(list)
        for target in targets:
            targets_by_start[target[0][0]].append(target)
        target_starts = sorted(targets_by_start)
        program = model.programs[role.program_index]
        for source_boundary, source_value in sources:
            prediction = program.apply(source_value)
            operations += len(source_value) * program.operations_per_input_byte
            position = bisect_left(
                target_starts,
                source_boundary[1] + model.config.minimum_relation_delay,
            )
            while position < len(target_starts) and target_starts[position] <= (
                source_boundary[1] + model.config.maximum_relation_delay
            ):
                selected = next(
                    (
                        target
                        for target in targets_by_start[target_starts[position]]
                        if len(target[1]) == len(prediction)
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
                position += 1
    return FactorizedEvaluation(
        source_total, target_total, tuple(predictions), scans, operations
    )


def predicted_boundary_scores(
    evaluation: FactorizedEvaluation,
    episodes: Sequence[HiddenContextEpisode],
) -> dict[str, float | int]:
    expected = {
        (episode.source_boundary, episode.target_boundary) for episode in episodes
    }
    predicted = {
        (row.source_boundary, row.target_boundary)
        for row in evaluation.paired_predictions
    }
    correct = len(expected & predicted)
    return {
        "expected_pairs": len(expected),
        "predicted_pairs": len(predicted),
        "correct_pairs": correct,
        "precision": correct / len(predicted) if predicted else 0.0,
        "recall": correct / len(expected) if expected else 0.0,
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


def _build_anchor_sets() -> tuple[tuple[tuple[bytes, ...], ...], ...]:
    alphabet = b"abcdefghjkmnpqrstuvwxyz23456789"
    base = len(alphabet)
    counter = 0
    roles: list[tuple[tuple[bytes, ...], ...]] = []
    for _ in range(3):
        positions: list[tuple[bytes, ...]] = []
        for _ in range(4):
            variants: list[bytes] = []
            for _ in range(4):
                value = counter
                counter += 1
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
        roles.append(tuple(positions))
    return tuple(roles)


ANCHOR_SETS = _build_anchor_sets()
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
    blocks = (
        tuple(
            tuple((index, (index + shift) % 4) for index in range(4))
            for shift in (1, 2, 3)
        )
        if split == "train"
        else tuple(
            tuple((index, index) for index in range(4))
            for _ in range(evaluation_repeats)
        )
    )

    pieces: list[bytes] = []
    episodes: list[HiddenContextEpisode] = []
    position = 0
    for block_index, combinations in enumerate(blocks):
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
                target_start = source_end + len(source_right) + len(middle) + len(target_left)
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
        if split == "train" and block_index == 1:
            bridge = _random_bytes(rng, 48, 48)
            pieces.append(bridge)
            position += len(bridge)
    return b"".join(pieces), roles, tuple(episodes)


def run_experiment() -> dict[str, object]:
    config = ContextDiscoveryConfig()
    training_stream, hidden_roles, training_episodes = make_combinatorial_context_stream(
        seed=7, split="train"
    )
    evaluation_stream, _roles2, evaluation_episodes = make_combinatorial_context_stream(
        seed=97, split="evaluation", evaluation_repeats=2
    )
    control_stream, _roles3, _episodes3 = make_combinatorial_context_stream(
        seed=1701, split="train", independent_targets=True
    )

    model = discover_factorized_context_model(training_stream, config)
    evaluation = evaluate_factorized_context_model(model, evaluation_stream)
    exact_pair = evaluate_exact_pair_baseline(model, evaluation_stream)
    control_model = discover_factorized_context_model(control_stream, config)
    old_exact_anchor = discover_loop_interchange_model(
        training_stream, DiscoveryConfig(maximum_gap=12)
    )

    training_boundaries = training_boundary_scores(model, training_episodes)
    evaluation_pairs = predicted_boundary_scores(evaluation, evaluation_episodes)
    expected_programs = {
        (role.program.reverse, role.program.body) for role in hidden_roles
    }
    discovered_programs = {
        (program.reverse, program.body) for program in model.programs
    }
    training_source_pairs = {row.source_context_pair for row in training_episodes}
    evaluation_source_pairs = {row.source_context_pair for row in evaluation_episodes}
    training_target_pairs = {row.target_context_pair for row in training_episodes}
    evaluation_target_pairs = {row.target_context_pair for row in evaluation_episodes}

    checks = {
        "one_raw_training_stream": isinstance(training_stream, bytes),
        "no_exact_source_pair_overlap": not training_source_pairs & evaluation_source_pairs,
        "no_exact_target_pair_overlap": not training_target_pairs & evaluation_target_pairs,
        "three_context_roles_discovered": len(model.roles) == 3,
        "three_programs_recovered": discovered_programs == expected_programs,
        "training_boundary_precision": training_boundaries["precision"] == 1.0,
        "training_boundary_recall": training_boundaries["recall"] == 1.0,
        "unseen_combination_pair_precision": evaluation_pairs["precision"] == 1.0,
        "unseen_combination_pair_recall": evaluation_pairs["recall"] == 1.0,
        "frozen_exact_predictions": evaluation.exact_accuracy == 1.0,
        "exact_pair_baseline_has_zero_pairs": exact_pair.paired == 0,
        "rii_002_exact_anchor_model_has_zero_links": len(old_exact_anchor.links) == 0,
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
            "paired_predictions": exact_pair.paired,
            "exact_accuracy": exact_pair.exact_accuracy,
        },
        "rii_002_exact_anchor_baseline": {
            "surface_links": len(old_exact_anchor.links)
        },
        "independent_target_control": {"context_roles": len(control_model.roles)},
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
