from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    LinearFactorizationModel,
    induce_linear_factorization,
)


AnonymousState = tuple[int, ...]

ENTITY_TOKENS = ("nara", "peli", "soma", "tuv")
ACTION_TOKENS = ("dax", "zup", "miv")
ACTION_BITS = {"dax": True, "zup": False, "miv": True}
TEMPLATE_BITS = {0: False, 1: True, 2: False}


class NonIdentifiableGroundingError(ValueError):
    pass


@dataclass(frozen=True)
class RawGroundingObservation:
    sentence: str
    before: AnonymousState
    after: AnonymousState

    @classmethod
    def build(
        cls,
        sentence: str,
        before: Sequence[int],
        after: Sequence[int],
    ) -> "RawGroundingObservation":
        before_row = tuple(int(value) for value in before)
        after_row = tuple(int(value) for value in after)
        if len(before_row) < 2 or len(before_row) != len(after_row):
            raise ValueError("anonymous states must have equal length >= 2")
        if len(sentence.casefold().split()) < 3:
            raise ValueError("raw sentence must contain at least three tokens")
        return cls(sentence.casefold(), before_row, after_row)

    @property
    def tokens(self) -> tuple[str, ...]:
        return tuple(self.sentence.split())


@dataclass(frozen=True)
class TransitionRoles:
    source: int
    destination: int


