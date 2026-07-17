from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
import math
import pickle
import re
import zlib
from typing import Iterable, Mapping

_PUNCT = re.compile(r"[\s、。！？；：・（）()「」『』【】\[\]]+")
_SLOT = re.compile(r"<V(\d+)>")


def _clean(text: str) -> str:
    return _PUNCT.sub("", text)


def _ngrams(text: str, lo: int = 2, hi: int = 5) -> Counter[str]:
    text = _clean(text)
    return Counter(
        text[i : i + width]
        for width in range(lo, min(hi, len(text)) + 1)
        for i in range(max(0, len(text) - width + 1))
    )


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    ln = math.sqrt(sum(value * value for value in left.values()))
    rn = math.sqrt(sum(value * value for value in right.values()))
    return dot / (ln * rn) if ln and rn else 0.0


@dataclass(frozen=True)
class World:
    facts: frozenset[tuple[str, str, str]] = frozenset()
    numbers: tuple[tuple[str, str, int], ...] = ()

    @classmethod
    def from_parts(
        cls,
        facts: Iterable[tuple[str, str, str]] = (),
        numbers: Mapping[tuple[str, str], int] | None = None,
    ) -> "World":
        rows = tuple(sorted((s, r, int(v)) for (s, r), v in (numbers or {}).items()))
        return cls(frozenset(facts), rows)

    def number_map(self) -> dict[tuple[str, str], int]:
        return {(s, r): value for s, r, value in self.numbers}


@dataclass(frozen=True)
class Edit:
    kind: str
    relation: str
    subject_slot: int
    object_slot: int | None = None
    target_value: int | None = None
    source_relation: str | None = None
    delta: int | None = None
    factor: int | None = None


@dataclass
class Program:
    program_id: str
    signature: tuple
    edits: tuple[Edit, ...]
    patterns: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ApplyResult:
    accepted: bool
    mechanism: str
    program_id: str | None
    world: World
    confidence: float


@dataclass(frozen=True)
class PlanResult:
    found: bool
    actions: tuple[str, ...]
    world: World
    expanded: int


