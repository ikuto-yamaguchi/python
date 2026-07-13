from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phase18d1_dataset_to_program_meta_learner import (
    EvaluationError,
    Expr,
    _example_signature,
    _probe_examples,
    canonical,
    decode_value,
    enumerate_expressions,
    evaluate_expr,
    value_kind,
)


class NoLatentPartitionError(ValueError):
    """No exact minimum-support partition is expressible in the frozen DSL."""


class NonIdentifiablePartitionError(ValueError):
    """Several behaviorally distinct minimum partitions explain the stream."""


class NonIdentifiableRoutingError(ValueError):
    """The supplied support examples do not select one latent program."""


@dataclass(frozen=True)
class StreamSignature:
    input_types: tuple[str, ...]
    output_type: str

    def render(self) -> str:
        return f"({','.join(self.input_types)})->{self.output_type}"


@dataclass(frozen=True)
class CandidateBehavior:
    expression: Expr
    local_mask: int
    probe_signature: tuple[Any, ...]
    cost: int


@dataclass(frozen=True)
class LatentProgram:
    signature: StreamSignature
    expression: Expr
    covered_indices: tuple[int, ...]
    probe_signature: tuple[Any, ...]
    cost: int

    @property
    def payload_bits(self) -> int:
        return len(self.expression.render().encode("utf-8")) * 8

    def predict(self, inputs: Mapping[str, Any]) -> Any:
        normalized = _normalize_inputs(inputs)
        environment = {
            name: decode_value(value)
            for name, value in normalized.items()
        }
        return evaluate_expr(self.expression, environment)

    def behavior_key(self) -> tuple[Any, ...]:
        return (self.signature, self.probe_signature)


@dataclass(frozen=True)
class PartitionStats:
    expressions_evaluated: int
    candidate_behaviors: int
    exact_cover_nodes: int
    optimum_solutions: int


@dataclass(frozen=True)
class LatentPartition:
    programs: tuple[LatentProgram, ...]
    stats: PartitionStats

    def fingerprint(self) -> tuple[Any, ...]:
        return tuple(sorted(program.behavior_key() for program in self.programs, key=repr))


def _normalize_inputs(inputs: Mapping[str, Any]) -> dict[str, Any]:
    return {f"v{index}": value for index, value in enumerate(inputs.values())}


def _normalize_example(example: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "inputs": _normalize_inputs(example["inputs"]),
        "output": example["output"],
    }


def _signature(example: Mapping[str, Any]) -> StreamSignature:
    normalized = _normalize_example(example)
    return StreamSignature(
        tuple(value_kind(decode_value(value)) for value in normalized["inputs"].values()),
        value_kind(decode_value(normalized["output"])),
    )


def load_stream(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).parents[2] / "data" / "phase18d3_unlabeled_stream.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported stream schema")
    return payload


def _candidate_behaviors(
    examples: Sequence[dict[str, Any]],
    signature: StreamSignature,
    *,
    max_cost: int,
    minimum_support: int,
) -> tuple[tuple[CandidateBehavior, ...], int]:
    input_types = {f"v{index}": kind for index, kind in enumerate(signature.input_types)}
    by_cost = enumerate_expressions(input_types, signature.output_type, max_cost)
    probes = _probe_examples(input_types)
    deduplicated: dict[tuple[int, tuple[Any, ...]], CandidateBehavior] = {}
    expressions_evaluated = 0

    for cost in range(1, max_cost + 1):
        for expression in by_cost.get(cost, ()):
            if expression.result_type != signature.output_type:
                continue
            expressions_evaluated += 1
            mask = 0
            for index, example in enumerate(examples):
                try:
                    prediction = evaluate_expr(
                        expression,
                        {
                            name: decode_value(value)
                            for name, value in example["inputs"].items()
                        },
                    )
                except EvaluationError:
                    continue
                if canonical(prediction) == canonical(decode_value(example["output"])):
                    mask |= 1 << index
            if mask.bit_count() < minimum_support:
                continue
            probe_signature = _example_signature(expression, probes)
            key = (mask, probe_signature)
            candidate = CandidateBehavior(expression, mask, probe_signature, cost)
            existing = deduplicated.get(key)
            if existing is None or (candidate.cost, candidate.expression.render()) < (
                existing.cost,
                existing.expression.render(),
            ):
                deduplicated[key] = candidate

    return tuple(deduplicated.values()), expressions_evaluated


