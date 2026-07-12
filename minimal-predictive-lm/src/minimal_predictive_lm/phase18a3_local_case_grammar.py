from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
import json
from math import exp
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from ._phase18a2_continuous_japanese_core import (
    ContinuousJapaneseModel,
    ContinuousJapaneseObservation,
    entity_spans,
    induce_continuous_japanese,
    infer_transition_roles,
    non_overlapping_occurrences,
)
from .phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    LinearFactorizationModel,
    induce_linear_factorization,
)


AnonymousState = tuple[int, ...]
OrderPattern = tuple[str, str, str]

ENTITY_LEXEMES = ("アキ", "ボブ", "チカ", "ダイ")
ACTION_LEXEMES = ("渡す", "受ける", "写す", "移す")
ACTION_BITS = {"渡す": True, "受ける": False, "写す": True, "移す": False}
PARTICLE_BITS = {
    "が": False,
    "から": False,
    "より": False,
    "に": True,
    "へ": True,
    "まで": True,
}
ORDER_PATTERNS: dict[int, OrderPattern] = {
    0: ("E0", "E1", "A"),
    1: ("A", "E0", "E1"),
    2: ("E0", "A", "E1"),
}
TRAINING_SPECS = (
    ("渡す", "が", "に", 0),
    ("渡す", "から", "へ", 1),
    ("渡す", "より", "まで", 2),
    ("渡す", "に", "が", 0),
    ("渡す", "へ", "から", 1),
    ("渡す", "まで", "より", 2),
    ("受ける", "が", "に", 0),
    ("写す", "から", "へ", 1),
    ("移す", "より", "まで", 2),
)
REPETITIONS = 19
FLIPS_PER_GROUP = 1


class NonIdentifiableLocalGrammarError(ValueError):
    pass


@dataclass(frozen=True)
class LocalGrammarFactor:
    action: str
    first_particle: str
    second_particle: str
    order: OrderPattern
    effective_forward: bool


@dataclass(frozen=True)
class LocalGrammarFit:
    particle_index: tuple[tuple[str, int], ...]
    order_patterns: tuple[OrderPattern, ...]
    factorization: LinearFactorizationModel
    training_errors: int
    semantic_rows: int
    skipped_rows: int


