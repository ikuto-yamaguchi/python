from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import permutations, product
import json
from math import exp
from pathlib import Path
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

from .phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    LinearFactorizationModel,
    induce_linear_factorization,
)


AnonymousState = tuple[int, ...]
FrameKey = tuple[str, str, int]

ENTITY_TOKENS = ("アキ", "ボブ", "チカ", "ダイ")
ACTION_TOKENS = ("渡す", "受ける", "写す", "移す")
ACTION_BITS = {"渡す": True, "受ける": False, "写す": True, "移す": False}
FRAME_BITS = {0: False, 1: True, 2: False, 3: True, 4: False}
IDENTIFYING_PAIRS = (
    ("渡す", 0),
    ("渡す", 1),
    ("渡す", 2),
    ("渡す", 3),
    ("渡す", 4),
    ("受ける", 0),
    ("写す", 0),
    ("移す", 0),
)
REPETITIONS = 21
FLIPS_PER_GROUP = 2

_PARTICLE = re.compile(r"^[ぁ-ゖ]{1,2}$")
_PUNCTUATION = "。、，,！？!?「」『』（）()【】"


class NonIdentifiableJapaneseGroundingError(ValueError):
    pass


@dataclass(frozen=True)
class JapaneseGroundingObservation:
    sentence: str
    before: AnonymousState
    after: AnonymousState

    @classmethod
    def build(
        cls,
        sentence: str,
        before: Sequence[int],
        after: Sequence[int],
    ) -> "JapaneseGroundingObservation":
        before_row = tuple(int(value) for value in before)
        after_row = tuple(int(value) for value in after)
        if len(before_row) < 2 or len(before_row) != len(after_row):
            raise ValueError("anonymous states must have equal length >= 2")
        if not normalize_tokens(sentence):
            raise ValueError("sentence must contain at least one token")
        return cls(sentence, before_row, after_row)

    @property
    def tokens(self) -> tuple[str, ...]:
        return normalize_tokens(self.sentence)


@dataclass(frozen=True)
class TransitionRoles:
    source: int
    destination: int


@dataclass(frozen=True)
class GroundingSearchResult:
    best_mappings: tuple[tuple[tuple[str, int], ...], ...]
    best_cost: int
    second_best_cost: int | None
    candidate_assignments: int

    @property
    def margin(self) -> int | None:
        if self.second_best_cost is None:
            return None
        return self.second_best_cost - self.best_cost


@dataclass(frozen=True)
class FactorObservation:
    action: str
    frame: FrameKey
    effective_forward: bool