def _exact_disjoint_cover(
    candidates: Sequence[CandidateBehavior],
    example_count: int,
) -> tuple[tuple[CandidateBehavior, ...], int, int]:
    full_mask = (1 << example_count) - 1
    by_bit: dict[int, list[CandidateBehavior]] = defaultdict(list)
    for candidate in candidates:
        for bit in range(example_count):
            if candidate.local_mask & (1 << bit):
                by_bit[bit].append(candidate)
    for rows in by_bit.values():
        rows.sort(
            key=lambda candidate: (
                -candidate.local_mask.bit_count(),
                candidate.cost,
                candidate.expression.render(),
            )
        )

    best_score: tuple[int, int] | None = None
    best_solutions: dict[tuple[Any, ...], tuple[CandidateBehavior, ...]] = {}
    nodes = 0

    def search(covered: int, chosen: tuple[CandidateBehavior, ...], total_cost: int) -> None:
        nonlocal best_score, nodes
        nodes += 1
        if covered == full_mask:
            score = (len(chosen), total_cost)
            key = tuple(
                sorted(
                    (
                        candidate.local_mask,
                        candidate.probe_signature,
                    )
                    for candidate in chosen
                , key=repr)
            )
            if best_score is None or score < best_score:
                best_score = score
                best_solutions.clear()
                best_solutions[key] = chosen
            elif score == best_score:
                best_solutions.setdefault(key, chosen)
            return

        if best_score is not None and len(chosen) >= best_score[0]:
            return

        uncovered_bits = [
            bit for bit in range(example_count) if not covered & (1 << bit)
        ]
        bit = min(
            uncovered_bits,
            key=lambda index: sum(
                1
                for candidate in by_bit.get(index, ())
                if not candidate.local_mask & covered
            ),
        )
        options = [
            candidate
            for candidate in by_bit.get(bit, ())
            if not candidate.local_mask & covered
        ]
        if not options:
            return
        for candidate in options:
            search(
                covered | candidate.local_mask,
                chosen + (candidate,),
                total_cost + candidate.cost,
            )

    search(0, (), 0)
    if best_score is None:
        raise NoLatentPartitionError("no exact disjoint cover")
    if len(best_solutions) != 1:
        raise NonIdentifiablePartitionError(
            f"minimum score {best_score}: {len(best_solutions)} behavior partitions"
        )
    return next(iter(best_solutions.values())), nodes, len(best_solutions)


