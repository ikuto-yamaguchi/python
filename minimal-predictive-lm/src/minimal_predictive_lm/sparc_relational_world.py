from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
import math
import pickle
import re
import zlib
from typing import Iterable, Mapping

ACTUAL = "実際"
OBS_ACTUAL = re.compile(r"実際には(?P<subject>[^、。]+?)の(?P<relation>[^、。]+?)は(?P<value>[^、。]+?)(?:だった|である)$")
OBS_VIEW = re.compile(r"(?P<observer>[^、。]+?)の認識では(?P<subject>[^、。]+?)の(?P<relation>[^、。]+?)は(?P<value>[^、。]+?)(?:だった|である)$")
Q_ACTUAL = re.compile(r"実際には(?P<subject>[^、。？?]+?)の(?P<relation>[^、。？?]+?)は(?:どこ|誰|何)ですか[？?]?$")
Q_VIEW = re.compile(r"(?P<observer>[^、。]+?)の認識では(?P<subject>[^、。？?]+?)の(?P<relation>[^、。？?]+?)は(?:どこ|誰|何)ですか[？?]?$")
Q_MATCH = re.compile(r"(?P<observer>[^、。]+?)の認識する(?P<subject>[^、。]+?)の(?P<relation>[^、。]+?)は実際と一致していますか[？?]?$")
Q_COMPARE = re.compile(r"(?P<observer>[^、。]+?)の認識と実際の(?P<subject>[^、。]+?)の(?P<relation>[^、。]+?)を教えて(?:ください)?[。！]?$")


def split_sentences(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"[。\n]+", text) if part.strip())


@dataclass(frozen=True, order=True)
class FactKey:
    scope: str
    relation: str
    subject: str


@dataclass(frozen=True)
class Atom:
    scope_kind: str
    scope_role: int
    relation: str
    subject_role: int
    value_kind: str
    value_role: int


@dataclass(frozen=True)
class Program:
    atoms: tuple[Atom, ...]


@dataclass(frozen=True)
class StepResult:
    status: str
    answer: str
    confidence: float
    program: Program | None
    candidates: int
    reads: int


def parse_observations(text: str) -> dict[FactKey, str]:
    facts: dict[FactKey, str] = {}
    for sentence in split_sentences(text):
        sentence = re.sub(r"^(?:当初の記録では|後の記録では|そして|また|なお)、?", "", sentence)
        match = OBS_ACTUAL.fullmatch(sentence)
        if match:
            facts[FactKey(ACTUAL, match["relation"], match["subject"])] = match["value"]
            continue
        match = OBS_VIEW.fullmatch(sentence)
        if match:
            facts[FactKey(match["observer"], match["relation"], match["subject"])] = match["value"]
    return facts


def parse_training_document(document: str) -> tuple[dict[FactKey, str], str, dict[FactKey, str]]:
    left, tail = document.split("出来事は「", 1)
    event, right = tail.split("」。後の記録では", 1)
    before = parse_observations(left)
    after = parse_observations("後の記録では" + right)
    if not before or not after:
        raise ValueError("document has no recoverable observations")
    return before, event, after


def entities(state: Mapping[FactKey, str]) -> set[str]:
    result = {key.subject for key in state}
    result.update(key.scope for key in state if key.scope != ACTUAL)
    result.update(state.values())
    return result


