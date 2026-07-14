from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import inf
from typing import Callable, Iterable, Mapping, Sequence


Distinction = tuple[str, str]


@dataclass(frozen=True)
class ExecutableComponent:
    name: str
    bits: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("component name must not be empty")
        if self.bits < 0:
            raise ValueError("component bits must be non-negative")


@dataclass(frozen=True)
class GrammarProbe:
    name: str
    components: frozenset[str]
    wrapper_bits: int
    operations: int
    peak_memory: int
    separated_pairs: frozenset[Distinction]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("probe name must not be empty")
        if min(self.wrapper_bits, self.operations, self.peak_memory) < 0:
            raise ValueError("probe resources must be non-negative")
        if not self.separated_pairs:
            raise ValueError("a theory probe must separate at least one pair")
        normalized = frozenset(tuple(sorted(pair)) for pair in self.separated_pairs)
        if normalized != self.separated_pairs:
            raise ValueError("separated pairs must use sorted endpoints")


@dataclass(frozen=True)
class ProbeGrammar:
    components: tuple[ExecutableComponent, ...]
    probes: tuple[GrammarProbe, ...]
    all_pairs: frozenset[Distinction]
    runtime_bits: int = 0

    def __post_init__(self) -> None:
        if self.runtime_bits < 0:
            raise ValueError("runtime bits must be non-negative")
        component_names = [component.name for component in self.components]
        probe_names = [probe.name for probe in self.probes]
        if len(component_names) != len(set(component_names)):
            raise ValueError("component names must be unique")
        if len(probe_names) != len(set(probe_names)):
            raise ValueError("probe names must be unique")
        available = set(component_names)
        for probe in self.probes:
            unknown = set(probe.components) - available
            if unknown:
                raise ValueError(f"unknown components: {sorted(unknown)}")
            if not probe.separated_pairs <= self.all_pairs:
                raise ValueError("probe separates a pair outside the declared universe")

    @property
    def component_map(self) -> dict[str, ExecutableComponent]:
        return {component.name: component for component in self.components}

    @property
    def probe_map(self) -> dict[str, GrammarProbe]:
        return {probe.name: probe for probe in self.probes}


@dataclass(frozen=True)
class ProbeBundleSelection:
    probes: tuple[str, ...]
    executable_bits: int
    isolated_bits: int
    operations: int
    peak_memory: int
    separated_pairs: frozenset[Distinction]
    all_pairs: frozenset[Distinction]

    @property
    def complete(self) -> bool:
        return self.separated_pairs == self.all_pairs


@dataclass(frozen=True)
class ObservationalPruningCounterexample:
    current_histories: tuple[str, ...]
    unseen_history: str
    probes: tuple[str, ...]
    responses: Mapping[tuple[str, str], str]

    def current_signatures_equal(self) -> bool:
        left, right = self.probes
        return all(
            self.responses[(history, left)] == self.responses[(history, right)]
            for history in self.current_histories
        )

    def unseen_signatures_differ(self) -> bool:
        left, right = self.probes
        return (
            self.responses[(self.unseen_history, left)]
            != self.responses[(self.unseen_history, right)]
        )


def _selected_probes(grammar: ProbeGrammar, probe_names: Iterable[str]) -> tuple[GrammarProbe, ...]:
    names = tuple(sorted(set(probe_names)))
    unknown = set(names) - set(grammar.probe_map)
    if unknown:
        raise ValueError(f"unknown probes: {sorted(unknown)}")
    return tuple(grammar.probe_map[name] for name in names)


def shared_executable_bits(grammar: ProbeGrammar, probe_names: Iterable[str]) -> int:
    probes = _selected_probes(grammar, probe_names)
    if not probes:
        return 0
    components = frozenset(
        component
        for probe in probes
        for component in probe.components
    )
    return (
        grammar.runtime_bits
        + sum(grammar.component_map[name].bits for name in components)
        + sum(probe.wrapper_bits for probe in probes)
    )


def isolated_executable_bits(grammar: ProbeGrammar, probe_names: Iterable[str]) -> int:
    probes = _selected_probes(grammar, probe_names)
    return sum(
        grammar.runtime_bits
        + sum(grammar.component_map[name].bits for name in probe.components)
        + probe.wrapper_bits
        for probe in probes
    )


def separation_coverage(
    grammar: ProbeGrammar,
    probe_names: Iterable[str],
) -> frozenset[Distinction]:
    probes = _selected_probes(grammar, probe_names)
    return frozenset().union(*(probe.separated_pairs for probe in probes)) if probes else frozenset()


def _selection(grammar: ProbeGrammar, probe_names: Iterable[str]) -> ProbeBundleSelection:
    probes = _selected_probes(grammar, probe_names)
    names = tuple(probe.name for probe in probes)
    return ProbeBundleSelection(
        names,
        shared_executable_bits(grammar, names),
        isolated_executable_bits(grammar, names),
        sum(probe.operations for probe in probes),
        max((probe.peak_memory for probe in probes), default=0),
        separation_coverage(grammar, names),
        grammar.all_pairs,
    )