@dataclass(frozen=True)
class JapaneseGroundingModel:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    frame_index: tuple[tuple[FrameKey, int], ...]
    factorization: LinearFactorizationModel
    training_rows: int

    def entity_map(self) -> dict[str, int]:
        return dict(self.entity_lexicon)

    def frame_map(self) -> dict[FrameKey, int]:
        return dict(self.frame_index)

    @property
    def description_bits(self) -> int:
        payload = {
            "entity_lexicon": [list(row) for row in self.entity_lexicon],
            "action_lexicon": list(self.action_lexicon),
            "frame_index": [[list(frame), index] for frame, index in self.frame_index],
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
        tokens = normalize_tokens(sentence)
        entity_map = self.entity_map()
        entity_set = set(entity_map)
        action_set = set(self.action_lexicon)

        entity_positions = [
            (index, token)
            for index, token in enumerate(tokens)
            if token in entity_set
        ]
        action_positions = [
            (index, token)
            for index, token in enumerate(tokens)
            if token in action_set
        ]
        if (
            len(entity_positions) != 2
            or entity_positions[0][1] == entity_positions[1][1]
            or len(action_positions) != 1
        ):
            return None

        action_index, action = action_positions[0]
        semantic_positions = sorted([*entity_positions, (action_index, action)])
        action_position = next(
            index
            for index, (_, token) in enumerate(semantic_positions)
            if token == action
        )
        (left_index, left), (right_index, right) = entity_positions
        frame = (
            particle_after(
                tokens,
                left_index,
                entity_set=entity_set,
                action_set=action_set,
            ),
            particle_after(
                tokens,
                right_index,
                entity_set=entity_set,
                action_set=action_set,
            ),
            action_position,
        )
        frame_id = self.frame_map().get(frame)
        if frame_id is None:
            return None
        direction = self.factorization.effective_forward(action, frame_id)
        if direction is None:
            return None

        left_coordinate = entity_map[left]
        right_coordinate = entity_map[right]
        if max(left_coordinate, right_coordinate) >= len(before_row):
            return None
        source, destination = (
            (left_coordinate, right_coordinate)
            if direction
            else (right_coordinate, left_coordinate)
        )
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


def normalize_tokens(sentence: str) -> tuple[str, ...]:
    text = unicodedata.normalize("NFKC", sentence)
    for mark in _PUNCTUATION:
        text = text.replace(mark, " ")
    return tuple(token for token in text.split() if token)


def infer_transition_roles(
    observation: JapaneseGroundingObservation,
) -> TransitionRoles:
    changed = [
        index
        for index, (before, after) in enumerate(
            zip(observation.before, observation.after)
        )
        if before != after
    ]
    if len(changed) != 1:
        raise ValueError("copy intervention must change exactly one coordinate")
    destination = changed[0]
    source_candidates = [
        index
        for index, value in enumerate(observation.before)
        if index != destination and value == observation.after[destination]
    ]
    if len(source_candidates) != 1:
        raise ValueError("transition must identify one unique source coordinate")
    return TransitionRoles(source_candidates[0], destination)


def token_signatures(
    observations: Sequence[JapaneseGroundingObservation],
) -> dict[str, tuple[bool, ...]]:
    vocabulary = sorted(
        {token for observation in observations for token in observation.tokens}
    )
    return {
        token: tuple(token in observation.tokens for observation in observations)
        for token in vocabulary
    }


def coordinate_signatures(
    observations: Sequence[JapaneseGroundingObservation],
) -> dict[int, tuple[bool, ...]]:
    if not observations:
        return {}
    coordinate_count = len(observations[0].before)
    if any(len(observation.before) != coordinate_count for observation in observations):
        raise ValueError("all observations must share one coordinate universe")
    roles = tuple(infer_transition_roles(observation) for observation in observations)
    return {
        coordinate: tuple(
            coordinate in (role.source, role.destination) for role in roles
        )
        for coordinate in range(coordinate_count)
    }


def hamming_distance(
    left: Sequence[bool],
    right: Sequence[bool],
) -> int:
    if len(left) != len(right):
        raise ValueError("signatures must have equal length")
    return sum(left_value != right_value for left_value, right_value in zip(left, right))


def robust_entity_grounding_search(
    observations: Iterable[JapaneseGroundingObservation],
) -> GroundingSearchResult:
    """Exhaustively minimize occurrence/participation Hamming loss.

    This replaces the exact-signature equality used in Phase 17g. The finite
    candidate universe is every surface token in the campaign. A unique
    minimum is required; equal-cost aliases are retained as non-identifiable.
    """

    rows = tuple(observations)
    if not rows:
        raise ValueError("at least one observation is required")
    token_rows = token_signatures(rows)
    coordinate_rows = coordinate_signatures(rows)
    vocabulary = tuple(sorted(token_rows))
    coordinates = tuple(sorted(coordinate_rows))
    if len(vocabulary) < len(coordinates):
        return GroundingSearchResult(tuple(), 0, None, 0)

    best_cost: int | None = None
    second_best_cost: int | None = None
    best_mappings: list[tuple[tuple[str, int], ...]] = []
    candidate_assignments = 0

    for assigned_tokens in permutations(vocabulary, len(coordinates)):
        candidate_assignments += 1
        cost = sum(
            hamming_distance(
                coordinate_rows[coordinate],
                token_rows[token],
            )
            for coordinate, token in zip(coordinates, assigned_tokens)
        )
        mapping = tuple(
            sorted(
                (token, coordinate)
                for coordinate, token in zip(coordinates, assigned_tokens)
            )
        )
        if best_cost is None or cost < best_cost:
            second_best_cost = best_cost
            best_cost = cost
            best_mappings = [mapping]
        elif cost == best_cost:
            best_mappings.append(mapping)
        elif second_best_cost is None or cost < second_best_cost:
            second_best_cost = cost

    return GroundingSearchResult(
        tuple(sorted(set(best_mappings))),
        int(best_cost if best_cost is not None else 0),
        second_best_cost,
        candidate_assignments,
    )


def induce_robust_entity_grounding(
    observations: Iterable[JapaneseGroundingObservation],
) -> tuple[tuple[tuple[str, int], ...], GroundingSearchResult]:
    search = robust_entity_grounding_search(observations)
    if len(search.best_mappings) != 1:
        raise NonIdentifiableJapaneseGroundingError(
            f"entity grounding has {len(search.best_mappings)} equal-cost optima"
        )
    if search.margin is not None and search.margin < 1:
        raise NonIdentifiableJapaneseGroundingError(
            "entity grounding has no positive loss margin"
        )
    return search.best_mappings[0], search


def is_predicate_candidate(token: str) -> bool:
    """Minimal declared Japanese morphology prior for this campaign."""

    return len(token) >= 2 and token.endswith(("す", "る"))


def particle_after(
    tokens: Sequence[str],
    index: int,
    *,
    entity_set: set[str],
    action_set: set[str],
) -> str:
    if index + 1 >= len(tokens):
        return "<ZERO>"
    following = tokens[index + 1]
    if following in entity_set or following in action_set:
        return "<ZERO>"
    if _PARTICLE.fullmatch(following):
        return following
    return "<ZERO>"


def extract_factor_observation(
    observation: JapaneseGroundingObservation,
    entity_grounding: Sequence[tuple[str, int]],
) -> FactorObservation:
    entity_map = dict(entity_grounding)
    entity_set = set(entity_map)
    tokens = observation.tokens

    entity_positions = [
        (index, token)
        for index, token in enumerate(tokens)
        if token in entity_set
    ]
    if (
        len(entity_positions) != 2
        or entity_positions[0][1] == entity_positions[1][1]
    ):
        raise ValueError("factor row must contain two distinct grounded entities")

    action_positions = [
        (index, token)
        for index, token in enumerate(tokens)
        if is_predicate_candidate(token)
    ]
    if len(action_positions) != 1:
        raise ValueError("factor row must contain one predicate candidate")
    action_index, action = action_positions[0]

    semantic_positions = sorted([*entity_positions, (action_index, action)])
    action_position = next(
        index
        for index, (_, token) in enumerate(semantic_positions)
        if token == action
    )
    (left_index, left), (right_index, right) = entity_positions
    frame = (
        particle_after(
            tokens,
            left_index,
            entity_set=entity_set,
            action_set={action},
        ),
        particle_after(
            tokens,
            right_index,
            entity_set=entity_set,
            action_set={action},
        ),
        action_position,
    )

    roles = infer_transition_roles(observation)
    left_coordinate = entity_map[left]
    right_coordinate = entity_map[right]
    if roles == TransitionRoles(left_coordinate, right_coordinate):
        effective_forward = True
    elif roles == TransitionRoles(right_coordinate, left_coordinate):
        effective_forward = False
    else:
        raise ValueError("surface participants do not explain the transition")
    return FactorObservation(action, frame, effective_forward)


def fit_factorization_from_grounding(
    observations: Iterable[JapaneseGroundingObservation],
    entity_grounding: Sequence[tuple[str, int]],
) -> tuple[
    tuple[str, ...],
    tuple[tuple[FrameKey, int], ...],
    LinearFactorizationModel,
    dict[tuple[str, FrameKey], float],
    int,
]:
    rows = tuple(observations)
    factors: list[FactorObservation] = []
    skipped = 0
    for observation in rows:
        try:
            factors.append(
                extract_factor_observation(observation, entity_grounding)
            )
        except ValueError:
            skipped += 1

    grouped: dict[
        tuple[str, FrameKey],
        Counter[bool],
    ] = defaultdict(Counter)
    for factor in factors:
        grouped[(factor.action, factor.frame)][factor.effective_forward] += 1
    if not grouped:
        raise NonIdentifiableJapaneseGroundingError(
            "no complete Japanese factor rows survived"
        )

    labels: dict[tuple[str, FrameKey], bool] = {}
    empirical_noise: dict[tuple[str, FrameKey], float] = {}
    for key, counts in grouped.items():
        if counts[True] == counts[False]:
            raise NonIdentifiableJapaneseGroundingError(
                f"majority label is tied for {key!r}"
            )
        labels[key] = counts[True] > counts[False]
        empirical_noise[key] = min(counts.values()) / sum(counts.values())

    actions = tuple(sorted({action for action, _ in labels}))
    frames = tuple(sorted({frame for _, frame in labels}, key=repr))
    frame_ids = {frame: index for index, frame in enumerate(frames)}
    edges = tuple(
        LabeledSemanticEdge(
            action,
            frame_ids[frame],
            label,
        )
        for (action, frame), label in sorted(labels.items(), key=repr)
    )
    try:
        factorization = induce_linear_factorization(
            edges,
            verbs=actions,
            template_positions=tuple(range(len(frames))),
        )
    except InconsistentSemanticsError as error:
        raise NonIdentifiableJapaneseGroundingError(
            "majority factors contain a contradictory cycle"
        ) from error
    if not factorization.identifiable:
        raise NonIdentifiableJapaneseGroundingError(
            "action/case-frame graph is disconnected"
        )

    return (
        actions,
        tuple((frame, frame_ids[frame]) for frame in frames),
        factorization,
        empirical_noise,
        skipped,
    )


def induce_japanese_grounding(
    observations: Iterable[JapaneseGroundingObservation],
) -> tuple[
    JapaneseGroundingModel,
    GroundingSearchResult,
    dict[tuple[str, FrameKey], float],
    int,
]:
    rows = tuple(observations)
    grounding, search = induce_robust_entity_grounding(rows)
    (
        actions,
        frame_index,
        factorization,
        empirical_noise,
        skipped,
    ) = fit_factorization_from_grounding(rows, grounding)
    return (
        JapaneseGroundingModel(
            tuple(grounding),
            actions,
            frame_index,
            factorization,
            len(rows),
        ),
        search,
        empirical_noise,
        skipped,
    )


def render_sentence(
    action: str,
    frame: int,
    left: str,
    right: str,
    *,
    index: int,
) -> str:
    if frame == 0:
        semantic = [left, "が", right, "に", action]
    elif frame == 1:
        semantic = [left, "に", right, "が", action]
    elif frame == 2:
        semantic = [left, "は", right, "へ", action]
    elif frame == 3:
        semantic = [action, left, "から", right, "へ"]
    elif frame == 4:
        semantic = [left, action, right, "に"]
    else:
        raise ValueError("unknown controlled case frame")

    prefixes = ((), ("今日は",), ("静かに",), ("このあと",))
    suffixes = ((), ("らしい",), ("ようだ",))
    tokens = [
        *prefixes[index % len(prefixes)],
        *semantic,
        *suffixes[(index // 2) % len(suffixes)],
    ]
    return " ".join(tokens) + "。"


def participant_pair(group_index: int, repetition: int) -> tuple[int, int]:
    left = (group_index + repetition) % len(ENTITY_TOKENS)
    right = (group_index + 2 * repetition + 1) % len(ENTITY_TOKENS)
    if right == left:
        right = (right + 1) % len(ENTITY_TOKENS)
    return left, right


def build_observation(
    *,
    action: str,
    frame: int,
    left_coordinate: int,
    right_coordinate: int,
    index: int,
    flip_label: bool = False,
    sentence: str | None = None,
) -> JapaneseGroundingObservation:
    before = tuple(index * 100 + coordinate + 1 for coordinate in range(4))
    effective_forward = ACTION_BITS[action] ^ FRAME_BITS[frame]
    if flip_label:
        effective_forward = not effective_forward
    source, destination = (
        (left_coordinate, right_coordinate)
        if effective_forward
        else (right_coordinate, left_coordinate)
    )
    after = list(before)
    after[destination] = before[source]
    rendered = sentence or render_sentence(
        action,
        frame,
        ENTITY_TOKENS[left_coordinate],
        ENTITY_TOKENS[right_coordinate],
        index=index,
    )
    return JapaneseGroundingObservation.build(rendered, before, after)


def semantic_training_observations() -> tuple[JapaneseGroundingObservation, ...]:
    rows: list[JapaneseGroundingObservation] = []
    for group_index, (action, frame) in enumerate(IDENTIFYING_PAIRS):
        for repetition in range(REPETITIONS):
            left, right = participant_pair(group_index, repetition)
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=left,
                    right_coordinate=right,
                    index=group_index * REPETITIONS + repetition,
                    flip_label=repetition < FLIPS_PER_GROUP,
                )
            )
    return tuple(rows)


def auxiliary_grounding_noise_observations(
) -> tuple[JapaneseGroundingObservation, ...]:
    # One omitted participant mention and one spurious non-participant mention.
    # These rows affect grounding signatures but are intentionally unusable as
    # complete semantic factor equations.
    return (
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=10_000,
            sentence="今日は アキ が 渡す。",
        ),
        build_observation(
            action="写す",
            frame=2,
            left_coordinate=2,
            right_coordinate=3,
            index=10_001,
            sentence="アキ を 見ながら チカ は ダイ へ 写す。",
        ),
    )


