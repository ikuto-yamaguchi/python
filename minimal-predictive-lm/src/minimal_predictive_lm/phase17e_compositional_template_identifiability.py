from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import product
import json
from math import ceil, log2
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .phase17d_semantic_identifiability import (
    SemanticFrame,
    SemanticObservation,
    State,
    exact_memorizer_coverage,
    normalize_state,
    representation_accuracy_upper_bound,
)


VERBS = ("dax", "zup", "miv", "rup")
TEMPLATE_POSITIONS = (0, 1, 2)
TRUE_FORWARD = {
    "dax": True,
    "zup": False,
    "miv": True,
    "rup": False,
}
TRUE_TEMPLATE_SWAP = {
    0: True,
    1: False,
    2: True,
}

# Six edges form a spanning tree over four verbs and three templates.
IDENTIFYING_EDGES = (
    ("dax", 1),
    ("zup", 1),
    ("miv", 1),
    ("rup", 1),
    ("dax", 0),
    ("dax", 2),
)

# All variables are observed, but the graph has two connected components.
NON_IDENTIFYING_EDGES = (
    ("dax", 0),
    ("zup", 0),
    ("dax", 1),
    ("miv", 2),
    ("rup", 2),
)


def sentence_for(
    verb: str,
    verb_position: int,
    left: str,
    right: str,
) -> str:
    if verb_position not in TEMPLATE_POSITIONS:
        raise ValueError("verb position must be 0, 1, or 2")
    tokens = [left, right]
    tokens.insert(verb_position, verb)
    return " ".join(tokens)


