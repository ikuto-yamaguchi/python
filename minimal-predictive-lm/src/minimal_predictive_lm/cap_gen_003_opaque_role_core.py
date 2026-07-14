from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

RawRecord = str
Pair = tuple[str, str]


@dataclass(frozen=True)
class OpaqueRecord:
    tag: str
    left: str
    right: str


@dataclass(frozen=True)
class RoleInterpretation:
    topology_tag: str | None
    action_tag: str | None
    topology_pairs: tuple[Pair, ...]
    action_pairs: tuple[Pair, ...]
    orientation_candidates: tuple[int, ...]
    complete_topology: bool
    valid: bool
    reason: str

    @property
    def role_mapping(self) -> tuple[tuple[str, str], ...]:
        rows: list[tuple[str, str]] = []
        if self.topology_tag is not None:
            rows.append((self.topology_tag, "topology"))
        if self.action_tag is not None:
            rows.append((self.action_tag, "action"))
        return tuple(sorted(rows))

    @property
    def unique_orientation(self) -> bool:
        return len(self.orientation_candidates) == 1


def parse_record(raw: RawRecord) -> OpaqueRecord:
    parts = raw.strip().split()
    if len(parts) != 3:
        raise ValueError(f"opaque records require exactly three fields: {raw!r}")
    if parts[0] in {"EDGE", "STEP", "RESET", "FREEZE"}:
        raise ValueError("semantic event labels and boundary markers are forbidden")
    return OpaqueRecord(*parts)


def normalize_edge(left: str, right: str) -> Pair:
    if left == right:
        raise ValueError("self edges are unsupported")
    return (left, right) if left < right else (right, left)


def adjacency(edges: Iterable[Pair]) -> dict[str, set[str]]:
    rows: dict[str, set[str]] = {}
    for left, right in edges:
        rows.setdefault(left, set()).add(right)
        rows.setdefault(right, set()).add(left)
    return rows


def graph_is_connected(edges: Iterable[Pair]) -> bool:
    rows = adjacency(edges)
    if not rows:
        return False
    pending = [next(iter(rows))]
    seen: set[str] = set()
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(rows[node] - seen)
    return len(seen) == len(rows)


def partial_cycle_is_possible(edges: Iterable[Pair]) -> bool:
    unique = {normalize_edge(left, right) for left, right in edges}
    if not unique:
        return True
    rows = adjacency(unique)
    if not graph_is_connected(unique):
        return False
    if any(len(neighbours) > 2 for neighbours in rows.values()):
        return False
    edge_count = len(unique)
    node_count = len(rows)
    if edge_count > node_count:
        return False
    if edge_count == node_count and not all(
        len(neighbours) == 2 for neighbours in rows.values()
    ):
        return False
    return True


def is_complete_simple_cycle(edges: Iterable[Pair]) -> bool:
    unique = {normalize_edge(left, right) for left, right in edges}
    rows = adjacency(unique)
    return (
        len(rows) >= 3
        and len(unique) == len(rows)
        and graph_is_connected(unique)
        and all(len(neighbours) == 2 for neighbours in rows.values())
    )


def cycle_orders(edges: Iterable[Pair]) -> tuple[tuple[str, ...], ...]:
    unique = {normalize_edge(left, right) for left, right in edges}
    if not is_complete_simple_cycle(unique):
        return ()
    rows = adjacency(unique)
    start = min(rows)
    orders: list[tuple[str, ...]] = []
    for first in sorted(rows[start]):
        order = [start]
        previous = start
        current = first
        while current != start:
            if current in order:
                break
            order.append(current)
            candidates = rows[current] - {previous}
            if len(candidates) != 1:
                break
            previous, current = current, next(iter(candidates))
        if current == start and len(order) == len(rows):
            orders.append(tuple(order))
    unique_orders = tuple(dict.fromkeys(orders))
    return unique_orders if len(unique_orders) == 2 else ()


def successor_map(order: Sequence[str]) -> dict[str, str]:
    return {
        state: order[(index + 1) % len(order)]
        for index, state in enumerate(order)
    }


def transition_table(order: Sequence[str]) -> tuple[Pair, ...]:
    return tuple(sorted(successor_map(order).items()))


