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
    """One sparse surface->latent-program->world executor.

    The same program bank and executor represent textbook fact acquisition, numeric
    state changes, causal interventions, multi-turn updates, and planning actions.
    It is intentionally small and grounded by before/after worlds; it is not an
    unrestricted language model.
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
        return sorted((a for a in atoms if len(a) >= 1 and a in clean), key=lambda x: (-len(x), x))

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
        added = sorted(after.facts - before.facts)
        removed = sorted(before.facts - after.facts)
        for subject, relation, obj in added:
            edits.append(Edit("add_fact", relation, cls._slot_for(subject, atoms), cls._slot_for(obj, atoms)))
        for subject, relation, obj in removed:
            edits.append(Edit("remove_fact", relation, cls._slot_for(subject, atoms), cls._slot_for(obj, atoms)))

        bnum = before.number_map()
        anum = after.number_map()
        for key in sorted(set(bnum) | set(anum)):
            old = bnum.get(key)
            new = anum.get(key)
            if old == new:
                continue
            subject, relation = key
            slot = cls._slot_for(subject, atoms)
            if new is None:
                edits.append(Edit("delete_number", relation, slot))
                continue
            if old is None:
                value_slot = cls._slot_for(str(new), atoms)
                edits.append(Edit("set_from_slot", relation, slot, value_slot))
                continue
            if new - old != 0 and str(abs(new - old)) in atoms:
                delta = new - old
                edits.append(Edit("add_const", relation, slot, delta=delta))
                continue
            if old != 0 and new % old == 0 and str(abs(new // old)) in atoms:
                edits.append(Edit("mul_const", relation, slot, factor=new // old))
                continue
            if str(new) in atoms:
                value_slot = cls._slot_for(str(new), atoms)
                edits.append(Edit("set_from_slot", relation, slot, value_slot))
                continue
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

    def _rank(self, text: str) -> list[tuple[float, Program, tuple[str, ...]]]:
        normalized = _clean(text)
        query = _ngrams(normalized)
        rows: list[tuple[float, Program, tuple[str, ...]]] = []
        reads = 0
        for program in self.programs.values():
            best_score = 0.0
            best_bindings: tuple[str, ...] = ()
            for pattern in program.patterns:
                matcher = self._compile(pattern).fullmatch(normalized)
                vector = _ngrams(pattern)
                reads += min(len(query), len(vector))
                if matcher:
                    bindings = tuple(matcher.groupdict().get(f"V{i}", "") for i in range(32))
                    while bindings and bindings[-1] == "":
                        bindings = bindings[:-1]
                    score = 1.0
                else:
                    bindings = ()
                    score = _cosine(query, vector)
                if score > best_score:
                    best_score, best_bindings = score, bindings
            rows.append((best_score, program, best_bindings))
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
                if edit.kind == "add_fact":
                    facts.add(fact)
                else:
                    facts.discard(fact)
            elif edit.kind == "delete_number":
                numbers.pop((subject, edit.relation), None)
            elif edit.kind == "set_from_slot":
                value = int(cls._binding(bindings, edit.object_slot))
                numbers[(subject, edit.relation)] = value
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
        score, program, bindings = rows[0]
        if not bindings:
            self.abstentions += 1
            return ApplyResult(False, "abstain-no-bindings", None, world, score)
        try:
            updated = self._execute(world, program, bindings)
        except (ValueError, TypeError):
            self.abstentions += 1
            return ApplyResult(False, "abstain-invalid-state", program.program_id, world, score)
        self.applied_episodes += 1
        return ApplyResult(True, "latent-program", program.program_id, updated, score)

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
            "last_candidates": self.last_candidates,
            "last_feature_reads": self.last_feature_reads,
            "serialized_bytes": len(self.to_bytes()),
            "shared_program_bank": True,
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
