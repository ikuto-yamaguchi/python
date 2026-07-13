from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .phase18a4_voice_polarity_morphology import (
    ENTITIES,
    Observation,
    Signature,
    WholeSurfaceMemorizer,
    aggregate_surface_evidence,
    exact_family_clusterings,
    parse_surface,
    positionless_upper_bound,
)

State = tuple[int, ...]
Operator = tuple[str, str]

CLASS_PARADIGMS: dict[str, dict[Operator, str]] = {
    "ichidan": {
        ("active", "positive"): "る",
        ("active", "negative"): "ない",
        ("passive", "positive"): "られる",
        ("passive", "negative"): "られない",
        ("causative", "positive"): "させる",
        ("causative", "negative"): "させない",
    },
    "godan_s": {
        ("active", "positive"): "す",
        ("active", "negative"): "さない",
        ("passive", "positive"): "される",
        ("passive", "negative"): "されない",
        ("causative", "positive"): "させる",
        ("causative", "negative"): "させない",
    },
    "godan_r": {
        ("active", "positive"): "る",
        ("active", "negative"): "らない",
        ("passive", "positive"): "られる",
        ("passive", "negative"): "られない",
        ("causative", "positive"): "らせる",
        ("causative", "negative"): "らせない",
    },
}
CLASS_FAMILIES = {
    "ichidan": (("受け", False), ("集め", True), ("伝え", False)),
    "godan_s": (("渡", True), ("写", False), ("移", True)),
    "godan_r": (("送", False), ("取", True), ("配", False)),
}
SUPPORT_STEMS = frozenset(
    stem
    for rows in CLASS_FAMILIES.values()
    for stem, _ in rows[:2]
)
TARGET_STEMS = frozenset(rows[2][0] for rows in CLASS_FAMILIES.values())
STEM_CLASS = {
    stem: class_name
    for class_name, rows in CLASS_FAMILIES.items()
    for stem, _ in rows
}
BASE_BITS = {
    stem: base
    for rows in CLASS_FAMILIES.values()
    for stem, base in rows
}
OPERATORS: tuple[Operator, ...] = (
    ("active", "positive"),
    ("active", "negative"),
    ("passive", "positive"),
    ("passive", "negative"),
    ("causative", "positive"),
    ("causative", "negative"),
)
REPETITIONS = 9
CORRUPTIONS_PER_CELL = 1


class NonIdentifiableConjugationError(ValueError):
    pass


@dataclass(frozen=True)
class Paradigm:
    class_id: int
    suffixes: tuple[tuple[str, str, str], ...]

    def suffix_map(self) -> dict[Operator, str]:
        return {
            (voice, polarity): suffix
            for voice, polarity, suffix in self.suffixes
        }


@dataclass(frozen=True)
class LexicalFamily:
    stem: str
    class_id: int
    base_bit: bool


@dataclass(frozen=True)
class ClassFit:
    families: tuple[LexicalFamily, ...]
    paradigms: tuple[Paradigm, ...]
    support_families_per_class: tuple[tuple[int, int], ...]
    family_clusterings: int
    recovered_training_errors: int


@dataclass(frozen=True)
class ConjugationClassModel:
    families: tuple[LexicalFamily, ...]
    paradigms: tuple[Paradigm, ...]

    def family_map(self) -> dict[str, LexicalFamily]:
        return {row.stem: row for row in self.families}

    def paradigm_map(self) -> dict[int, dict[Operator, str]]:
        return {row.class_id: row.suffix_map() for row in self.paradigms}

    @property
    def description_bits(self) -> int:
        payload = {
            "f": [
                (row.stem, row.class_id, int(row.base_bit))
                for row in self.families
            ],
            "p": [
                (
                    row.class_id,
                    [suffix for _, _, suffix in row.suffixes],
                )
                for row in self.paradigms
            ],
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ) * 8

    def generate(self, stem: str, voice: str, polarity: str) -> str | None:
        family = self.family_map().get(stem)
        if family is None:
            return None
        suffix = self.paradigm_map()[family.class_id].get(
            (voice, polarity)
        )
        if suffix is None:
            return None
        return stem + suffix

    def decode(
        self, predicate: str
    ) -> tuple[LexicalFamily, str, str] | None:
        matches: list[tuple[LexicalFamily, str, str]] = []
        paradigms = self.paradigm_map()
        for family in self.families:
            if not predicate.startswith(family.stem):
                continue
            suffix = predicate[len(family.stem) :]
            for (voice, polarity), expected in paradigms[
                family.class_id
            ].items():
                if suffix == expected:
                    matches.append((family, voice, polarity))
        return matches[0] if len(matches) == 1 else None

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        try:
            parsed = parse_surface(sentence)
        except ValueError:
            return None
        decoded = self.decode(parsed.predicate)
        if decoded is None:
            return None
        family, voice, polarity = decoded
        arity = 3 if voice == "causative" else 2
        if len(parsed.participants) != arity:
            return None
        before_row = tuple(before)
        if polarity == "negative":
            return before_row
        base = family.base_bit
        if voice == "active":
            positions = (0, 1) if base else (1, 0)
        elif voice == "passive":
            positions = (1, 0) if base else (0, 1)
        else:
            positions = (1, 2) if base else (2, 1)
        source, destination = (
            parsed.participants[index] for index in positions
        )
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