def training_observations() -> tuple[JapaneseGroundingObservation, ...]:
    return (
        *semantic_training_observations(),
        *auxiliary_grounding_noise_observations(),
    )


def heldout_unseen_compositions() -> tuple[JapaneseGroundingObservation, ...]:
    unseen = tuple(
        pair
        for pair in product(ACTION_TOKENS, range(len(FRAME_BITS)))
        if pair not in IDENTIFYING_PAIRS
    )
    rows: list[JapaneseGroundingObservation] = []
    for pair_index, (action, frame) in enumerate(unseen):
        left = pair_index % len(ENTITY_TOKENS)
        right = (pair_index + 2) % len(ENTITY_TOKENS)
        before_index = 20_000 + pair_index
        surface_index = 30_000 + pair_index
        for pair_left, pair_right in ((left, right), (right, left)):
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=pair_left,
                    right_coordinate=pair_right,
                    index=before_index,
                    sentence=render_sentence(
                        action,
                        frame,
                        ENTITY_TOKENS[pair_left],
                        ENTITY_TOKENS[pair_right],
                        index=surface_index,
                    ),
                )
            )
    return tuple(rows)


def evaluate_model(
    model: JapaneseGroundingModel,
    observations: Iterable[JapaneseGroundingObservation],
) -> tuple[float, float]:
    rows = tuple(observations)
    answered = 0
    correct = 0
    for observation in rows:
        predicted = model.predict(observation.sentence, observation.before)
        if predicted is None:
            continue
        answered += 1
        correct += int(predicted == observation.after)
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def positionless_surface_upper_bound(
    observations: Iterable[JapaneseGroundingObservation],
) -> float:
    rows = tuple(observations)
    grouped: dict[
        tuple[tuple[str, ...], AnonymousState],
        Counter[AnonymousState],
    ] = defaultdict(Counter)
    for observation in rows:
        grouped[
            (tuple(sorted(observation.tokens)), observation.before)
        ][observation.after] += 1
    return (
        sum(max(counts.values()) for counts in grouped.values()) / len(rows)
        if rows
        else 0.0
    )