def discover_partition(
    stream: Sequence[Mapping[str, Any]],
    *,
    max_cost: int = 3,
    minimum_support: int = 5,
) -> LatentPartition:
    grouped: dict[StreamSignature, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for global_index, raw_example in enumerate(stream):
        normalized = _normalize_example(raw_example)
        grouped[_signature(raw_example)].append((global_index, normalized))

    programs: list[LatentProgram] = []
    expressions_evaluated = candidate_count = nodes = optimums = 0
    for signature, rows in grouped.items():
        local_examples = [example for _, example in rows]
        candidates, evaluated = _candidate_behaviors(
            local_examples,
            signature,
            max_cost=max_cost,
            minimum_support=minimum_support,
        )
        if not candidates:
            raise NoLatentPartitionError(
                f"no candidate with support {minimum_support} for {signature.render()}"
            )
        chosen, local_nodes, solution_count = _exact_disjoint_cover(
            candidates, len(local_examples)
        )
        expressions_evaluated += evaluated
        candidate_count += len(candidates)
        nodes += local_nodes
        optimums += solution_count
        for candidate in chosen:
            covered = tuple(
                rows[local_index][0]
                for local_index in range(len(rows))
                if candidate.local_mask & (1 << local_index)
            )
            programs.append(
                LatentProgram(
                    signature,
                    candidate.expression,
                    covered,
                    candidate.probe_signature,
                    candidate.cost,
                )
            )

    return LatentPartition(
        tuple(sorted(programs, key=lambda program: repr(program.behavior_key()))),
        PartitionStats(expressions_evaluated, candidate_count, nodes, optimums),
    )


def route_from_support(
    partition: LatentPartition,
    support: Sequence[Mapping[str, Any]],
) -> LatentProgram:
    if not support:
        raise NonIdentifiableRoutingError("support is empty")
    signature = _signature(support[0])
    if any(_signature(example) != signature for example in support):
        raise NonIdentifiableRoutingError("support type changed")
    matches: list[LatentProgram] = []
    for program in partition.programs:
        if program.signature != signature:
            continue
        valid = True
        for example in support:
            try:
                prediction = program.predict(example["inputs"])
            except EvaluationError:
                valid = False
                break
            if canonical(prediction) != canonical(decode_value(example["output"])):
                valid = False
                break
        if valid:
            matches.append(program)
    behavior_matches = {program.behavior_key(): program for program in matches}
    if len(behavior_matches) != 1:
        raise NonIdentifiableRoutingError(
            f"support selects {len(behavior_matches)} behaviors"
        )
    return next(iter(behavior_matches.values()))


def evaluate_episodes(
    partition: LatentPartition,
    episodes: Sequence[Mapping[str, Any]],
) -> tuple[int, int, int]:
    correct = covered = total = 0
    for episode in episodes:
        total += len(episode["queries"])
        try:
            program = route_from_support(partition, episode["support"])
        except NonIdentifiableRoutingError:
            continue
        covered += len(episode["queries"])
        for query in episode["queries"]:
            try:
                prediction = program.predict(query["inputs"])
            except EvaluationError:
                continue
            correct += canonical(prediction) == canonical(decode_value(query["output"]))
    return correct, covered, total


def audit_gold_separation(
    partition: LatentPartition,
    stream: Sequence[Mapping[str, Any]],
) -> bool:
    recovered: set[str] = set()
    for program in partition.programs:
        labels = {str(stream[index]["gold"]) for index in program.covered_indices}
        if len(labels) != 1:
            return False
        recovered.update(labels)
    return recovered == {str(example["gold"]) for example in stream}


def _ambiguous_support_rejected(partition: LatentPartition) -> bool:
    support = ({"inputs": {"u": 0, "v": 0}, "output": 0},)
    try:
        route_from_support(partition, support)
    except NonIdentifiableRoutingError:
        return True
    return False


def _failure_controls(payload: Mapping[str, Any]) -> dict[str, bool]:
    initial = tuple(payload["stream"])
    post = tuple(payload["post_freeze_stream"])
    controls: dict[str, bool] = {}
    try:
        discover_partition(post[:4])
    except NoLatentPartitionError:
        controls["subminimum_cluster_abstains"] = True
    else:
        controls["subminimum_cluster_abstains"] = False

    contradictory = initial + (
        {"inputs": {"u": 11, "v": 13}, "output": 999, "gold": "audit-only"},
    )
    try:
        discover_partition(contradictory)
    except NoLatentPartitionError:
        controls["uncovered_outlier_abstains"] = True
    else:
        controls["uncovered_outlier_abstains"] = False
    return controls


def run() -> dict[str, Any]:
    payload = load_stream()
    initial_stream = tuple(payload["stream"])
    post_stream = tuple(payload["post_freeze_stream"])
    initial = discover_partition(initial_stream)
    initial_correct, initial_covered, initial_total = evaluate_episodes(
        initial, payload["episodes"]
    )

    frozen_fingerprint = set(initial.fingerprint())
    final_stream = initial_stream + post_stream
    final = discover_partition(final_stream)
    all_episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    final_correct, final_covered, final_total = evaluate_episodes(final, all_episodes)
    old_programs_unchanged = frozen_fingerprint.issubset(set(final.fingerprint()))

    reversed_partition = discover_partition(tuple(reversed(initial_stream)))
    relabeled = tuple({**example, "gold": "ignored"} for example in initial_stream)
    relabeled_partition = discover_partition(relabeled)
    controls = _failure_controls(payload)
    source = inspect.getsource(inspect.getmodule(run))
    gold_names_absent_from_source = all(
        str(example["gold"]) not in source for example in final_stream
    )

    checks = {
        "initial_task_count_inferred": len(initial.programs) == 7,
        "post_freeze_task_count_inferred": len(final.programs) == 8,
        "initial_gold_partition_recovered": audit_gold_separation(initial, initial_stream),
        "final_gold_partition_recovered": audit_gold_separation(final, final_stream),
        "initial_query_accuracy": initial_correct == initial_total,
        "initial_query_coverage": initial_covered == initial_total,
        "post_freeze_query_accuracy": final_correct == final_total,
        "post_freeze_query_coverage": final_covered == final_total,
        "old_programs_unchanged": old_programs_unchanged,
        "stream_order_invariance": initial.fingerprint() == reversed_partition.fingerprint(),
        "audit_labels_not_used": initial.fingerprint() == relabeled_partition.fingerprint(),
        "ambiguous_support_rejected": _ambiguous_support_rejected(final),
        "failure_controls": all(controls.values()),
        "gold_program_names_absent_from_source": gold_names_absent_from_source,
        "no_task_id_in_learning_stream": all("id" not in example for example in final_stream),
    }

    return {
        "campaign": {
            "name": "phase18d3-latent-task-partition-c1",
            "explicit_task_ids": False,
            "explicit_task_count": False,
            "structured_input_output": True,
            "support_examples_used_for_query_routing": True,
            "source_changes_for_post_freeze_task": 0,
        },
        "induction": {
            "initial_examples": len(initial_stream),
            "initial_latent_programs": len(initial.programs),
            "post_freeze_examples": len(post_stream),
            "final_latent_programs": len(final.programs),
            "initial_programs": [program.expression.render() for program in initial.programs],
            "final_programs": [program.expression.render() for program in final.programs],
        },
        "evaluation": {
            "initial_correct": initial_correct,
            "initial_covered": initial_covered,
            "initial_total": initial_total,
            "final_correct": final_correct,
            "final_covered": final_covered,
            "final_total": final_total,
        },
        "continual_learning": {
            "old_programs_unchanged": old_programs_unchanged,
            "new_programs_discovered_from_appended_examples": len(final.programs) - len(initial.programs),
        },
        "controls": controls,
        "resources": {
            "initial_expressions_evaluated": initial.stats.expressions_evaluated,
            "final_expressions_evaluated": final.stats.expressions_evaluated,
            "initial_candidate_behaviors": initial.stats.candidate_behaviors,
            "final_candidate_behaviors": final.stats.candidate_behaviors,
            "initial_exact_cover_nodes": initial.stats.exact_cover_nodes,
            "final_exact_cover_nodes": final.stats.exact_cover_nodes,
            "learned_payload_bits": sum(program.payload_bits for program in final.programs),
            "maximum_program_cost": 3,
            "minimum_cluster_support": 5,
            "source_bytes": len(Path(__file__).read_bytes()),
            "data_bytes": len((Path(__file__).parents[2] / "data" / "phase18d3_unlabeled_stream.json").read_bytes()),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "latent_task_partition_without_ids": all(checks.values()),
            "few_shot_routing_without_task_name": all(checks.values()),
            "raw_unlabeled_pretraining": False,
            "autonomous_type_system": False,
            "open_ended_primitive_invention": False,
            "llm_like_general_learning": False,
            "general_intelligence": False,
        },
        "limitations": [
            "Outputs are supervised and examples are already structured into input/output records.",
            "A human-designed type system and frozen primitive DSL remain.",
            "Queries receive one or more support input/output examples; routing without any local evidence is not identifiable.",
            "The exact-cover search is exponential and currently demonstrated only on small streams.",
            "Minimum cluster support is fixed at five examples.",
        ],
    }


def markdown(payload: Mapping[str, Any]) -> str:
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resources"]
    return f"""# Phase 18d-3 results: latent task partition without task IDs

- Mixed initial examples: **{induction['initial_examples']}**
- Inferred initial latent programs: **{induction['initial_latent_programs']}**
- Appended post-freeze examples: **{induction['post_freeze_examples']}**
- Inferred final latent programs: **{induction['final_latent_programs']}**
- Initial support-routed held-out: **{evaluation['initial_correct']}/{evaluation['initial_total']}**
- Final support-routed held-out: **{evaluation['final_correct']}/{evaluation['final_total']}**
- Source changes for the appended task: **{payload['campaign']['source_changes_for_post_freeze_task']}**
- Old programs unchanged: **{payload['continual_learning']['old_programs_unchanged']}**
- Final learned payload: **{resources['learned_payload_bits']} bits**
- Final expression evaluations / exact-cover nodes: **{resources['final_expressions_evaluated']} / {resources['final_exact_cover_nodes']}**

A minimum-description exact partition recovered heterogeneous latent programs from a shuffled stream with no task IDs or declared task count. A local support example selected the relevant learned behavior for each query. This removes explicit task labels in the controlled typed setting, but it is still supervised program induction rather than LLM-scale raw-data learning.
"""


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d3.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