@dataclass(frozen=True)
class GlobalSuffixAnalyzer:
    family_bits: tuple[tuple[str, bool], ...]
    suffix_operators: tuple[tuple[str, str, str], ...]

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        try:
            parsed = parse_surface(sentence)
        except ValueError:
            return None
        family_matches = [
            row
            for row in self.family_bits
            if parsed.predicate.startswith(row[0])
        ]
        if len(family_matches) != 1:
            return None
        stem, base = family_matches[0]
        suffix = parsed.predicate[len(stem) :]
        operators = [
            (voice, polarity)
            for known, voice, polarity in self.suffix_operators
            if known == suffix
        ]
        if len(set(operators)) != 1:
            return None
        voice, polarity = operators[0]
        if polarity == "negative":
            return tuple(before)
        expected = 3 if voice == "causative" else 2
        if len(parsed.participants) != expected:
            return None
        if voice == "active":
            positions = (0, 1) if base else (1, 0)
        elif voice == "passive":
            positions = (1, 0) if base else (0, 1)
        else:
            positions = (1, 2) if base else (2, 1)
        source, destination = (
            parsed.participants[index] for index in positions
        )
        after = list(before)
        after[destination] = before[source]
        return tuple(after)


def surface_form(stem: str, voice: str, polarity: str) -> str:
    return stem + CLASS_PARADIGMS[STEM_CLASS[stem]][(voice, polarity)]


def render_sentence(
    stem: str,
    voice: str,
    polarity: str,
    actor: str,
    target: str,
    causer: str,
    *,
    index: int,
    evaluation: bool = False,
    predicate_override: str | None = None,
) -> str:
    predicate = predicate_override or surface_form(stem, voice, polarity)
    if voice == "active":
        core = actor + "が" + target + "に" + predicate
    elif voice == "passive":
        core = target + "が" + actor + "に" + predicate
    else:
        core = causer + "が" + actor + "に" + target + "へ" + predicate
    prefixes = ("今日は", "記録では", "その後", "静かに")
    if evaluation:
        prefixes = ("念のため", "報告では", "あとで")
    return prefixes[index % len(prefixes)] + core + "。"


def build_observation(
    stem: str,
    voice: str,
    polarity: str,
    actor: int,
    target: int,
    causer: int,
    *,
    index: int,
    corrupt: bool = False,
    evaluation: bool = False,
    predicate_override: str | None = None,
) -> Observation:
    before = tuple(
        index * 100 + coordinate + 1
        for coordinate in range(len(ENTITIES))
    )
    after = list(before)
    if polarity == "positive":
        source, destination = (
            (actor, target) if BASE_BITS[stem] else (target, actor)
        )
        if corrupt:
            source, destination = destination, source
        after[destination] = before[source]
    elif corrupt:
        after[target] = before[actor]
    sentence = render_sentence(
        stem,
        voice,
        polarity,
        ENTITIES[actor],
        ENTITIES[target],
        ENTITIES[causer],
        index=index,
        evaluation=evaluation,
        predicate_override=predicate_override,
    )
    return Observation(sentence, before, tuple(after))


def participants(cell_index: int, repetition: int) -> tuple[int, int, int]:
    actor = (cell_index + repetition) % len(ENTITIES)
    target = (cell_index + 2 * repetition + 1) % len(ENTITIES)
    if actor == target:
        target = (target + 1) % len(ENTITIES)
    causer = (cell_index + 3 * repetition + 2) % len(ENTITIES)
    while causer in (actor, target):
        causer = (causer + 1) % len(ENTITIES)
    return actor, target, causer