def exact_accuracy(predictions: Iterable[Pair], truth: Iterable[Pair]) -> float:
    predicted = dict(predictions)
    expected = dict(truth)
    if not expected:
        return 0.0
    return (
        sum(predicted.get(source) == target for source, target in expected.items())
        / len(expected)
    )


def action_table_is_functional(actions: Iterable[Pair]) -> bool:
    observed: dict[str, str] = {}
    for source, target in actions:
        previous = observed.get(source)
        if previous is not None and previous != target:
            return False
        observed[source] = target
    return True


def orientation_candidates(
    topology_pairs: Iterable[Pair],
    action_pairs: Iterable[Pair],
) -> tuple[int, ...]:
    orders = cycle_orders(topology_pairs)
    if not orders or not action_table_is_functional(action_pairs):
        return ()
    observed = dict(action_pairs)
    nodes = set(orders[0])
    if any(
        source not in nodes or target not in nodes
        for source, target in observed.items()
    ):
        return ()
    candidates: list[int] = []
    for index, order in enumerate(orders):
        mapping = successor_map(order)
        if all(mapping[source] == target for source, target in observed.items()):
            candidates.append(index)
    return tuple(candidates)


def evaluate_assignment(
    records: Sequence[OpaqueRecord],
    topology_tag: str | None,
    action_tag: str | None,
) -> RoleInterpretation:
    topology = tuple(
        (record.left, record.right)
        for record in records
        if record.tag == topology_tag
    )
    actions = tuple(
        (record.left, record.right)
        for record in records
        if record.tag == action_tag
    )
    if topology_tag is not None and not partial_cycle_is_possible(topology):
        return RoleInterpretation(
            topology_tag, action_tag, topology, actions, (), False, False,
            "topology records cannot be a connected degree-two cycle prefix",
        )
    if not action_table_is_functional(actions):
        return RoleInterpretation(
            topology_tag, action_tag, topology, actions, (), False, False,
            "action records are not a deterministic transition table",
        )
    complete = topology_tag is not None and is_complete_simple_cycle(topology)
    if complete:
        candidates = orientation_candidates(topology, actions)
        if actions and not candidates:
            return RoleInterpretation(
                topology_tag, action_tag, topology, actions, (), True, False,
                "action records contradict every orientation of the topology",
            )
    else:
        candidates = ()
    return RoleInterpretation(
        topology_tag, action_tag, topology, actions, candidates, complete, True,
        "assignment remains structurally possible",
    )


def infer_role_interpretations(
    records: Sequence[OpaqueRecord],
) -> tuple[RoleInterpretation, ...]:
    tags = tuple(sorted({record.tag for record in records}))
    if not tags or len(tags) > 2:
        return ()
    candidates: list[RoleInterpretation] = []
    if len(tags) == 1:
        tag = tags[0]
        candidates.extend(
            (
                evaluate_assignment(records, tag, None),
                evaluate_assignment(records, None, tag),
            )
        )
    else:
        left, right = tags
        candidates.extend(
            (
                evaluate_assignment(records, left, right),
                evaluate_assignment(records, right, left),
            )
        )
    return tuple(candidate for candidate in candidates if candidate.valid)


def make_opaque_cycle_records(
    states: Sequence[str],
    *,
    topology_tag: str,
    action_tag: str,
    orientation: int,
    active_sources: Sequence[str] | None = None,
) -> tuple[tuple[RawRecord, ...], tuple[Pair, ...]]:
    if len(states) < 3:
        raise ValueError("at least three states are required")
    raw_cycle = tuple(
        (states[index], states[(index + 1) % len(states)])
        for index in range(len(states))
    )
    normalized = tuple(normalize_edge(left, right) for left, right in raw_cycle)
    orders = cycle_orders(normalized)
    if orientation not in (0, 1):
        raise ValueError("orientation must be zero or one")
    truth = transition_table(orders[orientation])
    mapping = dict(truth)
    sources = tuple(states) if active_sources is None else tuple(active_sources)
    topology_records = tuple(
        f"{topology_tag} {left} {right}" for left, right in normalized
    )
    action_records = tuple(
        f"{action_tag} {source} {mapping[source]}" for source in sources
    )
    return topology_records + action_records, truth


def make_opaque_path_records(
    states: Sequence[str],
    *,
    topology_tag: str,
) -> tuple[RawRecord, ...]:
    return tuple(
        f"{topology_tag} {states[index]} {states[index + 1]}"
        for index in range(len(states) - 1)
    )