def exact_sentence_memorizer_coverage(
    training: Iterable[JapaneseGroundingObservation],
    evaluation: Iterable[JapaneseGroundingObservation],
) -> float:
    known = {observation.sentence for observation in training}
    rows = tuple(evaluation)
    return (
        sum(observation.sentence in known for observation in rows) / len(rows)
        if rows
        else 0.0
    )


def factor_baseline(
    training: Iterable[JapaneseGroundingObservation],
    evaluation: Iterable[JapaneseGroundingObservation],
    entity_grounding: Sequence[tuple[str, int]],
    *,
    use_action: bool,
    use_frame: bool,
) -> tuple[float, float]:
    train_factors = tuple(
        extract_factor_observation(observation, entity_grounding)
        for observation in training
    )
    evaluation_factors = tuple(
        extract_factor_observation(observation, entity_grounding)
        for observation in evaluation
    )
    grouped: dict[object, Counter[bool]] = defaultdict(Counter)

    def key(factor: FactorObservation) -> object:
        return (
            factor.action if use_action else None,
            factor.frame if use_frame else None,
        )

    for factor in train_factors:
        grouped[key(factor)][factor.effective_forward] += 1

    answered = 0
    correct = 0
    for factor in evaluation_factors:
        counts = grouped.get(key(factor))
        if not counts:
            continue
        prediction = counts[True] >= counts[False]
        answered += 1
        correct += int(prediction == factor.effective_forward)
    return (
        correct / len(evaluation_factors) if evaluation_factors else 0.0,
        answered / len(evaluation_factors) if evaluation_factors else 0.0,
    )