@dataclass(frozen=True)
class TemplateSemanticHypothesis:
    """Factorized lexical direction and template orientation.

    The effective surface direction for pair ``(verb, template)`` is the XOR of
    the verb-direction bit and template-swap bit. Flipping every lexical and every
    template bit is a global coordinate gauge and changes no world behavior.
    """

    template_swap_by_position: tuple[tuple[int, bool], ...]
    forward_by_verb: tuple[tuple[str, bool], ...]

    def template_map(self) -> dict[int, bool]:
        return dict(self.template_swap_by_position)

    def verb_map(self) -> dict[str, bool]:
        return dict(self.forward_by_verb)

    def frame(self, sentence: str, before: State) -> SemanticFrame:
        tokens = sentence.casefold().split()
        if len(tokens) != 3:
            raise ValueError("Phase 17e micro-language requires three tokens")
        entities = set(dict(before))
        action_positions = [index for index, token in enumerate(tokens) if token not in entities]
        if len(action_positions) != 1:
            raise ValueError("exactly one token must be grounded as a non-entity action")
        action_position = action_positions[0]
        verb = tokens[action_position]
        template_map = self.template_map()
        verb_map = self.verb_map()
        if action_position not in template_map or verb not in verb_map:
            raise ValueError("unknown template or verb")

        participants = [token for index, token in enumerate(tokens) if index != action_position]
        first, second = participants
        if template_map[action_position]:
            first, second = second, first
        source, destination = (
            (first, second) if verb_map[verb] else (second, first)
        )
        return SemanticFrame(verb, source, destination)

    def execute_frame(self, frame: SemanticFrame, before: State) -> State:
        state = dict(before)
        if frame.source not in state or frame.destination not in state:
            raise ValueError("participants must exist in the world state")
        state[frame.destination] = state[frame.source]
        return normalize_state(state)

    def predict(self, sentence: str, before: State) -> State:
        return self.execute_frame(self.frame(sentence, before), before)

    def render(self) -> object:
        return {
            "template_swap_by_position": [list(row) for row in self.template_swap_by_position],
            "forward_by_verb": [list(row) for row in self.forward_by_verb],
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


def true_hypothesis() -> TemplateSemanticHypothesis:
    return TemplateSemanticHypothesis(
        tuple(TRUE_TEMPLATE_SWAP.items()),
        tuple(TRUE_FORWARD.items()),
    )


def all_hypotheses() -> tuple[TemplateSemanticHypothesis, ...]:
    return tuple(
        TemplateSemanticHypothesis(
            tuple(zip(TEMPLATE_POSITIONS, template_bits)),
            tuple(zip(VERBS, verb_bits)),
        )
        for template_bits in product((False, True), repeat=len(TEMPLATE_POSITIONS))
        for verb_bits in product((False, True), repeat=len(VERBS))
    )


def _observe(
    verb: str,
    verb_position: int,
    *,
    left: str,
    right: str,
    before: Mapping[str, int],
) -> SemanticObservation:
    sentence = sentence_for(verb, verb_position, left, right)
    normalized = normalize_state(before)
    return SemanticObservation(
        sentence,
        normalized,
        true_hypothesis().predict(sentence, normalized),
    )


def observations_for_edges(
    edges: Sequence[tuple[str, int]],
) -> tuple[SemanticObservation, ...]:
    rows: list[SemanticObservation] = []
    for index, (verb, position) in enumerate(edges):
        before = (
            {"alice": 1, "bob": 0}
            if index % 2 == 0
            else {"alice": 0, "bob": 1}
        )
        rows.append(
            _observe(
                verb,
                position,
                left="alice",
                right="bob",
                before=before,
            )
        )
    return tuple(rows)


def is_consistent(
    hypothesis: TemplateSemanticHypothesis,
    observations: Iterable[SemanticObservation],
) -> bool:
    for observation in observations:
        try:
            predicted = hypothesis.predict(observation.sentence, observation.before)
        except ValueError:
            return False
        if predicted != observation.after:
            return False
    return True


def version_space(
    observations: Iterable[SemanticObservation],
    hypotheses: Sequence[TemplateSemanticHypothesis] | None = None,
) -> tuple[TemplateSemanticHypothesis, ...]:
    candidates = all_hypotheses() if hypotheses is None else tuple(hypotheses)
    rows = tuple(observations)
    return tuple(candidate for candidate in candidates if is_consistent(candidate, rows))


def _probe_cases() -> tuple[tuple[str, State], ...]:
    states = (
        normalize_state({"left": 1, "right": 0}),
        normalize_state({"left": 0, "right": 1}),
    )
    rows: list[tuple[str, State]] = []
    for verb in VERBS:
        for position in TEMPLATE_POSITIONS:
            for left, right in (("left", "right"), ("right", "left")):
                sentence = sentence_for(verb, position, left, right)
                rows.extend((sentence, state) for state in states)
    return tuple(rows)


def behavior_signature(hypothesis: TemplateSemanticHypothesis) -> tuple[State, ...]:
    return tuple(
        hypothesis.predict(sentence, before)
        for sentence, before in _probe_cases()
    )


def behavior_classes(
    hypotheses: Iterable[TemplateSemanticHypothesis],
) -> dict[tuple[State, ...], tuple[TemplateSemanticHypothesis, ...]]:
    groups: dict[tuple[State, ...], list[TemplateSemanticHypothesis]] = defaultdict(list)
    for hypothesis in hypotheses:
        groups[behavior_signature(hypothesis)].append(hypothesis)
    return {signature: tuple(rows) for signature, rows in groups.items()}


def observation_graph_components(
    edges: Sequence[tuple[str, int]],
) -> tuple[frozenset[tuple[str, object]], ...]:
    nodes = {
        *(("verb", verb) for verb in VERBS),
        *(("template", position) for position in TEMPLATE_POSITIONS),
    }
    adjacency: dict[tuple[str, object], set[tuple[str, object]]] = {
        node: set() for node in nodes
    }
    for verb, position in edges:
        left = ("verb", verb)
        right = ("template", position)
        adjacency[left].add(right)
        adjacency[right].add(left)

    unseen = set(nodes)
    components: list[frozenset[tuple[str, object]]] = []
    while unseen:
        root = min(unseen, key=repr)
        queue = deque([root])
        visited: set[tuple[str, object]] = set()
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adjacency[node] - visited)
        components.append(frozenset(visited))
        unseen -= visited
    return tuple(sorted(components, key=lambda row: repr(sorted(row, key=repr))))


def heldout_unseen_compositions() -> tuple[SemanticObservation, ...]:
    trained = set(IDENTIFYING_EDGES)
    remaining = [
        (verb, position)
        for verb in VERBS
        for position in TEMPLATE_POSITIONS
        if (verb, position) not in trained
    ]
    names = (
        ("eve", "frank"),
        ("grace", "heidi"),
        ("ivan", "judy"),
        ("karl", "lena"),
        ("mona", "nora"),
        ("omar", "piper"),
    )
    rows: list[SemanticObservation] = []
    for (verb, position), (left, right) in zip(remaining, names):
        before = {left: 1, right: 0}
        rows.append(
            _observe(verb, position, left=left, right=right, before=before)
        )
        rows.append(
            _observe(verb, position, left=right, right=left, before=before)
        )
    return tuple(rows)


def semantic_accuracy(
    hypothesis: TemplateSemanticHypothesis,
    observations: Iterable[SemanticObservation],
) -> float:
    rows = tuple(observations)
    correct = sum(
        hypothesis.predict(row.sentence, row.before) == row.after for row in rows
    )
    return correct / len(rows) if rows else 0.0


