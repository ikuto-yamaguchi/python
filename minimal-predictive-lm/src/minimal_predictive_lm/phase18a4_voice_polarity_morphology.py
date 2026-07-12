from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import unicodedata

State = tuple[int, ...]

ENTITIES = ("アキ", "ボブ", "チカ", "ダイ", "エリ")
INHERITED_PARTICLES = ("が", "に", "へ")
STEMS = ("受け", "集め", "伝え", "分け", "固め", "求め")
BASE_BITS = {
    "受け": True,
    "集め": False,
    "伝え": True,
    "分け": False,
    "固め": True,
    "求め": False,
}
VOICE_MORPHS = {"active": "", "passive": "られ", "causative": "させ"}
POLARITY_MORPHS = {"positive": "る", "negative": "ない"}
TRAINING_NONACTIVE = {
    "受け": "passive",
    "集め": "causative",
    "伝え": "passive",
    "分け": "causative",
    "固め": "passive",
    "求め": "causative",
}
REPETITIONS = 11
CORRUPTIONS_PER_CELL = 1
_PUNCTUATION = "。、，,！？!?「」『』（）()【】"


class NonIdentifiableMorphologyError(ValueError):
    pass


@dataclass(frozen=True)
class Observation:
    sentence: str
    before: State
    after: State

    @property
    def text(self) -> str:
        return normalize(self.sentence)


@dataclass(frozen=True)
class ParsedSurface:
    predicate: str
    participants: tuple[int, ...]
    markers: tuple[str, ...]


@dataclass(frozen=True)
class Signature:
    arity: int
    forward: bool | None
    noop: bool


@dataclass(frozen=True)
class Family:
    stem: str
    surfaces: tuple[str, ...]
    base_bit: bool


@dataclass(frozen=True)
class MorphologyFit:
    families: tuple[Family, ...]
    active_prefix: str
    passive_prefix: str
    causative_prefix: str
    positive_ending: str
    negative_ending: str
    unique_factorizations: int
    family_clusterings: int
    recovered_training_errors: int


@dataclass(frozen=True)
class FactorizedMorphologyModel:
    families: tuple[Family, ...]
    active_prefix: str
    passive_prefix: str
    causative_prefix: str
    positive_ending: str
    negative_ending: str

    @property
    def description_bits(self) -> int:
        payload = {
            "families": [(row.stem, row.base_bit) for row in self.families],
            "voices": [self.active_prefix, self.passive_prefix, self.causative_prefix],
            "polarities": [self.positive_ending, self.negative_ending],
            "particles": list(INHERITED_PARTICLES),
            "entities": list(ENTITIES),
        }
        return len(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8

    def family_map(self) -> dict[str, bool]:
        return {row.stem: row.base_bit for row in self.families}

    def decode_predicate(self, predicate: str) -> tuple[str, str, str] | None:
        candidates: list[tuple[str, str, str]] = []
        voices = (
            ("active", self.active_prefix),
            ("passive", self.passive_prefix),
            ("causative", self.causative_prefix),
        )
        polarities = (
            ("positive", self.positive_ending),
            ("negative", self.negative_ending),
        )
        for stem in self.family_map():
            if not predicate.startswith(stem):
                continue
            residual = predicate[len(stem) :]
            for voice, voice_prefix in voices:
                for polarity, ending in polarities:
                    if residual == voice_prefix + ending:
                        candidates.append((stem, voice, polarity))
        if len(candidates) != 1:
            return None
        return candidates[0]

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        before_row = tuple(int(value) for value in before)
        try:
            parsed = parse_surface(sentence)
        except ValueError:
            return None
        decoded = self.decode_predicate(parsed.predicate)
        if decoded is None:
            return None
        stem, voice, polarity = decoded
        expected_arity = 3 if voice == "causative" else 2
        if len(parsed.participants) != expected_arity:
            return None
        if polarity == "negative":
            return before_row
        base = self.family_map()[stem]
        if voice == "active":
            source_pos, destination_pos = ((0, 1) if base else (1, 0))
        elif voice == "passive":
            source_pos, destination_pos = ((1, 0) if base else (0, 1))
        else:
            source_pos, destination_pos = ((1, 2) if base else (2, 1))
        source = parsed.participants[source_pos]
        destination = parsed.participants[destination_pos]
        if max(source, destination) >= len(before_row):
            return None
        after = list(before_row)
        after[destination] = before_row[source]
        return tuple(after)


@dataclass(frozen=True)
class WholeSurfaceMemorizer:
    table: tuple[tuple[str, Signature], ...]

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        try:
            parsed = parse_surface(sentence)
        except ValueError:
            return None
        signature = dict(self.table).get(parsed.predicate)
        if signature is None:
            return None
        return apply_signature(signature, parsed.participants, tuple(before))


@dataclass(frozen=True)
class WholeSuffixModel:
    family_bits: tuple[tuple[str, bool], ...]
    suffix_operators: tuple[tuple[str, str, str], ...]

    def predict(self, sentence: str, before: Sequence[int]) -> State | None:
        try:
            parsed = parse_surface(sentence)
        except ValueError:
            return None
        matches: list[tuple[str, bool, str, str]] = []
        for stem, base in self.family_bits:
            if not parsed.predicate.startswith(stem):
                continue
            suffix = parsed.predicate[len(stem) :]
            for known_suffix, voice, polarity in self.suffix_operators:
                if suffix == known_suffix:
                    matches.append((stem, base, voice, polarity))
        if len(matches) != 1:
            return None
        _, base, voice, polarity = matches[0]
        if polarity == "negative":
            return tuple(before)
        expected_arity = 3 if voice == "causative" else 2
        if len(parsed.participants) != expected_arity:
            return None
        if voice == "active":
            positions = (0, 1) if base else (1, 0)
        elif voice == "passive":
            positions = (1, 0) if base else (0, 1)
        else:
            positions = (1, 2) if base else (2, 1)
        source, destination = (parsed.participants[index] for index in positions)
        after = list(before)
        after[destination] = before[source]
        return tuple(after)


def normalize(sentence: str) -> str:
    text = unicodedata.normalize("NFKC", sentence)
    for mark in _PUNCTUATION:
        text = text.replace(mark, "")
    return "".join(text.split())


def surface_form(stem: str, voice: str, polarity: str) -> str:
    return stem + VOICE_MORPHS[voice] + POLARITY_MORPHS[polarity]


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
) -> str:
    predicate = surface_form(stem, voice, polarity)
    if voice == "active":
        core = actor + "が" + target + "に" + predicate
    elif voice == "passive":
        core = target + "が" + actor + "に" + predicate
    elif voice == "causative":
        core = causer + "が" + actor + "に" + target + "へ" + predicate
    else:
        raise ValueError(f"unknown voice: {voice}")
    prefixes = ("今日は", "記録では", "その後", "静かに")
    if evaluation:
        prefixes = ("念のため", "報告では", "あとで")
    return prefixes[index % len(prefixes)] + core + "。"


