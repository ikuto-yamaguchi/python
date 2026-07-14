from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import ceil, log2
from random import Random
from typing import Sequence

from .cap_gen_002_raw_interchange_induction import (
    DiscoveryConfig,
    HiddenEpisode,
    RelationLink,
    SlotTemplate,
    _extract_slot_templates,
    _pair_occurrences,
    boundary_scores,
    discover_interchange_model,
    find_template_occurrences,
)


INSTRUCTIONS = ("INC", "DEC", "NOT", "EMIT")


@dataclass(frozen=True)
class LoopProgram:
    """One resource-bounded loop over a discovered source span.

    `reverse` selects the initial traversal direction. The body is not a semantic task
    name; it is composed from byte-level state updates and output operations. The loop is
    intentionally weaker than a universal machine, but it can synthesize length-changing
    programs that the previous affine transducer family cannot represent.
    """

    reverse: bool
    body: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.body or self.body[-1] != "EMIT":
            raise ValueError("program body must end by emitting observable output")
        if any(instruction not in INSTRUCTIONS for instruction in self.body):
            raise ValueError("unknown loop instruction")

    @property
    def signature(self) -> tuple[bool, tuple[str, ...]]:
        return (self.reverse, self.body)

    @property
    def description_bits(self) -> int:
        # Loop framing, direction bit, and a fixed-width opcode stream.
        return 5 + 1 + 3 * len(self.body)

    @property
    def operations_per_input_byte(self) -> int:
        return 1 + len(self.body)

    def apply(self, source: bytes) -> bytes:
        output: list[int] = []
        values = reversed(source) if self.reverse else source
        for value in values:
            accumulator = value
            for instruction in self.body:
                if instruction == "INC":
                    accumulator = (accumulator + 1) & 0xFF
                elif instruction == "DEC":
                    accumulator = (accumulator - 1) & 0xFF
                elif instruction == "NOT":
                    accumulator = (~accumulator) & 0xFF
                elif instruction == "EMIT":
                    output.append(accumulator)
                else:  # pragma: no cover - guarded by __post_init__
                    raise ValueError(instruction)
        return bytes(output)


@dataclass(frozen=True)
class LoopDiscoveryStats:
    program_library_candidates: int
    relation_candidates_with_support: int
    program_candidates_executed: int
    validation_bytes_checked: int


@dataclass(frozen=True)
class LoopInterchangeModel:
    programs: tuple[LoopProgram, ...]
    links: tuple[RelationLink, ...]
    config: DiscoveryConfig
    stats: LoopDiscoveryStats

    @property
    def learned_payload_bits(self) -> int:
        program_index_bits = 0 if len(self.programs) <= 1 else ceil(log2(len(self.programs)))
        return sum(program.description_bits for program in self.programs) + sum(
            8 * sum(len(part) for part in link.source + link.target)
            + program_index_bits
            + ceil(log2(self.config.maximum_relation_distance + 1))
            + 2 * ceil(log2(self.config.maximum_gap + 1))
            for link in self.links
        )


@dataclass(frozen=True)
class LoopFrozenEvaluation:
    target_spans: int
    covered_spans: int
    exact_spans: int
    inference_operations: int

    @property
    def coverage(self) -> float:
        return self.covered_spans / self.target_spans if self.target_spans else 0.0

    @property
    def exact_accuracy(self) -> float:
        return self.exact_spans / self.target_spans if self.target_spans else 0.0


@dataclass(frozen=True)
class HiddenLoopRelation:
    source: tuple[bytes, bytes]
    target: tuple[bytes, bytes]
    program: LoopProgram


def enumerate_loop_programs(maximum_body_length: int = 5) -> tuple[LoopProgram, ...]:
    if maximum_body_length < 1:
        raise ValueError("maximum body length must be positive")
    candidates: list[LoopProgram] = []
    for reverse in (False, True):
        for body_length in range(1, maximum_body_length + 1):
            for body in product(INSTRUCTIONS, repeat=body_length):
                if body[-1] != "EMIT":
                    continue
                candidates.append(LoopProgram(reverse, body))
    candidates.sort(key=lambda row: (row.description_bits, row.reverse, row.body))
    return tuple(candidates)


DEFAULT_PROGRAM_LIBRARY = enumerate_loop_programs()


def _synthesize_loop_program(
    examples: Sequence[tuple[bytes, bytes]],
    program_library: Sequence[LoopProgram],
) -> tuple[LoopProgram | None, int]:
    examined = 0
    for program in program_library:
        examined += 1
        if all(program.apply(source) == target for source, target in examples):
            return program, examined
    return None, examined


def _relation_gain_bits(
    source: SlotTemplate,
    target: SlotTemplate,
    program: LoopProgram,
    pairs: Sequence[tuple[object, object]],
    config: DiscoveryConfig,
) -> int:
    literal_bits = 8 * sum(len(target_row.value) for _source_row, target_row in pairs)
    link_bits = 8 * sum(len(part) for part in source.key + target.key)
    per_example_bits = (
        ceil(log2(config.maximum_relation_distance + 1))
        + ceil(log2(config.maximum_gap + 1))
    )
    encoded_bits = program.description_bits + link_bits + per_example_bits * len(pairs)
    return literal_bits - encoded_bits


