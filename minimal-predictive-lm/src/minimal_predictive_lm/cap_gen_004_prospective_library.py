from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from math import log2
from typing import Iterable, Sequence

Program = tuple[str, ...]
Helper = tuple[str, ...]


def contiguous_subprograms(
    program: Program,
    *,
    min_length: int = 2,
    max_length: int = 4,
) -> set[Helper]:
    output: set[Helper] = set()
    for length in range(min_length, min(max_length, len(program)) + 1):
        for start in range(len(program) - length + 1):
            output.add(program[start : start + length])
    return output


def encoded_length(program: Program, library: set[Helper]) -> int:
    """Shortest number of primitive/helper calls for one exact program."""
    size = len(program)
    best = [10**9] * (size + 1)
    best[size] = 0
    for index in range(size - 1, -1, -1):
        best[index] = 1 + best[index + 1]
        for helper in library:
            end = index + len(helper)
            if program[index:end] == helper:
                best[index] = min(best[index], 1 + best[end])
    return best[0]


def exhaustive_search_nodes(
    program: Program,
    library: set[Helper],
    primitive_vocabulary: int,
) -> int:
    """Exact prefix-coded exhaustive-search size at the shortest length.

    The code alphabet includes the primitive vocabulary and current helpers, so
    helper-induced alphabet growth is charged rather than ignored.
    """
    alphabet = primitive_vocabulary + len(library)
    bits_per_call = log2(alphabet)
    bits = bits_per_call * encoded_length(program, library)
    return int(2**bits)


def _contains_subprogram(container: Helper, candidate: Helper) -> bool:
    return any(
        container[start : start + len(candidate)] == candidate
        for start in range(len(container) - len(candidate) + 1)
    )


@dataclass
class RunLengthForecaster:
    """Causal cross-task forecaster over maximal recurring subprogram runs."""

    completed_lengths: list[int] = field(default_factory=list)
    active_lengths: dict[Helper, int] = field(default_factory=dict)

    def update(self, present: set[Helper]) -> None:
        ending = {
            helper: length
            for helper, length in self.active_lengths.items()
            if helper not in present and length >= 2
        }
        # Overlapping subprograms from one motif are not independent evidence.
        for helper, length in ending.items():
            dominated = any(
                other_length == length
                and len(other) > len(helper)
                and _contains_subprogram(other, helper)
                for other, other_length in ending.items()
            )
            if not dominated:
                self.completed_lengths.append(length)

        for helper in list(self.active_lengths):
            if helper not in present:
                del self.active_lengths[helper]
        for helper in present:
            self.active_lengths[helper] = self.active_lengths.get(helper, 0) + 1

    def expected_remaining(self, current_length: int, *, min_runs: int = 2) -> float:
        eligible = [
            total
            for total in self.completed_lengths
            if total >= current_length
        ]
        if len(eligible) < min_runs:
            return 0.0
        return sum(total - current_length for total in eligible) / len(eligible)


@dataclass(frozen=True)
class AdmissionEvent:
    task_index: int
    helper: Helper
    kind: str
    score: float
    expected_remaining: float


@dataclass(frozen=True)
class LearnerResult:
    mode: str
    search_nodes: int
    induction_operations: int
    permanent_storage_tokens: int
    probation_storage_tokens: int
    total_cost: int
    permanent_library: tuple[Helper, ...]
    events: tuple[AdmissionEvent, ...]


