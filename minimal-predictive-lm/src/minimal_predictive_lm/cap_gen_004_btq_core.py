from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence


Trace = tuple[str, ...]
TemplateSignature = tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]


@dataclass(frozen=True)
class TraceTemplate:
    prefix: tuple[str, ...]
    motif: tuple[str, ...]
    suffix: tuple[str, ...]
    min_repeats: int
    max_repeats: int

    @property
    def signature(self) -> TemplateSignature:
        return (self.prefix, self.motif, self.suffix)


@dataclass(frozen=True)
class Program:
    domain: str
    name: str
    source_tokens: tuple[str, ...]
    runner: Callable[[Any], tuple[Any, Trace]]

    def run(self, value: Any) -> tuple[Any, Trace]:
        return self.runner(value)


@dataclass(frozen=True)
class SynthesisTask:
    name: str
    domain: str
    train_examples: tuple[tuple[Any, Any], ...]
    test_examples: tuple[tuple[Any, Any], ...] = ()


@dataclass(frozen=True)
class SolvedTask:
    task_name: str
    domain: str
    program_name: str
    source_tokens: tuple[str, ...]
    template: TraceTemplate


@dataclass(frozen=True)
class TraceLibrary:
    signatures: tuple[TemplateSignature, ...]
    support: tuple[tuple[TemplateSignature, tuple[str, ...]], ...]


@dataclass(frozen=True)
class SearchResult:
    task_name: str
    exact_programs: tuple[str, ...]
    chosen_program: str | None
    train_exact: bool
    test_accuracy: float
    candidate_count: int
    candidate_executions: int


def _decompose_with_motif(
    sequence: Trace,
    prefix: tuple[str, ...],
    motif: tuple[str, ...],
    suffix: tuple[str, ...],
) -> int | None:
    if len(sequence) < len(prefix) + len(suffix):
        return None
    if sequence[: len(prefix)] != prefix:
        return None
    if suffix and sequence[-len(suffix) :] != suffix:
        return None

    stop = len(sequence) - len(suffix) if suffix else len(sequence)
    middle = sequence[len(prefix) : stop]
    if len(middle) % len(motif):
        return None
    repeats = len(middle) // len(motif)
    if middle != motif * repeats:
        return None
    return repeats


def infer_repeat_template(traces: Sequence[Trace]) -> TraceTemplate | None:
    """Infer one repeated-motif template without domain or source tokens."""
    if not traces:
        return None
    sequences = [tuple(trace) for trace in traces]
    minimum_length = min(len(sequence) for sequence in sequences)
    best: tuple[int, int, int, TraceTemplate] | None = None

    for prefix_length in range(minimum_length + 1):
        for suffix_length in range(minimum_length - prefix_length + 1):
            prefix = sequences[0][:prefix_length]
            suffix = sequences[0][-suffix_length:] if suffix_length else ()
            if any(
                sequence[:prefix_length] != prefix
                or (sequence[-suffix_length:] if suffix_length else ()) != suffix
                for sequence in sequences
            ):
                continue

            middles = [
                sequence[
                    prefix_length : len(sequence) - suffix_length
                    if suffix_length
                    else len(sequence)
                ]
                for sequence in sequences
            ]
            max_middle_length = max(len(middle) for middle in middles)

            for motif_length in range(1, max_middle_length + 1):
                source = next(
                    (middle for middle in middles if len(middle) >= motif_length),
                    None,
                )
                if source is None:
                    continue
                motif = source[:motif_length]
                repeats: list[int] = []
                for sequence in sequences:
                    count = _decompose_with_motif(
                        sequence,
                        prefix,
                        motif,
                        suffix,
                    )
                    if count is None:
                        break
                    repeats.append(count)
                else:
                    if max(repeats) == 0:
                        continue
                    description_length = (
                        len(prefix) + len(motif) + len(suffix) + 2
                    )
                    candidate = (
                        description_length,
                        -len(set(repeats)),
                        prefix_length + suffix_length,
                        TraceTemplate(
                            prefix=prefix,
                            motif=motif,
                            suffix=suffix,
                            min_repeats=min(repeats),
                            max_repeats=max(repeats),
                        ),
                    )
                    if best is None or candidate[:3] < best[:3]:
                        best = candidate

    if best is not None:
        return best[3]
    if all(sequence == sequences[0] for sequence in sequences):
        return TraceTemplate(
            prefix=sequences[0],
            motif=(),
            suffix=(),
            min_repeats=1,
            max_repeats=1,
        )
    return None