def discover_loop_interchange_model(
    stream: bytes,
    config: DiscoveryConfig = DiscoveryConfig(maximum_gap=12),
    program_library: Sequence[LoopProgram] = DEFAULT_PROGRAM_LIBRARY,
) -> LoopInterchangeModel:
    """Joint raw-boundary discovery plus compositional loop-program synthesis."""

    config.validate()
    if not program_library:
        raise ValueError("program library must not be empty")
    templates, _slot_windows, _peak_entries = _extract_slot_templates(stream, config)

    raw_candidates: list[tuple[RelationLink, LoopProgram]] = []
    relation_candidates = program_executions = validation_bytes = 0
    for source in templates:
        for target in templates:
            if source.key == target.key:
                continue
            pairs = _pair_occurrences(source, target, config.maximum_relation_distance)
            if len(pairs) < config.minimum_relation_support:
                continue
            relation_candidates += 1
            validation_count = max(2, ceil(len(pairs) * config.validation_fraction))
            split = len(pairs) - validation_count
            if split < 2:
                continue

            program, examined = _synthesize_loop_program(
                [(source_row.value, target_row.value) for source_row, target_row in pairs[:split]],
                program_library,
            )
            program_executions += examined
            if program is None:
                continue

            valid = True
            for source_row, target_row in pairs[split:]:
                validation_bytes += len(target_row.value)
                if program.apply(source_row.value) != target_row.value:
                    valid = False
                    break
            if not valid:
                continue

            gain_bits = _relation_gain_bits(source, target, program, pairs, config)
            if gain_bits <= 0:
                continue
            raw_candidates.append(
                (
                    RelationLink(
                        source.key,
                        target.key,
                        -1,
                        split,
                        validation_count,
                        gain_bits,
                        tuple(source_row.boundary for source_row, _target_row in pairs),
                        tuple(target_row.boundary for _source_row, target_row in pairs),
                    ),
                    program,
                )
            )

    # Anchor descriptions of different lengths can identify the same exact target spans.
    # Keep the most compressive coding of each observed target-boundary footprint.
    best: dict[tuple[tuple[int, int], ...], tuple[RelationLink, LoopProgram]] = {}
    for link, program in raw_candidates:
        incumbent = best.get(link.target_boundaries)
        if incumbent is None or (
            link.gain_bits,
            -sum(len(part) for part in link.source + link.target),
        ) > (
            incumbent[0].gain_bits,
            -sum(len(part) for part in incumbent[0].source + incumbent[0].target),
        ):
            best[link.target_boundaries] = (link, program)

    selected = sorted(best.values(), key=lambda row: (-row[0].gain_bits, row[0].target))
    programs: list[LoopProgram] = []
    program_indices: dict[tuple[bool, tuple[str, ...]], int] = {}
    links: list[RelationLink] = []
    for link, program in selected:
        index = program_indices.get(program.signature)
        if index is None:
            index = len(programs)
            program_indices[program.signature] = index
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

    return LoopInterchangeModel(
        tuple(programs),
        tuple(links),
        config,
        LoopDiscoveryStats(
            len(program_library),
            relation_candidates,
            program_executions,
            validation_bytes,
        ),
    )


def evaluate_frozen_loop_model(
    model: LoopInterchangeModel,
    stream: bytes,
) -> LoopFrozenEvaluation:
    target_spans = covered = exact = operations = 0
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
        for source_row, target_row in _pair_occurrences(
            source, target, model.config.maximum_relation_distance
        ):
            program = model.programs[link.program_index]
            prediction = program.apply(source_row.value)
            covered += 1
            exact += int(prediction == target_row.value)
            operations += len(source_row.value) * program.operations_per_input_byte
    return LoopFrozenEvaluation(target_spans, covered, exact, operations)


def _random_bytes(rng: Random, minimum: int, maximum: int) -> bytes:
    alphabet = b"abcdefghjkmnpqrstuvwxyz23456789"
    return bytes(rng.choice(alphabet) for _ in range(rng.randint(minimum, maximum)))