def majority_recovery_union_bound(
    *,
    groups: int,
    repetitions: int,
    flip_probability: float,
) -> float:
    """Hoeffding union bound for independent binary label flips."""

    if groups < 1 or repetitions < 1:
        raise ValueError("groups and repetitions must be positive")
    if not 0.0 <= flip_probability < 0.5:
        raise ValueError("flip probability must be in [0, 0.5)")
    gap = 0.5 - flip_probability
    return min(1.0, groups * exp(-2.0 * repetitions * gap * gap))


def collision_control_groundings() -> int:
    modified = tuple(
        JapaneseGroundingObservation.build(
            observation.sentence
            + (" 影" if "アキ" in observation.tokens else ""),
            observation.before,
            observation.after,
        )
        for observation in training_observations()
    )
    return len(robust_entity_grounding_search(modified).best_mappings)


def tied_majority_is_rejected() -> bool:
    grounding = tuple(
        (token, index) for index, token in enumerate(ENTITY_TOKENS)
    )
    rows = (
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=60_000,
            flip_label=False,
        ),
        build_observation(
            action="渡す",
            frame=0,
            left_coordinate=0,
            right_coordinate=1,
            index=60_001,
            flip_label=True,
        ),
    )
    try:
        fit_factorization_from_grounding(rows, grounding)
    except NonIdentifiableJapaneseGroundingError:
        return True
    return False