def exact_programs(
    programs: Sequence[Program],
    task: SynthesisTask,
) -> tuple[Program, ...]:
    return tuple(
        program
        for program in programs
        if all(
            program.run(input_value)[0] == expected
            for input_value, expected in task.train_examples
        )
    )


def solve_task(
    programs: Sequence[Program],
    task: SynthesisTask,
) -> SolvedTask:
    exact = exact_programs(programs, task)
    if len(exact) != 1:
        raise ValueError(
            f"{task.name} must have one exact program, found {len(exact)}"
        )
    program = exact[0]
    template = infer_repeat_template(
        tuple(
            program.run(input_value)[1]
            for input_value, _ in task.train_examples
        )
    )
    if template is None:
        raise ValueError(f"{task.name} has no reusable trace template")
    return SolvedTask(
        task_name=task.name,
        domain=task.domain,
        program_name=program.name,
        source_tokens=program.source_tokens,
        template=template,
    )


def induce_cross_domain_library(
    solved_tasks: Sequence[SolvedTask],
    minimum_domains: int = 2,
) -> TraceLibrary:
    by_signature: dict[
        TemplateSignature,
        list[SolvedTask],
    ] = defaultdict(list)
    for solved in solved_tasks:
        by_signature[solved.template.signature].append(solved)

    retained: list[TemplateSignature] = []
    support_rows: list[
        tuple[TemplateSignature, tuple[str, ...]]
    ] = []
    for signature, rows in sorted(by_signature.items(), key=repr):
        domains = tuple(sorted({row.domain for row in rows}))
        if len(domains) < minimum_domains:
            continue
        retained.append(signature)
        support_rows.append((signature, domains))

    return TraceLibrary(
        signatures=tuple(retained),
        support=tuple(support_rows),
    )


def source_ngram_overlap(
    solved_tasks: Sequence[SolvedTask],
    n: int = 2,
) -> tuple[tuple[str, ...], ...]:
    """A deliberately weak syntax-only control, not a SOTA baseline."""
    per_domain: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    for solved in solved_tasks:
        tokens = solved.source_tokens
        per_domain[solved.domain].update(
            tuple(tokens[index : index + n])
            for index in range(max(0, len(tokens) - n + 1))
        )
    if len(per_domain) < 2:
        return ()
    sets = list(per_domain.values())
    overlap = set.intersection(*sets)
    return tuple(sorted(overlap))


def build_trace_index(
    programs: Sequence[Program],
    probe_inputs: Sequence[Any],
) -> tuple[
    dict[TemplateSignature, tuple[Program, ...]],
    int,
]:
    rows: dict[TemplateSignature, list[Program]] = defaultdict(list)
    for program in programs:
        template = infer_repeat_template(
            tuple(program.run(value)[1] for value in probe_inputs)
        )
        if template is not None:
            rows[template.signature].append(program)
    frozen = {
        signature: tuple(programs_for_signature)
        for signature, programs_for_signature in rows.items()
    }
    return frozen, len(programs) * len(probe_inputs)


def guided_programs(
    index: dict[TemplateSignature, tuple[Program, ...]],
    library: TraceLibrary,
) -> tuple[Program, ...]:
    unique: dict[tuple[str, str], Program] = {}
    for signature in library.signatures:
        for program in index.get(signature, ()):
            unique[(program.domain, program.name)] = program
    return tuple(unique[key] for key in sorted(unique))


def evaluate_search(
    programs: Sequence[Program],
    task: SynthesisTask,
) -> SearchResult:
    exact = exact_programs(programs, task)
    chosen = exact[0] if len(exact) == 1 else None
    if chosen is None:
        test_accuracy = 0.0
    elif not task.test_examples:
        test_accuracy = 1.0
    else:
        test_accuracy = sum(
            chosen.run(input_value)[0] == expected
            for input_value, expected in task.test_examples
        ) / len(task.test_examples)

    return SearchResult(
        task_name=task.name,
        exact_programs=tuple(program.name for program in exact),
        chosen_program=chosen.name if chosen is not None else None,
        train_exact=chosen is not None,
        test_accuracy=test_accuracy,
        candidate_count=len(programs),
        candidate_executions=len(programs) * len(task.train_examples),
    )


def total_search_executions(results: Iterable[SearchResult]) -> int:
    return sum(result.candidate_executions for result in results)