def training_cells() -> tuple[tuple[str, str, str], ...]:
    cells: list[tuple[str, str, str]] = []
    for rows in CLASS_FAMILIES.values():
        for stem, _ in rows[:2]:
            cells.extend(
                (stem, voice, polarity)
                for voice, polarity in OPERATORS
            )
        target = rows[2][0]
        cells.extend(
            (
                (target, "active", "positive"),
                (target, "active", "negative"),
            )
        )
    return tuple(cells)


def training_observations() -> tuple[Observation, ...]:
    result: list[Observation] = []
    for cell_index, (stem, voice, polarity) in enumerate(training_cells()):
        for repetition in range(REPETITIONS):
            actor, target, causer = participants(cell_index, repetition)
            result.append(
                build_observation(
                    stem,
                    voice,
                    polarity,
                    actor,
                    target,
                    causer,
                    index=cell_index * REPETITIONS + repetition,
                    corrupt=repetition < CORRUPTIONS_PER_CELL,
                )
            )
    return tuple(result)


def target_heldout_cells() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (stem, voice, polarity)
        for stem in sorted(TARGET_STEMS)
        for voice, polarity in OPERATORS
        if voice != "active"
    )


def heldout_observations() -> tuple[Observation, ...]:
    rows: list[Observation] = []
    for cell_index, (stem, voice, polarity) in enumerate(
        target_heldout_cells()
    ):
        actor = cell_index % len(ENTITIES)
        target = (cell_index + 1) % len(ENTITIES)
        causer = (cell_index + 2) % len(ENTITIES)
        while causer in (actor, target):
            causer = (causer + 1) % len(ENTITIES)
        for swap in (False, True):
            a, t = ((target, actor) if swap else (actor, target))
            rows.append(
                build_observation(
                    stem,
                    voice,
                    polarity,
                    a,
                    t,
                    causer,
                    index=30_000 + cell_index,
                    evaluation=True,
                )
            )
    return tuple(rows)


def label_complete_paradigm(
    mapping: Mapping[str, Signature],
) -> dict[Operator, str]:
    positives = [
        (suffix, signature)
        for suffix, signature in mapping.items()
        if not signature.noop
    ]
    negatives = [
        (suffix, signature)
        for suffix, signature in mapping.items()
        if signature.noop
    ]
    if len(positives) != 3 or len(negatives) != 3:
        raise NonIdentifiableConjugationError(
            "support family lacks a complete six-cell paradigm"
        )
    causative_positive = [
        row for row in positives if row[1].arity == 3
    ]
    causative_negative = [
        row for row in negatives if row[1].arity == 3
    ]
    binary_positive = [row for row in positives if row[1].arity == 2]
    binary_negative = [row for row in negatives if row[1].arity == 2]
    if not (
        len(causative_positive) == len(causative_negative) == 1
        and len(binary_positive) == len(binary_negative) == 2
    ):
        raise NonIdentifiableConjugationError(
            "voice arities do not identify one causative paradigm"
        )
    active_positive = min(
        binary_positive, key=lambda row: (len(row[0]), row[0])
    )
    if (
        sum(
            len(row[0]) == len(active_positive[0])
            for row in binary_positive
        )
        != 1
    ):
        raise NonIdentifiableConjugationError(
            "active positive anchor is not uniquely minimal"
        )
    passive_positive = next(
        row for row in binary_positive if row != active_positive
    )
    active_negative = min(
        binary_negative, key=lambda row: (len(row[0]), row[0])
    )
    if (
        sum(
            len(row[0]) == len(active_negative[0])
            for row in binary_negative
        )
        != 1
    ):
        raise NonIdentifiableConjugationError(
            "active negative anchor is not uniquely minimal"
        )
    passive_negative = next(
        row for row in binary_negative if row != active_negative
    )
    if passive_positive[1].forward == active_positive[1].forward:
        raise NonIdentifiableConjugationError(
            "passive positive does not reverse the surface relation"
        )
    if causative_positive[0][1].forward != active_positive[1].forward:
        raise NonIdentifiableConjugationError(
            "causative positive disagrees with the base event"
        )
    return {
        ("active", "positive"): active_positive[0],
        ("active", "negative"): active_negative[0],
        ("passive", "positive"): passive_positive[0],
        ("passive", "negative"): passive_negative[0],
        ("causative", "positive"): causative_positive[0][0],
        ("causative", "negative"): causative_negative[0][0],
    }