def exact_probe_bundle(
    grammar: ProbeGrammar,
    *,
    accounting: str = "shared",
) -> ProbeBundleSelection:
    if accounting not in {"shared", "isolated"}:
        raise ValueError("accounting must be shared or isolated")
    best: tuple[tuple[int, int, int, int, tuple[str, ...]], ProbeBundleSelection] | None = None
    probes = grammar.probes
    for size in range(len(probes) + 1):
        for subset in combinations(probes, size):
            selection = _selection(grammar, (probe.name for probe in subset))
            if not selection.complete:
                continue
            primary = (
                selection.executable_bits
                if accounting == "shared"
                else selection.isolated_bits
            )
            key = (
                primary,
                selection.operations,
                selection.peak_memory,
                len(selection.probes),
                selection.probes,
            )
            if best is None or key < best[0]:
                best = key, selection
    if best is None:
        return _selection(grammar, ())
    return best[1]


def myopic_marginal_greedy(grammar: ProbeGrammar) -> ProbeBundleSelection:
    selected: set[str] = set()
    covered: set[Distinction] = set()
    remaining = {probe.name for probe in grammar.probes}
    while frozenset(covered) != grammar.all_pairs and remaining:
        current_bits = shared_executable_bits(grammar, selected)
        candidates: list[tuple[float, int, str, frozenset[Distinction]]] = []
        for name in remaining:
            new_pairs = grammar.probe_map[name].separated_pairs - covered
            marginal_bits = shared_executable_bits(grammar, selected | {name}) - current_bits
            ratio = inf if marginal_bits == 0 and new_pairs else len(new_pairs) / max(marginal_bits, 1)
            candidates.append((-ratio, marginal_bits, name, new_pairs))
        _negative_ratio, _marginal_bits, chosen, new_pairs = min(candidates)
        if not new_pairs:
            break
        selected.add(chosen)
        remaining.remove(chosen)
        covered.update(new_pairs)
    return _selection(grammar, selected)


def is_monotone_submodular(
    ground: Sequence[str],
    value: Callable[[frozenset[str]], int],
) -> bool:
    items = tuple(ground)
    subsets = [
        frozenset(subset)
        for size in range(len(items) + 1)
        for subset in combinations(items, size)
    ]
    for left in subsets:
        for right in subsets:
            if left <= right and value(left) > value(right):
                return False
            if not left <= right:
                continue
            for item in set(items) - right:
                left_gain = value(left | {item}) - value(left)
                right_gain = value(right | {item}) - value(right)
                if left_gain < right_gain:
                    return False
    return True


def make_two_distinction_fixture() -> ProbeGrammar:
    pairs = frozenset({("r0", "r1"), ("r2", "r3")})
    components = (
        ExecutableComponent("shared-core", 10),
        ExecutableComponent("shared-a", 1),
        ExecutableComponent("shared-b", 1),
        ExecutableComponent("direct-a", 7),
        ExecutableComponent("direct-b", 7),
    )
    probes = (
        GrammarProbe("shared-probe-a", frozenset({"shared-core", "shared-a"}), 0, 2, 2, frozenset({("r0", "r1")})),
        GrammarProbe("shared-probe-b", frozenset({"shared-core", "shared-b"}), 0, 2, 2, frozenset({("r2", "r3")})),
        GrammarProbe("direct-probe-a", frozenset({"direct-a"}), 0, 1, 1, frozenset({("r0", "r1")})),
        GrammarProbe("direct-probe-b", frozenset({"direct-b"}), 0, 1, 1, frozenset({("r2", "r3")})),
    )
    return ProbeGrammar(components, probes, pairs)


def make_greedy_counterexample(n: int, setup_bits: int | None = None) -> ProbeGrammar:
    if n < 2:
        raise ValueError("n must be at least two")
    setup = n * n if setup_bits is None else setup_bits
    if setup <= 1:
        raise ValueError("setup bits must exceed one")
    pairs = frozenset((f"a{index}", f"b{index}") for index in range(n))
    components: list[ExecutableComponent] = [ExecutableComponent("shared-core", setup)]
    probes: list[GrammarProbe] = []
    for index, pair in enumerate(sorted(pairs)):
        shared_leaf = f"shared-leaf-{index}"
        direct = f"direct-component-{index}"
        components.append(ExecutableComponent(shared_leaf, 1))
        components.append(ExecutableComponent(direct, setup - 1))
        probes.append(
            GrammarProbe(
                f"shared-{index}",
                frozenset({"shared-core", shared_leaf}),
                0,
                2,
                2,
                frozenset({pair}),
            )
        )
        probes.append(
            GrammarProbe(
                f"direct-{index}",
                frozenset({direct}),
                0,
                1,
                1,
                frozenset({pair}),
            )
        )
    return ProbeGrammar(tuple(components), tuple(probes), pairs)