def make_loop_microprogram_stream(
    *,
    seed: int,
    instances_per_relation: int,
    independent_targets: bool = False,
) -> tuple[bytes, tuple[HiddenLoopRelation, ...], tuple[HiddenEpisode, ...]]:
    rng = Random(seed)
    relations = (
        HiddenLoopRelation((b"ab[", b"]cd"), (b"ef{", b"}gh"), LoopProgram(True, ("EMIT",))),
        HiddenLoopRelation((b"jk<", b">lm"), (b"np(", b")qr"), LoopProgram(True, ("EMIT",))),
        HiddenLoopRelation(
            (b"st[", b"]uv"),
            (b"wx{", b"}yz"),
            LoopProgram(False, ("INC", "INC", "INC", "EMIT")),
        ),
        HiddenLoopRelation(
            (b"12<", b">34"),
            (b"56(", b")78"),
            LoopProgram(False, ("INC", "INC", "INC", "EMIT")),
        ),
        HiddenLoopRelation(
            (b"ka[", b"]la"),
            (b"ma{", b"}na"),
            LoopProgram(False, ("EMIT", "EMIT")),
        ),
        HiddenLoopRelation(
            (b"pa<", b">ra"),
            (b"sa(", b")ta"),
            LoopProgram(False, ("EMIT", "EMIT")),
        ),
    )
    schedule = [
        relation_index
        for _ in range(instances_per_relation)
        for relation_index in range(len(relations))
    ]
    rng.shuffle(schedule)

    pieces: list[bytes] = []
    episodes: list[HiddenEpisode] = []
    position = 0
    for relation_index in schedule:
        relation = relations[relation_index]
        source_value = _random_bytes(rng, 4, 6)
        target_value = (
            _random_bytes(rng, 4, 12)
            if independent_targets
            else relation.program.apply(source_value)
        )
        prefix = _random_bytes(rng, 1, 5)
        middle = _random_bytes(rng, 1, 7)
        suffix = _random_bytes(rng, 1, 5)
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
    return b"".join(pieces), relations, tuple(episodes)


def run_experiment() -> dict[str, object]:
    config = DiscoveryConfig(maximum_gap=12)
    training_stream, hidden_relations, episodes = make_loop_microprogram_stream(
        seed=7,
        instances_per_relation=16,
    )
    evaluation_stream, _relations2, _episodes2 = make_loop_microprogram_stream(
        seed=97,
        instances_per_relation=8,
    )
    control_stream, _relations3, _episodes3 = make_loop_microprogram_stream(
        seed=1701,
        instances_per_relation=16,
        independent_targets=True,
    )

    model = discover_loop_interchange_model(training_stream, config)
    evaluation = evaluate_frozen_loop_model(model, evaluation_stream)
    control = discover_loop_interchange_model(control_stream, config)
    old_affine_model = discover_interchange_model(training_stream, config)
    boundaries = boundary_scores(model, episodes)
    expected_programs = {relation.program.signature for relation in hidden_relations}
    discovered_programs = {program.signature for program in model.programs}

    checks = {
        "one_raw_stream_without_boundaries": isinstance(training_stream, bytes),
        "all_boundaries_recovered": boundaries["recall"] == 1.0,
        "no_false_boundaries": boundaries["precision"] == 1.0,
        "six_surface_links_discovered": len(model.links) == 6,
        "three_programs_shared_across_surfaces": len(model.programs) == 3,
        "hidden_program_set_recovered": discovered_programs == expected_programs,
        "length_changing_duplicate_discovered": any(
            program.body == ("EMIT", "EMIT") for program in model.programs
        ),
        "frozen_exact_generalization": (
            evaluation.coverage == 1.0 and evaluation.exact_accuracy == 1.0
        ),
        "old_affine_family_misses_duplicate_links": len(old_affine_model.links) == 4,
        "independent_control_rejected": len(control.links) == 0,
        "positive_mdl_gain": all(link.gain_bits > 0 for link in model.links),
    }
    return {
        "capability_id": "CAP-GEN-002-RII-002",
        "claim": (
            "joint raw-span discovery and compositional loop-microprogram synthesis, "
            "including a length-changing transformation outside the RII-001 affine family"
        ),
        "claim_boundary": (
            "loop-normal-form byte VM over synthetic repeated contexts; not a universal "
            "operator language, natural concept learning, public-axis improvement, or human-level intelligence"
        ),
        "training": {
            "raw_bytes": len(training_stream),
            "event_boundaries_visible_to_learner": False,
            "aligned_examples_visible_to_learner": False,
            "task_ids_visible_to_learner": False,
        },
        "program_search": {
            "instruction_set": list(INSTRUCTIONS),
            "program_library_candidates": model.stats.program_library_candidates,
            "program_candidates_executed": model.stats.program_candidates_executed,
            "relation_candidates_with_support": model.stats.relation_candidates_with_support,
            "validation_bytes_checked": model.stats.validation_bytes_checked,
        },
        "model": {
            "surface_links": len(model.links),
            "shared_programs": len(model.programs),
            "programs": [
                {"reverse": program.reverse, "body": list(program.body)}
                for program in model.programs
            ],
            "learned_payload_bits": model.learned_payload_bits,
            "minimum_link_gain_bits": min(link.gain_bits for link in model.links),
        },
        "boundary_recovery": boundaries,
        "frozen_evaluation": {
            "target_spans": evaluation.target_spans,
            "coverage": evaluation.coverage,
            "exact_accuracy": evaluation.exact_accuracy,
            "inference_operations": evaluation.inference_operations,
        },
        "rii_001_affine_baseline": {
            "surface_links": len(old_affine_model.links),
            "shared_programs": len(old_affine_model.programs),
            "missed_length_changing_surface_links": 6 - len(old_affine_model.links),
        },
        "independent_target_control": {"accepted_links": len(control.links)},
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_experiment(), ensure_ascii=False, indent=2, sort_keys=True))
