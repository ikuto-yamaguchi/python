from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from math import exp
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from ._phase18a2_continuous_japanese_core import (
    ContinuousJapaneseObservation,
    action_candidate_lexemes,
    complete_semantic_rows,
    entity_spans,
    exact_cover_action_lexicons,
    induce_entity_grounding,
    infer_transition_roles,
    non_overlapping_occurrences,
)
from .phase17f_linear_semantic_induction import (
    InconsistentSemanticsError,
    LabeledSemanticEdge,
    LinearFactorizationModel,
    induce_linear_factorization,
)

State = tuple[int, ...]
Order = tuple[str, str, str]

ENTITIES = ("アキ", "ボブ", "チカ", "ダイ")
ACTIONS = ("渡す", "受ける", "写す", "移す")
ACTION_BITS = {"渡す": True, "受ける": False, "写す": True, "移す": False}
PARTICLE_BITS = {
    "が": False, "から": False, "より": False,
    "に": True, "へ": True, "まで": True,
}
ORDERS: dict[int, Order] = {
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
FLIPS = 1


class NonIdentifiableLocalGrammarError(ValueError):
    pass


@dataclass(frozen=True)
class Factor:
    action: str
    first_particle: str
    second_particle: str
    order: Order
    forward: bool


@dataclass(frozen=True)
class Fit:
    particle_index: tuple[tuple[str, int], ...]
    orders: tuple[Order, ...]
    xor: LinearFactorizationModel
    errors: int
    rows: int
    skipped: int
    action_candidates: int = 0
    action_covers: int = 0
    valid_action_models: int = 0
    best_action_models: int = 0


@dataclass(frozen=True)
class LocalModel:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    particle_index: tuple[tuple[str, int], ...]
    orders: tuple[Order, ...]
    xor: LinearFactorizationModel

    @property
    def order_patterns(self) -> tuple[Order, ...]:
        return self.orders

    @property
    def description_bits(self) -> int:
        payload = {
            "entities": self.entity_lexicon,
            "actions": self.action_lexicon,
            "particles": self.particle_index,
            "orders": self.orders,
            "xor": self.xor.render(),
        }
        return len(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()) * 8

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        row = ContinuousJapaneseObservation.build(sentence, before, before)
        try:
            factor, coords = extract_factor(
                row, self.entity_lexicon, self.action_lexicon, transition=False
            )
        except ValueError:
            return None
        pmap = dict(self.particle_index)
        p0 = pmap.get(factor.first_particle)
        p1 = pmap.get(factor.second_particle)
        if factor.order not in self.orders or p0 is None or p1 is None:
            return None
        bits = dict(self.xor.template_bits)
        if bits[p0] == bits[p1]:
            return None
        direction = self.xor.effective_forward(factor.action, p0)
        if direction is None:
            return None
        source, destination = coords if direction else (coords[1], coords[0])
        state = list(before)
        state[destination] = before[source]
        return tuple(state)


@dataclass(frozen=True)
class LiteralBaseline:
    entity_lexicon: tuple[tuple[str, int], ...]
    action_lexicon: tuple[str, ...]
    table: tuple[tuple[str, str, str, Order, bool], ...]

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        row = ContinuousJapaneseObservation.build(sentence, before, before)
        try:
            factor, coords = extract_factor(
                row, self.entity_lexicon, self.action_lexicon, transition=False
            )
        except ValueError:
            return None
        lookup = {
            (a, p0, p1, order): value
            for a, p0, p1, order, value in self.table
        }
        direction = lookup.get((
            factor.action, factor.first_particle, factor.second_particle, factor.order
        ))
        if direction is None:
            return None
        source, destination = coords if direction else (coords[1], coords[0])
        state = list(before)
        state[destination] = before[source]
        return tuple(state)


def render(
    action: str, p0: str, p1: str, order: int,
    e0: str, e1: str, *, index: int, evaluation: bool = False,
) -> str:
    atoms = {"E0": e0 + p0, "E1": e1 + p1, "A": action}
    prefixes = ("", "今日は", "記録では", "その後")
    if evaluation:
        prefixes = ("念のため", "報告では", "あとで")
    return prefixes[index % len(prefixes)] + "".join(
        atoms[label] for label in ORDERS[order]
    ) + "。"


def build(
    spec: tuple[str, str, str, int], first: int, second: int, index: int,
    *, flip: bool = False, sentence: str | None = None, evaluation: bool = False,
) -> ContinuousJapaneseObservation:
    action, p0, p1, order = spec
    before = tuple(index * 100 + coordinate + 1 for coordinate in range(4))
    forward = ACTION_BITS[action] ^ PARTICLE_BITS[p0] ^ flip
    source, destination = (first, second) if forward else (second, first)
    after = list(before)
    after[destination] = before[source]
    return ContinuousJapaneseObservation.build(
        sentence or render(
            action, p0, p1, order, ENTITIES[first], ENTITIES[second],
            index=index, evaluation=evaluation,
        ),
        before,
        after,
    )


def participant_pair(group: int, repetition: int) -> tuple[int, int]:
    first = (group + repetition) % 4
    second = (group + 2 * repetition + 1) % 4
    return (first, (second + (second == first)) % 4)


def semantic_training_observations() -> tuple[ContinuousJapaneseObservation, ...]:
    return tuple(
        build(
            spec,
            *participant_pair(group, repetition),
            group * REPETITIONS + repetition,
            flip=repetition < FLIPS,
        )
        for group, spec in enumerate(TRAINING_SPECS)
        for repetition in range(REPETITIONS)
    )


def training_observations() -> tuple[ContinuousJapaneseObservation, ...]:
    noise = (
        build(TRAINING_SPECS[0], 0, 1, 10_000, sentence="今日はアキが渡す。"),
        build(
            TRAINING_SPECS[7], 2, 3, 10_001,
            sentence="アキを見ながら写すチカからダイへ。",
        ),
    )
    return (*semantic_training_observations(), *noise)


def heldout_specs() -> tuple[tuple[str, str, str, int], ...]:
    seen_ap = {(a, p0) for a, p0, _, _ in TRAINING_SPECS}
    seen_pairs = {(p0, p1) for _, p0, p1, _ in TRAINING_SPECS}
    seen_po = {(p0, order) for _, p0, _, order in TRAINING_SPECS}
    source = tuple(p for p, bit in PARTICLE_BITS.items() if not bit)
    destination = tuple(p for p, bit in PARTICLE_BITS.items() if bit)
    result: list[tuple[str, str, str, int]] = []
    for p0, bit in PARTICLE_BITS.items():
        for order in ORDERS:
            if (p0, order) in seen_po:
                continue
            options = source if bit else destination
            chosen = next(
                (a, p0, p1, order)
                for a in ("受ける", "写す", "移す")
                if (a, p0) not in seen_ap
                for p1 in options
                if (p0, p1) not in seen_pairs
            )
            result.append(chosen)
    return tuple(result)


def heldout_observations() -> tuple[ContinuousJapaneseObservation, ...]:
    result: list[ContinuousJapaneseObservation] = []
    for index, spec in enumerate(heldout_specs()):
        first, second = index % 4, (index + 2) % 4
        for e0, e1 in ((first, second), (second, first)):
            result.append(build(
                spec, e0, e1, 20_000 + index, evaluation=True
            ))
    return tuple(result)


def extract_factor(
    row: ContinuousJapaneseObservation,
    entity_lexicon: Sequence[tuple[str, int]],
    action_lexicon: Sequence[str],
    *,
    transition: bool = True,
) -> tuple[Factor, tuple[int, int]]:
    entities = entity_spans(row, entity_lexicon)
    if len(entities) != 2 or entities[0][2] == entities[1][2]:
        raise ValueError("need two distinct entities")
    entities = tuple(sorted(entities))
    blocked = tuple((start, end) for start, end, _, _ in entities)
    actions: list[tuple[int, int, str]] = []
    for action in action_lexicon:
        spans = non_overlapping_occurrences(row.text, action, blocked)
        if len(spans) > 1:
            raise ValueError("repeated action")
        if spans:
            actions.append((*spans[0], action))
    if len(actions) != 1:
        raise ValueError("need one action")
    astart, aend, action = actions[0]
    spans = tuple(sorted((
        (entities[0][0], entities[0][1], "E0"),
        (entities[1][0], entities[1][1], "E1"),
        (astart, aend, "A"),
    )))
    order: Order = tuple(label for _, _, label in spans)  # type: ignore[assignment]
    markers: dict[str, str] = {}
    for index, (_, end, label) in enumerate(spans):
        next_start = spans[index + 1][0] if index + 1 < len(spans) else len(row.text)
        gap = row.text[end:next_start]
        if label.startswith("E"):
            if not gap:
                raise ValueError("empty case marker")
            markers[label] = gap
        elif gap:
            raise ValueError("nonempty action gap")
    coords = (entities[0][3], entities[1][3])
    if not transition:
        return Factor(action, markers["E0"], markers["E1"], order, False), coords
    roles = infer_transition_roles(row)
    if (roles.source, roles.destination) == coords:
        forward = True
    elif (roles.source, roles.destination) == (coords[1], coords[0]):
        forward = False
    else:
        raise ValueError("transition not explained")
    return Factor(action, markers["E0"], markers["E1"], order, forward), coords


def fit_factors(factors: Iterable[Factor]) -> Fit:
    rows = tuple(factors)
    grouped: dict[tuple[str, str], Counter[bool]] = defaultdict(Counter)
    for row in rows:
        grouped[(row.action, row.first_particle)][row.forward] += 1
    labels: dict[tuple[str, str], bool] = {}
    errors = 0
    for key, counts in grouped.items():
        if counts[True] == counts[False]:
            raise NonIdentifiableLocalGrammarError("tied majority")
        labels[key] = counts[True] > counts[False]
        errors += min(counts.values())
    actions = tuple(sorted({a for a, _ in labels}))
    particles = tuple(sorted({
        particle for row in rows
        for particle in (row.first_particle, row.second_particle)
    }))
    ids = {particle: index for index, particle in enumerate(particles)}
    edges = tuple(
        LabeledSemanticEdge(action, ids[particle], label)
        for (action, particle), label in sorted(labels.items())
    )
    try:
        xor = induce_linear_factorization(
            edges, verbs=actions, template_positions=tuple(range(len(particles)))
        )
    except InconsistentSemanticsError as error:
        raise NonIdentifiableLocalGrammarError("contradictory cycle") from error
    if not xor.identifiable:
        raise NonIdentifiableLocalGrammarError("disconnected graph")
    bits = dict(xor.template_bits)
    if any(
        bits[ids[row.first_particle]] == bits[ids[row.second_particle]]
        for row in rows
    ):
        raise NonIdentifiableLocalGrammarError("same-role case pair")
    return Fit(
        tuple((particle, ids[particle]) for particle in particles),
        tuple(sorted({row.order for row in rows})),
        xor, errors, len(rows), 0,
    )


def fit_rows(
    rows: Iterable[ContinuousJapaneseObservation],
    entities: Sequence[tuple[str, int]],
    actions: Sequence[str],
) -> Fit:
    factors: list[Factor] = []
    skipped = 0
    for row in rows:
        try:
            factors.append(extract_factor(row, entities, actions)[0])
        except ValueError:
            skipped += 1
    fit = fit_factors(factors)
    return Fit(
        fit.particle_index, fit.orders, fit.xor, fit.errors, fit.rows, skipped
    )


def fit_literal(
    rows: Iterable[ContinuousJapaneseObservation],
    entities: Sequence[tuple[str, int]],
    actions: Sequence[str],
) -> LiteralBaseline:
    grouped: dict[tuple[str, str, str, Order], Counter[bool]] = defaultdict(Counter)
    for row in rows:
        factor, _ = extract_factor(row, entities, actions)
        grouped[(
            factor.action, factor.first_particle, factor.second_particle, factor.order
        )][factor.forward] += 1
    table = tuple(
        (*key, counts[True] > counts[False])
        for key, counts in sorted(grouped.items(), key=repr)
        if counts[True] != counts[False]
    )
    return LiteralBaseline(tuple(entities), tuple(actions), table)


def induce_local_case_grammar(
    rows: Iterable[ContinuousJapaneseObservation],
) -> tuple[LocalModel, LiteralBaseline, Fit]:
    rows = tuple(rows)
    entities, _ = induce_entity_grounding(rows)
    semantic = complete_semantic_rows(rows, entities)
    candidates = action_candidate_lexemes(semantic, entities)
    covers = exact_cover_action_lexicons(semantic, entities, candidates)
    valid: list[tuple[tuple[int, int], tuple[str, ...], Fit]] = []
    for actions in covers:
        try:
            fit = fit_rows(semantic, entities, actions)
        except NonIdentifiableLocalGrammarError:
            continue
        if fit.skipped:
            continue
        description = (
            sum(map(len, actions))
            + sum(len(p) for p, _ in fit.particle_index)
            + len(fit.orders)
            + len(fit.xor.verb_bits)
            + len(fit.xor.template_bits)
        )
        valid.append(((fit.errors, description), tuple(actions), fit))
    if not valid:
        raise NonIdentifiableLocalGrammarError("no valid action segmentation")
    best_score = min(score for score, _, _ in valid)
    best = [row for row in valid if row[0] == best_score]
    if len(best) != 1:
        raise NonIdentifiableLocalGrammarError("ambiguous action segmentation")
    _, actions, _ = best[0]
    fit = fit_rows(rows, entities, actions)
    fit = Fit(
        fit.particle_index, fit.orders, fit.xor, fit.errors, fit.rows, fit.skipped,
        len(candidates), len(covers), len(valid), len(best),
    )
    model = LocalModel(
        tuple(entities), actions, fit.particle_index, fit.orders, fit.xor
    )
    return model, fit_literal(semantic, entities, actions), fit


def score(model: object, rows: Iterable[ContinuousJapaneseObservation]) -> tuple[float, float]:
    rows = tuple(rows)
    answers = [model.predict(row.sentence, row.before) for row in rows]
    answered = sum(answer is not None for answer in answers)
    correct = sum(answer == row.after for answer, row in zip(answers, rows))
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def evaluate_model(
    model: LocalModel,
    rows: Iterable[ContinuousJapaneseObservation],
) -> tuple[float, float]:
    return score(model, rows)


def heldout_unseen_local_compositions(
) -> tuple[ContinuousJapaneseObservation, ...]:
    return heldout_observations()


def positionless_bound(rows: Iterable[ContinuousJapaneseObservation]) -> float:
    groups: dict[tuple[tuple[str, ...], State], Counter[State]] = defaultdict(Counter)
    rows = tuple(rows)
    for row in rows:
        groups[(tuple(sorted(row.text)), row.before)][row.after] += 1
    return sum(max(counts.values()) for counts in groups.values()) / len(rows)


def memorizer_coverage(
    train: Iterable[ContinuousJapaneseObservation],
    test: Iterable[ContinuousJapaneseObservation],
    model: LocalModel,
    fields: tuple[str, ...],
) -> float:
    def key(factor: Factor) -> tuple[object, ...]:
        values = {
            "action": factor.action,
            "p0": factor.first_particle,
            "p1": factor.second_particle,
            "order": factor.order,
        }
        return tuple(values[field] for field in fields)
    known = {
        key(extract_factor(row, model.entity_lexicon, model.action_lexicon)[0])
        for row in train
    }
    test = tuple(test)
    return sum(
        key(extract_factor(row, model.entity_lexicon, model.action_lexicon)[0]) in known
        for row in test
    ) / len(test)


def union_bound() -> float:
    gap = 0.5 - FLIPS / REPETITIONS
    return len(TRAINING_SPECS) * exp(-2 * REPETITIONS * gap * gap)


def tied_majority_is_rejected() -> bool:
    rows = (
        Factor("a", "p0", "p1", ORDERS[0], True),
        Factor("a", "p0", "p1", ORDERS[0], False),
    )
    try:
        fit_factors(rows)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def disconnected_graph_is_rejected() -> bool:
    rows = (
        Factor("a0", "p0", "p1", ORDERS[0], True),
        Factor("a1", "p2", "p3", ORDERS[0], False),
    )
    try:
        fit_factors(rows)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def contradictory_cycle_is_rejected() -> bool:
    rows = (
        Factor("a0", "p0", "p1", ORDERS[0], True),
        Factor("a0", "p1", "p0", ORDERS[0], False),
        Factor("a1", "p0", "p1", ORDERS[0], True),
        Factor("a1", "p1", "p0", ORDERS[0], True),
    )
    try:
        fit_factors(rows)
    except NonIdentifiableLocalGrammarError:
        return True
    return False


def same_polarity_pair_abstains(model: LocalModel) -> bool:
    row = build(("渡す", "が", "から", 0), 0, 1, 80_000)
    return model.predict(row.sentence, row.before) is None


def unknown_particle_abstains(model: LocalModel) -> bool:
    sentence = render("渡す", "側", "に", 0, "アキ", "ボブ", index=90_000)
    return model.predict(sentence, (1, 2, 3, 4)) is None


def literal_bits(templates: Iterable[tuple[str, str, str, Order]]) -> int:
    rows = sorted((a, p0, p1, list(order)) for a, p0, p1, order in set(templates))
    return len(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()) * 8


def run() -> dict[str, object]:
    train = training_observations()
    semantic = semantic_training_observations()
    test = heldout_observations()
    model, literal, fit = induce_local_case_grammar(train)
    accuracy, coverage = score(model, test)
    literal_accuracy, literal_coverage = score(literal, test)
    pmap = dict(model.particle_index)
    bits = dict(model.xor.template_bits)
    zeros = sum(not bit for bit in bits.values())
    ones = sum(bits.values())
    valid_pairs = 2 * zeros * ones
    expressible = len(model.action_lexicon) * valid_pairs * len(model.orders)
    observed_bits = literal_bits((
        (a, p0, p1, ORDERS[order]) for a, p0, p1, order in TRAINING_SPECS
    ))
    exhaustive_bits = literal_bits((
        (a, p0, p1, order)
        for a in model.action_lexicon
        for p0, i0 in model.particle_index
        for p1, i1 in model.particle_index
        if bits[i0] != bits[i1]
        for order in model.orders
    ))
    full_cov = memorizer_coverage(
        semantic, test, model, ("action", "p0", "p1", "order")
    )
    ap_cov = memorizer_coverage(semantic, test, model, ("action", "p0"))
    pair_cov = memorizer_coverage(semantic, test, model, ("p0", "p1"))
    po_cov = memorizer_coverage(semantic, test, model, ("p0", "order"))
    checks = {
        "continuous_entity_and_action_segmentation_is_unique": (
            len(model.entity_lexicon) == 4
            and len(model.action_lexicon) == 4
            and fit.best_action_models == 1
        ),
        "all_six_case_markers_are_induced": len(model.particle_index) == 6,
        "all_three_action_positions_are_induced": len(model.orders) == 3,
        "local_graph_is_connected": model.xor.identifiable,
        "case_pairs_have_opposite_polarity": all(
            bits[pmap[p0]] != bits[pmap[p1]]
            for _, p0, p1, _ in TRAINING_SPECS
        ),
        "bounded_noise_is_recovered": fit.errors == len(TRAINING_SPECS) * FLIPS,
        "finite_sample_bound_is_below_one_percent": union_bound() < 0.01,
        "two_incomplete_rows_are_skipped": fit.skipped == 2,
        "tied_majority_is_rejected": tied_majority_is_rejected(),
        "disconnected_graph_is_rejected": disconnected_graph_is_rejected(),
        "contradictory_cycle_is_rejected": contradictory_cycle_is_rejected(),
        "same_role_pair_abstains": same_polarity_pair_abstains(model),
        "unknown_particle_abstains": unknown_particle_abstains(model),
        "unseen_whole_forms_are_perfect": accuracy == coverage == 1.0,
        "literal_frame_baseline_has_zero_coverage": literal_coverage == 0.0,
        "full_tuple_memorizer_has_zero_coverage": full_cov == 0.0,
        "action_particle_memorizer_has_zero_coverage": ap_cov == 0.0,
        "particle_pair_memorizer_has_zero_coverage": pair_cov == 0.0,
        "particle_order_memorizer_has_zero_coverage": po_cov == 0.0,
        "positionless_character_bound_is_half": positionless_bound(test) == 0.5,
        "atomic_grammar_expands_nine_to_216_forms": expressible == 216,
        "atomic_payload_beats_exhaustive_enumeration": (
            model.description_bits < exhaustive_bits
        ),
        "sentences_have_no_whitespace": all(
            not any(character.isspace() for character in row.sentence)
            for row in (*train, *test)
        ),
    }
    return {
        "campaign": {
            "name": "phase18a3-local-case-grammar-c1",
            "literal_whole_frames_stored_in_final_model": False,
            "action_segmentation_selected_by_local_grammar": True,
            "public_benchmark_examples_used": 0,
        },
        "grammar": {
            "actions": len(model.action_lexicon),
            "particles": len(model.particle_index),
            "orders": len(model.orders),
            "observed_whole_forms": len(TRAINING_SPECS),
            "valid_directed_particle_pairs": valid_pairs,
            "expressible_atomic_cross_product_forms": expressible,
            "heldout_whole_forms": len(heldout_specs()),
            "action_candidates": fit.action_candidates,
            "action_exact_covers": fit.action_covers,
            "valid_action_models": fit.valid_action_models,
            "best_action_models": fit.best_action_models,
            "particle_bits": [
                [particle, bits[index]] for particle, index in model.particle_index
            ],
        },
        "evaluation": {
            "training_rows": len(train),
            "semantic_rows": len(semantic),
            "skipped_rows": fit.skipped,
            "heldout_specs": len(heldout_specs()),
            "heldout_reversal_rows": len(test),
            "accuracy": accuracy,
            "coverage": coverage,
            "literal_frame_accuracy": literal_accuracy,
            "literal_frame_coverage": literal_coverage,
            "full_tuple_memorizer_coverage": full_cov,
            "action_particle_memorizer_coverage": ap_cov,
            "particle_pair_memorizer_coverage": pair_cov,
            "particle_order_memorizer_coverage": po_cov,
            "positionless_character_upper_bound": positionless_bound(test),
        },
        "theory": {
            "edges": len(TRAINING_SPECS),
            "repetitions": REPETITIONS,
            "flips_per_edge": FLIPS,
            "flip_rate": FLIPS / REPETITIONS,
            "iid_hoeffding_union_bound": union_bound(),
            "condition": (
                "connected cycle-consistent action/first-marker XOR graph, "
                "opposite polarity for the second marker, and independently "
                "learned action-position atoms"
            ),
        },
        "resources": {
            "atomic_model_bits": model.description_bits,
            "observed_literal_bits": observed_bits,
            "exhaustive_literal_bits": exhaustive_bits,
            "source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "literal_frame_storage_removed": all(checks.values()),
            "unseen_local_recombination_demonstrated": all(checks.values()),
            "general_japanese_grammar_demonstrated": False,
            "high_school_intelligence_demonstrated": False,
        },
        "limitations": [
            "entity search is inherited from Phase 18a-2 and not globally co-optimized",
            "one nonempty marker must immediately follow each entity",
            "only prefix discourse, three action positions, and one copy event are supported",
            "inflection, passive, causative, negation, synonymy, ellipsis, and discourse reference are absent",
            "Python and its standard library are excluded substrate",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    grammar = payload["grammar"]
    evaluation = payload["evaluation"]
    theory = payload["theory"]
    resources = payload["resources"]
    lines = [
        "# Phase 18a-3 results: local Japanese case grammar", "",
        "The final model stores action bits, case-marker bits, and order atoms rather",
        "than complete Japanese case-frame strings.", "",
        "## Atomic grammar", "",
        f"- Actions / particles / orders: **{grammar['actions']} / {grammar['particles']} / {grammar['orders']}**",
        f"- Observed whole forms: **{grammar['observed_whole_forms']}**",
        f"- Expressible atomic cross product: **{grammar['expressible_atomic_cross_product_forms']}**",
        f"- Held-out whole forms: **{grammar['heldout_whole_forms']}**", "",
        "## Held-out transfer", "",
        f"- Training / semantic / skipped rows: **{evaluation['training_rows']} / {evaluation['semantic_rows']} / {evaluation['skipped_rows']}**",
        f"- Held-out forms / reversal rows: **{evaluation['heldout_specs']} / {evaluation['heldout_reversal_rows']}**",
        f"- Local grammar accuracy / coverage: **{100 * evaluation['accuracy']:.1f}% / {100 * evaluation['coverage']:.1f}%**",
        f"- Literal whole-frame baseline coverage: **{100 * evaluation['literal_frame_coverage']:.1f}%**",
        f"- Action+marker / marker-pair / marker+order memorizer coverage: **{100 * evaluation['action_particle_memorizer_coverage']:.1f}% / {100 * evaluation['particle_pair_memorizer_coverage']:.1f}% / {100 * evaluation['particle_order_memorizer_coverage']:.1f}%**",
        f"- Positionless character upper bound: **{100 * evaluation['positionless_character_upper_bound']:.1f}%**", "",
        "## Noise and resources", "",
        f"- Direction flip rate: **{100 * theory['flip_rate']:.1f}%**",
        f"- IID Hoeffding union bound: **{100 * theory['iid_hoeffding_union_bound']:.3f}%**",
        f"- Atomic model / observed literal / exhaustive literal: **{resources['atomic_model_bits']} / {resources['observed_literal_bits']} / {resources['exhaustive_literal_bits']} bits**",
        f"- Source: **{resources['source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and declared", "",
        "## Claim boundary", "",
        "This rejects literal whole-frame memorization on the declared cross product.",
        "It is still a controlled micro-grammar, not unrestricted Japanese or",
        "Japanese high-school-level intelligence.", "", "## Limitations", "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase18a3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = render_markdown(payload)
    (output / "phase18a3.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