def observational_probe_groups(
    current_histories: Sequence[str],
    probes: Sequence[str],
    responses: Mapping[tuple[str, str], str],
) -> tuple[tuple[str, ...], ...]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for probe in probes:
        signature = tuple(responses[(history, probe)] for history in current_histories)
        groups.setdefault(signature, []).append(probe)
    return tuple(sorted(tuple(sorted(group)) for group in groups.values()))


def make_observational_pruning_counterexample() -> ObservationalPruningCounterexample:
    current = ("h0", "h1")
    unseen = "h2"
    probes = ("probe-left", "probe-right")
    responses = {
        ("h0", "probe-left"): "0",
        ("h0", "probe-right"): "0",
        ("h1", "probe-left"): "1",
        ("h1", "probe-right"): "1",
        ("h2", "probe-left"): "0",
        ("h2", "probe-right"): "1",
    }
    return ObservationalPruningCounterexample(current, unseen, probes, responses)


def run_theory_gate() -> dict[str, object]:
    fixture = make_two_distinction_fixture()
    shared_exact = exact_probe_bundle(fixture, accounting="shared")
    isolated_exact = exact_probe_bundle(fixture, accounting="isolated")

    adversarial = make_greedy_counterexample(6)
    adversarial_exact = exact_probe_bundle(adversarial, accounting="shared")
    adversarial_greedy = myopic_marginal_greedy(adversarial)
    greedy_ratio = adversarial_greedy.executable_bits / adversarial_exact.executable_bits

    names = tuple(probe.name for probe in fixture.probes)
    code_submodular = is_monotone_submodular(
        names,
        lambda selected: shared_executable_bits(fixture, selected),
    )
    coverage_submodular = is_monotone_submodular(
        names,
        lambda selected: len(separation_coverage(fixture, selected)),
    )

    pruning = make_observational_pruning_counterexample()
    current_groups = observational_probe_groups(
        pruning.current_histories,
        pruning.probes,
        pruning.responses,
    )

    checks = {
        "shared_code_is_monotone_submodular": code_submodular,
        "separation_is_monotone_submodular": coverage_submodular,
        "true_shared_accounting_selects_shared_bundle": shared_exact.probes
        == ("shared-probe-a", "shared-probe-b")
        and shared_exact.executable_bits == 12,
        "isolated_accounting_reverses_choice": isolated_exact.probes
        == ("direct-probe-a", "direct-probe-b")
        and isolated_exact.isolated_bits == 14,
        "exact_adversarial_solver_selects_shared_family": all(
            name.startswith("shared-") for name in adversarial_exact.probes
        ),
        "myopic_greedy_selects_direct_family": all(
            name.startswith("direct-") for name in adversarial_greedy.probes
        ),
        "greedy_counterexample_ratio_is_large": greedy_ratio >= 5.0,
        "current_observational_quotient_collapses_probes": current_groups
        == (("probe-left", "probe-right"),),
        "prospective_unseen_row_separates_collapsed_probes": pruning.current_signatures_equal()
        and pruning.unseen_signatures_differ(),
    }
    return {
        "capability_id": "CAP-GEN-002-SPG-001",
        "claim": (
            "finite theory gate for shared executable probe cost, pair-separation coverage, "
            "and failure of isolated accounting and one-step marginal greedy"
        ),
        "claim_boundary": (
            "submodular-cost cover, active distinguishing tests, and observational quotienting "
            "are prior art; joint raw acquisition of the shared probe grammar remains an "
            "unverified novelty candidate"
        ),
        "two_distinction_fixture": {
            "shared_optimum": shared_exact.probes,
            "shared_optimum_bits": shared_exact.executable_bits,
            "isolated_optimum": isolated_exact.probes,
            "isolated_optimum_bits": isolated_exact.isolated_bits,
        },
        "greedy_counterexample": {
            "n": 6,
            "setup_bits": 36,
            "exact_probes": adversarial_exact.probes,
            "exact_bits": adversarial_exact.executable_bits,
            "greedy_probes": adversarial_greedy.probes,
            "greedy_bits": adversarial_greedy.executable_bits,
            "ratio": greedy_ratio,
        },
        "submodularity": {
            "shared_code": code_submodular,
            "separation_coverage": coverage_submodular,
        },
        "prospective_pruning_counterexample": {
            "current_groups": current_groups,
            "current_signatures_equal": pruning.current_signatures_equal(),
            "unseen_signatures_differ": pruning.unseen_signatures_differ(),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_theory_gate(), ensure_ascii=False, indent=2, sort_keys=True))