class OnlineLibraryLearner:
    """No-library, retrospective, or prospective online library learner.

    Prospective-only admissions enter a one-task probationary cache. They become
    permanent only if the immediately following task obtains a real encoding
    benefit. This bounds damage when the task generator changes unexpectedly.
    """

    def __init__(
        self,
        mode: str,
        *,
        primitive_vocabulary: int,
        minimum_completed_runs: int = 2,
    ) -> None:
        if mode not in {"none", "retrospective", "prospective"}:
            raise ValueError(f"unknown mode: {mode}")
        self.mode = mode
        self.primitive_vocabulary = primitive_vocabulary
        self.minimum_completed_runs = minimum_completed_runs

    def run(self, programs: Sequence[Program]) -> LearnerResult:
        permanent: set[Helper] = set()
        probation: set[Helper] = set()
        history: list[Program] = []
        forecaster = RunLengthForecaster()
        search_nodes = 0
        induction_operations = 0
        probation_storage = 0
        events: list[AdmissionEvent] = []

        for task_index, program in enumerate(programs):
            active_library = permanent | probation
            search_nodes += exhaustive_search_nodes(
                program,
                active_library,
                self.primitive_vocabulary,
            )

            # Resolve last task's real-option admissions after observing this task.
            for helper in sorted(probation):
                gain = encoded_length(program, permanent) - encoded_length(
                    program,
                    permanent | {helper},
                )
                probation_storage += len(helper) + 1
                if gain > 0:
                    permanent.add(helper)
                    events.append(
                        AdmissionEvent(
                            task_index=task_index,
                            helper=helper,
                            kind="confirmed",
                            score=float(gain),
                            expected_remaining=0.0,
                        )
                    )
            probation.clear()

            history.append(program)
            present = contiguous_subprograms(program)
            forecaster.update(present)
            scored: list[tuple[float, int, int, Helper, str, float]] = []

            for helper in present:
                induction_operations += 1
                if self.mode == "none" or helper in permanent:
                    continue
                current_run = forecaster.active_lengths.get(helper, 0)
                if current_run < 2:
                    continue

                with_helper = permanent | {helper}
                past_gain = sum(
                    encoded_length(item, permanent)
                    - encoded_length(item, with_helper)
                    for item in history
                )
                current_gain = encoded_length(program, permanent) - encoded_length(
                    program,
                    with_helper,
                )
                definition_cost = len(helper) + 1
                retrospective_score = past_gain - definition_cost
                expected_remaining = 0.0
                if self.mode == "prospective":
                    expected_remaining = forecaster.expected_remaining(
                        current_run,
                        min_runs=self.minimum_completed_runs,
                    )
                prospective_score = retrospective_score + expected_remaining * current_gain

                if retrospective_score > 0:
                    scored.append(
                        (
                            retrospective_score,
                            current_gain,
                            len(helper),
                            helper,
                            "direct",
                            expected_remaining,
                        )
                    )
                elif self.mode == "prospective" and prospective_score > 0:
                    scored.append(
                        (
                            prospective_score,
                            current_gain,
                            len(helper),
                            helper,
                            "probation",
                            expected_remaining,
                        )
                    )

            if scored:
                scored.sort(reverse=True)
                score, _, _, helper, kind, expected_remaining = scored[0]
                if kind == "direct":
                    permanent.add(helper)
                else:
                    probation.add(helper)
                events.append(
                    AdmissionEvent(
                        task_index=task_index,
                        helper=helper,
                        kind=kind,
                        score=float(score),
                        expected_remaining=float(expected_remaining),
                    )
                )

        for helper in probation:
            probation_storage += len(helper) + 1

        permanent_storage = sum(len(helper) + 1 for helper in permanent)
        total_cost = (
            search_nodes
            + induction_operations
            + permanent_storage
            + probation_storage
        )
        return LearnerResult(
            mode=self.mode,
            search_nodes=search_nodes,
            induction_operations=induction_operations,
            permanent_storage_tokens=permanent_storage,
            probation_storage_tokens=probation_storage,
            total_cost=total_cost,
            permanent_library=tuple(sorted(permanent)),
            events=tuple(events),
        )


def helper_group(helper: Helper, prefix: str, *, length: int = 4) -> list[Program]:
    return [
        (f"{prefix}_pre{index}",) + helper + (f"{prefix}_post{index}",)
        for index in range(length)
    ]


def heterogeneous_curriculum() -> tuple[Program, ...]:
    groups = (
        ("list-a", ("map_inc", "filter_even", "reverse")),
        ("list-b", ("drop_null", "sort", "take3")),
        ("string", ("strip", "lower", "split")),
        ("grid", ("crop", "rotate90", "recolor")),
    )
    output: list[Program] = []
    for name, helper in groups:
        output.extend(helper_group(helper, name))
        output.append((f"{name}_gap",))
    return tuple(output)


def isolated_control() -> tuple[Program, ...]:
    return tuple(
        (f"x{index}a", f"x{index}b", f"x{index}c", f"x{index}d", f"x{index}e")
        for index in range(12)
    )