def build_observation(
    stem: str,
    voice: str,
    polarity: str,
    actor_coordinate: int,
    target_coordinate: int,
    causer_coordinate: int,
    *,
    index: int,
    corrupt: bool = False,
    evaluation: bool = False,
) -> Observation:
    before = tuple(
        index * 100 + coordinate + 1 for coordinate in range(len(ENTITIES))
    )
    after = list(before)
    base = BASE_BITS[stem]
    if polarity == "positive":
        source, destination = (
            (actor_coordinate, target_coordinate)
            if base
            else (target_coordinate, actor_coordinate)
        )
        if corrupt:
            source, destination = destination, source
        after[destination] = before[source]
    elif corrupt:
        after[target_coordinate] = before[actor_coordinate]
    sentence = render_sentence(
        stem,
        voice,
        polarity,
        ENTITIES[actor_coordinate],
        ENTITIES[target_coordinate],
        ENTITIES[causer_coordinate],
        index=index,
        evaluation=evaluation,
    )
    return Observation(sentence, before, tuple(after))


def participant_coordinates(cell_index: int, repetition: int) -> tuple[int, int, int]:
    actor = (cell_index + repetition) % len(ENTITIES)
    target = (cell_index + 2 * repetition + 1) % len(ENTITIES)
    if target == actor:
        target = (target + 1) % len(ENTITIES)
    causer = (cell_index + 3 * repetition + 2) % len(ENTITIES)
    while causer in (actor, target):
        causer = (causer + 1) % len(ENTITIES)
    return actor, target, causer


def training_cells() -> tuple[tuple[str, str, str], ...]:
    cells: list[tuple[str, str, str]] = []
    for stem in STEMS:
        cells.extend(
            ((stem, "active", "positive"), (stem, "active", "negative"))
        )
        cells.append((stem, TRAINING_NONACTIVE[stem], "positive"))
    return tuple(cells)


def training_observations() -> tuple[Observation, ...]:
    rows: list[Observation] = []
    for cell_index, (stem, voice, polarity) in enumerate(training_cells()):
        for repetition in range(REPETITIONS):
            actor, target, causer = participant_coordinates(cell_index, repetition)
            rows.append(
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
    return tuple(rows)


def positive_family_voice_heldout_cells() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (
            stem,
            "causative" if TRAINING_NONACTIVE[stem] == "passive" else "passive",
            "positive",
        )
        for stem in STEMS
    )


def globally_composed_negative_cells() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (stem, voice, "negative")
        for stem in STEMS
        for voice in ("passive", "causative")
    )