def disconnected_case_frame_graph_is_rejected() -> bool:
    disconnected_pairs = (
        ("渡す", 0),
        ("渡す", 1),
        ("受ける", 0),
        ("写す", 2),
        ("写す", 3),
        ("写す", 4),
        ("移す", 2),
    )
    rows: list[JapaneseGroundingObservation] = []
    for group_index, (action, frame) in enumerate(disconnected_pairs):
        for repetition in range(5):
            left, right = participant_pair(group_index, repetition)
            rows.append(
                build_observation(
                    action=action,
                    frame=frame,
                    left_coordinate=left,
                    right_coordinate=right,
                    index=50_000 + group_index * 5 + repetition,
                )
            )
    try:
        induce_japanese_grounding(rows)
    except NonIdentifiableJapaneseGroundingError:
        return True
    return False


def run() -> dict[str, object]:
    training = training_observations()
    semantic_training = semantic_training_observations()
    heldout = heldout_unseen_compositions()
    (
        model,
        grounding_search,
        empirical_noise,
        skipped_rows,
    ) = induce_japanese_grounding(training)
    accuracy, coverage = evaluate_model(model, heldout)
    true_grounding = tuple(
        (token, index) for index, token in enumerate(ENTITY_TOKENS)
    )
    action_only_accuracy, action_only_coverage = factor_baseline(
        semantic_training,
        heldout,
        true_grounding,
        use_action=True,
        use_frame=False,
    )
    frame_only_accuracy, frame_only_coverage = factor_baseline(
        semantic_training,
        heldout,
        true_grounding,
        use_action=False,
        use_frame=True,
    )
    joint_memorizer_accuracy, joint_memorizer_coverage = factor_baseline(
        semantic_training,
        heldout,
        true_grounding,
        use_action=True,
        use_frame=True,
    )
    flip_rate = FLIPS_PER_GROUP / REPETITIONS
    recovery_bound = majority_recovery_union_bound(
        groups=len(IDENTIFYING_PAIRS),
        repetitions=REPETITIONS,
        flip_probability=flip_rate,
    )
    collision_groundings = collision_control_groundings()
    token_lengths = tuple(
        len(observation.tokens) for observation in (*training, *heldout)
    )

    theorem_checks = {
        "noisy_entity_grounding_has_one_optimum": len(
            grounding_search.best_mappings
        )
        == 1,
        "noisy_entity_grounding_has_positive_margin": (
            grounding_search.margin is None or grounding_search.margin > 0
        ),
        "auxiliary_ellipsis_and_spurious_rows_are_skipped": skipped_rows == 2,
        "entity_mimicking_distractor_is_non_identifying": collision_groundings
        > 1,
        "bounded_label_noise_is_recovered": all(
            rate == flip_rate for rate in empirical_noise.values()
        ),
        "finite_sample_majority_bound_is_below_one_percent": recovery_bound
        < 0.01,
        "tied_majority_is_rejected": tied_majority_is_rejected(),
        "disconnected_case_frame_graph_is_rejected": (
            disconnected_case_frame_graph_is_rejected()
        ),
        "heldout_action_case_compositions_are_perfect": (
            accuracy == 1.0 and coverage == 1.0
        ),
        "positionless_surface_classifier_bound_is_half": (
            positionless_surface_upper_bound(heldout) == 0.5
        ),
        "joint_action_frame_memorizer_has_zero_coverage": (
            joint_memorizer_coverage == 0.0
        ),
        "action_only_ablation_is_not_sufficient": action_only_accuracy < 1.0,
        "frame_only_ablation_is_not_sufficient": frame_only_accuracy < 1.0,
        "raw_sentences_have_variable_length": min(token_lengths)
        < max(token_lengths),
    }

    return {
        "campaign": {
            "name": "phase18a1-noisy-japanese-case-grounding-c1",
            "language": "whitespace-tokenized controlled Japanese",
            "anonymous_world_coordinates": True,
            "entity_labels_provided": False,
            "bounded_direction_label_noise": True,
            "ellipsis_and_spurious_mentions_in_grounding_data": True,
            "optional_modifiers_and_punctuation": True,
            "public_benchmark_examples_used": 0,
        },
        "theory": {
            "identifying_action_frame_edges": len(IDENTIFYING_PAIRS),
            "repetitions_per_edge": REPETITIONS,
            "adversarially_placed_flips_per_edge": FLIPS_PER_GROUP,
            "empirical_flip_rate": flip_rate,
            "iid_hoeffding_union_bound": recovery_bound,
            "bound_assumption": (
                "independent Bernoulli label flips below one half; the generated "
                "campaign uses a deterministic bounded flip count"
            ),
            "entity_grounding_objective": (
                "minimum total Hamming distance between token occurrence and "
                "anonymous coordinate participation signatures"
            ),
            "semantic_identifiability": (
                "majority-cleaned action/case-frame XOR graph must be connected "
                "and cycle-consistent"
            ),
        },
        "grounding": {
            "candidate_assignments": grounding_search.candidate_assignments,
            "best_hamming_cost": grounding_search.best_cost,
            "second_best_hamming_cost": grounding_search.second_best_cost,
            "loss_margin": grounding_search.margin,
            "best_groundings": len(grounding_search.best_mappings),
            "collision_control_groundings": collision_groundings,
            "skipped_incomplete_or_spurious_rows": skipped_rows,
        },
        "evaluation": {
            "training_rows": len(training),
            "semantic_training_rows": len(semantic_training),
            "heldout_unseen_compositions": len(heldout),
            "heldout_accuracy": accuracy,
            "heldout_coverage": coverage,
            "positionless_surface_upper_bound": positionless_surface_upper_bound(
                heldout
            ),
            "exact_sentence_memorizer_coverage": exact_sentence_memorizer_coverage(
                training, heldout
            ),
            "action_only_accuracy": action_only_accuracy,
            "action_only_coverage": action_only_coverage,
            "frame_only_accuracy": frame_only_accuracy,
            "frame_only_coverage": frame_only_coverage,
            "joint_action_frame_memorizer_accuracy": joint_memorizer_accuracy,
            "joint_action_frame_memorizer_coverage": joint_memorizer_coverage,
            "minimum_raw_tokens": min(token_lengths),
            "maximum_raw_tokens": max(token_lengths),
        },
        "resource_accounting": {
            "serialized_acquired_model_bits": model.description_bits,
            "phase18a1_module_source_bytes": Path(__file__).read_bytes().__len__(),
            "entity_assignment_search_space": grounding_search.candidate_assignments,
            "factorization_operations": model.factorization.operations,
            "python_runtime_and_standard_library_bytes_included": False,
        },
        "learned_model": {
            "entity_lexicon": [list(row) for row in model.entity_lexicon],
            "action_lexicon": list(model.action_lexicon),
            "frame_index": [
                [list(frame), index] for frame, index in model.frame_index
            ],
            "factorization": model.factorization.render(),
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "noise_tolerant_controlled_japanese_grounding_demonstrated": all(
                theorem_checks.values()
            ),
            "particle_and_order_information_is_causally_required": all(
                theorem_checks.values()
            ),
            "autonomous_japanese_tokenization_demonstrated": False,
            "open_domain_japanese_understanding_demonstrated": False,
            "japanese_high_school_intelligence_demonstrated": False,
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "morpheme boundaries are supplied by whitespace",
            "predicate candidates use the handwritten Japanese suffix prior -す/-る",
            "particles are recognized by a one- or two-hiragana shape prior",
            "label-noise recovery uses repeated observations of the same latent action/frame edge",
            "entity grounding still assumes a finite anonymous coordinate vector",
            "each complete semantic row contains one binary copy event with two participants",
            "the Hoeffding bound assumes independent random flips while the generated flips are deterministic",
            "polysemy, synonymy, negation, discourse, unrestricted ellipsis, and multiple events remain absent",
            "Python and its standard library are declared substrate rather than counted system bytes",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    theory = payload["theory"]
    grounding = payload["grounding"]
    evaluation = payload["evaluation"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 18a-1 results: noisy controlled-Japanese grounding",
        "",
        "This campaign moves from artificial token strings to a controlled,",
        "whitespace-tokenized Japanese case-frame language. It jointly recovers",
        "surface entity aliases, action meanings, and particle/order frames from",
        "anonymous before/after interventions.",
        "",
        "## Noise and identifiability",
        "",
        f"- Action/frame edges: **{theory['identifying_action_frame_edges']}**",
        f"- Repetitions per edge: **{theory['repetitions_per_edge']}**",
        f"- Flipped labels per edge: **{theory['adversarially_placed_flips_per_edge']}**",
        f"- Empirical flip rate: **{100 * theory['empirical_flip_rate']:.2f}%**",
        f"- IID Hoeffding union bound: **{100 * theory['iid_hoeffding_union_bound']:.3f}%**",
        f"- Entity-grounding best cost / margin: **{grounding['best_hamming_cost']} / {grounding['loss_margin']}**",
        f"- Equal-signature collision groundings: **{grounding['collision_control_groundings']}**",
        "",
        "## Held-out composition",
        "",
        f"- Training rows: **{evaluation['training_rows']}**",
        f"- Held-out unseen action/frame rows: **{evaluation['heldout_unseen_compositions']}**",
        f"- Accuracy / coverage: **{100 * evaluation['heldout_accuracy']:.1f}% / {100 * evaluation['heldout_coverage']:.1f}%**",
        f"- Positionless surface upper bound: **{100 * evaluation['positionless_surface_upper_bound']:.1f}%**",
        f"- Action-only ablation: **{100 * evaluation['action_only_accuracy']:.1f}%**",
        f"- Frame-only ablation: **{100 * evaluation['frame_only_accuracy']:.1f}%**",
        f"- Memorized action/frame-pair coverage: **{100 * evaluation['joint_action_frame_memorizer_coverage']:.1f}%**",
        "",
        "## Resource accounting",
        "",
        f"- Serialized acquired model: **{resources['serialized_acquired_model_bits']} bits**",
        f"- Entity-assignment hypotheses checked: **{resources['entity_assignment_search_space']}**",
        f"- Factorization operations: **{resources['factorization_operations']}**",
        f"- Phase 18a-1 source: **{resources['phase18a1_module_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and explicitly declared",
        "",
        "## Claim boundary",
        "",
        "The result demonstrates noise-tolerant grounding and compositional transfer",
        "inside a small Japanese case-frame language. It does not demonstrate",
        "autonomous tokenization, open-domain Japanese understanding, or high-school",
        "level intelligence.",
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
    (output / "phase18a1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a1.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