@dataclass(frozen=True)
class JointGroundingModel:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    factorization: LinearFactorizationModel
    training_observations: int

    def entity_map(self) -> dict[str, int]:
        return dict(self.entity_lexicon)

    @property
    def description_bits(self) -> int:
        payload = {
            "entity_lexicon": [list(row) for row in self.entity_lexicon],
            "action_lexicon": list(self.action_lexicon),
            "factorization": self.factorization.render(),
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8

    def predict(self, sentence: str, before: Sequence[int]) -> AnonymousState | None:
        before_row = tuple(int(value) for value in before)
        entity_map = self.entity_map()
        action_set = set(self.action_lexicon)
        semantic = [
            token
            for token in sentence.casefold().split()
            if token in entity_map or token in action_set
        ]
        actions = [token for token in semantic if token in action_set]
        entities = [token for token in semantic if token in entity_map]
        if len(semantic) != 3 or len(actions) != 1 or len(entities) != 2:
            return None
        if entities[0] == entities[1]:
            return None
        action = actions[0]
        action_position = semantic.index(action)
        direction = self.factorization.effective_forward(action, action_position)
        if direction is None:
            return None
        left = entity_map[entities[0]]
        right = entity_map[entities[1]]
        source, destination = (left, right) if direction else (right, left)
        if max(source, destination) >= len(before_row):
            return None
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


def infer_transition_roles(observation: RawGroundingObservation) -> TransitionRoles:
    changed = [
        index
        for index, (before, after) in enumerate(zip(observation.before, observation.after))
        if before != after
    ]
    if len(changed) != 1:
        raise ValueError("copy intervention must change exactly one anonymous coordinate")
    destination = changed[0]
    source_candidates = [
        index
        for index, value in enumerate(observation.before)
        if index != destination and value == observation.after[destination]
    ]
    if len(source_candidates) != 1:
        raise ValueError("transition does not identify a unique source coordinate")
    return TransitionRoles(source_candidates[0], destination)


def _token_signatures(
    observations: Sequence[RawGroundingObservation],
) -> dict[str, tuple[bool, ...]]:
    vocabulary = sorted({token for row in observations for token in row.tokens})
    return {
        token: tuple(token in row.tokens for row in observations)
        for token in vocabulary
    }


def _coordinate_signatures(
    observations: Sequence[RawGroundingObservation],
) -> dict[int, tuple[bool, ...]]:
    if not observations:
        return {}
    coordinate_count = len(observations[0].before)
    roles = tuple(infer_transition_roles(row) for row in observations)
    return {
        coordinate: tuple(
            coordinate in (role.source, role.destination) for role in roles
        )
        for coordinate in range(coordinate_count)
    }


def enumerate_entity_groundings(
    observations: Iterable[RawGroundingObservation],
) -> tuple[tuple[tuple[str, int], ...], ...]:
    """Enumerate token-to-coordinate maps allowed by causal incidence evidence."""

    rows = tuple(observations)
    if not rows:
        return tuple()
    if any(len(row.before) != len(rows[0].before) for row in rows):
        raise ValueError("all anonymous states must share one coordinate universe")
    token_signatures = _token_signatures(rows)
    coordinate_signatures = _coordinate_signatures(rows)
    candidates = {
        coordinate: tuple(
            token
            for token, signature in token_signatures.items()
            if signature == coordinate_signature
        )
        for coordinate, coordinate_signature in coordinate_signatures.items()
    }
    if any(not options for options in candidates.values()):
        return tuple()

    mappings: list[tuple[tuple[str, int], ...]] = []
    coordinates = tuple(sorted(candidates))

    def search(index: int, chosen: dict[str, int]) -> None:
        if index == len(coordinates):
            mappings.append(tuple(sorted(chosen.items())))
            return
        coordinate = coordinates[index]
        for token in candidates[coordinate]:
            if token in chosen:
                continue
            chosen[token] = coordinate
            search(index + 1, chosen)
            del chosen[token]

    search(0, {})
    return tuple(sorted(set(mappings)))


def _semantic_edge(
    observation: RawGroundingObservation,
    *,
    entity_map: Mapping[str, int],
    action_token: str,
) -> LabeledSemanticEdge:
    semantic = [
        token
        for token in observation.tokens
        if token in entity_map or token == action_token
    ]
    if len(semantic) != 3 or semantic.count(action_token) != 1:
        raise ValueError("candidate action does not form one two-entity event")
    entities = [token for token in semantic if token != action_token]
    if len(entities) != 2 or entities[0] == entities[1]:
        raise ValueError("candidate event must contain two distinct grounded entities")
    action_position = semantic.index(action_token)
    left, right = (entity_map[token] for token in entities)
    roles = infer_transition_roles(observation)
    if roles == TransitionRoles(left, right):
        effective_forward = True
    elif roles == TransitionRoles(right, left):
        effective_forward = False
    else:
        raise ValueError("grounded participants do not explain the state transition")
    return LabeledSemanticEdge(action_token, action_position, effective_forward)


def enumerate_action_factorizations(
    observations: Iterable[RawGroundingObservation],
    entity_grounding: Sequence[tuple[str, int]],
) -> tuple[tuple[tuple[str, ...], LinearFactorizationModel], ...]:
    rows = tuple(observations)
    entity_map = dict(entity_grounding)
    counts = Counter(token for row in rows for token in set(row.tokens))
    candidates = tuple(
        sorted(
            token
            for token, count in counts.items()
            if token not in entity_map and 2 <= count < len(rows)
        )
    )
    valid: list[tuple[tuple[str, ...], LinearFactorizationModel]] = []
    for size in range(1, len(candidates) + 1):
        for action_subset in combinations(candidates, size):
            action_set = set(action_subset)
            if any(sum(token in action_set for token in row.tokens) != 1 for row in rows):
                continue
            try:
                edges = tuple(
                    _semantic_edge(
                        row,
                        entity_map=entity_map,
                        action_token=next(token for token in row.tokens if token in action_set),
                    )
                    for row in rows
                )
                positions = tuple(sorted({edge.template_position for edge in edges}))
                model = induce_linear_factorization(
                    edges,
                    verbs=action_subset,
                    template_positions=positions,
                )
            except (ValueError, InconsistentSemanticsError):
                continue
            if model.identifiable:
                valid.append((tuple(action_subset), model))
    return tuple(valid)


def enumerate_joint_models(
    observations: Iterable[RawGroundingObservation],
) -> tuple[JointGroundingModel, ...]:
    rows = tuple(observations)
    models: list[JointGroundingModel] = []
    for entity_grounding in enumerate_entity_groundings(rows):
        for action_lexicon, factorization in enumerate_action_factorizations(
            rows, entity_grounding
        ):
            models.append(
                JointGroundingModel(
                    tuple(entity_grounding),
                    tuple(action_lexicon),
                    factorization,
                    len(rows),
                )
            )
    unique: dict[str, JointGroundingModel] = {}
    for model in models:
        key = json.dumps(
            {
                "entities": model.entity_lexicon,
                "actions": model.action_lexicon,
                "factorization": model.factorization.render(),
            },
            sort_keys=True,
        )
        unique[key] = model
    return tuple(unique[key] for key in sorted(unique))


def induce_joint_grounding(
    observations: Iterable[RawGroundingObservation],
) -> JointGroundingModel:
    models = enumerate_joint_models(observations)
    if len(models) != 1:
        raise NonIdentifiableGroundingError(
            f"joint role/meaning grounding has {len(models)} surviving models"
        )
    return models[0]


def _semantic_tokens(action: str, position: int, left: str, right: str) -> list[str]:
    rows = [left, right]
    rows.insert(position, action)
    return rows


def _render_training_sentence(semantic: Sequence[str], *, index: int) -> str:
    tokens = ["ka", *semantic]
    if index in {0, 4, 8}:
        tokens.insert(1 + (index % len(tokens)), "near")
    if index in {1, 5}:
        tokens.append("quiet")
    tokens.insert(index % (len(tokens) + 1), f"noise{index}")
    return " ".join(tokens)


def _build_observation(
    *,
    action: str,
    position: int,
    left_coordinate: int,
    right_coordinate: int,
    index: int,
    sentence: str | None = None,
) -> RawGroundingObservation:
    before = tuple(index * 100 + coordinate + 1 for coordinate in range(4))
    effective_forward = ACTION_BITS[action] ^ TEMPLATE_BITS[position]
    source, destination = (
        (left_coordinate, right_coordinate)
        if effective_forward
        else (right_coordinate, left_coordinate)
    )
    after = list(before)
    after[destination] = before[source]
    semantic = _semantic_tokens(
        action,
        position,
        ENTITY_TOKENS[left_coordinate],
        ENTITY_TOKENS[right_coordinate],
    )
    raw_sentence = sentence or _render_training_sentence(semantic, index=index)
    return RawGroundingObservation.build(raw_sentence, before, after)


def training_observations() -> tuple[RawGroundingObservation, ...]:
    specs = (
        ("dax", 0, 0, 1),
        ("dax", 0, 2, 3),
        ("dax", 1, 0, 2),
        ("dax", 1, 1, 3),
        ("zup", 1, 0, 3),
        ("zup", 1, 1, 2),
        ("zup", 2, 0, 1),
        ("zup", 2, 2, 3),
        ("miv", 2, 0, 2),
        ("miv", 2, 1, 3),
    )
    return tuple(
        _build_observation(
            action=action,
            position=position,
            left_coordinate=left,
            right_coordinate=right,
            index=index,
        )
        for index, (action, position, left, right) in enumerate(specs)
    )


def heldout_role_reversal_pairs() -> tuple[RawGroundingObservation, ...]:
    specs = (
        ("dax", 2, 0, 3),
        ("zup", 0, 1, 2),
        ("miv", 0, 0, 1),
        ("miv", 1, 2, 3),
    )
    rows: list[RawGroundingObservation] = []
    for pair_index, (action, position, left, right) in enumerate(specs):
        index = 100 + pair_index
        for pair_left, pair_right in ((left, right), (right, left)):
            semantic = _semantic_tokens(
                action,
                position,
                ENTITY_TOKENS[pair_left],
                ENTITY_TOKENS[pair_right],
            )
            sentence = " ".join(["unseen", semantic[0], "glint", *semantic[1:], "today"])
            rows.append(
                _build_observation(
                    action=action,
                    position=position,
                    left_coordinate=pair_left,
                    right_coordinate=pair_right,
                    index=index,
                    sentence=sentence,
                )
            )
    return tuple(rows)


def semantic_accuracy(
    model: JointGroundingModel,
    observations: Iterable[RawGroundingObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for row in rows:
        predicted = model.predict(row.sentence, row.before)
        if predicted is None:
            continue
        answered += 1
        correct += int(predicted == row.after)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def positionless_surface_upper_bound(
    observations: Iterable[RawGroundingObservation],
) -> float:
    groups: dict[
        tuple[tuple[str, ...], AnonymousState], Counter[AnonymousState]
    ] = defaultdict(Counter)
    rows = tuple(observations)
    for row in rows:
        representation = (tuple(sorted(row.tokens)), row.before)
        groups[representation][row.after] += 1
    return (
        sum(max(counts.values()) for counts in groups.values()) / len(rows)
        if rows
        else 0.0
    )


def exact_memorizer_coverage(
    training: Iterable[RawGroundingObservation],
    evaluation: Iterable[RawGroundingObservation],
) -> float:
    known = {row.sentence for row in training}
    rows = tuple(evaluation)
    return sum(row.sentence in known for row in rows) / len(rows) if rows else 0.0


def duplicate_entity_signature_control() -> int:
    observations = (
        RawGroundingObservation.build("a dax b", (1, 2), (1, 1)),
        RawGroundingObservation.build("b dax a", (3, 4), (4, 4)),
    )
    return len(enumerate_entity_groundings(observations))


def distractor_collision_control() -> int:
    rows = training_observations()
    q0_signature = _coordinate_signatures(rows)[0]
    modified = tuple(
        RawGroundingObservation.build(
            row.sentence + (" shadow" if participates else ""),
            row.before,
            row.after,
        )
        for row, participates in zip(rows, q0_signature)
    )
    return len(enumerate_entity_groundings(modified))


def disconnected_semantic_control() -> int:
    rows = training_observations()
    subset = (rows[0], rows[1], rows[4], rows[5], rows[8], rows[9])
    return len(enumerate_joint_models(subset))


def run() -> dict[str, object]:
    training = training_observations()
    heldout = heldout_role_reversal_pairs()
    entity_models = enumerate_entity_groundings(training)
    joint_models = enumerate_joint_models(training)
    learned = induce_joint_grounding(training)
    accuracy, coverage = semantic_accuracy(learned, heldout)
    lengths = tuple(len(row.tokens) for row in (*training, *heldout))

    theorem_checks = {
        "entity_incidence_grounding_is_unique": len(entity_models) == 1,
        "joint_role_and_semantic_model_is_unique": len(joint_models) == 1,
        "duplicate_entity_signatures_are_non_identifying": duplicate_entity_signature_control()
        > 1,
        "distractor_signature_collision_is_non_identifying": distractor_collision_control()
        > 1,
        "disconnected_action_template_graph_is_rejected": disconnected_semantic_control()
        == 0,
        "heldout_unseen_compositions_are_perfect": accuracy == 1.0 and coverage == 1.0,
        "positionless_surface_classifier_bound_is_half": positionless_surface_upper_bound(
            heldout
        )
        == 0.5,
        "exact_sentence_memorizer_has_zero_coverage": exact_memorizer_coverage(
            training, heldout
        )
        == 0.0,
        "sentences_have_variable_raw_length": min(lengths) < max(lengths),
    }

    return {
        "campaign": {
            "name": "phase17g-joint-role-grounding-c1",
            "raw_variable_length_token_sequences": True,
            "entity_category_labels_provided": False,
            "state_coordinate_names_overlap_surface_tokens": False,
            "unknown_training_and_evaluation_distractors": True,
            "world_supervision": "anonymous before/after copy interventions",
            "public_benchmark_examples_used": 0,
        },
        "theory": {
            "positive_entity_groundings": len(entity_models),
            "positive_joint_models": len(joint_models),
            "duplicate_signature_control_groundings": duplicate_entity_signature_control(),
            "distractor_collision_control_groundings": distractor_collision_control(),
            "disconnected_semantic_control_models": disconnected_semantic_control(),
            "criterion": (
                "unique uncontaminated entity incidence signatures plus a connected "
                "action-template XOR graph are sufficient for unique grounding in the "
                "declared finite factorized class"
            ),
        },
        "evaluation": {
            "training_observations": len(training),
            "heldout_observations": len(heldout),
            "heldout_accuracy": accuracy,
            "heldout_coverage": coverage,
            "positionless_surface_upper_bound": positionless_surface_upper_bound(heldout),
            "exact_memorizer_coverage": exact_memorizer_coverage(training, heldout),
            "minimum_raw_tokens": min(lengths),
            "maximum_raw_tokens": max(lengths),
        },
        "resource_accounting": {
            "serialized_acquired_model_bits": learned.description_bits,
            "phase17g_module_source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "learned_model": {
            "entity_lexicon": [list(row) for row in learned.entity_lexicon],
            "action_lexicon": list(learned.action_lexicon),
            "factorization": learned.factorization.render(),
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "controlled_unsupervised_token_role_grounding_demonstrated": all(
                theorem_checks.values()
            ),
            "surface_bag_classifier_refuted_on_declared_pairs": all(
                theorem_checks.values()
            ),
            "arbitrary_sequence_classifier_refuted": False,
            "natural_language_understanding_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "copy transitions expose a unique source and destination because state values are noiseless and distinct",
            "entity grounding uses exact occurrence-signature equality rather than a noise-tolerant statistical estimator",
            "the number of latent coordinates is provided by the anonymous state vector length",
            "sentences contain exactly one event with two entities and one reusable action after nuisance removal",
            "polysemy, synonymy, negation, recursion, discourse, and continuous observations are absent",
            "Python and its standard library are declared substrate rather than counted system bytes",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    theory = payload["theory"]
    evaluation = payload["evaluation"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 17g results: joint token-role and semantic grounding",
        "",
        "Phase 17g removes direct entity-category supervision. Surface tokens do not",
        "match anonymous world-coordinate names. Entity aliases are inferred from",
        "causal participation signatures, while action words and word-order semantics",
        "are selected jointly from the remaining recurrent tokens.",
        "",
        "## Identifiability controls",
        "",
        f"- Positive entity groundings: **{theory['positive_entity_groundings']}**",
        f"- Positive joint role/semantic models: **{theory['positive_joint_models']}**",
        f"- Duplicate-signature control groundings: **{theory['duplicate_signature_control_groundings']}**",
        f"- Entity-mimicking distractor control groundings: **{theory['distractor_collision_control_groundings']}**",
        f"- Disconnected semantic control models: **{theory['disconnected_semantic_control_models']}**",
        "",
        "## Held-out evaluation",
        "",
        f"- Training observations: **{evaluation['training_observations']}**",
        f"- Held-out unseen compositions: **{evaluation['heldout_observations']}**",
        f"- Accuracy / coverage: **{100 * evaluation['heldout_accuracy']:.1f}% / {100 * evaluation['heldout_coverage']:.1f}%**",
        f"- Positionless surface upper bound: **{100 * evaluation['positionless_surface_upper_bound']:.1f}%**",
        f"- Exact sentence memorizer coverage: **{100 * evaluation['exact_memorizer_coverage']:.1f}%**",
        f"- Raw sentence lengths: **{evaluation['minimum_raw_tokens']}--{evaluation['maximum_raw_tokens']} tokens**",
        "",
        "## Resource accounting",
        "",
        f"- Serialized acquired model: **{resources['serialized_acquired_model_bits']} bits**",
        f"- Phase 17g source: **{resources['phase17g_module_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and explicitly declared",
        "",
        "## Claim boundary",
        "",
        "This demonstrates joint token-role grounding and compositional transfer in a",
        "small interventionally supervised language. It does not demonstrate natural",
        "language understanding or refute arbitrary sequence models.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase17g.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase17g.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