def induce_conjugation_classes(
    observations: Iterable[Observation],
) -> tuple[
    ConjugationClassModel,
    ClassFit,
    WholeSurfaceMemorizer,
    GlobalSuffixAnalyzer,
]:
    evidence, recovered_errors = aggregate_surface_evidence(observations)
    clusterings = exact_family_clusterings(tuple(evidence))
    candidates: list[
        tuple[
            tuple[int, int],
            ConjugationClassModel,
            tuple[Paradigm, ...],
            tuple[tuple[int, int], ...],
        ]
    ] = []
    for clustering in clusterings:
        suffix_maps: dict[str, dict[str, Signature]] = {}
        for stem, surfaces in clustering:
            mapping = {
                surface[len(stem) :]: evidence[surface]
                for surface in surfaces
            }
            if not all(mapping) or len(mapping) != len(surfaces):
                break
            suffix_maps[stem] = mapping
        else:
            complete: dict[str, dict[Operator, str]] = {}
            anchors: dict[str, tuple[str, str, bool]] = {}
            valid = True
            for stem, mapping in suffix_maps.items():
                if len(mapping) == 6:
                    try:
                        paradigm = label_complete_paradigm(mapping)
                    except NonIdentifiableConjugationError:
                        valid = False
                        break
                    complete[stem] = paradigm
                    active_signature = mapping[
                        paradigm[("active", "positive")]
                    ]
                    anchors[stem] = (
                        paradigm[("active", "positive")],
                        paradigm[("active", "negative")],
                        bool(active_signature.forward),
                    )
                elif len(mapping) == 2:
                    positive = [
                        row
                        for row in mapping.items()
                        if not row[1].noop and row[1].arity == 2
                    ]
                    negative = [
                        row
                        for row in mapping.items()
                        if row[1].noop and row[1].arity == 2
                    ]
                    if len(positive) != 1 or len(negative) != 1:
                        valid = False
                        break
                    anchors[stem] = (
                        positive[0][0],
                        negative[0][0],
                        bool(positive[0][1].forward),
                    )
                else:
                    valid = False
                    break
            if not valid:
                continue

            paradigm_groups: dict[
                tuple[tuple[str, str, str], ...], list[str]
            ] = defaultdict(list)
            for stem, paradigm in complete.items():
                key = tuple(
                    (
                        voice,
                        polarity,
                        paradigm[(voice, polarity)],
                    )
                    for voice, polarity in OPERATORS
                )
                paradigm_groups[key].append(stem)
            if len(paradigm_groups) != 3 or any(
                len(stems) < 2 for stems in paradigm_groups.values()
            ):
                continue
            keys = tuple(sorted(paradigm_groups))
            class_ids = {key: index for index, key in enumerate(keys)}
            anchor_to_class: dict[tuple[str, str], list[int]] = defaultdict(
                list
            )
            paradigms: list[Paradigm] = []
            supports: list[tuple[int, int]] = []
            for key in keys:
                class_id = class_ids[key]
                paradigms.append(Paradigm(class_id, key))
                suffix_map = {
                    (voice, polarity): suffix
                    for voice, polarity, suffix in key
                }
                anchor_to_class[
                    (
                        suffix_map[("active", "positive")],
                        suffix_map[("active", "negative")],
                    )
                ].append(class_id)
                supports.append((class_id, len(paradigm_groups[key])))
            families: list[LexicalFamily] = []
            for stem, (
                positive_suffix,
                negative_suffix,
                base,
            ) in sorted(anchors.items()):
                matches = anchor_to_class.get(
                    (positive_suffix, negative_suffix), []
                )
                if len(matches) != 1:
                    valid = False
                    break
                families.append(LexicalFamily(stem, matches[0], base))
            if not valid:
                continue
            model = ConjugationClassModel(
                tuple(families), tuple(paradigms)
            )
            description = sum(
                len(row.stem) + 2 for row in families
            ) + sum(
                len(suffix)
                for paradigm in paradigms
                for _, _, suffix in paradigm.suffixes
            )
            candidates.append(
                (
                    (len(paradigms), description),
                    model,
                    tuple(paradigms),
                    tuple(supports),
                )
            )
    if not candidates:
        raise NonIdentifiableConjugationError(
            "no three-class allomorphy model survives"
        )
    best_score = min(row[0] for row in candidates)
    best = [row for row in candidates if row[0] == best_score]
    behavior = {}
    for row in best:
        model = row[1]
        key = tuple(
            (
                stem,
                voice,
                polarity,
                model.generate(stem, voice, polarity),
            )
            for stem in sorted(model.family_map())
            for voice, polarity in OPERATORS
        )
        behavior[key] = row
    if len(behavior) != 1:
        raise NonIdentifiableConjugationError(
            f"class induction has {len(behavior)} behavioral optima"
        )
    _, model, paradigms, supports = next(iter(behavior.values()))
    fit = ClassFit(
        model.families,
        paradigms,
        supports,
        len(clusterings),
        recovered_errors,
    )
    memorizer = WholeSurfaceMemorizer(tuple(sorted(evidence.items())))
    suffix_ops: dict[str, set[Operator]] = defaultdict(set)
    for paradigm in paradigms:
        for voice, polarity, suffix in paradigm.suffixes:
            suffix_ops[suffix].add((voice, polarity))
    global_rows = tuple(
        (
            suffix,
            next(iter(operators))[0],
            next(iter(operators))[1],
        )
        for suffix, operators in sorted(suffix_ops.items())
        if len(operators) == 1
    )
    global_model = GlobalSuffixAnalyzer(
        tuple((row.stem, row.base_bit) for row in model.families),
        global_rows,
    )
    return model, fit, memorizer, global_model