@dataclass(frozen=True)
class LocalCaseGrammarModel:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    particle_index: tuple[tuple[str, int], ...]
    order_patterns: tuple[OrderPattern, ...]
    factorization: LinearFactorizationModel
    training_rows: int

    def particle_map(self) -> dict[str, int]:
        return dict(self.particle_index)

    @property
    def description_bits(self) -> int:
        payload = {
            "entity_lexicon": [list(row) for row in self.entity_lexicon],
            "action_lexicon": list(self.action_lexicon),
            "particle_index": [list(row) for row in self.particle_index],
            "order_patterns": [list(row) for row in self.order_patterns],
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

    def predict(
        self,
        sentence: str,
        before: Sequence[int],
    ) -> AnonymousState | None:
        before_row = tuple(int(value) for value in before)
        try:
            factor, coordinates = extract_local_factor(
                ContinuousJapaneseObservation.build(
                    sentence,
                    before_row,
                    before_row,
                ),
                entity_grounding=self.entity_lexicon,
                action_lexicon=self.action_lexicon,
                require_transition=False,
            )
        except ValueError:
            return None

        if factor.order not in set(self.order_patterns):
            return None
        particle_map = self.particle_map()
        first_id = particle_map.get(factor.first_particle)
        second_id = particle_map.get(factor.second_particle)
        if first_id is None or second_id is None:
            return None
        particle_bits = dict(self.factorization.template_bits)
        if particle_bits[first_id] == particle_bits[second_id]:
            return None

        direction = self.factorization.effective_forward(
            factor.action,
            first_id,
        )
        if direction is None:
            return None
        first_coordinate, second_coordinate = coordinates
        if max(first_coordinate, second_coordinate) >= len(before_row):
            return None
        source, destination = (
            (first_coordinate, second_coordinate)
            if direction
            else (second_coordinate, first_coordinate)
        )
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


def render_sentence(
    action: str,
    first_particle: str,
    second_particle: str,
    order: int,
    first_entity: str,
    second_entity: str,
    *,
    index: int,
    evaluation: bool = False,
) -> str:
    items = {
        "E0": first_entity + first_particle,
        "E1": second_entity + second_particle,
        "A": action,
    }
    prefixes = (
        ("", "今日は", "記録では", "その後")
        if not evaluation
        else ("念のため", "報告では", "あとで")
    )
    return (
        prefixes[index % len(prefixes)]
        + "".join(items[label] for label in ORDER_PATTERNS[order])
        + "。"
    )


def participant_pair(group_index: int, repetition: int) -> tuple[int, int]:
    first = (group_index + repetition) % len(ENTITY_LEXEMES)
    second = (group_index + 2 * repetition + 1) % len(ENTITY_LEXEMES)
    if first == second:
        second = (second + 1) % len(ENTITY_LEXEMES)
    return first, second


def build_observation(
    *,
    action: str,
    first_particle: str,
    second_particle: str,
    order: int,
    first_coordinate: int,
    second_coordinate: int,
    index: int,
    flip_label: bool = False,
    sentence: str | None = None,
    evaluation: bool = False,
) -> ContinuousJapaneseObservation:
    before = tuple(index * 100 + coordinate + 1 for coordinate in range(4))
    effective_forward = ACTION_BITS[action] ^ PARTICLE_BITS[first_particle]
    if flip_label:
        effective_forward = not effective_forward
    source, destination = (
        (first_coordinate, second_coordinate)
        if effective_forward
        else (second_coordinate, first_coordinate)
    )
    after = list(before)
    after[destination] = before[source]
    rendered = sentence or render_sentence(
        action,
        first_particle,
        second_particle,
        order,
        ENTITY_LEXEMES[first_coordinate],
        ENTITY_LEXEMES[second_coordinate],
        index=index,
        evaluation=evaluation,
    )
    return ContinuousJapaneseObservation.build(rendered, before, after)


def semantic_training_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    rows: list[ContinuousJapaneseObservation] = []
    for group_index, spec in enumerate(TRAINING_SPECS):
        action, first_particle, second_particle, order = spec
        for repetition in range(REPETITIONS):
            first, second = participant_pair(group_index, repetition)
            rows.append(
                build_observation(
                    action=action,
                    first_particle=first_particle,
                    second_particle=second_particle,
                    order=order,
                    first_coordinate=first,
                    second_coordinate=second,
                    index=group_index * REPETITIONS + repetition,
                    flip_label=repetition < FLIPS_PER_GROUP,
                )
            )
    return tuple(rows)


def auxiliary_noise_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    return (
        build_observation(
            action="渡す",
            first_particle="が",
            second_particle="に",
            order=0,
            first_coordinate=0,
            second_coordinate=1,
            index=10_000,
            sentence="今日はアキが渡す。",
        ),
        build_observation(
            action="写す",
            first_particle="から",
            second_particle="へ",
            order=1,
            first_coordinate=2,
            second_coordinate=3,
            index=10_001,
            sentence="アキを見ながら写すチカからダイへ。",
        ),
    )


def training_observations(
) -> tuple[ContinuousJapaneseObservation, ...]:
    return (
        *semantic_training_observations(),
        *auxiliary_noise_observations(),
    )


def heldout_specs() -> tuple[tuple[str, str, str, int], ...]:
    seen_action_particle = {
        (action, first_particle)
        for action, first_particle, _, _ in TRAINING_SPECS
    }
    seen_particle_pairs = {
        (first_particle, second_particle)
        for _, first_particle, second_particle, _ in TRAINING_SPECS
    }
    seen_particle_orders = {
        (first_particle, order)
        for _, first_particle, _, order in TRAINING_SPECS
    }
    non_anchor_actions = ("受ける", "写す", "移す")
    source_particles = tuple(
        particle for particle, bit in PARTICLE_BITS.items() if not bit
    )
    destination_particles = tuple(
        particle for particle, bit in PARTICLE_BITS.items() if bit
    )
    rows: list[tuple[str, str, str, int]] = []
    for first_particle, bit in PARTICLE_BITS.items():
        opposite = source_particles if bit else destination_particles
        for order in ORDER_PATTERNS:
            if (first_particle, order) in seen_particle_orders:
                continue
            selected: tuple[str, str, str, int] | None = None
            for action in non_anchor_actions:
                if (action, first_particle) in seen_action_particle:
                    continue
                for second_particle in opposite:
                    if (first_particle, second_particle) in seen_particle_pairs:
                        continue
                    selected = (
                        action,
                        first_particle,
                        second_particle,
                        order,
                    )
                    break
                if selected is not None:
                    break
            if selected is None:
                raise RuntimeError("unable to construct frozen held-out local grammar")
            rows.append(selected)
    return tuple(rows)


def heldout_unseen_local_compositions(
) -> tuple[ContinuousJapaneseObservation, ...]:
    rows: list[ContinuousJapaneseObservation] = []
    for spec_index, spec in enumerate(heldout_specs()):
        action, first_particle, second_particle, order = spec
        first = spec_index % len(ENTITY_LEXEMES)
        second = (spec_index + 2) % len(ENTITY_LEXEMES)
        state_index = 20_000 + spec_index
        for surface_first, surface_second in (
            (first, second),
            (second, first),
        ):
            rows.append(
                build_observation(
                    action=action,
                    first_particle=first_particle,
                    second_particle=second_particle,
                    order=order,
                    first_coordinate=surface_first,
                    second_coordinate=surface_second,
                    index=state_index,
                    evaluation=True,
                )
            )
    return tuple(rows)


def extract_local_factor(
    observation: ContinuousJapaneseObservation,
    *,
    entity_grounding: Sequence[tuple[str, int]],
    action_lexicon: Sequence[str],
    require_transition: bool = True,
) -> tuple[LocalGrammarFactor, tuple[int, int]]:
    text = observation.text
    entities = entity_spans(observation, entity_grounding)
    if len(entities) != 2 or entities[0][2] == entities[1][2]:
        raise ValueError("local grammar row requires two distinct entities")
    blocked = tuple((start, end) for start, end, _, _ in entities)

    actions: list[tuple[int, int, str]] = []
    for action in action_lexicon:
        spans = non_overlapping_occurrences(text, action, blocked)
        if len(spans) > 1:
            raise ValueError("an action lexeme occurs more than once")
        if len(spans) == 1:
            actions.append((*spans[0], action))
    if len(actions) != 1:
        raise ValueError("local grammar row requires exactly one action")
    action_start, action_end, action = actions[0]

    surface_entities = tuple(sorted(entities))
    semantic_spans = tuple(
        sorted(
            (
                (
                    surface_entities[0][0],
                    surface_entities[0][1],
                    "E0",
                ),
                (
                    surface_entities[1][0],
                    surface_entities[1][1],
                    "E1",
                ),
                (action_start, action_end, "A"),
            )
        )
    )
    order = tuple(label for _, _, label in semantic_spans)
    markers: dict[str, str] = {}
    for index, (_, end, label) in enumerate(semantic_spans):
        next_start = (
            semantic_spans[index + 1][0]
            if index + 1 < len(semantic_spans)
            else len(text)
        )
        gap = text[end:next_start]
        if label in {"E0", "E1"}:
            if not gap:
                raise ValueError("each entity requires a nonempty local marker")
            markers[label] = gap
        elif gap:
            raise ValueError("action-local gap is outside the declared grammar")

    coordinates = (
        surface_entities[0][3],
        surface_entities[1][3],
    )
    if not require_transition:
        return (
            LocalGrammarFactor(
                action,
                markers["E0"],
                markers["E1"],
                order,
                False,
            ),
            coordinates,
        )

    roles = infer_transition_roles(observation)
    if roles.source == coordinates[0] and roles.destination == coordinates[1]:
        effective_forward = True
    elif roles.source == coordinates[1] and roles.destination == coordinates[0]:
        effective_forward = False
    else:
        raise ValueError("surface entities do not explain the transition")
    return (
        LocalGrammarFactor(
            action,
            markers["E0"],
            markers["E1"],
            order,
            effective_forward,
        ),
        coordinates,
    )


def fit_local_case_grammar_from_factors(
    factors: Iterable[LocalGrammarFactor],
) -> LocalGrammarFit:
    rows = tuple(factors)
    if not rows:
        raise NonIdentifiableLocalGrammarError("no local grammar factors supplied")

    grouped: dict[tuple[str, str], Counter[bool]] = defaultdict(Counter)
    for factor in rows:
        grouped[(factor.action, factor.first_particle)][
            factor.effective_forward
        ] += 1

    labels: dict[tuple[str, str], bool] = {}
    training_errors = 0
    for key, counts in grouped.items():
        if counts[True] == counts[False]:
            raise NonIdentifiableLocalGrammarError(
                f"local majority is tied for {key!r}"
            )
        labels[key] = counts[True] > counts[False]
        training_errors += min(counts.values())

    actions = tuple(sorted({action for action, _ in labels}))
    particles = tuple(
        sorted(
            {
                particle
                for factor in rows
                for particle in (
                    factor.first_particle,
                    factor.second_particle,
                )
            }
        )
    )
    particle_ids = {particle: index for index, particle in enumerate(particles)}
    edges = tuple(
        LabeledSemanticEdge(
            action,
            particle_ids[particle],
            label,
        )
        for (action, particle), label in sorted(labels.items())
    )
    try:
        factorization = induce_linear_factorization(
            edges,
            verbs=actions,
            template_positions=tuple(range(len(particles))),
        )
    except InconsistentSemanticsError as error:
        raise NonIdentifiableLocalGrammarError(
            "local action-particle graph has a contradictory cycle"
        ) from error
    if not factorization.identifiable:
        raise NonIdentifiableLocalGrammarError(
            "local action-particle graph is disconnected"
        )

    particle_bits = dict(factorization.template_bits)
    for factor in rows:
        first_id = particle_ids[factor.first_particle]
        second_id = particle_ids[factor.second_particle]
        if particle_bits[first_id] == particle_bits[second_id]:
            raise NonIdentifiableLocalGrammarError(
                "observed case markers do not encode opposite local roles"
            )

    return LocalGrammarFit(
        tuple((particle, particle_ids[particle]) for particle in particles),
        tuple(sorted({factor.order for factor in rows})),
        factorization,
        training_errors,
        len(rows),
        0,
    )


def fit_local_case_grammar(
    observations: Iterable[ContinuousJapaneseObservation],
    *,
    entity_grounding: Sequence[tuple[str, int]],
    action_lexicon: Sequence[str],
) -> LocalGrammarFit:
    factors: list[LocalGrammarFactor] = []
    skipped = 0
    for observation in observations:
        try:
            factor, _ = extract_local_factor(
                observation,
                entity_grounding=entity_grounding,
                action_lexicon=action_lexicon,
            )
            factors.append(factor)
        except ValueError:
            skipped += 1
    fitted = fit_local_case_grammar_from_factors(factors)
    return LocalGrammarFit(
        fitted.particle_index,
        fitted.order_patterns,
        fitted.factorization,
        fitted.training_errors,
        fitted.semantic_rows,
        skipped,
    )


def induce_local_case_grammar(
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[
    LocalCaseGrammarModel,
    ContinuousJapaneseModel,
    LocalGrammarFit,
]:
    rows = tuple(observations)
    segmentation_model, _, _, _ = induce_continuous_japanese(rows)
    fitted = fit_local_case_grammar(
        rows,
        entity_grounding=segmentation_model.entity_lexicon,
        action_lexicon=segmentation_model.action_lexicon,
    )
    return (
        LocalCaseGrammarModel(
            segmentation_model.entity_lexicon,
            segmentation_model.action_lexicon,
            fitted.particle_index,
            fitted.order_patterns,
            fitted.factorization,
            len(rows),
        ),
        segmentation_model,
        fitted,
    )


def evaluate_model(
    model: LocalCaseGrammarModel,
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for observation in rows:
        prediction = model.predict(observation.sentence, observation.before)
        if prediction is None:
            continue
        answered += 1
        correct += int(prediction == observation.after)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def evaluate_template_model(
    model: ContinuousJapaneseModel,
    observations: Iterable[ContinuousJapaneseObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for observation in rows:
        prediction = model.predict(observation.sentence, observation.before)
        if prediction is None:
            continue
        answered += 1
        correct += int(prediction == observation.after)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def positionless_character_upper_bound(
    observations: Iterable[ContinuousJapaneseObservation],
) -> float:
    rows = tuple(observations)
    grouped: dict[
        tuple[tuple[str, ...], AnonymousState],
        Counter[AnonymousState],
    ] = defaultdict(Counter)
    for observation in rows:
        grouped[
            (tuple(sorted(observation.text)), observation.before)
        ][observation.after] += 1
    return (
        sum(max(counts.values()) for counts in grouped.values()) / len(rows)
        if rows
        else 0.0
    )


def exact_sentence_memorizer_coverage(
    training: Iterable[ContinuousJapaneseObservation],
    evaluation: Iterable[ContinuousJapaneseObservation],
) -> float:
    known = {observation.text for observation in training}
    rows = tuple(evaluation)
    return (
        sum(observation.text in known for observation in rows) / len(rows)
        if rows
        else 0.0
    )


def factor_memorizer_coverage(
    training: Iterable[ContinuousJapaneseObservation],
    evaluation: Iterable[ContinuousJapaneseObservation],
    model: LocalCaseGrammarModel,
    *,
    fields: tuple[str, ...],
) -> float:
    def factor_key(factor: LocalGrammarFactor) -> tuple[object, ...]:
        values: dict[str, object] = {
            "action": factor.action,
            "first_particle": factor.first_particle,
            "second_particle": factor.second_particle,
            "order": factor.order,
        }
        return tuple(values[field] for field in fields)

    known: set[tuple[object, ...]] = set()
    for observation in training:
        try:
            factor, _ = extract_local_factor(
                observation,
                entity_grounding=model.entity_lexicon,
                action_lexicon=model.action_lexicon,
            )
        except ValueError:
            continue
        known.add(factor_key(factor))

    rows = tuple(evaluation)
    covered = 0
    for observation in rows:
        factor, _ = extract_local_factor(
            observation,
            entity_grounding=model.entity_lexicon,
            action_lexicon=model.action_lexicon,
        )
        covered += int(factor_key(factor) in known)
    return covered / len(rows) if rows else 0.0


def majority_recovery_union_bound(
    *,
    groups: int,
    repetitions: int,
    flip_probability: float,
) -> float:
    if groups < 1 or repetitions < 1:
        raise ValueError("groups and repetitions must be positive")
    if not 0.0 <= flip_probability < 0.5:
        raise ValueError("flip probability must be in [0, 0.5)")
    gap = 0.5 - flip_probability
    return min(1.0, groups * exp(-2.0 * repetitions * gap * gap))


def tied_majority_is_rejected() -> bool:
    factors = (
        LocalGrammarFactor("a0", "p0", "p1", ("E0", "E1", "A"), True),
        LocalGrammarFactor("a0", "p0", "p1", ("E0", "E1", "A"), False),
    )
    try:
        fit_local_case_grammar_from_factors(factors)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def disconnected_graph_is_rejected() -> bool:
    factors = (
        LocalGrammarFactor("a0", "p0", "p1", ("E0", "E1", "A"), True),
        LocalGrammarFactor("a1", "p2", "p3", ("E0", "E1", "A"), False),
    )
    try:
        fit_local_case_grammar_from_factors(factors)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def contradictory_cycle_is_rejected() -> bool:
    factors = (
        LocalGrammarFactor("a0", "p0", "p1", ("E0", "E1", "A"), True),
        LocalGrammarFactor("a0", "p1", "p0", ("E0", "E1", "A"), False),
        LocalGrammarFactor("a1", "p0", "p1", ("E0", "E1", "A"), True),
        LocalGrammarFactor("a1", "p1", "p0", ("E0", "E1", "A"), True),
    )
    try:
        fit_local_case_grammar_from_factors(factors)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def same_polarity_pair_abstains(model: LocalCaseGrammarModel) -> bool:
    observation = build_observation(
        action="渡す",
        first_particle="が",
        second_particle="から",
        order=0,
        first_coordinate=0,
        second_coordinate=1,
        index=80_000,
    )
    return model.predict(observation.sentence, observation.before) is None


def unknown_particle_abstains(model: LocalCaseGrammarModel) -> bool:
    before = (1, 2, 3, 4)
    sentence = render_sentence(
        "渡す",
        "側",
        "に",
        0,
        "アキ",
        "ボブ",
        index=90_000,
        evaluation=True,
    )
    return model.predict(sentence, before) is None


def literal_template_payload_bits(
    templates: Iterable[tuple[str, str, str, OrderPattern]],
) -> int:
    unique = set(templates)
    return len(
        json.dumps(
            sorted(
                (
                    action,
                    first,
                    second,
                    list(order),
                )
                for action, first, second, order in unique
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


def run() -> dict[str, object]:
    training = training_observations()
    semantic_training = semantic_training_observations()
    heldout = heldout_unseen_local_compositions()
    model, template_model, fitted = induce_local_case_grammar(training)

    accuracy, coverage = evaluate_model(model, heldout)
    template_accuracy, template_coverage = evaluate_template_model(
        template_model,
        heldout,
    )
    flip_rate = FLIPS_PER_GROUP / REPETITIONS
    recovery_bound = majority_recovery_union_bound(
        groups=len(TRAINING_SPECS),
        repetitions=REPETITIONS,
        flip_probability=flip_rate,
    )
    full_template_coverage = factor_memorizer_coverage(
        semantic_training,
        heldout,
        model,
        fields=("action", "first_particle", "second_particle", "order"),
    )
    action_particle_coverage = factor_memorizer_coverage(
        semantic_training,
        heldout,
        model,
        fields=("action", "first_particle"),
    )
    particle_pair_coverage = factor_memorizer_coverage(
        semantic_training,
        heldout,
        model,
        fields=("first_particle", "second_particle"),
    )
    particle_order_coverage = factor_memorizer_coverage(
        semantic_training,
        heldout,
        model,
        fields=("first_particle", "order"),
    )

    particle_bits = dict(fitted.factorization.template_bits)
    source_count = sum(not bit for bit in particle_bits.values())
    destination_count = sum(bit for bit in particle_bits.values())
    valid_directed_pairs = 2 * source_count * destination_count
    expressible_templates = (
        len(model.action_lexicon)
        * valid_directed_pairs
        * len(model.order_patterns)
    )
    observed_full_templates = len(TRAINING_SPECS)
    observed_literal_bits = literal_template_payload_bits(
        (
            (
                action,
                first_particle,
                second_particle,
                ORDER_PATTERNS[order],
            )
            for action, first_particle, second_particle, order in TRAINING_SPECS
        )
    )
    exhaustive_literal_bits = literal_template_payload_bits(
        (
            (action, first_particle, second_particle, order)
            for action in model.action_lexicon
            for first_particle, first_id in model.particle_index
            for second_particle, second_id in model.particle_index
            if particle_bits[first_id] != particle_bits[second_id]
            for order in model.order_patterns
        )
    )

    theorem_checks = {
        "whitespace_free_segmentation_still_succeeds": (
            tuple(sorted(model.entity_lexicon))
            == tuple(sorted(template_model.entity_lexicon))
            and tuple(sorted(model.action_lexicon))
            == tuple(sorted(template_model.action_lexicon))
        ),
        "local_action_particle_graph_is_connected": (
            fitted.factorization.identifiable
        ),
        "all_six_case_markers_are_induced": len(model.particle_index) == 6,
        "all_three_action_positions_are_induced": (
            len(model.order_patterns) == 3
        ),
        "opposite_case_polarities_are_required": all(
            particle_bits[dict(model.particle_index)[first]]
            != particle_bits[dict(model.particle_index)[second]]
            for _, first, second, _ in TRAINING_SPECS
        ),
        "bounded_direction_noise_is_recovered": (
            fitted.training_errors
            == len(TRAINING_SPECS) * FLIPS_PER_GROUP
        ),
        "finite_sample_bound_is_below_one_percent": recovery_bound < 0.01,
        "auxiliary_incomplete_rows_are_skipped": fitted.skipped_rows == 2,
        "tied_majority_is_rejected": tied_majority_is_rejected(),
        "disconnected_graph_is_rejected": disconnected_graph_is_rejected(),
        "contradictory_cycle_is_rejected": contradictory_cycle_is_rejected(),
        "same_polarity_particle_pair_abstains": (
            same_polarity_pair_abstains(model)
        ),
        "unknown_particle_abstains": unknown_particle_abstains(model),
        "heldout_local_compositions_are_perfect": (
            accuracy == 1.0 and coverage == 1.0
        ),
        "literal_template_model_has_zero_coverage": template_coverage == 0.0,
        "full_tuple_memorizer_has_zero_coverage": full_template_coverage == 0.0,
        "action_particle_memorizer_has_zero_coverage": (
            action_particle_coverage == 0.0
        ),
        "particle_pair_memorizer_has_zero_coverage": (
            particle_pair_coverage == 0.0
        ),
        "particle_order_memorizer_has_zero_coverage": (
            particle_order_coverage == 0.0
        ),
        "positionless_character_upper_bound_is_half": (
            positionless_character_upper_bound(heldout) == 0.5
        ),
        "exact_sentence_memorizer_has_zero_coverage": (
            exact_sentence_memorizer_coverage(training, heldout) == 0.0
        ),
        "local_grammar_expands_beyond_observed_templates": (
            expressible_templates > observed_full_templates
        ),
        "local_grammar_payload_is_smaller_than_exhaustive_templates": (
            model.description_bits < exhaustive_literal_bits
        ),
        "all_raw_sentences_are_continuous": all(
            not any(character.isspace() for character in observation.sentence)
            for observation in (*training, *heldout)
        ),
    }

    return {
        "campaign": {
            "name": "phase18a3-local-case-grammar-c1",
            "language": "controlled continuous Japanese character strings",
            "full_case_frame_templates_stored_in_final_model": False,
            "entity_and_action_segmentation_reused_from_phase18a2": True,
            "anonymous_world_coordinates": True,
            "bounded_direction_noise": True,
            "public_benchmark_examples_used": 0,
        },
        "grammar": {
            "actions": len(model.action_lexicon),
            "case_markers": len(model.particle_index),
            "order_patterns": len(model.order_patterns),
            "observed_action_case_order_templates": observed_full_templates,
            "valid_directed_case_pairs": valid_directed_pairs,
            "expressible_atomic_cross_product_templates": expressible_templates,
            "heldout_full_templates": len(heldout_specs()),
            "learned_particle_bits": [
                [particle, particle_bits[index]]
                for particle, index in model.particle_index
            ],
        },
        "evaluation": {
            "training_observations": len(training),
            "semantic_training_observations": len(semantic_training),
            "skipped_incomplete_observations": fitted.skipped_rows,
            "heldout_specifications": len(heldout_specs()),
            "heldout_role_reversal_rows": len(heldout),
            "heldout_accuracy": accuracy,
            "heldout_coverage": coverage,
            "phase18a2_literal_template_accuracy": template_accuracy,
            "phase18a2_literal_template_coverage": template_coverage,
            "full_tuple_memorizer_coverage": full_template_coverage,
            "action_first_particle_memorizer_coverage": (
                action_particle_coverage
            ),
            "particle_pair_memorizer_coverage": particle_pair_coverage,
            "particle_order_memorizer_coverage": particle_order_coverage,
            "positionless_character_upper_bound": (
                positionless_character_upper_bound(heldout)
            ),
            "exact_sentence_memorizer_coverage": (
                exact_sentence_memorizer_coverage(training, heldout)
            ),
        },
        "theory": {
            "identifying_action_particle_edges": len(TRAINING_SPECS),
            "repetitions_per_edge": REPETITIONS,
            "adversarial_flips_per_edge": FLIPS_PER_GROUP,
            "empirical_flip_rate": flip_rate,
            "iid_hoeffding_union_bound": recovery_bound,
            "identifiability_condition": (
                "the action-to-first-case-marker XOR graph is connected and "
                "cycle-consistent; every observed second marker has the opposite "
                "latent case polarity; all accepted order atoms are learned "
                "independently of action and case-pair identity"
            ),
        },
        "resource_accounting": {
            "serialized_local_grammar_model_bits": model.description_bits,
            "literal_observed_template_payload_bits": observed_literal_bits,
            "literal_exhaustive_template_payload_bits": exhaustive_literal_bits,
            "phase18a3_module_source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "learned_model": {
            "entity_lexicon": [list(row) for row in model.entity_lexicon],
            "action_lexicon": list(model.action_lexicon),
            "particle_index": [list(row) for row in model.particle_index],
            "order_patterns": [list(row) for row in model.order_patterns],
            "factorization": model.factorization.render(),
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "literal_case_frame_storage_removed": all(
                theorem_checks.values()
            ),
            "unseen_local_grammar_recombination_demonstrated": all(
                theorem_checks.values()
            ),
            "general_japanese_grammar_demonstrated": False,
            "passive_causative_or_inflection_understanding_demonstrated": False,
            "natural_language_understanding_demonstrated": False,
            "japanese_high_school_intelligence_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "entity and action segmentation are inherited from Phase 18a-2 rather than jointly reoptimized with the local grammar",
            "the declared grammar attaches one nonempty marker immediately after each entity",
            "discourse material is restricted to prefixes outside the semantic core",
            "only three action positions and one binary copy event are supported",
            "case markers are monosemous and do not undergo phonological or orthographic variation",
            "verb inflection, passive, causative, negation, synonymy, ellipsis, and discourse reference remain absent",
            "world interventions remain noiseless apart from bounded direction-label flips",
            "Python and its standard library remain excluded substrate",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    grammar = payload["grammar"]
    evaluation = payload["evaluation"]
    theory = payload["theory"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 18a-3 results: local Japanese case grammar",
        "",
        "Phase 18a-3 removes literal whole-frame storage from the final semantic",
        "model. It learns action meaning, local case-marker polarity, and action",
        "position atoms separately, then recombines them on unseen full forms.",
        "",
        "## Atomic grammar",
        "",
        f"- Actions / case markers / order atoms: **{grammar['actions']} / {grammar['case_markers']} / {grammar['order_patterns']}**",
        f"- Observed full action-case-order templates: **{grammar['observed_action_case_order_templates']}**",
        f"- Valid directed case pairs: **{grammar['valid_directed_case_pairs']}**",
        f"- Expressible atomic cross-product templates: **{grammar['expressible_atomic_cross_product_templates']}**",
        f"- Held-out whole templates: **{grammar['heldout_full_templates']}**",
        "",
        "## Held-out transfer",
        "",
        f"- Training / semantic / skipped rows: **{evaluation['training_observations']} / {evaluation['semantic_training_observations']} / {evaluation['skipped_incomplete_observations']}**",
        f"- Held-out specifications / reversal rows: **{evaluation['heldout_specifications']} / {evaluation['heldout_role_reversal_rows']}**",
        f"- Local grammar accuracy / coverage: **{100 * evaluation['heldout_accuracy']:.1f}% / {100 * evaluation['heldout_coverage']:.1f}%**",
        f"- Phase 18a-2 literal-template coverage: **{100 * evaluation['phase18a2_literal_template_coverage']:.1f}%**",
        f"- Action+first-case memorizer coverage: **{100 * evaluation['action_first_particle_memorizer_coverage']:.1f}%**",
        f"- Case-pair memorizer coverage: **{100 * evaluation['particle_pair_memorizer_coverage']:.1f}%**",
        f"- Case+order memorizer coverage: **{100 * evaluation['particle_order_memorizer_coverage']:.1f}%**",
        f"- Positionless character upper bound: **{100 * evaluation['positionless_character_upper_bound']:.1f}%**",
        "",
        "## Noise and resource accounting",
        "",
        f"- Direction flip rate: **{100 * theory['empirical_flip_rate']:.1f}%**",
        f"- IID Hoeffding union bound: **{100 * theory['iid_hoeffding_union_bound']:.3f}%**",
        f"- Serialized local grammar: **{resources['serialized_local_grammar_model_bits']} bits**",
        f"- Literal observed-template payload: **{resources['literal_observed_template_payload_bits']} bits**",
        f"- Literal exhaustive supported-template payload: **{resources['literal_exhaustive_template_payload_bits']} bits**",
        f"- Phase 18a-3 source: **{resources['phase18a3_module_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and declared",
        "",
        "## Claim boundary",
        "",
        "This refutes literal whole-case-frame memorization for the declared",
        "held-out cross product. It remains a small controlled grammar, not general",
        "Japanese syntax, reading comprehension, or high-school intelligence.",
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
    (output / "phase18a3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a3.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
