from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Callable, FrozenSet, Iterable, Sequence

Symbol = int
Fact = tuple[Symbol, ...]


class SymbolTable:
    """One canonical symbol table shared by every capability."""

    def __init__(self) -> None:
        self._to_id: dict[str, int] = {}
        self._to_text: list[str] = []

    def intern(self, text: str) -> int:
        existing = self._to_id.get(text)
        if existing is not None:
            return existing
        symbol = len(self._to_text)
        self._to_id[text] = symbol
        self._to_text.append(text)
        return symbol

    def fact(self, *items: str) -> Fact:
        return tuple(self.intern(item) for item in items)

    def decode(self, symbol: int) -> str:
        return self._to_text[symbol]

    @property
    def count(self) -> int:
        return len(self._to_text)

    @property
    def runtime_bits_per_symbol(self) -> int:
        return max(1, (max(1, self.count) - 1).bit_length())


@dataclass(frozen=True)
class State:
    facts: FrozenSet[Fact]
    output: tuple[Symbol, ...] = ()
    trace: tuple[str, ...] = ()


@dataclass(frozen=True)
class Rule:
    """A single sparse graph rewrite.

    New capabilities are programs made from the same primitive:
    match facts, delete facts, add facts, optionally emit symbols.
    """

    name: str
    require: FrozenSet[Fact] = frozenset()
    forbid: FrozenSet[Fact] = frozenset()
    add: FrozenSet[Fact] = frozenset()
    remove: FrozenSet[Fact] = frozenset()
    emit: tuple[Symbol, ...] = ()
    cost_bits: int = 1

    def applicable(self, state: State) -> bool:
        return self.require.issubset(state.facts) and self.forbid.isdisjoint(state.facts)

    def apply(self, state: State) -> State:
        return State(
            facts=frozenset((state.facts - self.remove) | self.add),
            output=state.output + self.emit,
            trace=state.trace + (self.name,),
        )


@dataclass(frozen=True)
class SearchResult:
    state: State
    objective_bits: int
    expanded_states: int
    generated_states: int
    rule_checks: int
    rule_applications: int
    peak_frontier: int


class IndexedProgram:
    """Index rewrites by one required fact to avoid scanning all rules."""

    def __init__(self, rules: Sequence[Rule]) -> None:
        self.rules = tuple(rules)
        self._unconditional: list[int] = []
        self._by_anchor: dict[Fact, list[int]] = {}

        for index, rule in enumerate(self.rules):
            if not rule.require:
                self._unconditional.append(index)
                continue
            anchor = min(rule.require, key=lambda fact: (len(fact), fact))
            self._by_anchor.setdefault(anchor, []).append(index)

    def candidate_indices(self, state: State) -> Iterable[int]:
        seen: set[int] = set()
        for index in self._unconditional:
            seen.add(index)
            yield index
        for fact in state.facts:
            for index in self._by_anchor.get(fact, ()):
                if index not in seen:
                    seen.add(index)
                    yield index


def shortest_program(
    initial: State,
    program: IndexedProgram,
    goal: Callable[[State], bool],
    *,
    max_expanded: int = 100_000,
) -> SearchResult:
    """Find the minimum-description execution trace satisfying a goal."""

    serial = count()
    frontier: list[tuple[int, int, State]] = [(0, next(serial), initial)]
    best: dict[tuple[FrozenSet[Fact], tuple[Symbol, ...]], int] = {
        (initial.facts, initial.output): 0
    }
    expanded = 0
    generated = 0
    checks = 0
    applications = 0
    peak_frontier = 1

    while frontier:
        objective, _, state = heappop(frontier)
        key = (state.facts, state.output)
        if objective != best.get(key):
            continue
        if goal(state):
            return SearchResult(
                state=state,
                objective_bits=objective,
                expanded_states=expanded,
                generated_states=generated,
                rule_checks=checks,
                rule_applications=applications,
                peak_frontier=peak_frontier,
            )

        expanded += 1
        if expanded > max_expanded:
            raise RuntimeError("search limit exceeded")

        for index in program.candidate_indices(state):
            checks += 1
            rule = program.rules[index]
            if not rule.applicable(state):
                continue
            applications += 1
            next_state = rule.apply(state)
            next_objective = objective + rule.cost_bits
            next_key = (next_state.facts, next_state.output)
            if next_objective < best.get(next_key, 1 << 60):
                best[next_key] = next_objective
                heappush(frontier, (next_objective, next(serial), next_state))
                generated += 1

        peak_frontier = max(peak_frontier, len(frontier))

    raise RuntimeError("no satisfying program found")