def role_intervention_consistency(
    hypothesis: TemplateSemanticHypothesis,
    paired_observations: Sequence[SemanticObservation],
) -> float:
    if len(paired_observations) % 2:
        raise ValueError("held-out suite must contain adjacent reversal pairs")
    correct = 0
    total = 0
    for index in range(0, len(paired_observations), 2):
        forward = paired_observations[index]
        reversed_surface = paired_observations[index + 1]
        frame = hypothesis.frame(forward.sentence, forward.before)
        swapped = SemanticFrame(frame.verb, frame.destination, frame.source)
        intervened = hypothesis.execute_frame(swapped, forward.before)
        predicted = hypothesis.predict(
            reversed_surface.sentence,
            reversed_surface.before,
        )
        correct += int(intervened == predicted)
        total += 1
    return correct / total if total else 0.0


def choose_canonical(
    hypotheses: Sequence[TemplateSemanticHypothesis],
) -> TemplateSemanticHypothesis:
    if not hypotheses:
        raise ValueError("empty version space")
    return min(
        hypotheses,
        key=lambda row: (
            row.description_bits,
            json.dumps(row.render(), sort_keys=True),
        ),
    )


def run() -> dict[str, object]:
    prior = all_hypotheses()
    negative_observations = observations_for_edges(NON_IDENTIFYING_EDGES)
    positive_observations = observations_for_edges(IDENTIFYING_EDGES)
    heldout = heldout_unseen_compositions()

    negative_space = version_space(negative_observations, prior)
    positive_space = version_space(positive_observations, prior)
    prior_classes = behavior_classes(prior)
    negative_classes = behavior_classes(negative_space)
    positive_classes = behavior_classes(positive_space)
    negative_components = observation_graph_components(NON_IDENTIFYING_EDGES)
    positive_components = observation_graph_components(IDENTIFYING_EDGES)
    learned = choose_canonical(positive_space)

    variables = len(VERBS) + len(TEMPLATE_POSITIONS)
    minimum_edges = variables - 1
    information_lower_bound_bits = ceil(log2(len(prior_classes)))
    predicted_negative_classes = 2 ** (len(negative_components) - 1)
    predicted_positive_classes = 2 ** (len(positive_components) - 1)
    dependency_source_bytes = sum(
        path.read_bytes().__len__()
        for path in (
            Path(__file__),
            Path(__file__).with_name("phase17d_semantic_identifiability.py"),
        )
    )

    theorem_checks = {
        "prior_behavior_classes_match_factorized_gauge_count": len(prior_classes)
        == 2 ** (variables - 1),
        "disconnected_graph_class_count_matches_theory": len(negative_classes)
        == predicted_negative_classes
        and len(negative_components) > 1,
        "connected_graph_identifies_behavior": len(positive_components) == 1
        and len(positive_classes) == predicted_positive_classes == 1,
        "only_global_gauge_parameterizations_remain": len(positive_space) == 2,
        "spanning_tree_observations_are_information_minimal": len(IDENTIFYING_EDGES)
        == minimum_edges
        == information_lower_bound_bits,
        "unseen_verb_template_compositions_generalize": semantic_accuracy(
            learned, heldout
        )
        == 1.0,
        "positionless_surface_bound_is_exact": representation_accuracy_upper_bound(
            heldout
        )
        == 0.5,
        "exact_memorizer_has_zero_coverage": exact_memorizer_coverage(
            positive_observations, heldout
        )
        == 0.0,
        "latent_role_intervention_is_causally_consistent": role_intervention_consistency(
            learned, heldout
        )
        == 1.0,
    }

    return {
        "campaign": {
            "name": "phase17e-compositional-template-identifiability-c1",
            "predecessor": "phase17d fixed-middle controlled micro-language",
            "architecture_change": (
                "infer action position from state grounding and factor lexical direction "
                "from template orientation"
            ),
            "verbs": list(VERBS),
            "template_positions": list(TEMPLATE_POSITIONS),
            "fixed_verb_position_used": False,
            "entity_grounding_from_world_state_used": True,
            "public_benchmark_examples_used": 0,
        },
        "theory": {
            "syntactic_hypotheses": len(prior),
            "semantic_behavior_classes": len(prior_classes),
            "unknown_binary_variables": variables,
            "global_gauge_dimensions": 1,
            "information_lower_bound_bits": information_lower_bound_bits,
            "minimum_connected_observation_edges": minimum_edges,
            "theorem": (
                "semantic behavior is identifiable modulo one global coordinate flip "
                "iff the verb-template observation graph is connected"
            ),
        },
        "negative_result": {
            "edges": [list(row) for row in NON_IDENTIFYING_EDGES],
            "graph_components": len(negative_components),
            "surviving_syntactic_hypotheses": len(negative_space),
            "surviving_behavior_classes": len(negative_classes),
            "predicted_behavior_classes": predicted_negative_classes,
            "identifiable": len(negative_classes) == 1,
        },
        "positive_result": {
            "edges": [list(row) for row in IDENTIFYING_EDGES],
            "graph_components": len(positive_components),
            "surviving_syntactic_hypotheses": len(positive_space),
            "surviving_behavior_classes": len(positive_classes),
            "identifiable_modulo_global_gauge": len(positive_classes) == 1,
            "heldout_unseen_composition_examples": len(heldout),
            "semantic_accuracy": semantic_accuracy(learned, heldout),
            "surface_unigram_upper_bound": representation_accuracy_upper_bound(heldout),
            "exact_memorizer_coverage": exact_memorizer_coverage(
                positive_observations, heldout
            ),
            "latent_role_intervention_consistency": role_intervention_consistency(
                learned, heldout
            ),
        },
        "resource_accounting": {
            "information_acquired_lower_bound_bits": information_lower_bound_bits,
            "serialized_acquired_hypothesis_bits": learned.description_bits,
            "phase17d_plus_phase17e_source_bytes": dependency_source_bytes,
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "compositional_lexical_template_grounding_demonstrated": all(
                theorem_checks.values()
            ),
            "unseen_verb_template_pair_transfer_demonstrated": all(
                theorem_checks.values()
            ),
            "free_form_syntax_induction_demonstrated": False,
            "natural_language_understanding_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "sentences still contain exactly two state-grounded entities and one action token",
            "the action category is inferred by exclusion from known state entities",
            "only three token positions and binary copy dynamics are in the hypothesis class",
            "the finite XOR factorization is not a model of unrestricted syntax or polysemy",
            "Python and its standard library remain declared external substrate",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    theory = payload["theory"]
    negative = payload["negative_result"]
    positive = payload["positive_result"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 17e results: compositional template identifiability",
        "",
        "Phase 17e removes the fixed-middle-verb assumption and factorizes meaning",
        "into lexical direction bits and template-orientation bits.",
        "",
        "## Graph identifiability theorem",
        "",
        f"- syntactic hypotheses: **{theory['syntactic_hypotheses']}**",
        f"- semantic behavior classes: **{theory['semantic_behavior_classes']}**",
        f"- independent semantic information: **{theory['information_lower_bound_bits']} bits**",
        f"- minimum informative observation edges: **{theory['minimum_connected_observation_edges']}**",
        "",
        "Each informative verb-template example supplies one XOR constraint. Semantic",
        "behavior is identifiable modulo a global latent-coordinate flip exactly when",
        "the bipartite observation graph is connected.",
        "",
        "| campaign | graph components | surviving behavior classes | identifiable |",
        "|---|---:|---:|---:|",
        f"| disconnected control | {negative['graph_components']} | {negative['surviving_behavior_classes']} | {negative['identifiable']} |",
        f"| connected spanning tree | {positive['graph_components']} | {positive['surviving_behavior_classes']} | {positive['identifiable_modulo_global_gauge']} |",
        "",
        "## Unseen composition test",
        "",
        "| evaluator | held-out result |",
        "|---|---:|",
        f"| any deterministic positionless-unigram classifier + full before-state | at most {100 * positive['surface_unigram_upper_bound']:.1f}% |",
        f"| exact sentence memorizer | {100 * positive['exact_memorizer_coverage']:.1f}% coverage |",
        f"| induced lexical-template factorization | {100 * positive['semantic_accuracy']:.1f}% accuracy |",
        f"| latent source/destination intervention | {100 * positive['latent_role_intervention_consistency']:.1f}% consistency |",
        "",
        f"The {positive['heldout_unseen_composition_examples']} evaluation sentences use",
        "verb-template combinations absent from training and new entity names.",
        "",
        "## Resource accounting",
        "",
        f"- acquired-information lower bound: {resources['information_acquired_lower_bound_bits']} bits",
        f"- serialized acquired hypothesis: {resources['serialized_acquired_hypothesis_bits']} bits",
        f"- Phase 17d + 17e source modules: {resources['phase17d_plus_phase17e_source_bytes']} bytes",
        "- Python runtime and standard library are not counted and remain declared substrate.",
        "",
        "## Claim boundary",
        "",
        "This proves compositional identification in a finite state-grounded language and",
        "shows transfer to unseen lexical-template pairs. It still does not induce free-form",
        "syntax, entity categories, polysemy, discourse, or natural-language semantics.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    if not payload["all_theorem_checks_pass"]:
        failed = [
            name for name, passed in payload["theorem_checks"].items() if not passed
        ]
        raise RuntimeError(f"Phase 17e theorem checks failed: {failed}")
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase17e.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17e.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
