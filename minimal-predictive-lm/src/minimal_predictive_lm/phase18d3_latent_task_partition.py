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
    pass


class NonIdentifiablePartitionError(ValueError):
    pass


class NonIdentifiableRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class StreamSignature:
    input_types: tuple[str, ...]
    output_type: str

    def render(self) -> str:
        return f"({','.join(self.input_types)})->{self.output_type}"


@dataclass(frozen=True)
class Candidate:
    expression: Expr
    mask: int
    probe: tuple[Any, ...]
    cost: int


@dataclass(frozen=True)
class LatentProgram:
    signature: StreamSignature
    expression: Expr
    covered_indices: tuple[int, ...]
    probe: tuple[Any, ...]
    cost: int

    def behavior_key(self) -> tuple[Any, ...]:
        return (self.signature, self.probe)

    @property
    def payload_bits(self) -> int:
        return len(self.expression.render().encode("utf-8")) * 8

    def predict(self, raw_inputs: Mapping[str, Any]) -> Any:
        normalized = _normalize_inputs(raw_inputs)
        environment = {
            name: decode_value(value) for name, value in normalized.items()
        }
        return evaluate_expr(self.expression, environment)


@dataclass(frozen=True)
class PartitionStats:
    expressions_evaluated: int
    candidate_behaviors: int
    exact_cover_nodes: int


@dataclass(frozen=True)
class LatentPartition:
    programs: tuple[LatentProgram, ...]
    stats: PartitionStats

    def fingerprint(self) -> tuple[Any, ...]:
        return tuple(
            sorted(
                (program.behavior_key() for program in self.programs),
                key=repr,
            )
        )


def _normalize_inputs(inputs: Mapping[str, Any]) -> dict[str, Any]:
    return {f"v{index}": value for index, value in enumerate(inputs.values())}


def _normalize_example(example: Mapping[str, Any]) -> dict[str, Any]:
    return {"inputs": _normalize_inputs(example["inputs"]), "output": example["output"]}


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


def _candidate_set(
    examples: Sequence[dict[str, Any]],
    signature: StreamSignature,
    *,
    max_cost: int,
    minimum_support: int,
) -> tuple[tuple[Candidate, ...], int]:
    input_types = {f"v{i}": kind for i, kind in enumerate(signature.input_types)}
    by_cost = enumerate_expressions(input_types, signature.output_type, max_cost)
    probes = _probe_examples(input_types)
    unique: dict[tuple[int, tuple[Any, ...]], Candidate] = {}
    evaluated = 0

    for cost in range(1, max_cost + 1):
        for expression in by_cost.get(cost, ()):
            if expression.result_type != signature.output_type:
                continue
            evaluated += 1
            mask = 0
            for index, example in enumerate(examples):
                environment = {
                    name: decode_value(value)
                    for name, value in example["inputs"].items()
                }
                try:
                    predicted = evaluate_expr(expression, environment)
                except EvaluationError:
                    continue
                if canonical(predicted) == canonical(decode_value(example["output"])):
                    mask |= 1 << index
            if mask.bit_count() < minimum_support:
                continue
            probe = _example_signature(expression, probes)
            key = (mask, probe)
            candidate = Candidate(expression, mask, probe, cost)
            old = unique.get(key)
            if old is None or (cost, expression.render()) < (old.cost, old.expression.render()):
                unique[key] = candidate
    return tuple(unique.values()), evaluated