def score(
    model: object, rows: Iterable[Observation]
) -> tuple[float, float]:
    rows = tuple(rows)
    answers = [model.predict(row.sentence, row.before) for row in rows]
    answered = sum(answer is not None for answer in answers)
    correct = sum(
        answer == row.after for answer, row in zip(answers, rows)
    )
    return correct / len(rows), answered / len(rows)


def generation_accuracy(model: ConjugationClassModel) -> float:
    cells = target_heldout_cells()
    return sum(
        model.generate(stem, voice, polarity)
        == surface_form(stem, voice, polarity)
        for stem, voice, polarity in cells
    ) / len(cells)


def class_agnostic_generation_accuracy(
    model: ConjugationClassModel,
) -> float:
    counts: dict[Operator, Counter[str]] = defaultdict(Counter)
    for paradigm in model.paradigms:
        for voice, polarity, suffix in paradigm.suffixes:
            if voice != "active":
                counts[(voice, polarity)][suffix] += 1
    selected = {
        operator: counter.most_common(1)[0][0]
        for operator, counter in counts.items()
    }
    cells = target_heldout_cells()
    return sum(
        stem + selected[(voice, polarity)]
        == surface_form(stem, voice, polarity)
        for stem, voice, polarity in cells
    ) / len(cells)


def wrong_class_decoys(
    model: ConjugationClassModel,
) -> tuple[Observation, ...]:
    rows: list[Observation] = []
    paradigms = model.paradigm_map()
    family_map = model.family_map()
    class_ids = sorted(paradigms)
    for cell_index, (stem, voice, polarity) in enumerate(
        target_heldout_cells()
    ):
        family = family_map[stem]
        correct = paradigms[family.class_id][(voice, polarity)]
        alternatives = sorted(
            {
                paradigms[class_id][(voice, polarity)]
                for class_id in class_ids
                if paradigms[class_id][(voice, polarity)] != correct
            }
        )
        if not alternatives:
            continue
        wrong_predicate = stem + alternatives[0]
        actor = cell_index % len(ENTITIES)
        target = (cell_index + 1) % len(ENTITIES)
        causer = (cell_index + 2) % len(ENTITIES)
        while causer in (actor, target):
            causer = (causer + 1) % len(ENTITIES)
        rows.append(
            build_observation(
                stem,
                voice,
                polarity,
                actor,
                target,
                causer,
                index=60_000 + cell_index,
                evaluation=True,
                predicate_override=wrong_predicate,
            )
        )
    return tuple(rows)