def heldout_observations(
    cells: Sequence[tuple[str, str, str]],
) -> tuple[Observation, ...]:
    rows: list[Observation] = []
    for cell_index, (stem, voice, polarity) in enumerate(cells):
        actor = cell_index % len(ENTITIES)
        target = (cell_index + 1) % len(ENTITIES)
        causer = (cell_index + 2) % len(ENTITIES)
        while causer in (actor, target):
            causer = (causer + 1) % len(ENTITIES)
        for swap in (False, True):
            surface_actor, surface_target = (
                (target, actor) if swap else (actor, target)
            )
            rows.append(
                build_observation(
                    stem,
                    voice,
                    polarity,
                    surface_actor,
                    surface_target,
                    causer,
                    index=20_000 + cell_index,
                    evaluation=True,
                )
            )
    return tuple(rows)


def parse_surface(sentence: str) -> ParsedSurface:
    text = normalize(sentence)
    spans: list[tuple[int, int, int, str]] = []
    for coordinate, entity in enumerate(ENTITIES):
        start = text.find(entity)
        if start < 0:
            continue
        if text.find(entity, start + 1) >= 0:
            raise ValueError("entity appears more than once")
        marker_start = start + len(entity)
        marker = next(
            (
                particle
                for particle in sorted(
                    INHERITED_PARTICLES, key=len, reverse=True
                )
                if text.startswith(particle, marker_start)
            ),
            None,
        )
        if marker is None:
            raise ValueError("grounded entity lacks an inherited case marker")
        spans.append((start, marker_start + len(marker), coordinate, marker))
    spans.sort()
    if len(spans) not in (2, 3):
        raise ValueError("voice row must contain two or three grounded participants")
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("participant spans overlap")
    predicate = text[spans[-1][1] :]
    if not predicate:
        raise ValueError("predicate suffix is empty")
    return ParsedSurface(
        predicate,
        tuple(row[2] for row in spans),
        tuple(row[3] for row in spans),
    )


def transition_signature(
    observation: Observation, parsed: ParsedSurface
) -> Signature:
    changed = [
        index
        for index, (before, after) in enumerate(
            zip(observation.before, observation.after)
        )
        if before != after
    ]
    if not changed:
        return Signature(len(parsed.participants), None, True)
    if len(changed) != 1:
        raise ValueError("one copy event may change at most one coordinate")
    destination = changed[0]
    sources = [
        index
        for index, value in enumerate(observation.before)
        if index != destination and value == observation.after[destination]
    ]
    if len(sources) != 1:
        raise ValueError("copy event must identify one source")
    source = sources[0]
    try:
        source_pos = parsed.participants.index(source)
        destination_pos = parsed.participants.index(destination)
    except ValueError as error:
        raise ValueError("transition participants are not surface-grounded") from error
    if len(parsed.participants) == 2:
        if (source_pos, destination_pos) == (0, 1):
            return Signature(2, True, False)
        if (source_pos, destination_pos) == (1, 0):
            return Signature(2, False, False)
    if len(parsed.participants) == 3:
        if (source_pos, destination_pos) == (1, 2):
            return Signature(3, True, False)
        if (source_pos, destination_pos) == (2, 1):
            return Signature(3, False, False)
    raise ValueError("transition does not match a supported participant relation")


def apply_signature(
    signature: Signature, participants: Sequence[int], before: State
) -> State | None:
    if len(participants) != signature.arity:
        return None
    if signature.noop:
        return before
    if signature.arity == 2:
        positions = (0, 1) if signature.forward else (1, 0)
    elif signature.arity == 3:
        positions = (1, 2) if signature.forward else (2, 1)
    else:
        return None
    source, destination = (participants[index] for index in positions)
    after = list(before)
    after[destination] = before[source]
    return tuple(after)


def aggregate_surface_evidence(
    observations: Iterable[Observation],
) -> tuple[dict[str, Signature], int]:
    grouped: dict[str, Counter[Signature]] = defaultdict(Counter)
    for observation in observations:
        parsed = parse_surface(observation.sentence)
        grouped[parsed.predicate][
            transition_signature(observation, parsed)
        ] += 1
    recovered_errors = 0
    resolved: dict[str, Signature] = {}
    for surface, counts in grouped.items():
        ranking = counts.most_common()
        if len(ranking) > 1 and ranking[0][1] == ranking[1][1]:
            raise NonIdentifiableMorphologyError(
                f"surface {surface!r} has a tied transition signature"
            )
        resolved[surface] = ranking[0][0]
        recovered_errors += sum(count for _, count in ranking[1:])
    return resolved, recovered_errors


def longest_common_prefix(rows: Sequence[str]) -> str:
    if not rows:
        return ""
    prefix = rows[0]
    for row in rows[1:]:
        while prefix and not row.startswith(prefix):
            prefix = prefix[:-1]
    return prefix