def duration_shift_control() -> tuple[Program, ...]:
    output: list[Program] = []
    for group_index, run_length in enumerate((4, 4, 2, 2)):
        helper = (
            f"h{group_index}a",
            f"h{group_index}b",
            f"h{group_index}c",
        )
        output.extend(helper_group(helper, f"shift{group_index}", length=run_length))
        output.append((f"shift{group_index}_gap",))
    return tuple(output)


def vocabulary_size(programs: Iterable[Program]) -> int:
    return len(set(chain.from_iterable(programs)))


def run_experiment() -> dict[str, object]:
    curriculum = heterogeneous_curriculum()
    vocabulary = vocabulary_size(curriculum)
    results = {
        mode: OnlineLibraryLearner(
            mode,
            primitive_vocabulary=vocabulary,
        ).run(curriculum)
        for mode in ("none", "retrospective", "prospective")
    }

    isolated = isolated_control()
    isolated_result = OnlineLibraryLearner(
        "prospective",
        primitive_vocabulary=vocabulary_size(isolated),
    ).run(isolated)

    shifted = duration_shift_control()
    shifted_vocabulary = vocabulary_size(shifted)
    shifted_retro = OnlineLibraryLearner(
        "retrospective",
        primitive_vocabulary=shifted_vocabulary,
    ).run(shifted)
    shifted_pro = OnlineLibraryLearner(
        "prospective",
        primitive_vocabulary=shifted_vocabulary,
    ).run(shifted)

    none = results["none"]
    retro = results["retrospective"]
    prospective = results["prospective"]
    prospective_options = [
        event for event in prospective.events if event.kind == "probation"
    ]

    return {
        "capability_id": "CAP-GEN-004-POLA-001",
        "hypothesis": (
            "a causal forecast of abstraction reuse duration can admit a "
            "probationary helper before retrospective compression justifies "
            "permanent admission"
        ),
        "curriculum": {
            "task_count": len(curriculum),
            "primitive_vocabulary": vocabulary,
            "semantic_families_for_evaluation_only": ["list", "string", "grid"],
            "family_labels_visible_to_learner": 0,
        },
        "costs": {
            "none": none.total_cost,
            "retrospective": retro.total_cost,
            "prospective": prospective.total_cost,
            "prospective_vs_retrospective_reduction": (
                retro.total_cost - prospective.total_cost
            ) / retro.total_cost,
            "prospective_vs_none_reduction": (
                none.total_cost - prospective.total_cost
            ) / none.total_cost,
        },
        "prospective": {
            "probation_events": len(prospective_options),
            "confirmed_events": sum(
                event.kind == "confirmed" for event in prospective.events
            ),
            "permanent_helpers": len(prospective.permanent_library),
            "probation_storage_tokens": prospective.probation_storage_tokens,
            "string_probation_task": next(
                event.task_index
                for event in prospective_options
                if event.helper == ("strip", "lower", "split")
            ),
            "grid_probation_task": next(
                event.task_index
                for event in prospective_options
                if event.helper == ("crop", "rotate90", "recolor")
            ),
        },
        "retrospective": {
            "string_admission_task": next(
                event.task_index
                for event in retro.events
                if event.helper == ("strip", "lower", "split")
            ),
            "grid_admission_task": next(
                event.task_index
                for event in retro.events
                if event.helper == ("crop", "rotate90", "recolor")
            ),
        },
        "controls": {
            "isolated_prospective_admissions": len(isolated_result.events),
            "duration_shift_regret": shifted_pro.total_cost - shifted_retro.total_cost,
            "duration_shift_probation_tokens": shifted_pro.probation_storage_tokens,
        },
        "passed": (
            prospective.total_cost < retro.total_cost < none.total_cost
            and len(prospective_options) == 2
            and isolated_result.events == ()
            and shifted_pro.total_cost - shifted_retro.total_cost <= 16
        ),
        "claim_boundary": (
            "The 2026 prospective-compression work establishes the normative "
            "principle and human evidence; POLA-001 is a candidate online "
            "algorithm that estimates reuse duration causally and uses a "
            "one-task real option. Novelty is not established until broader "
            "prior-art review and public heterogeneous benchmarks."
        ),
    }


def main() -> None:
    import json

    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