class SparseGeneralLearner:
    """Sparse bidirectional surface-schema -> latent-program -> world learner.

    A program owns multiple observed surface schemas. Their literal fragments are
    reused compositionally to recover bindings from unseen combinations, and the
    same schemas verbalize learned worlds. No task/domain selector is supplied.
    """

    def __init__(self, *, threshold: float = 0.76, margin: float = 0.08, max_candidates: int = 16):
        self.threshold = threshold
        self.margin = margin
        self.max_candidates = max_candidates
        self.programs: dict[str, Program] = {}
        self.next_program = 0
        self.last_candidates = 0
        self.last_feature_reads = 0
        self.training_episodes = 0
        self.applied_episodes = 0
        self.abstentions = 0
        self.schema_compositions = 0
        self.verbalizations = 0

    @staticmethod
    def _visible_atoms(text: str, before: World, after: World) -> list[str]:
        atoms: set[str] = set()
        for world in (before, after):
            for s, _r, o in world.facts:
                atoms.update((s, o))
            for s, _r, value in world.numbers:
                atoms.add(s)
                atoms.add(str(value))
        clean = _clean(text)
        atoms.update(re.findall(r"-?\d+", clean))
        return sorted((a for a in atoms if a and a in clean), key=lambda x: (-len(x), x))

    @classmethod
    def _abstract(cls, text: str, before: World, after: World) -> tuple[str, tuple[str, ...]]:
        text = _clean(text)
        atoms = cls._visible_atoms(text, before, after)
        used: list[str] = []
        occupied: list[tuple[int, int]] = []
        hits: list[tuple[int, int, str]] = []
        for atom in atoms:
            start = text.find(atom)
            if start < 0:
                continue
            end = start + len(atom)
            if any(not (end <= left or start >= right) for left, right in occupied):
                continue
            occupied.append((start, end))
            hits.append((start, end, atom))
        hits.sort()
        if not hits:
            return text, ()
        out: list[str] = []
        cursor = 0
        for index, (start, end, atom) in enumerate(hits):
            out.append(text[cursor:start])
            out.append(f"<V{index}>")
            used.append(atom)
            cursor = end
        out.append(text[cursor:])
        return "".join(out), tuple(used)

    @staticmethod
    def _slot_for(value: str, atoms: tuple[str, ...]) -> int:
        try:
            return atoms.index(str(value))
        except ValueError as exc:
            raise ValueError(f"grounded value {value!r} is not visible in the episode text") from exc

    @classmethod
    def _derive_edits(cls, before: World, after: World, atoms: tuple[str, ...]) -> tuple[Edit, ...]:
        edits: list[Edit] = []
        for subject, relation, obj in sorted(after.facts - before.facts):
            edits.append(Edit("add_fact", relation, cls._slot_for(subject, atoms), cls._slot_for(obj, atoms)))
        for subject, relation, obj in sorted(before.facts - after.facts):
            edits.append(Edit("remove_fact", relation, cls._slot_for(subject, atoms), cls._slot_for(obj, atoms)))
        bnum = before.number_map()
        anum = after.number_map()
        for key in sorted(set(bnum) | set(anum)):
            old, new = bnum.get(key), anum.get(key)
            if old == new:
                continue
            subject, relation = key
            slot = cls._slot_for(subject, atoms)
            if new is None:
                edits.append(Edit("delete_number", relation, slot))
            elif old is None:
                edits.append(Edit("set_from_slot", relation, slot, cls._slot_for(str(new), atoms)))
            elif new - old != 0 and str(abs(new - old)) in atoms:
                edits.append(Edit("add_const", relation, slot, delta=new - old))
            elif old != 0 and new % old == 0 and str(abs(new // old)) in atoms:
                edits.append(Edit("mul_const", relation, slot, factor=new // old))
            elif str(new) in atoms:
                edits.append(Edit("set_from_slot", relation, slot, cls._slot_for(str(new), atoms)))
            else:
                raise ValueError(f"cannot derive compact edit for {key}: {old}->{new}")
        if not edits:
            raise ValueError("episode has no state change")
        return tuple(edits)

    @staticmethod
    def _signature(edits: tuple[Edit, ...]) -> tuple:
        return tuple(
            (e.kind, e.relation, e.subject_slot, e.object_slot, e.target_value, e.source_relation, e.delta, e.factor)
            for e in edits
        )

    def teach(self, text: str, before: World, after: World) -> str:
        pattern, atoms = self._abstract(text, before, after)
        edits = self._derive_edits(before, after, atoms)
        signature = self._signature(edits)
        program = next((p for p in self.programs.values() if p.signature == signature), None)
        if program is None:
            pid = f"P{self.next_program}"
            self.next_program += 1
            program = Program(pid, signature, edits)
            self.programs[pid] = program
        program.patterns.add(pattern)
        self.training_episodes += 1
        return program.program_id

    @staticmethod
    def _compile(pattern: str) -> re.Pattern[str]:
        parts = re.split(r"(<V\d+>)", pattern)
        out = ""
        seen: set[int] = set()
        for part in parts:
            match = _SLOT.fullmatch(part)
            if match:
                index = int(match.group(1))
                if index in seen:
                    out += rf"(?P=V{index})"
                else:
                    out += rf"(?P<V{index}>.+?)"
                    seen.add(index)
            else:
                out += re.escape(part)
        return re.compile("^" + out + "$")

    @staticmethod
    def _literal_fragments(pattern: str) -> tuple[str, ...]:
        return tuple(part for part in re.split(r"<V\d+>", pattern) if part)

    @classmethod
    def _schema_bind(cls, program: Program, text: str) -> tuple[tuple[str, ...], float, int]:
        slot_count = 1 + max(
            index
            for edit in program.edits
            for index in (edit.subject_slot, edit.object_slot)
            if index is not None
        )
        fragments = sorted(
            {fragment for pattern in program.patterns for fragment in cls._literal_fragments(pattern)},
            key=lambda value: (-len(value), value),
        )
        marked = text
        covered = 0
        reads = 0
        for fragment in fragments:
            reads += 1
            if fragment not in marked:
                continue
            count = marked.count(fragment)
            covered += len(fragment) * count
            marked = marked.replace(fragment, "\0")
        bindings = tuple(part for part in marked.split("\0") if part)
        cue_ratio = covered / max(1, len(text))
        if len(bindings) != slot_count or cue_ratio < 0.35:
            return (), cue_ratio, reads
        if any(len(value) > 24 or not value for value in bindings):
            return (), cue_ratio, reads
        return bindings, min(0.99, 0.70 + 0.29 * cue_ratio), reads

    def _rank(self, text: str) -> list[tuple[float, Program, tuple[str, ...], str]]:
        normalized = _clean(text)
        query = _ngrams(normalized)
        rows: list[tuple[float, Program, tuple[str, ...], str]] = []
        reads = 0
        for program in self.programs.values():
            best_score = 0.0
            best_bindings: tuple[str, ...] = ()
            mechanism = "surface-similarity"
            for pattern in program.patterns:
                matcher = self._compile(pattern).fullmatch(normalized)
                vector = _ngrams(pattern)
                reads += min(len(query), len(vector))
                if matcher:
                    bindings = tuple(matcher.groupdict().get(f"V{i}", "") for i in range(32))
                    while bindings and bindings[-1] == "":
                        bindings = bindings[:-1]
                    score = 1.0
                    candidate_mechanism = "exact-surface-schema"
                else:
                    bindings = ()
                    score = _cosine(query, vector)
                    candidate_mechanism = "surface-similarity"
                if score > best_score:
                    best_score, best_bindings, mechanism = score, bindings, candidate_mechanism
            if not best_bindings:
                composed, composed_score, composed_reads = self._schema_bind(program, normalized)
                reads += composed_reads
                if composed and composed_score > best_score:
                    best_score, best_bindings, mechanism = composed_score, composed, "composed-surface-schema"
            rows.append((best_score, program, best_bindings, mechanism))
        rows.sort(key=lambda row: (-row[0], row[1].program_id))
        self.last_candidates = min(len(rows), self.max_candidates)
        self.last_feature_reads = reads
        return rows[: self.max_candidates]

    @staticmethod
    def _binding(bindings: tuple[str, ...], index: int | None) -> str:
        if index is None or index >= len(bindings) or bindings[index] == "":
            raise ValueError("missing surface binding")
        return bindings[index]

    @classmethod
    def _execute(cls, world: World, program: Program, bindings: tuple[str, ...]) -> World:
        facts = set(world.facts)
        numbers = world.number_map()
        for edit in program.edits:
            subject = cls._binding(bindings, edit.subject_slot)
            if edit.kind in {"add_fact", "remove_fact"}:
                obj = cls._binding(bindings, edit.object_slot)
                fact = (subject, edit.relation, obj)
                facts.add(fact) if edit.kind == "add_fact" else facts.discard(fact)
            elif edit.kind == "delete_number":
                numbers.pop((subject, edit.relation), None)
            elif edit.kind == "set_from_slot":
                numbers[(subject, edit.relation)] = int(cls._binding(bindings, edit.object_slot))
            elif edit.kind == "add_const":
                key = (subject, edit.relation)
                if key not in numbers:
                    raise ValueError("missing numeric state")
                numbers[key] += int(edit.delta or 0)
            elif edit.kind == "mul_const":
                key = (subject, edit.relation)
                if key not in numbers:
                    raise ValueError("missing numeric state")
                numbers[key] *= int(edit.factor or 1)
            else:
                raise ValueError(f"unknown edit {edit.kind}")
        return World.from_parts(facts, numbers)

    def apply(self, text: str, world: World) -> ApplyResult:
        rows = self._rank(text)
        if not rows or rows[0][0] < self.threshold:
            self.abstentions += 1
            return ApplyResult(False, "abstain-unknown-surface", None, world, rows[0][0] if rows else 0.0)
        if len(rows) > 1 and rows[0][0] - rows[1][0] < self.margin and rows[0][1].program_id != rows[1][1].program_id:
            self.abstentions += 1
            return ApplyResult(False, "abstain-ambiguous-program", None, world, rows[0][0])
        score, program, bindings, mechanism = rows[0]
        if not bindings:
            self.abstentions += 1
            return ApplyResult(False, "abstain-no-bindings", None, world, score)
        try:
            updated = self._execute(world, program, bindings)
        except (ValueError, TypeError):
            self.abstentions += 1
            return ApplyResult(False, "abstain-invalid-state", program.program_id, world, score)
        self.applied_episodes += 1
        self.schema_compositions += int(mechanism == "composed-surface-schema")
        return ApplyResult(True, mechanism, program.program_id, updated, score)

    @staticmethod
    def _render_pattern(pattern: str, bindings: Mapping[int, str]) -> str:
        return _SLOT.sub(lambda match: bindings.get(int(match.group(1)), ""), pattern)

    def explain(self, world: World) -> str:
        sentences: list[str] = []
        for subject, relation, obj in sorted(world.facts):
            candidates = []
            for program in self.programs.values():
                for edit in program.edits:
                    if edit.kind == "add_fact" and edit.relation == relation and edit.object_slot is not None:
                        for pattern in program.patterns:
                            candidates.append((len(pattern), pattern, edit))
            if not candidates:
                continue
            _length, pattern, edit = min(candidates, key=lambda row: (row[0], row[1]))
            sentences.append(self._render_pattern(pattern, {edit.subject_slot: subject, edit.object_slot: obj}))
        for subject, relation, value in world.numbers:
            sentences.append(f"{subject}の{relation}は{value}である")
        if sentences:
            self.verbalizations += 1
        return "。".join(sentences) + ("。" if sentences else "")

    def plan(self, world: World, goal: World, action_texts: Iterable[str], *, max_depth: int = 6) -> PlanResult:
        actions = tuple(action_texts)
        queue = deque([(world, ())])
        seen = {world}
        expanded = 0
        while queue:
            current, path = queue.popleft()
            if goal.facts.issubset(current.facts) and all(current.number_map().get(k) == v for k, v in goal.number_map().items()):
                return PlanResult(True, path, current, expanded)
            if len(path) >= max_depth:
                continue
            expanded += 1
            for action in actions:
                result = self.apply(action, current)
                if not result.accepted or result.world in seen:
                    continue
                seen.add(result.world)
                queue.append((result.world, path + (action,)))
        return PlanResult(False, (), world, expanded)

    def report(self) -> dict[str, object]:
        return {
            "programs": len(self.programs),
            "surfaces": sum(len(p.patterns) for p in self.programs.values()),
            "training_episodes": self.training_episodes,
            "applied_episodes": self.applied_episodes,
            "abstentions": self.abstentions,
            "schema_compositions": self.schema_compositions,
            "verbalizations": self.verbalizations,
            "last_candidates": self.last_candidates,
            "last_feature_reads": self.last_feature_reads,
            "serialized_bytes": len(self.to_bytes()),
            "shared_program_bank": True,
            "bidirectional_surface_schema": True,
            "task_names_supplied": False,
            "transformer_used": False,
            "dense_attention_used": False,
        }

    def to_bytes(self) -> bytes:
        return zlib.compress(pickle.dumps(self, protocol=5), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseGeneralLearner":
        value = pickle.loads(zlib.decompress(data))
        if not isinstance(value, cls):
            raise TypeError("invalid sparse general learner")
        return value