def target_negative_anchor_is_necessary() -> bool:
    rows = tuple(
        row
        for row in training_observations()
        if not any(
            row.text.endswith(
                surface_form(stem, "active", "negative")
            )
            for stem in TARGET_STEMS
        )
    )
    try:
        induce_conjugation_classes(rows)
    except (NonIdentifiableConjugationError, ValueError):
        return True
    return False


def recurring_support_is_necessary() -> bool:
    removed = {rows[1][0] for rows in CLASS_FAMILIES.values()}
    rows = tuple(
        row
        for row in training_observations()
        if not any(
            row.text.endswith(surface_form(stem, voice, polarity))
            for stem in removed
            for voice, polarity in OPERATORS
        )
    )
    try:
        induce_conjugation_classes(rows)
    except (NonIdentifiableConjugationError, ValueError):
        return True
    return False


def unknown_anchor_abstains(model: ConjugationClassModel) -> bool:
    return model.generate("調べ", "passive", "positive") is None


def literal_bits(forms: Iterable[str]) -> int:
    return len(
        json.dumps(
            sorted(set(forms)), ensure_ascii=False, separators=(",", ":")
        ).encode()
    ) * 8


def run() -> dict[str, object]:
    train = training_observations()
    heldout = heldout_observations()
    model, fit, memorizer, global_model = induce_conjugation_classes(
        train
    )
    accuracy, coverage = score(model, heldout)
    memorizer_accuracy, memorizer_coverage = score(memorizer, heldout)
    global_accuracy, global_coverage = score(global_model, heldout)
    decoys = wrong_class_decoys(model)
    model_decoy_acceptance = score(model, decoys)[1] if decoys else 0.0
    global_decoy_acceptance = (
        score(global_model, decoys)[1] if decoys else 0.0
    )
    generated = generation_accuracy(model)
    global_generated = class_agnostic_generation_accuracy(model)
    all_forms = [
        surface_form(stem, voice, polarity)
        for stem in BASE_BITS
        for voice, polarity in OPERATORS
    ]
    observed_forms = [
        parse_surface(row.sentence).predicate for row in train
    ]
    positive_rows = tuple(
        row
        for row in heldout
        if parse_surface(row.sentence).predicate.endswith(("る", "す"))
        and row.before != row.after
    )
    checks = {
        "nine_lexical_families_are_induced": len(model.families) == 9,
        "three_recurring_conjugation_classes_are_induced": (
            len(model.paradigms) == 3
        ),
        "each_class_has_two_support_families": all(
            count == 2 for _, count in fit.support_families_per_class
        ),
        "target_heldout_interpretation_is_perfect": (
            accuracy == coverage == 1.0
        ),
        "target_heldout_generation_is_perfect": generated == 1.0,
        "whole_surface_memorizer_has_zero_coverage": (
            memorizer_coverage == 0.0
        ),
        "single_global_suffix_generator_is_insufficient": (
            global_generated < 1.0
        ),
        "class_conditioning_rejects_wrong_class_allomorphs": (
            model_decoy_acceptance == 0.0
        ),
        "global_suffix_analyzer_false_accepts_decoys": (
            global_decoy_acceptance > 0.0
        ),
        "bounded_transition_noise_is_recovered": (
            fit.recovered_training_errors
            == len(training_cells()) * CORRUPTIONS_PER_CELL
        ),
        "target_negative_anchor_is_necessary": (
            target_negative_anchor_is_necessary()
        ),
        "recurring_support_is_necessary": recurring_support_is_necessary(),
        "unknown_anchor_abstains": unknown_anchor_abstains(model),
        "positive_role_swap_character_bound_is_half": (
            positionless_upper_bound(positive_rows) == 0.5
        ),
    }
    return {
        "campaign": {
            "name": "phase18a5-conjugation-class-allomorphy-c1",
            "classes": 3,
            "families": 9,
            "support_families_per_class": 2,
            "target_families_per_class": 1,
            "public_benchmark_examples_used": 0,
        },
        "induction": {
            "best_family_clusterings": fit.family_clusterings,
            "learned_families": [
                [row.stem, row.class_id, row.base_bit]
                for row in model.families
            ],
            "learned_paradigms": [
                {
                    "class_id": row.class_id,
                    "suffixes": [list(item) for item in row.suffixes],
                }
                for row in model.paradigms
            ],
            "support_counts": [
                list(row) for row in fit.support_families_per_class
            ],
            "recovered_training_errors": fit.recovered_training_errors,
        },
        "evaluation": {
            "training_cells": len(training_cells()),
            "training_observations": len(train),
            "heldout_cells": len(target_heldout_cells()),
            "heldout_rows": len(heldout),
            "interpretation_accuracy": accuracy,
            "interpretation_coverage": coverage,
            "generation_accuracy": generated,
            "whole_surface_memorizer_accuracy": memorizer_accuracy,
            "whole_surface_memorizer_coverage": memorizer_coverage,
            "global_suffix_interpretation_accuracy": global_accuracy,
            "global_suffix_interpretation_coverage": global_coverage,
            "class_agnostic_generation_accuracy": global_generated,
            "wrong_class_decoy_rows": len(decoys),
            "class_model_decoy_acceptance": model_decoy_acceptance,
            "global_suffix_decoy_acceptance": global_decoy_acceptance,
            "positive_character_bag_upper_bound": (
                positionless_upper_bound(positive_rows)
            ),
        },
        "resource_accounting": {
            "serialized_class_model_bits": model.description_bits,
            "observed_42_form_table_bits": literal_bits(observed_forms),
            "exhaustive_54_form_table_bits": literal_bits(all_forms),
            "phase18a5_source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_and_standard_library_included": False,
        },
        "theorem_checks": checks,
        "all_theorem_checks_pass": all(checks.values()),
        "claim_boundary": {
            "three_class_allomorphy_and_bidirectional_transfer_demonstrated": (
                all(checks.values())
            ),
            "unrestricted_japanese_conjugation_demonstrated": False,
            "general_japanese_understanding_demonstrated": False,
            "japanese_high_school_intelligence_demonstrated": False,
        },
        "limitations": [
            "family grouping still relies on recurring initial substrings",
            "only three regular conjugation classes are represented",
            "irregular verbs, phonological alternation, tense, aspect, and politeness are absent",
            "semantic evaluation remains one controlled copy-event ontology",
            "target families expose active positive and active negative anchors before held-out evaluation",
            "Python and its standard library remain excluded substrate",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    campaign = payload["campaign"]
    evaluation = payload["evaluation"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 18a-5 results: conjugation classes and allomorphy",
        "",
        "Phase 18a-5 induces three recurring conjugation paradigms from six support",
        "families, classifies three sparse target families from active anchors, and",
        "tests held-out analysis plus generation.",
        "",
        "## Frozen campaign",
        "",
        f"- Classes / families: **{campaign['classes']} / {campaign['families']}**",
        f"- Training cells / observations: **{evaluation['training_cells']} / {evaluation['training_observations']}**",
        f"- Held-out target cells / rows: **{evaluation['heldout_cells']} / {evaluation['heldout_rows']}**",
        "",
        "## Results",
        "",
        f"- Interpretation accuracy / coverage: **{100 * evaluation['interpretation_accuracy']:.1f}% / {100 * evaluation['interpretation_coverage']:.1f}%**",
        f"- Exact inflection generation: **{100 * evaluation['generation_accuracy']:.1f}%**",
        f"- Whole-surface memorizer coverage: **{100 * evaluation['whole_surface_memorizer_coverage']:.1f}%**",
        f"- Class-agnostic generation: **{100 * evaluation['class_agnostic_generation_accuracy']:.1f}%**",
        f"- Wrong-class allomorph acceptance, class model / global suffix: **{100 * evaluation['class_model_decoy_acceptance']:.1f}% / {100 * evaluation['global_suffix_decoy_acceptance']:.1f}%**",
        f"- Positive role-swap character-bag upper bound: **{100 * evaluation['positive_character_bag_upper_bound']:.1f}%**",
        "",
        "## Resource accounting",
        "",
        f"- Serialized class model: **{resources['serialized_class_model_bits']} bits**",
        f"- Observed 42-form table: **{resources['observed_42_form_table_bits']} bits**",
        f"- Exhaustive 54-form table: **{resources['exhaustive_54_form_table_bits']} bits**",
        f"- Phase 18a-5 source: **{resources['phase18a5_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and declared",
        "",
        "## Claim boundary",
        "",
        "This is evidence for three-class allomorphy and bidirectional transfer in a",
        "controlled Japanese microgrammar. It is not unrestricted conjugation, reading",
        "comprehension, or Japanese high-school-level intelligence.",
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
    (output / "phase18a5.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a5.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