def candidate_family_clusters(
    surfaces: Sequence[str],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    universe = tuple(sorted(set(surfaces)))
    clusters: dict[frozenset[str], str] = {}
    for surface in universe:
        for end in range(1, len(surface)):
            prefix = surface[:end]
            members = frozenset(row for row in universe if row.startswith(prefix))
            if len(members) < 2:
                continue
            stem = longest_common_prefix(tuple(sorted(members)))
            if stem:
                clusters[members] = stem
    return tuple(
        sorted((stem, tuple(sorted(members))) for members, stem in clusters.items())
    )


def exact_family_clusterings(
    surfaces: Sequence[str],
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], ...]:
    universe = frozenset(surfaces)
    candidates = candidate_family_clusters(surfaces)
    by_surface: dict[str, list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
    for candidate in candidates:
        for surface in candidate[1]:
            by_surface[surface].append(candidate)
    solutions: set[tuple[tuple[str, tuple[str, ...]], ...]] = set()

    def search(
        uncovered: frozenset[str],
        chosen: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> None:
        if not uncovered:
            solutions.add(tuple(sorted(chosen)))
            return
        pivot = min(uncovered, key=lambda row: len(by_surface[row]))
        for candidate in by_surface[pivot]:
            members = frozenset(candidate[1])
            if members.issubset(uncovered):
                search(uncovered - members, (*chosen, candidate))

    search(universe, tuple())
    if not solutions:
        raise NonIdentifiableMorphologyError(
            "surface forms cannot be covered by recurring-prefix families"
        )
    scored: list[
        tuple[
            tuple[int, int],
            tuple[tuple[str, tuple[str, ...]], ...],
        ]
    ] = []
    for solution in solutions:
        residual_units = sum(
            len(surface) - len(stem)
            for stem, members in solution
            for surface in members
        )
        scored.append(((len(solution), residual_units), solution))
    best_score = min(score for score, _ in scored)
    return tuple(solution for score, solution in scored if score == best_score)


def suffix_splits(suffix: str) -> tuple[tuple[str, str], ...]:
    return tuple((suffix[:index], suffix[index:]) for index in range(len(suffix)))


def infer_morphology(
    observations: Iterable[Observation],
) -> tuple[
    FactorizedMorphologyModel,
    MorphologyFit,
    WholeSurfaceMemorizer,
    WholeSuffixModel,
]:
    rows = tuple(observations)
    evidence, recovered_errors = aggregate_surface_evidence(rows)
    clusterings = exact_family_clusterings(tuple(evidence))
    valid_results: list[
        tuple[
            tuple[int, int, tuple],
            FactorizedMorphologyModel,
            tuple[tuple[str, str, str], ...],
        ]
    ] = []

    for clustering in clusterings:
        if len(clustering) < 2:
            continue
        family_suffixes: dict[str, dict[str, Signature]] = {}
        for stem, members in clustering:
            suffix_map: dict[str, Signature] = {}
            for surface in members:
                suffix = surface[len(stem) :]
                if not suffix or suffix in suffix_map:
                    break
                suffix_map[suffix] = evidence[surface]
            else:
                family_suffixes[stem] = suffix_map
                continue
            family_suffixes = {}
            break
        if not family_suffixes:
            continue
        suffixes = tuple(
            sorted(
                {
                    suffix
                    for mapping in family_suffixes.values()
                    for suffix in mapping
                }
            )
        )
        if len(suffixes) != 4:
            continue

        assignments: list[tuple[tuple[str, str, str], ...]] = []
        split_options = [suffix_splits(suffix) for suffix in suffixes]

        def split_search(
            index: int, selected: list[tuple[str, str, str]]
        ) -> None:
            if index == len(suffixes):
                assignments.append(tuple(selected))
                return
            suffix = suffixes[index]
            for voice_prefix, polarity_ending in split_options[index]:
                selected.append((suffix, voice_prefix, polarity_ending))
                split_search(index + 1, selected)
                selected.pop()

        split_search(0, [])
        for assignment in assignments:
            voice_prefixes = {voice for _, voice, _ in assignment}
            endings = {ending for _, _, ending in assignment}
            if len(voice_prefixes) != 3 or len(endings) != 2:
                continue
            pair_map = {
                (voice, ending): suffix
                for suffix, voice, ending in assignment
            }
            if len(pair_map) != len(assignment):
                continue
            suffix_to_pair = {
                suffix: (voice, ending)
                for suffix, voice, ending in assignment
            }

            ending_signatures: dict[str, list[Signature]] = defaultdict(list)
            voice_signatures: dict[str, list[Signature]] = defaultdict(list)
            voice_family_presence: dict[str, set[str]] = defaultdict(set)
            for stem, mapping in family_suffixes.items():
                for suffix, signature in mapping.items():
                    voice, ending = suffix_to_pair[suffix]
                    ending_signatures[ending].append(signature)
                    voice_signatures[voice].append(signature)
                    voice_family_presence[voice].add(stem)
            negative_candidates = [
                ending
                for ending, signatures in ending_signatures.items()
                if signatures and all(signature.noop for signature in signatures)
            ]
            positive_candidates = [
                ending
                for ending, signatures in ending_signatures.items()
                if signatures and all(not signature.noop for signature in signatures)
            ]
            if len(negative_candidates) != 1 or len(positive_candidates) != 1:
                continue
            negative_ending = negative_candidates[0]
            positive_ending = positive_candidates[0]

            causative_candidates = [
                voice
                for voice, signatures in voice_signatures.items()
                if any(not signature.noop for signature in signatures)
                and all(
                    signature.noop or signature.arity == 3
                    for signature in signatures
                )
            ]
            if len(causative_candidates) != 1:
                continue
            causative_prefix = causative_candidates[0]
            binary_voices = sorted(voice_prefixes - {causative_prefix})
            if len(binary_voices) != 2:
                continue
            active_candidates = [
                voice
                for voice in binary_voices
                if (voice, positive_ending) in pair_map
                and (voice, negative_ending) in pair_map
                and voice_family_presence[voice] == set(family_suffixes)
            ]
            if len(active_candidates) != 1:
                continue
            active_prefix = active_candidates[0]
            passive_prefix = next(
                voice for voice in binary_voices if voice != active_prefix
            )
            if (passive_prefix, positive_ending) not in pair_map:
                continue

            families: list[Family] = []
            consistent = True
            for stem, mapping in sorted(family_suffixes.items()):
                active_suffix = pair_map[(active_prefix, positive_ending)]
                active_signature = mapping.get(active_suffix)
                if (
                    active_signature is None
                    or active_signature.noop
                    or active_signature.arity != 2
                ):
                    consistent = False
                    break
                base = bool(active_signature.forward)
                passive_suffix = pair_map.get(
                    (passive_prefix, positive_ending)
                )
                if passive_suffix in mapping:
                    signature = mapping[passive_suffix]
                    if (
                        signature.noop
                        or signature.arity != 2
                        or signature.forward == base
                    ):
                        consistent = False
                        break
                causative_suffix = pair_map.get(
                    (causative_prefix, positive_ending)
                )
                if causative_suffix in mapping:
                    signature = mapping[causative_suffix]
                    if (
                        signature.noop
                        or signature.arity != 3
                        or signature.forward != base
                    ):
                        consistent = False
                        break
                active_negative_suffix = pair_map[
                    (active_prefix, negative_ending)
                ]
                negative_signature = mapping.get(active_negative_suffix)
                if (
                    negative_signature is None
                    or not negative_signature.noop
                    or negative_signature.arity != 2
                ):
                    consistent = False
                    break
                families.append(
                    Family(
                        stem,
                        tuple(sorted(stem + suffix for suffix in mapping)),
                        base,
                    )
                )
            if not consistent:
                continue
            model = FactorizedMorphologyModel(
                tuple(families),
                active_prefix,
                passive_prefix,
                causative_prefix,
                positive_ending,
                negative_ending,
            )
            description_units = (
                sum(len(row.stem) for row in families)
                + sum(
                    len(value)
                    for value in (
                        active_prefix,
                        passive_prefix,
                        causative_prefix,
                        positive_ending,
                        negative_ending,
                    )
                )
                + len(families)
            )
            behavior_key = tuple(
                (
                    stem,
                    voice,
                    polarity,
                    model.decode_predicate(
                        stem
                        + VOICE_MORPHS[voice]
                        + POLARITY_MORPHS[polarity]
                    ),
                )
                for stem in STEMS
                for voice in ("active", "passive", "causative")
                for polarity in ("positive", "negative")
            )
            score = (description_units, len(clustering), behavior_key)
            valid_results.append((score, model, assignment))

    if not valid_results:
        raise NonIdentifiableMorphologyError(
            "no voice/polarity factorization survives"
        )
    best_description = min(row[0][:2] for row in valid_results)
    best = [
        row for row in valid_results if row[0][:2] == best_description
    ]
    by_behavior: dict[
        tuple,
        tuple[
            tuple[int, int, tuple],
            FactorizedMorphologyModel,
            tuple[tuple[str, str, str], ...],
        ],
    ] = {}
    for row in best:
        by_behavior[row[0][2]] = row
    if len(by_behavior) != 1:
        raise NonIdentifiableMorphologyError(
            f"morphology has {len(by_behavior)} behaviorally distinct optima"
        )
    _, model, assignment = next(iter(by_behavior.values()))
    fit = MorphologyFit(
        model.families,
        model.active_prefix,
        model.passive_prefix,
        model.causative_prefix,
        model.positive_ending,
        model.negative_ending,
        len(by_behavior),
        len(clusterings),
        recovered_errors,
    )
    memorizer = WholeSurfaceMemorizer(tuple(sorted(evidence.items())))
    observed_suffix_operators: set[tuple[str, str, str]] = set()
    for suffix, voice_prefix, ending in assignment:
        voice = (
            "active"
            if voice_prefix == model.active_prefix
            else "passive"
            if voice_prefix == model.passive_prefix
            else "causative"
        )
        polarity = (
            "positive" if ending == model.positive_ending else "negative"
        )
        observed_suffix_operators.add((suffix, voice, polarity))
    suffix_model = WholeSuffixModel(
        tuple((row.stem, row.base_bit) for row in model.families),
        tuple(sorted(observed_suffix_operators)),
    )
    return model, fit, memorizer, suffix_model


def score(
    model: object, observations: Iterable[Observation]
) -> tuple[float, float]:
    rows = tuple(observations)
    answers = [model.predict(row.sentence, row.before) for row in rows]
    answered = sum(answer is not None for answer in answers)
    correct = sum(
        answer == row.after for answer, row in zip(answers, rows)
    )
    return (
        correct / len(rows) if rows else 0.0,
        answered / len(rows) if rows else 0.0,
    )


def positionless_upper_bound(observations: Iterable[Observation]) -> float:
    grouped: dict[tuple[tuple[str, ...], State], Counter[State]] = defaultdict(
        Counter
    )
    rows = tuple(observations)
    for row in rows:
        grouped[(tuple(sorted(row.text)), row.before)][row.after] += 1
    return sum(max(counts.values()) for counts in grouped.values()) / len(rows)


def literal_form_bits(forms: Iterable[str]) -> int:
    return len(
        json.dumps(
            sorted(set(forms)), ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ) * 8


def missing_negative_anchor_is_rejected() -> bool:
    rows = tuple(
        row for row in training_observations() if not row.text.endswith("ない")
    )
    try:
        infer_morphology(rows)
    except NonIdentifiableMorphologyError:
        return True
    return False


def missing_passive_voice_is_rejected() -> bool:
    rows = tuple(
        row for row in training_observations() if "られる" not in row.text
    )
    try:
        infer_morphology(rows)
    except NonIdentifiableMorphologyError:
        return True
    return False


def tied_surface_signature_is_rejected() -> bool:
    row = build_observation(
        "受け", "active", "positive", 0, 1, 2, index=90_000
    )
    reverse = build_observation(
        "受け",
        "active",
        "positive",
        0,
        1,
        2,
        index=90_000,
        corrupt=True,
    )
    try:
        aggregate_surface_evidence((row, reverse))
    except NonIdentifiableMorphologyError:
        return True
    return False


def unknown_morphology_abstains(
    model: FactorizedMorphologyModel,
) -> bool:
    sentence = "記録ではアキがボブに受けた。"
    return model.predict(sentence, (1, 2, 3, 4, 5)) is None


def wrong_arity_abstains(model: FactorizedMorphologyModel) -> bool:
    sentence = "記録ではアキがボブに受けさせる。"
    return model.predict(sentence, (1, 2, 3, 4, 5)) is None


def voice_intervention_preserves_event(
    model: FactorizedMorphologyModel,
) -> bool:
    before = (11, 22, 33, 44, 55)
    active = render_sentence(
        "受け",
        "active",
        "positive",
        "アキ",
        "ボブ",
        "チカ",
        index=0,
    )
    passive = render_sentence(
        "受け",
        "passive",
        "positive",
        "アキ",
        "ボブ",
        "チカ",
        index=0,
    )
    return model.predict(active, before) == model.predict(
        passive, before
    ) != before


def polarity_intervention_suppresses_event(
    model: FactorizedMorphologyModel,
) -> bool:
    before = (11, 22, 33, 44, 55)
    positive = render_sentence(
        "受け",
        "passive",
        "positive",
        "アキ",
        "ボブ",
        "チカ",
        index=0,
    )
    negative = render_sentence(
        "受け",
        "passive",
        "negative",
        "アキ",
        "ボブ",
        "チカ",
        index=0,
    )
    return (
        model.predict(positive, before) != before
        and model.predict(negative, before) == before
    )


def run() -> dict[str, object]:
    train = training_observations()
    positive_cells = positive_family_voice_heldout_cells()
    composed_negative_cells = globally_composed_negative_cells()
    positive_test = heldout_observations(positive_cells)
    negative_test = heldout_observations(composed_negative_cells)
    all_test = (*positive_test, *negative_test)
    model, fit, memorizer, suffix_model = infer_morphology(train)

    positive_accuracy, positive_coverage = score(model, positive_test)
    negative_accuracy, negative_coverage = score(model, negative_test)
    total_accuracy, total_coverage = score(model, all_test)
    memorizer_accuracy, memorizer_coverage = score(memorizer, all_test)
    suffix_positive_accuracy, suffix_positive_coverage = score(
        suffix_model, positive_test
    )
    suffix_negative_accuracy, suffix_negative_coverage = score(
        suffix_model, negative_test
    )

    observed_forms = [parse_surface(row.sentence).predicate for row in train]
    exhaustive_forms = [
        surface_form(stem, voice, polarity)
        for stem in STEMS
        for voice in ("active", "passive", "causative")
        for polarity in ("positive", "negative")
    ]
    theorem_checks = {
        "six_lexical_families_are_induced": len(model.families) == 6,
        "three_voice_morphs_are_induced": len(
            {
                model.active_prefix,
                model.passive_prefix,
                model.causative_prefix,
            }
        )
        == 3,
        "two_polarity_endings_are_induced": (
            model.positive_ending != model.negative_ending
        ),
        "global_missing_negative_compositions_are_recovered": (
            negative_accuracy == negative_coverage == 1.0
        ),
        "unseen_family_voice_positive_combinations_transfer": (
            positive_accuracy == positive_coverage == 1.0
        ),
        "all_heldout_rows_are_perfect": (
            total_accuracy == total_coverage == 1.0
        ),
        "whole_surface_memorizer_has_zero_coverage": memorizer_coverage
        == 0.0,
        "whole_suffix_model_covers_positive_recombination": (
            suffix_positive_accuracy == suffix_positive_coverage == 1.0
        ),
        "whole_suffix_model_cannot_cover_unseen_composed_negatives": (
            suffix_negative_coverage == 0.0
        ),
        "positive_positionless_character_bound_is_half": (
            positionless_upper_bound(positive_test) == 0.5
        ),
        "bounded_signature_noise_is_recovered": (
            fit.recovered_training_errors
            == len(training_cells()) * CORRUPTIONS_PER_CELL
        ),
        "negative_anchor_is_necessary": missing_negative_anchor_is_rejected(),
        "passive_voice_evidence_is_necessary": missing_passive_voice_is_rejected(),
        "tied_surface_signature_is_rejected": tied_surface_signature_is_rejected(),
        "unknown_morphology_abstains": unknown_morphology_abstains(model),
        "wrong_arity_abstains": wrong_arity_abstains(model),
        "voice_intervention_preserves_underlying_event": (
            voice_intervention_preserves_event(model)
        ),
        "polarity_intervention_suppresses_event": (
            polarity_intervention_suppresses_event(model)
        ),
        "sentences_are_continuous_without_whitespace": all(
            not any(character.isspace() for character in row.sentence)
            for row in (*train, *all_test)
        ),
    }

    return {
        "campaign": {
            "name": "phase18a4-voice-polarity-morphology-c1",
            "inherited_from_phase18a3": (
                "entity lexicon and local case-marker inventory"
            ),
            "raw_predicates_have_no_voice_or_polarity_labels": True,
            "training_surface_cells": len(training_cells()),
            "globally_unseen_composed_suffix_cells": len(
                composed_negative_cells
            ),
            "unseen_family_voice_positive_cells": len(positive_cells),
            "public_benchmark_examples_used": 0,
        },
        "induction": {
            "unique_surface_forms": len(set(observed_forms)),
            "best_family_clusterings": fit.family_clusterings,
            "behaviorally_distinct_morphology_optima": (
                fit.unique_factorizations
            ),
            "learned_stems": [row.stem for row in model.families],
            "learned_base_bits": [
                [row.stem, row.base_bit] for row in model.families
            ],
            "learned_voice_prefixes": {
                "active": model.active_prefix,
                "passive": model.passive_prefix,
                "causative": model.causative_prefix,
            },
            "learned_polarity_endings": {
                "positive": model.positive_ending,
                "negative": model.negative_ending,
            },
            "recovered_training_errors": fit.recovered_training_errors,
        },
        "evaluation": {
            "training_observations": len(train),
            "positive_family_voice_heldout_rows": len(positive_test),
            "global_composed_negative_heldout_rows": len(negative_test),
            "total_heldout_rows": len(all_test),
            "positive_accuracy": positive_accuracy,
            "positive_coverage": positive_coverage,
            "composed_negative_accuracy": negative_accuracy,
            "composed_negative_coverage": negative_coverage,
            "total_accuracy": total_accuracy,
            "total_coverage": total_coverage,
            "whole_surface_memorizer_accuracy": memorizer_accuracy,
            "whole_surface_memorizer_coverage": memorizer_coverage,
            "whole_suffix_positive_accuracy": suffix_positive_accuracy,
            "whole_suffix_positive_coverage": suffix_positive_coverage,
            "whole_suffix_composed_negative_accuracy": suffix_negative_accuracy,
            "whole_suffix_composed_negative_coverage": suffix_negative_coverage,
            "positive_positionless_character_upper_bound": (
                positionless_upper_bound(positive_test)
            ),
        },
        "resource_accounting": {
            "serialized_factorized_model_bits": model.description_bits,
            "observed_surface_form_table_bits": literal_form_bits(
                observed_forms
            ),
            "exhaustive_36_form_table_bits": literal_form_bits(
                exhaustive_forms
            ),
            "phase18a4_source_bytes": Path(__file__).read_bytes().__len__(),
            "python_runtime_and_standard_library_included": False,
        },
        "theorem_checks": theorem_checks,
        "all_theorem_checks_pass": all(theorem_checks.values()),
        "claim_boundary": {
            "voice_and_polarity_recombination_in_controlled_ichidan_microgrammar": (
                all(theorem_checks.values())
            ),
            "multiple_japanese_conjugation_classes_demonstrated": False,
            "general_japanese_morphology_demonstrated": False,
            "reading_comprehension_demonstrated": False,
            "japanese_high_school_intelligence_demonstrated": False,
        },
        "limitations": [
            "Phase 18a-3 entity and case-marker atoms are inherited rather than re-induced jointly in this campaign",
            "all six predicate families use one regular ichidan-like conjugation class",
            "voice and polarity are tested on one controlled copy-event ontology",
            "negative observations are identified through repeated no-change interventions",
            "passive and causative argument structures are limited to one surface realization each",
            "ellipsis, aspect, tense, modality, honorifics, and lexical polysemy remain absent",
            "Python and its standard library remain excluded substrate",
        ],
    }


def render_markdown(payload: Mapping[str, object]) -> str:
    campaign = payload["campaign"]
    induction = payload["induction"]
    evaluation = payload["evaluation"]
    resources = payload["resource_accounting"]
    lines = [
        "# Phase 18a-4 results: induced voice and polarity morphology",
        "",
        "Phase 18a-4 replaces whole inflected-predicate memorization with a learned",
        "stem × voice-prefix × polarity-ending factorization. Passive-negative and",
        "causative-negative suffixes are absent globally during training.",
        "",
        "## Induction",
        "",
        f"- Training surface cells / observations: **{campaign['training_surface_cells']} / {evaluation['training_observations']}**",
        f"- Unique observed surface predicates: **{induction['unique_surface_forms']}**",
        f"- Behaviorally distinct best factorizations: **{induction['behaviorally_distinct_morphology_optima']}**",
        f"- Learned stems: **{'・'.join(induction['learned_stems'])}**",
        f"- Learned voice prefixes: **{induction['learned_voice_prefixes']}**",
        f"- Learned polarity endings: **{induction['learned_polarity_endings']}**",
        f"- Recovered bounded corruptions: **{induction['recovered_training_errors']}**",
        "",
        "## Frozen held-out transfer",
        "",
        f"- Unseen family × positive voice rows: **{evaluation['positive_family_voice_heldout_rows']}**",
        f"- Globally unseen passive/causative negative rows: **{evaluation['global_composed_negative_heldout_rows']}**",
        f"- Total accuracy / coverage: **{100 * evaluation['total_accuracy']:.1f}% / {100 * evaluation['total_coverage']:.1f}%**",
        f"- Whole-surface memorizer coverage: **{100 * evaluation['whole_surface_memorizer_coverage']:.1f}%**",
        f"- Whole-suffix model positive coverage: **{100 * evaluation['whole_suffix_positive_coverage']:.1f}%**",
        f"- Whole-suffix model composed-negative coverage: **{100 * evaluation['whole_suffix_composed_negative_coverage']:.1f}%**",
        f"- Positive role-swap character-bag upper bound: **{100 * evaluation['positive_positionless_character_upper_bound']:.1f}%**",
        "",
        "## Resource accounting",
        "",
        f"- Serialized factorized model: **{resources['serialized_factorized_model_bits']} bits**",
        f"- Observed 18-form table: **{resources['observed_surface_form_table_bits']} bits**",
        f"- Exhaustive 36-form table: **{resources['exhaustive_36_form_table_bits']} bits**",
        f"- Phase 18a-4 source: **{resources['phase18a4_source_bytes']} bytes**",
        "- Python runtime and standard library: excluded and declared",
        "",
        "## Claim boundary",
        "",
        "This establishes voice/polarity recombination only in a controlled regular",
        "ichidan-like microgrammar. It is not evidence for unrestricted Japanese",
        "morphology, reading comprehension, or high-school-level intelligence.",
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
    (output / "phase18a4.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(payload)
    (output / "phase18a4.md").write_text(markdown, encoding="utf-8")
    print(markdown, end="")


if __name__ == "__main__":
    main()