def _canonical_program(before: Mapping[FactKey, str], after: Mapping[FactKey, str], event: str) -> tuple[Program, dict[int, str]]:
    changed = [(key, value) for key, value in after.items() if before.get(key) != value]
    if not changed:
        raise ValueError("no changed facts")
    changed.sort(key=lambda row: (row[0].relation, 0 if row[0].scope == ACTUAL else 1, row[0].subject, row[0].scope))
    role_of: dict[str, int] = {}
    role_entity: dict[int, str] = {}

    def role(entity: str) -> int:
        if entity not in role_of:
            index = len(role_of)
            role_of[entity] = index
            role_entity[index] = entity
        return role_of[entity]

    for key, _ in changed:
        role(key.subject)
    for key, value in changed:
        actual_key = FactKey(ACTUAL, key.relation, key.subject)
        if key.scope != ACTUAL and after.get(actual_key) == value:
            continue
        source = next(
            (
                candidate.subject
                for candidate, old_value in before.items()
                if candidate.scope == ACTUAL
                and candidate.relation == key.relation
                and old_value == value
                and candidate.subject != key.subject
                and candidate.subject in event
                and value not in event
            ),
            None,
        )
        role(source if source is not None else value)
    for key, _ in changed:
        if key.scope != ACTUAL:
            role(key.scope)

    atoms: list[Atom] = []
    for key, value in changed:
        subject_role = role_of[key.subject]
        scope_kind = "actual" if key.scope == ACTUAL else "view"
        scope_role = -1 if key.scope == ACTUAL else role_of[key.scope]
        actual_key = FactKey(ACTUAL, key.relation, key.subject)
        if key.scope != ACTUAL and after.get(actual_key) == value:
            value_kind, value_role = "actual", subject_role
        else:
            source = next(
                (
                    candidate.subject
                    for candidate, old_value in before.items()
                    if candidate.scope == ACTUAL
                    and candidate.relation == key.relation
                    and old_value == value
                    and candidate.subject != key.subject
                    and candidate.subject in event
                    and value not in event
                ),
                None,
            )
            if source is not None:
                value_kind, value_role = "old", role_of[source]
            else:
                value_kind, value_role = "role", role_of[value]
        atoms.append(Atom(scope_kind, scope_role, key.relation, subject_role, value_kind, value_role))
    return Program(tuple(atoms)), role_entity


def char_ngrams(text: str, lo: int = 2, hi: int = 5) -> Counter[str]:
    text = re.sub(r"[、。！？\s\d]+", "", text)
    grams: Counter[str] = Counter()
    for size in range(lo, hi + 1):
        for index in range(max(0, len(text) - size + 1)):
            grams[text[index : index + size]] += 1
    return grams


def normalise(values: Mapping[str, float], limit: int = 256) -> dict[str, float]:
    rows = sorted(values.items(), key=lambda item: (-abs(item[1]), item[0]))[:limit]
    norm = math.sqrt(sum(value * value for _, value in rows))
    return {} if norm == 0.0 else {key: value / norm for key, value in rows}


def cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def mask_entities(text: str, values: Iterable[str]) -> str:
    for value in sorted(set(values), key=len, reverse=True):
        if value:
            text = text.replace(value, "対象")
    return re.sub(r"\d+", "数", text)


def context_features(text: str, entity: str, all_entities: Iterable[str]) -> dict[str, float]:
    if entity not in text:
        return {}
    masked = text
    for other in sorted(set(all_entities) - {entity}, key=len, reverse=True):
        masked = masked.replace(other, "対象")
    masked = masked.replace(entity, "◆", 1)
    index = masked.find("◆")
    return normalise(char_ngrams(masked[max(0, index - 10) : index + 11], 1, 4), 96)