def _solve_exact_cover(
    candidates: Sequence[Candidate],
    example_count: int,
) -> tuple[tuple[Candidate, ...], int]:
    full = (1 << example_count) - 1
    by_bit: dict[int, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        for bit in range(example_count):
            if candidate.mask & (1 << bit):
                by_bit[bit].append(candidate)
    for rows in by_bit.values():
        rows.sort(key=lambda row: (-row.mask.bit_count(), row.cost, row.expression.render()))

    best_score: tuple[int, int] | None = None
    solutions: dict[tuple[Any, ...], tuple[Candidate, ...]] = {}
    nodes = 0

    def search(covered: int, chosen: tuple[Candidate, ...], cost: int) -> None:
        nonlocal best_score, nodes
        nodes += 1
        if covered == full:
            score = (len(chosen), cost)
            key = tuple(
                sorted(
                    ((row.mask, row.probe) for row in chosen),
                    key=repr,
                )
            )
            if best_score is None or score < best_score:
                best_score = score
                solutions.clear()
                solutions[key] = chosen
            elif score == best_score:
                solutions.setdefault(key, chosen)
            return
        if best_score is not None and len(chosen) >= best_score[0]:
            return

        uncovered = [bit for bit in range(example_count) if not covered & (1 << bit)]
        bit = min(
            uncovered,
            key=lambda item: sum(
                1 for row in by_bit.get(item, ()) if not row.mask & covered
            ),
        )
        options = [row for row in by_bit.get(bit, ()) if not row.mask & covered]
        for row in options:
            search(covered | row.mask, chosen + (row,), cost + row.cost)

    search(0, (), 0)
    if best_score is None:
        raise NoLatentPartitionError("no exact disjoint cover")
    if len(solutions) != 1:
        raise NonIdentifiablePartitionError(
            f"score={best_score}, behavior_partitions={len(solutions)}"
        )
    return next(iter(solutions.values())), nodes


def discover_partition(
    stream: Sequence[Mapping[str, Any]],
    *,
    max_cost: int = 3,
    minimum_support: int = 5,
) -> LatentPartition:
    groups: dict[StreamSignature, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for global_index, example in enumerate(stream):
        groups[_signature(example)].append((global_index, _normalize_example(example)))

    programs: list[LatentProgram] = []
    evaluated = candidate_count = nodes = 0
    for signature, rows in groups.items():
        normalized = [example for _, example in rows]
        candidates, local_evaluated = _candidate_set(
            normalized,
            signature,
            max_cost=max_cost,
            minimum_support=minimum_support,
        )
        if not candidates:
            raise NoLatentPartitionError(f"no supported behavior for {signature.render()}")
        chosen, local_nodes = _solve_exact_cover(candidates, len(rows))
        evaluated += local_evaluated
        candidate_count += len(candidates)
        nodes += local_nodes
        for candidate in chosen:
            covered = tuple(
                rows[local][0]
                for local in range(len(rows))
                if candidate.mask & (1 << local)
            )
            programs.append(
                LatentProgram(
                    signature,
                    candidate.expression,
                    covered,
                    candidate.probe,
                    candidate.cost,
                )
            )

    programs.sort(key=lambda program: repr(program.behavior_key()))
    return LatentPartition(
        tuple(programs),
        PartitionStats(evaluated, candidate_count, nodes),
    )


def route_from_support(
    partition: LatentPartition,
    support: Sequence[Mapping[str, Any]],
) -> LatentProgram:
    if not support:
        raise NonIdentifiableRoutingError("empty support")
    signature = _signature(support[0])
    if any(_signature(example) != signature for example in support):
        raise NonIdentifiableRoutingError("support signature changed")

    matches: dict[tuple[Any, ...], LatentProgram] = {}
    for program in partition.programs:
        if program.signature != signature:
            continue
        valid = True
        for example in support:
            try:
                predicted = program.predict(example["inputs"])
            except EvaluationError:
                valid = False
                break
            if canonical(predicted) != canonical(decode_value(example["output"])):
                valid = False
                break
        if valid:
            matches[program.behavior_key()] = program
    if len(matches) != 1:
        raise NonIdentifiableRoutingError(f"support selects {len(matches)} behaviors")
    return next(iter(matches.values()))


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
                predicted = program.predict(query["inputs"])
            except EvaluationError:
                continue
            correct += canonical(predicted) == canonical(decode_value(query["output"]))
    return correct, covered, total


def audit_gold_separation(
    partition: LatentPartition,
    stream: Sequence[Mapping[str, Any]],
) -> bool:
    labels_seen: set[str] = set()
    for program in partition.programs:
        labels = {str(stream[index]["gold"]) for index in program.covered_indices}
        if len(labels) != 1:
            return False
        labels_seen.update(labels)
    return labels_seen == {str(example["gold"]) for example in stream}


def _failure_controls(payload: Mapping[str, Any], final: LatentPartition) -> dict[str, bool]:
    results: dict[str, bool] = {}
    try:
        discover_partition(tuple(payload["post_freeze_stream"][:4]))
    except NoLatentPartitionError:
        results["subminimum_cluster_abstains"] = True
    else:
        results["subminimum_cluster_abstains"] = False

    corrupted = tuple(payload["stream"]) + (
        {"inputs": {"u": 11, "v": 13}, "output": 999, "gold": "audit"},
    )
    try:
        discover_partition(corrupted)
    except NoLatentPartitionError:
        results["uncovered_outlier_abstains"] = True
    else:
        results["uncovered_outlier_abstains"] = False

    ambiguous = ({"inputs": {"u": 0, "v": 0}, "output": 0},)
    try:
        route_from_support(final, ambiguous)
    except NonIdentifiableRoutingError:
        results["ambiguous_support_abstains"] = True
    else:
        results["ambiguous_support_abstains"] = False
    return results


def run() -> dict[str, Any]:
    payload = load_stream()
    initial_stream = tuple(payload["stream"])
    appended = tuple(payload["post_freeze_stream"])
    initial = discover_partition(initial_stream)
    initial_correct, initial_covered, initial_total = evaluate_episodes(
        initial, payload["episodes"]
    )

    final_stream = initial_stream + appended
    final = discover_partition(final_stream)
    all_episodes = tuple(payload["episodes"]) + tuple(payload["post_freeze_episodes"])
    final_correct, final_covered, final_total = evaluate_episodes(final, all_episodes)

    initial_fingerprint = set(initial.fingerprint())
    old_unchanged = initial_fingerprint.issubset(set(final.fingerprint()))
    reversed_partition = discover_partition(tuple(reversed(initial_stream)))
    relabeled = tuple({**example, "gold": "ignored"} for example in initial_stream)
    relabeled_partition = discover_partition(relabeled)
    controls = _failure_controls(payload, final)
    source = inspect.getsource(inspect.getmodule(run))
    gold_names_absent = all(str(example["gold"]) not in source for example in final_stream)

    checks = {
        "initial_program_count": len(initial.programs) == 7,
        "final_program_count": len(final.programs) == 8,
        "initial_partition_matches_audit": audit_gold_separation(initial, initial_stream),
        "final_partition_matches_audit": audit_gold_separation(final, final_stream),
        "initial_accuracy": initial_correct == initial_total,
        "initial_coverage": initial_covered == initial_total,
        "final_accuracy": final_correct == final_total,
        "final_coverage": final_covered == final_total,
        "old_programs_unchanged": old_unchanged,
        "stream_order_invariance": initial.fingerprint() == reversed_partition.fingerprint(),
        "audit_labels_not_used": initial.fingerprint() == relabeled_partition.fingerprint(),
        "failure_controls": all(controls.values()),
        "gold_names_absent_from_source": gold_names_absent,
        "no_task_id_records": all("id" not in example for example in final_stream),
    }

    return {
        "campaign": {
            "name": "phase18d3-latent-task-partition-c1",
            "explicit_task_ids": False,
            "explicit_task_count": False,
            "support_examples_for_query_routing": True,
            "source_changes_for_appended_task": 0,
        },
        "induction": {
            "initial_examples": len(initial_stream),
            "initial_latent_programs": len(initial.programs),
            "appended_examples": len(appended),
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
            "old_programs_unchanged": old_unchanged,
            "new_programs_from_appended_data": len(final.programs) - len(initial.programs),
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
            "Every stream record still contains a supervised output.",
            "Inputs and outputs are structured, typed values rather than raw documents.",
            "The primitive DSL and type system are human-designed.",
            "A support input/output example is needed to route a query when several learned programs share a type signature.",
            "Exact-cover partitioning is exponential and only tested on a small stream.",
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
- Appended post-freeze examples: **{induction['appended_examples']}**
- Inferred final latent programs: **{induction['final_latent_programs']}**
- Initial support-routed held-out: **{evaluation['initial_correct']}/{evaluation['initial_total']}**
- Final support-routed held-out: **{evaluation['final_correct']}/{evaluation['final_total']}**
- Source changes for the appended task: **{payload['campaign']['source_changes_for_appended_task']}**
- Old programs unchanged: **{payload['continual_learning']['old_programs_unchanged']}**
- Final learned payload: **{resources['learned_payload_bits']} bits**
- Final expression evaluations / exact-cover nodes: **{resources['final_expressions_evaluated']} / {resources['final_exact_cover_nodes']}**

A minimum-description exact partition recovered heterogeneous programs from a shuffled supervised stream without task IDs or a declared task count. Local support examples selected the relevant behavior for held-out queries. This removes explicit task labels in a controlled typed setting; it is not raw-document pretraining or LLM-like open-ended learning.
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
