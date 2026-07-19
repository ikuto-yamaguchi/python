from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from typing import Hashable, Iterable, Mapping, MutableMapping, Sequence

Scalar = int | float | str | bool | None
WorldState = dict[str, dict[str, Scalar]]


def clone_state(state: Mapping[str, Mapping[str, Scalar]]) -> WorldState:
    return {entity: dict(slots) for entity, slots in state.items()}


@dataclass(frozen=True, order=True)
class SlotEdit:
    """One reversible state edit over an abstract entity variable."""

    entity_var: int
    slot: str
    operation: str
    argument: Scalar
    inverse_argument: Scalar

    def apply(self, state: MutableMapping[str, dict[str, Scalar]], bindings: Sequence[str]) -> None:
        entity = bindings[self.entity_var]
        slots = state.setdefault(entity, {})
        if self.operation == "add":
            current = slots.get(self.slot)
            if not isinstance(current, (int, float)) or isinstance(current, bool):
                raise ValueError(f"slot {entity}.{self.slot} is not numeric")
            slots[self.slot] = current + self.argument  # type: ignore[operator]
        elif self.operation == "set":
            slots[self.slot] = self.argument
        elif self.operation == "create":
            if self.slot in slots:
                raise ValueError(f"slot {entity}.{self.slot} already exists")
            slots[self.slot] = self.argument
        elif self.operation == "delete":
            if slots.get(self.slot) != self.inverse_argument:
                raise ValueError(f"slot {entity}.{self.slot} does not match delete precondition")
            del slots[self.slot]
        else:
            raise ValueError(f"unknown operation: {self.operation}")

    def apply_inverse(
        self, state: MutableMapping[str, dict[str, Scalar]], bindings: Sequence[str]
    ) -> None:
        entity = bindings[self.entity_var]
        slots = state.setdefault(entity, {})
        if self.operation == "add":
            current = slots.get(self.slot)
            if not isinstance(current, (int, float)) or isinstance(current, bool):
                raise ValueError(f"slot {entity}.{self.slot} is not numeric")
            slots[self.slot] = current + self.inverse_argument  # type: ignore[operator]
        elif self.operation == "set":
            slots[self.slot] = self.inverse_argument
        elif self.operation == "create":
            if slots.get(self.slot) != self.argument:
                raise ValueError(f"slot {entity}.{self.slot} does not match created value")
            del slots[self.slot]
        elif self.operation == "delete":
            if self.slot in slots:
                raise ValueError(f"slot {entity}.{self.slot} already exists")
            slots[self.slot] = self.inverse_argument
        else:
            raise ValueError(f"unknown operation: {self.operation}")


@dataclass
class ReversibleEventProgram:
    program_id: str
    edits: tuple[SlotEdit, ...]
    support: int = 1
    provenance: set[Hashable] = field(default_factory=set)

    @property
    def arity(self) -> int:
        if not self.edits:
            return 0
        return 1 + max(edit.entity_var for edit in self.edits)

    def forward(self, state: Mapping[str, Mapping[str, Scalar]], bindings: Sequence[str]) -> WorldState:
        self._validate_bindings(bindings)
        result = clone_state(state)
        for edit in self.edits:
            edit.apply(result, bindings)
        return result

    def inverse(self, state: Mapping[str, Mapping[str, Scalar]], bindings: Sequence[str]) -> WorldState:
        self._validate_bindings(bindings)
        result = clone_state(state)
        for edit in reversed(self.edits):
            edit.apply_inverse(result, bindings)
        return result

    def _validate_bindings(self, bindings: Sequence[str]) -> None:
        if len(bindings) != self.arity:
            raise ValueError(f"expected {self.arity} bindings, got {len(bindings)}")
        if len(set(bindings)) != len(bindings):
            raise ValueError("bindings must refer to distinct entities")

    def estimated_bytes(self) -> int:
        payload = {
            "id": self.program_id,
            "support": self.support,
            "edits": [edit.__dict__ for edit in self.edits],
        }
        return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


@dataclass(frozen=True)
class ProgramObservation:
    program_id: str
    bindings: tuple[str, ...]
    reused_existing_program: bool