class RelationalWorldLearner:
    """Learns graph-update programs and keeps actual and observer-specific worlds."""

    def __init__(self, threshold: float = 0.12, margin: float = 0.0, max_candidates: int = 12) -> None:
        self.threshold = threshold
        self.margin = margin
        self.max_candidates = max_candidates
        self.program_sums: dict[Program, Counter[str]] = defaultdict(Counter)
        self.program_counts: Counter[Program] = Counter()
        self.program_vectors: dict[Program, dict[str, float]] = {}
        self.role_sums: dict[tuple[Program, int], Counter[str]] = defaultdict(Counter)
        self.role_vectors: dict[tuple[Program, int], dict[str, float]] = {}
        self.postings: dict[str, set[Program]] = defaultdict(set)
        self.examples = 0
        self.state: dict[FactKey, str] = {}
        self.focus_subject: str | None = None
        self.max_seen_candidates = 0
        self.max_seen_reads = 0
        self.known_entities: set[str] = set()
        self.relation_values: dict[str, set[str]] = defaultdict(set)
        self.relation_subjects: dict[str, set[str]] = defaultdict(set)
        self.observers: set[str] = set()

    def _register_state(self, state: Mapping[FactKey, str]) -> None:
        for key, value in state.items():
            self.known_entities.update((key.subject, value))
            self.relation_subjects[key.relation].add(key.subject)
            self.relation_values[key.relation].add(value)
            if key.scope != ACTUAL:
                self.known_entities.add(key.scope)
                self.observers.add(key.scope)

    def learn_documents(self, documents: Iterable[str], reset: bool = False) -> int:
        if reset:
            self.program_sums.clear()
            self.program_counts.clear()
            self.role_sums.clear()
            self.examples = 0
        for document in documents:
            before, event, after = parse_training_document(document)
            self._register_state(before)
            self._register_state(after)
            program, role_entities = _canonical_program(before, after, event)
            universe = entities(before) | entities(after)
            self.program_sums[program].update(char_ngrams(mask_entities(event, universe)))
            self.program_counts[program] += 1
            for role_id, entity in role_entities.items():
                self.role_sums[(program, role_id)].update(context_features(event, entity, universe))
            self.examples += 1
        self.program_vectors = {program: normalise(vector, 384) for program, vector in self.program_sums.items()}
        self.role_vectors = {key: normalise(vector, 128) for key, vector in self.role_sums.items()}
        self.postings.clear()
        for program, vector in self.program_vectors.items():
            for feature, _ in sorted(vector.items(), key=lambda item: (-abs(item[1]), item[0]))[:96]:
                self.postings[feature].add(program)
        return len(self.program_vectors)

    def initialise(self, text: str) -> int:
        facts = parse_observations(text)
        self.state.update(facts)
        self._register_state(facts)
        if facts:
            self.focus_subject = next(reversed(facts)).subject
        return len(facts)

    def _program_candidates(self, event: str) -> tuple[list[tuple[float, Program]], int]:
        universe = set(self.known_entities) | entities(self.state)
        query = normalise(char_ngrams(mask_entities(event, universe)), 384)
        votes: Counter[Program] = Counter()
        reads = 0
        for feature, weight in query.items():
            for program in self.postings.get(feature, ()):
                votes[program] += abs(weight)
                reads += 1
        candidates = sorted(
            votes or Counter(self.program_vectors),
            key=lambda program: (-votes[program], -self.program_counts[program], str(program)),
        )[: self.max_candidates]
        scored: list[tuple[float, Program]] = []
        for program in candidates:
            reads += min(len(query), len(self.program_vectors[program]))
            scored.append((cosine(query, self.program_vectors[program]), program))
        scored.sort(key=lambda row: (-row[0], str(row[1])))
        return scored, reads

    def _bind_roles(self, program: Program, event: str) -> tuple[dict[int, str] | None, int]:
        universe = set(self.known_entities) | entities(self.state)
        subjects = set().union(*self.relation_subjects.values()) if self.relation_subjects else {key.subject for key in self.state}
        roles = sorted(
            {atom.subject_role for atom in program.atoms}
            | {atom.value_role for atom in program.atoms if atom.value_kind in {"role", "old"}}
            | {atom.scope_role for atom in program.atoms if atom.scope_kind == "view"}
        )
        allowed = {role_id: set(universe) for role_id in roles}
        for atom in program.atoms:
            allowed[atom.subject_role] &= self.relation_subjects.get(atom.relation, subjects)
            if atom.scope_kind == "view":
                allowed[atom.scope_role] &= self.observers
            if atom.value_kind == "role":
                allowed[atom.value_role] &= self.relation_values.get(atom.relation, set(universe))
            elif atom.value_kind == "old":
                allowed[atom.value_role] &= self.relation_subjects.get(atom.relation, subjects)
        mentioned = {entity for entity in universe if entity in event}
        pools: list[list[str]] = []
        for role_id in roles:
            pool = sorted(allowed[role_id] & mentioned, key=lambda entity: (event.find(entity), -len(entity), entity))
            if not pool and self.focus_subject in allowed[role_id]:
                pool = [self.focus_subject]
            if not pool:
                return None, 0
            pools.append(pool[:4])
        best: tuple[float, tuple[str, ...]] | None = None
        reads = 0
        for assignment in product(*pools):
            if len(set(assignment)) < len(assignment):
                continue
            score = 0.0
            for role_id, entity in zip(roles, assignment):
                query = context_features(event, entity, universe)
                prototype = self.role_vectors.get((program, role_id), {})
                reads += min(len(query), len(prototype))
                score += cosine(query, prototype)
            candidate = (score, assignment)
            if best is None or candidate > best:
                best = candidate
        if best is None:
            return None, reads
        return dict(zip(roles, best[1])), reads

    def _apply(self, program: Program, binding: Mapping[int, str]) -> dict[FactKey, str] | None:
        before = dict(self.state)
        after = dict(before)
        for atom in program.atoms:
            subject = binding.get(atom.subject_role)
            scope = ACTUAL if atom.scope_kind == "actual" else binding.get(atom.scope_role)
            if not subject or not scope:
                return None
            if atom.value_kind == "role":
                value = binding.get(atom.value_role)
            elif atom.value_kind == "actual":
                value = after.get(FactKey(ACTUAL, atom.relation, subject))
            else:
                source = binding.get(atom.value_role)
                value = before.get(FactKey(ACTUAL, atom.relation, source or ""))
            if value is None:
                return None
            after[FactKey(scope, atom.relation, subject)] = value
        return after

    def process(self, text: str) -> StepResult:
        text = text.strip()
        facts = parse_observations(text)
        if facts:
            self.state.update(facts)
            self._register_state(facts)
            self.focus_subject = next(reversed(facts)).subject
            return StepResult("observed", f"{len(facts)}件の関係を記憶しました。", 1.0, None, 0, 0)
        for regex, kind in ((Q_ACTUAL, "actual"), (Q_VIEW, "view"), (Q_MATCH, "match"), (Q_COMPARE, "compare")):
            match = regex.fullmatch(text)
            if not match:
                continue
            subject = match["subject"]
            relation = match["relation"]
            if kind == "actual":
                value = self.state.get(FactKey(ACTUAL, relation, subject))
                answer = "分かりません。" if value is None else f"{subject}の{relation}は{value}です。"
            elif kind == "view":
                observer = match["observer"]
                value = self.state.get(FactKey(observer, relation, subject))
                answer = "分かりません。" if value is None else f"{observer}は{subject}の{relation}を{value}だと認識しています。"
            elif kind == "match":
                observer = match["observer"]
                actual = self.state.get(FactKey(ACTUAL, relation, subject))
                view = self.state.get(FactKey(observer, relation, subject))
                answer = "分かりません。" if actual is None or view is None else ("一致しています。" if actual == view else "一致していません。")
            else:
                observer = match["observer"]
                actual = self.state.get(FactKey(ACTUAL, relation, subject))
                view = self.state.get(FactKey(observer, relation, subject))
                answer = "分かりません。" if actual is None or view is None else f"実際は{actual}、{observer}の認識は{view}です。"
            self.focus_subject = subject
            return StepResult("answered", answer, 1.0, None, 0, 0)
        scored, reads = self._program_candidates(text)
        if not scored:
            return StepResult("abstained", "その出来事はまだ理解できません。", 0.0, None, 0, reads)
        score, program = scored[0]
        runner = scored[1][0] if len(scored) > 1 else 0.0
        gap = score - runner
        confidence = max(0.0, min(1.0, 0.65 * score + 0.35 * gap))
        if score < self.threshold or gap < self.margin:
            return StepResult("abstained", "その出来事はまだ理解できません。", confidence, None, len(scored), reads)
        binding, role_reads = self._bind_roles(program, text)
        reads += role_reads
        if binding is None:
            return StepResult("abstained", "登場する対象を特定できません。", confidence, None, len(scored), reads)
        after = self._apply(program, binding)
        if after is None:
            return StepResult("abstained", "関係を安全に更新できません。", confidence, None, len(scored), reads)
        self.state = after
        self.focus_subject = binding.get(program.atoms[0].subject_role)
        self.max_seen_candidates = max(self.max_seen_candidates, len(scored))
        self.max_seen_reads = max(self.max_seen_reads, reads)
        return StepResult("updated", "出来事を関係世界に反映しました。", confidence, program, len(scored), reads)

    def to_bytes(self) -> bytes:
        return zlib.compress(pickle.dumps(self, protocol=5), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "RelationalWorldLearner":
        model = pickle.loads(zlib.decompress(data))
        if not isinstance(model, cls):
            raise TypeError("invalid model")
        return model
