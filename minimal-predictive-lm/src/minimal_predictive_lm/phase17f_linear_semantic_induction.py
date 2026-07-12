from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .phase17d_semantic_identifiability import SemanticObservation, State, normalize_state
from .phase17e_compositional_template_identifiability import (
    IDENTIFYING_EDGES,
    TEMPLATE_POSITIONS,
    VERBS,
    TemplateSemanticHypothesis,
    heldout_unseen_compositions,
    observations_for_edges,
)


class InconsistentSemanticsError(ValueError):
    pass


@dataclass(frozen=True)
class LabeledSemanticEdge:
    verb: str
    template_position: int
    effective_forward: bool


@dataclass(frozen=True)
class LinearFactorizationModel:
    verb_bits: tuple[tuple[str, bool], ...]
    template_bits: tuple[tuple[int, bool], ...]
    component_ids: tuple[tuple[str, str, int], ...]
    observations: int
    operations: int

    def _verb_map(self) -> dict[str, bool]:
        return dict(self.verb_bits)

    def _template_map(self) -> dict[int, bool]:
        return dict(self.template_bits)

    def _component_map(self) -> dict[tuple[str, object], int]:
        return {
            (kind, int(name) if kind == "template" else name): component
            for kind, name, component in self.component_ids
        }

    @property
    def component_count(self) -> int:
        return len(set(component for _, _, component in self.component_ids))

    @property
    def identifiable(self) -> bool:
        return self.component_count == 1

    def effective_forward(self, verb: str, template_position: int) -> bool | None:
        components = self._component_map()
        verb_node = ("verb", verb)
        template_node = ("template", template_position)
        if verb_node not in components or template_node not in components:
            return None
        if components[verb_node] != components[template_node]:
            return None
        return self._verb_map()[verb] ^ self._template_map()[template_position]

    def to_hypothesis(self) -> TemplateSemanticHypothesis:
        if not self.identifiable:
            raise ValueError("disconnected factorization cannot produce total semantics")
        return TemplateSemanticHypothesis(self.template_bits, self.verb_bits)

    def render(self) -> object:
        return {
            "verb_bits": [list(row) for row in self.verb_bits],
            "template_bits": [list(row) for row in self.template_bits],
            "component_ids": [list(row) for row in self.component_ids],
        }

    @property
    def description_bits(self) -> int:
        return len(
            json.dumps(
                self.render(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8


def _node(kind: str, value: object) -> tuple[str, object]:
    return (kind, value)


def induce_linear_factorization(
    edges: Iterable[LabeledSemanticEdge],
    *,
    verbs: Sequence[str],
    template_positions: Sequence[int],
) -> LinearFactorizationModel:
    """Solve lexical/template XOR semantics in O(V + T + E).

    Each edge imposes ``verb_bit XOR template_bit = effective_forward``.
    One root bit per connected component is fixed to zero as a coordinate gauge.
    Contradictory cycles are rejected. Cross-component pairs remain undefined.
    """

    edge_rows = tuple(edges)
    nodes = {
        *(_node("verb", verb) for verb in verbs),
        *(_node("template", position) for position in template_positions),
    }
    adjacency: dict[tuple[str, object], list[tuple[tuple[str, object], bool]]] = {
        node: [] for node in nodes
    }
    operations = 0
    for edge in edge_rows:
        left = _node("verb", edge.verb)
        right = _node("template", edge.template_position)
        if left not in adjacency or right not in adjacency:
            raise ValueError("edge references a symbol outside the declared universe")
        adjacency[left].append((right, edge.effective_forward))
        adjacency[right].append((left, edge.effective_forward))
        operations += 1

    values: dict[tuple[str, object], bool] = {}
    components: dict[tuple[str, object], int] = {}
    component_id = 0
    for root in sorted(nodes, key=repr):
        if root in values:
            continue
        values[root] = False
        components[root] = component_id
        queue = deque([root])
        while queue:
            current = queue.popleft()
            operations += 1
            for neighbor, label in adjacency[current]:
                operations += 1
                expected = values[current] ^ label
                if neighbor in values:
                    if values[neighbor] != expected:
                        raise InconsistentSemanticsError(
                            "contradictory lexical-template cycle"
                        )
                    continue
                values[neighbor] = expected
                components[neighbor] = component_id
                queue.append(neighbor)
        component_id += 1

    verb_bits = tuple((verb, values[_node("verb", verb)]) for verb in verbs)
    template_bits = tuple(
        (position, values[_node("template", position)])
        for position in template_positions
    )
    component_ids = tuple(
        (
            kind,
            str(value),
            components[(kind, value)],
        )
        for kind, value in sorted(nodes, key=repr)
    )
    return LinearFactorizationModel(
        verb_bits,
        template_bits,
        component_ids,
        len(edge_rows),
        operations,
    )


def _copy_state(before: State, source: str, destination: str) -> State:
    state = dict(before)
    state[destination] = state[source]
    return normalize_state(state)


def edge_from_observation(observation: SemanticObservation) -> LabeledSemanticEdge:
    tokens = observation.sentence.casefold().split()
    entities = set(dict(observation.before))
    action_positions = [index for index, token in enumerate(tokens) if token not in entities]
    if len(tokens) != 3 or len(action_positions) != 1:
        raise ValueError("observation is outside the Phase 17e controlled language")
    action_position = action_positions[0]
    verb = tokens[action_position]
    participants = [token for index, token in enumerate(tokens) if index != action_position]
    left, right = participants
    forward_after = _copy_state(observation.before, left, right)
    reverse_after = _copy_state(observation.before, right, left)
    if forward_after == reverse_after:
        raise ValueError("symmetric state does not identify edge direction")
    if observation.after == forward_after:
        label = True
    elif observation.after == reverse_after:
        label = False
    else:
        raise ValueError("transition is not representable by binary copy semantics")
    return LabeledSemanticEdge(verb, action_position, label)


def edges_from_observations(
    observations: Iterable[SemanticObservation],
) -> tuple[LabeledSemanticEdge, ...]:
    return tuple(edge_from_observation(row) for row in observations)


def semantic_accuracy(
    model: LinearFactorizationModel,
    observations: Iterable[SemanticObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for observation in rows:
        tokens = observation.sentence.casefold().split()
        entities = set(dict(observation.before))
        action_positions = [index for index, token in enumerate(tokens) if token not in entities]
        if len(tokens) != 3 or len(action_positions) != 1:
            continue
        action_position = action_positions[0]
        verb = tokens[action_position]
        direction = model.effective_forward(verb, action_position)
        if direction is None:
            continue
        participants = [token for index, token in enumerate(tokens) if index != action_position]
        left, right = participants
        predicted = (
            _copy_state(observation.before, left, right)
            if direction
            else _copy_state(observation.before, right, left)
        )
        answered += 1
        correct += int(predicted == observation.after)
    accuracy = correct / len(rows) if rows else 0.0
    coverage = answered / len(rows) if rows else 0.0
    return accuracy, coverage


def _synthetic_bits(index: int, *, salt: int) -> bool:
    return ((index * 1103515245 + salt * 12345) >> 4) & 1 == 1


def synthetic_spanning_tree(
    verb_count: int,
    template_count: int,
) -> tuple[tuple[str, ...], tuple[int, ...], tuple[LabeledSemanticEdge, ...]]:
    if verb_count < 1 or template_count < 1:
        raise ValueError("synthetic dimensions must be positive")
    verbs = tuple(f"verb_{index:05d}" for index in range(verb_count))
    templates = tuple(range(template_count))
    verb_bits = {verb: _synthetic_bits(index, salt=7) for index, verb in enumerate(verbs)}
    template_bits = {
        template: _synthetic_bits(template, salt=19) for template in templates
    }
    edge_pairs = [
        *((verb, templates[0]) for verb in verbs),
        *((verbs[0], template) for template in templates[1:]),
    ]
    edges = tuple(
        LabeledSemanticEdge(
            verb,
            template,
            verb_bits[verb] ^ template_bits[template],
        )
        for verb, template in edge_pairs
    )
    return verbs, templates, edges


def verify_synthetic_model(
    model: LinearFactorizationModel,
    edges: Sequence[LabeledSemanticEdge],
    *,
    verbs: Sequence[str],
    templates: Sequence[int],
) -> bool:
    if not model.identifiable:
        return False
    if any(
        model.effective_forward(edge.verb, edge.template_position)
        != edge.effective_forward
        for edge in edges
    ):
        return False
    probes = {
        (verbs[0], templates[0]),
        (verbs[-1], templates[-1]),
        (verbs[len(verbs) // 2], templates[len(templates) // 2]),
    }
    # A connected factorization gives a definite answer for every unseen pair.
    return all(model.effective_forward(verb, template) is not None for verb, template in probes)


def disconnected_control() -> tuple[LinearFactorizationModel, bool]:
    edges = (
        LabeledSemanticEdge("v0", 0, True),
        LabeledSemanticEdge("v1", 1, False),
    )
    model = induce_linear_factorization(
        edges,
        verbs=("v0", "v1"),
        template_positions=(0, 1),
    )
    return model, model.effective_forward("v0", 1) is None


def contradiction_detected() -> bool:
    edges = (
        LabeledSemanticEdge("v0", 0, True),
        LabeledSemanticEdge("v0", 0, False),
    )
    try:
        induce_linear_factorization(edges, verbs=("v0",), template_positions=(0,))
    except InconsistentSemanticsError:
        return True
    return False


def run() -> dict[str, object]:
    training = observations_for_edges(IDENTIFYING_EDGES)
    heldout = heldout_unseen_compositions()
    learned = induce_linear_factorization(
        edges_from_observations(training),
        verbs=VERBS,
        template_positions=TEMPLATE_POSITIONS,
    )
    heldout_accuracy, heldout_coverage = semantic_accuracy(learned, heldout)
    disconnected, cross_component_abstains = disconnected_control()

    scaling_rows: list[dict[str, object]] = []
    for verb_count, template_count in (
        (4, 3),
        (64, 64),
        (256, 256),
        (1024, 1024),
    ):
        verbs, templates, edges = synthetic_spanning_tree(
            verb_count,
            template_count,
        )
        model = induce_linear_factorization(
            edges,
            verbs=verbs,
            template_positions=templates,
        )
        nodes = verb_count + template_count
        edge_count = len(edges)
        scaling_rows.append(
            {
                "verbs": verb_count,
                "templates": template_count,
                "nodes": nodes,
                "edges": edge_count,
                "logical_semantic_bits": nodes - 1,
                "log2_exhaustive_parameterizations": nodes,
                "linear_operations": model.operations,
                "operation_bound_3e_plus_n": 3 * edge_count + nodes,
                "within_declared_linear_bound": model.operations
                <= 3 * edge_count + nodes,
                "verified": verify_synthetic_model(
                    model,
                    edges,
                    verbs=verbs,
                    templates=templates,
                ),
                "serialized_model_bits": model.description_bits,
            }
        )

    source_paths = (
        Path(__file__).with_name("phase17d_semantic_identifiability.py"),
        Path(__file__).with_name("phase17e_compositional_template_identifiability.py"),
        Path(__file__),
    )
    source_bytes = sum(path.read_bytes().__len__() for path in source_paths)
    theorem_checks = {
        "small_connected_graph_identifiable": learned.identifiable,
        "small_heldout_compositions_correct": heldout_accuracy == 1.0
        and heldout_coverage == 1.0,
        "disconnected_cross_component_pairs_abstain": not disconnected.identifiable
        and cross_component_abstains,
        "contradictory_cycles_rejected": contradiction_detected(),
        "all_scaling_points_verify": all(row["verified"] for row in scaling_rows),
        "all_scaling_points_respect_linear_operation_bound": all(
            row["within_declared_linear_bound"] for row in scaling_rows
        ),
        "largest_point_avoids_exhaustive_search": scaling_rows[-1][
            "log2_exhaustive_parameterizations"
        ]
        == 2048
        and scaling_rows[-1]["linear_operations"]
        <= scaling_rows[-1]["operation_bound_3e_plus_n"],
    }

    return {
        "campaign": {
            "name": "phase17f-linear-semantic-induction-c1",
            "predecessor": "phase17e exhaustive factorization",
            "architecture_change": (
                "replace 2^(V+T) enumeration with graph propagation over XOR constraints"
            ),
            "public_benchmark_examples_used": 0,
        },
        "small_controlled_language": {
            "training_observations": len(training),
            "heldout_examples": len(heldout),
            "heldout_accuracy": heldout_accuracy,
            "heldout_coverage": heldout_coverage,
            "components": learned.component_count,
            "operations": learned.operations,
            "serialized_model_bits": learned.description_bits,
        },
        "scaling": scaling_rows,
        "resource_accounting": {
            "phase17d_to_phase17f_source_bytes": source_bytes,
            "python_runtime_and_standard_library_bytes_included": False,
            "operation_metric": "edge ingestion + queue node visits + adjacency inspections",
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "linear_time_semantic_factor_recovery_demonstrated": all(
                theorem_checks.values()
            ),
            "exponential_hypothesis_enumeration_required": False,
            "arbitrary_grammar_induction_demonstrated": False,
            "natural_language_understanding_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "the XOR semantic structure is supplied as the hypothesis family",
            "observations are noiseless and edge labels must be identifiable from asymmetric states",
            "entity grounding and the one-action controlled language assumptions remain",
            "linear recovery of this factor graph does not imply efficient search over arbitrary programs",
            "Python remains external platform substrate",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    small = payload["small_controlled_language"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 17f results: linear semantic induction",
        "",
        "Phase 17f replaces exhaustive lexical-template hypothesis enumeration with",
        "a graph solver for equations of the form `verb_bit XOR template_bit = label`.",
        "",
        "## Controlled-language preservation",
        "",
        f"- training observations: {small['training_observations']}",
        f"- held-out unseen compositions: {small['heldout_examples']}",
        f"- held-out accuracy / coverage: {100 * small['heldout_accuracy']:.1f}% / {100 * small['heldout_coverage']:.1f}%",
        f"- induction operations: {small['operations']}",
        "",
        "Disconnected graphs abstain on cross-component meanings, and contradictory",
        "cycles are rejected rather than silently fitted.",
        "",
        "## Scaling",
        "",
        "| verbs | templates | nodes | edges | logical semantic bits | exhaustive search log2 | linear operations | bound | verified |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["scaling"]:
        lines.append(
            f"| {row['verbs']} | {row['templates']} | {row['nodes']} | {row['edges']} | "
            f"{row['logical_semantic_bits']} | {row['log2_exhaustive_parameterizations']} | "
            f"{row['linear_operations']} | {row['operation_bound_3e_plus_n']} | {row['verified']} |"
        )
    lines.extend(
        [
            "",
            "At the largest point, exhaustive enumeration would contain `2^2048` raw",
            "parameter assignments, while graph propagation remains linear in nodes and",
            "observed edges.",
            "",
            "## Resource accounting",
            "",
            f"- Phase 17d--17f source modules: {resources['phase17d_to_phase17f_source_bytes']} bytes",
            f"- operation metric: {resources['operation_metric']}",
            "- Python runtime and standard library remain excluded platform substrate.",
            "",
            "## Claim boundary",
            "",
            "This proves computational discoverability for the finite XOR-factorized",
            "semantic family. It does not prove that unrestricted syntax, world models,",
            "or arbitrary semantic programs can be found in linear time.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    if not payload["all_theorem_checks_pass"]:
        failed = [
            name for name, passed in payload["theorem_checks"].items() if not passed
        ]
        raise RuntimeError(f"Phase 17f theorem checks failed: {failed}")
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase17f.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17f.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