class EventProgramBank:
    """Induces entity-name-invariant reversible programs from world-state changes."""

    def __init__(self) -> None:
        self._programs: dict[str, ReversibleEventProgram] = {}

    @property
    def programs(self) -> Mapping[str, ReversibleEventProgram]:
        return self._programs

    def observe_transition(
        self,
        before: Mapping[str, Mapping[str, Scalar]],
        after: Mapping[str, Mapping[str, Scalar]],
        *,
        source_id: Hashable | None = None,
    ) -> ProgramObservation:
        bindings, edits = self._abstract_transition(before, after)
        fingerprint = self._fingerprint(edits)
        reused = fingerprint in self._programs
        if reused:
            program = self._programs[fingerprint]
            program.support += 1
        else:
            program = ReversibleEventProgram(program_id=fingerprint, edits=edits)
            self._programs[fingerprint] = program
        if source_id is not None:
            program.provenance.add(source_id)
        return ProgramObservation(
            program_id=fingerprint,
            bindings=bindings,
            reused_existing_program=reused,
        )

    def get(self, program_id: str) -> ReversibleEventProgram:
        return self._programs[program_id]

    def estimated_bytes(self) -> int:
        return sum(program.estimated_bytes() for program in self._programs.values())

    @staticmethod
    def _abstract_transition(
        before: Mapping[str, Mapping[str, Scalar]],
        after: Mapping[str, Mapping[str, Scalar]],
    ) -> tuple[tuple[str, ...], tuple[SlotEdit, ...]]:
        changed_entities: list[str] = []
        for entity in sorted(set(before) | set(after)):
            if dict(before.get(entity, {})) != dict(after.get(entity, {})):
                changed_entities.append(entity)
        entity_index = {entity: index for index, entity in enumerate(changed_entities)}
        edits: list[SlotEdit] = []
        for entity in changed_entities:
            before_slots = before.get(entity, {})
            after_slots = after.get(entity, {})
            for slot in sorted(set(before_slots) | set(after_slots)):
                old_present = slot in before_slots
                new_present = slot in after_slots
                old = before_slots.get(slot)
                new = after_slots.get(slot)
                if old_present and new_present and old == new:
                    continue
                if not old_present and new_present:
                    edits.append(SlotEdit(entity_index[entity], slot, "create", new, None))
                elif old_present and not new_present:
                    edits.append(SlotEdit(entity_index[entity], slot, "delete", None, old))
                elif (
                    isinstance(old, (int, float))
                    and not isinstance(old, bool)
                    and isinstance(new, (int, float))
                    and not isinstance(new, bool)
                ):
                    delta = new - old
                    edits.append(SlotEdit(entity_index[entity], slot, "add", delta, -delta))
                else:
                    edits.append(SlotEdit(entity_index[entity], slot, "set", new, old))
        if not edits:
            raise ValueError("transition contains no observable state change")
        return tuple(changed_entities), tuple(edits)

    @staticmethod
    def _fingerprint(edits: Iterable[SlotEdit]) -> str:
        canonical = [edit.__dict__ for edit in edits]
        raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.blake2s(raw.encode("utf-8"), digest_size=10).hexdigest()
        return f"ravel:{digest}"


@dataclass(frozen=True)
class MacroProgram:
    macro_id: str
    program_ids: tuple[str, ...]
    support: int

    @property
    def primitive_steps(self) -> int:
        return len(self.program_ids)

    @property
    def active_steps(self) -> int:
        return 1


class RecursiveMacroCompiler:
    """Compiles repeated program chains into one reusable hierarchical instruction."""

    def __init__(self, bank: EventProgramBank, *, min_support: int = 3, max_length: int = 8) -> None:
        if min_support < 2:
            raise ValueError("min_support must be at least 2")
        if max_length < 2:
            raise ValueError("max_length must be at least 2")
        self.bank = bank
        self.min_support = min_support
        self.max_length = max_length
        self._counts: Counter[tuple[str, ...]] = Counter()
        self._macros: dict[tuple[str, ...], MacroProgram] = {}

    @property
    def macros(self) -> Mapping[tuple[str, ...], MacroProgram]:
        return self._macros

    def observe_sequence(self, program_ids: Sequence[str]) -> tuple[MacroProgram, ...]:
        for program_id in program_ids:
            self.bank.get(program_id)
        created: list[MacroProgram] = []
        upper = min(self.max_length, len(program_ids))
        for length in range(2, upper + 1):
            for start in range(0, len(program_ids) - length + 1):
                chain = tuple(program_ids[start : start + length])
                self._counts[chain] += 1
                if self._counts[chain] == self.min_support:
                    macro = self._build_macro(chain, self._counts[chain])
                    self._macros[chain] = macro
                    created.append(macro)
                elif chain in self._macros:
                    old = self._macros[chain]
                    self._macros[chain] = MacroProgram(old.macro_id, chain, self._counts[chain])
        return tuple(created)

    def longest_macro_prefix(self, program_ids: Sequence[str]) -> MacroProgram | None:
        matches = [
            macro
            for chain, macro in self._macros.items()
            if len(chain) <= len(program_ids) and tuple(program_ids[: len(chain)]) == chain
        ]
        return max(matches, key=lambda macro: macro.primitive_steps, default=None)

    def execute_forward(
        self,
        macro: MacroProgram,
        state: Mapping[str, Mapping[str, Scalar]],
        bindings_per_program: Sequence[Sequence[str]],
    ) -> WorldState:
        if len(bindings_per_program) != len(macro.program_ids):
            raise ValueError("one binding sequence is required per primitive program")
        result = clone_state(state)
        for program_id, bindings in zip(macro.program_ids, bindings_per_program, strict=True):
            result = self.bank.get(program_id).forward(result, bindings)
        return result

    def execute_inverse(
        self,
        macro: MacroProgram,
        state: Mapping[str, Mapping[str, Scalar]],
        bindings_per_program: Sequence[Sequence[str]],
    ) -> WorldState:
        if len(bindings_per_program) != len(macro.program_ids):
            raise ValueError("one binding sequence is required per primitive program")
        result = clone_state(state)
        for program_id, bindings in reversed(
            list(zip(macro.program_ids, bindings_per_program, strict=True))
        ):
            result = self.bank.get(program_id).inverse(result, bindings)
        return result

    @staticmethod
    def _build_macro(chain: tuple[str, ...], support: int) -> MacroProgram:
        raw = "|".join(chain).encode("utf-8")
        digest = hashlib.blake2s(raw, digest_size=10).hexdigest()
        return MacroProgram(macro_id=f"macro:{digest}", program_ids=chain, support=support)


def explanatory_work(
    *,
    eliminated_residual_bits: int,
    stored_program_bytes: int,
    active_execution_cost: int,
    contradiction_cost: int = 0,
) -> float:
    """RAVEL's selection score for a reusable explanation."""

    denominator = stored_program_bytes + active_execution_cost + contradiction_cost
    if eliminated_residual_bits < 0:
        raise ValueError("eliminated_residual_bits must be non-negative")
    if denominator <= 0:
        raise ValueError("total cost must be positive")
    return eliminated_residual_bits / denominator
