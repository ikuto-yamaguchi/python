from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Mapping, Sequence


State = str
Surface = str
Environment = str


@dataclass(frozen=True)
class PassiveDecomposition:
    """One explanation of a raw trace.

    `actuation_positions` is intentionally latent.  The same raw trace can admit several
    incompatible assignments when no action marker, policy shift, or intervention record
    is observable.
    """

    raw_trace: tuple[str, ...]
    actuation_positions: frozenset[int]
    explanation: str


@dataclass(frozen=True)
class FiniteRegimeTable:
    """Exact finite table used after a predictive state quotient is available.

    The theory gate does not assume semantic action labels.  It sees surface strings,
    environment-indexed occurrence counts, a passive successor, and the successor observed
    after each surface.  Environments are policy regimes: the world mechanism must remain
    fixed while surface-selection frequencies may change.
    """

    states: tuple[State, ...]
    surfaces: tuple[Surface, ...]
    environments: tuple[Environment, ...]
    selection_counts: Mapping[tuple[Environment, State, Surface], int]
    passive_successor: Mapping[State, State]
    surface_successor: Mapping[tuple[State, Surface], State]

    def validate(self) -> None:
        if not self.states or not self.surfaces or not self.environments:
            raise ValueError("states, surfaces, and environments must be non-empty")
        state_set = set(self.states)
        for state in self.states:
            if self.passive_successor[state] not in state_set:
                raise ValueError("passive successor leaves the state set")
            for surface in self.surfaces:
                if self.surface_successor[(state, surface)] not in state_set:
                    raise ValueError("surface successor leaves the state set")
                for environment in self.environments:
                    count = self.selection_counts[(environment, state, surface)]
                    if count < 0:
                        raise ValueError("selection counts must be non-negative")


@dataclass(frozen=True)
class SurfaceRoleEvidence:
    surface: Surface
    policy_varies: bool
    changes_successor: bool
    role: str
    selection_signatures: tuple[tuple[int, ...], ...]
    effect_signature: tuple[State, ...]


@dataclass(frozen=True)
class ResourceComparison:
    state_count: int
    surface_count: int
    action_class_count: int
    parser_bits: int
    flat_transition_bits: int
    quotient_transition_bits: int
    surface_to_class_bits: int
    quotient_total_bits: int

    @property
    def compression_ratio(self) -> float:
        return self.flat_transition_bits / self.quotient_total_bits


def passive_actuation_counterexample() -> tuple[PassiveDecomposition, PassiveDecomposition]:
    """Return two incompatible controlled/autonomous explanations of one raw trace.

    With no observable actuation marker, a learner cannot know whether the middle spans
    were actions chosen by an agent or autonomous emissions of the environment.  Both
    decompositions reproduce exactly the same bytes and therefore every passive statistic.
    """

    trace = ("s0", "u", "s1", "v", "s0", "u", "s1")
    controlled = PassiveDecomposition(
        raw_trace=trace,
        actuation_positions=frozenset({1, 3, 5}),
        explanation=(
            "u and v are agent-selected probes; state transitions are controlled by them"
        ),
    )
    autonomous = PassiveDecomposition(
        raw_trace=trace,
        actuation_positions=frozenset(),
        explanation=(
            "u and v are ordinary emissions; one autonomous generator emits the full trace"
        ),
    )
    return controlled, autonomous


def _policy_varies(table: FiniteRegimeTable, surface: Surface) -> bool:
    """Whether the selection distribution changes across policy regimes.

    Counts are normalized per `(environment, state)` before comparison, so a mere change
    in total sample size does not create false policy variation.
    """

    for state in table.states:
        distributions: list[tuple[int, ...]] = []
        for environment in table.environments:
            counts = tuple(
                table.selection_counts[(environment, state, candidate)]
                for candidate in table.surfaces
            )
            total = sum(counts)
            if total == 0:
                distributions.append(tuple(0 for _ in counts))
                continue
            # Exact integer cross-products are used instead of floating point.
            target = table.selection_counts[(environment, state, surface)]
            distributions.append(tuple(target * total2 for total2 in (1, total)))

        # Compare exact fractions count/total via cross multiplication.
        for left_index in range(len(table.environments)):
            left_environment = table.environments[left_index]
            left_count = table.selection_counts[(left_environment, state, surface)]
            left_total = sum(
                table.selection_counts[(left_environment, state, candidate)]
                for candidate in table.surfaces
            )
            for right_index in range(left_index + 1, len(table.environments)):
                right_environment = table.environments[right_index]
                right_count = table.selection_counts[(right_environment, state, surface)]
                right_total = sum(
                    table.selection_counts[(right_environment, state, candidate)]
                    for candidate in table.surfaces
                )
                if left_total == 0 or right_total == 0:
                    if left_total != right_total:
                        return True
                    continue
                if left_count * right_total != right_count * left_total:
                    return True
    return False


def _changes_successor(table: FiniteRegimeTable, surface: Surface) -> bool:
    return any(
        table.surface_successor[(state, surface)] != table.passive_successor[state]
        for state in table.states
    )


def classify_surface_roles(
    table: FiniteRegimeTable,
) -> tuple[SurfaceRoleEvidence, ...]:
    """Classify only under the declared policy-shift/invariant-effect assumptions.

    - `action`: selection changes across regimes and the surface changes at least one
      successor relative to passive dynamics.
    - `observation`: selection is invariant and the surface never changes the successor.
    - `abstain`: the finite evidence does not identify the role.

    This is deliberately conservative.  Correlated observations, policy-invariant actions,
    or regime-varying sensors remain unresolved rather than being forced into a class.
    """

    table.validate()
    output: list[SurfaceRoleEvidence] = []
    for surface in table.surfaces:
        varies = _policy_varies(table, surface)
        changes = _changes_successor(table, surface)
        if varies and changes:
            role = "action"
        elif not varies and not changes:
            role = "observation"
        else:
            role = "abstain"

        selection_signatures = tuple(
            tuple(
                table.selection_counts[(environment, state, surface)]
                for environment in table.environments
            )
            for state in table.states
        )
        effect_signature = tuple(
            table.surface_successor[(state, surface)] for state in table.states
        )
        output.append(
            SurfaceRoleEvidence(
                surface,
                varies,
                changes,
                role,
                selection_signatures,
                effect_signature,
            )
        )
    return tuple(output)


def group_behavioral_action_surfaces(
    table: FiniteRegimeTable,
    evidence: Sequence[SurfaceRoleEvidence] | None = None,
) -> tuple[tuple[Surface, ...], ...]:
    """Quotient action spellings by their complete successor effect signature."""

    rows = classify_surface_roles(table) if evidence is None else tuple(evidence)
    groups: dict[tuple[State, ...], list[Surface]] = {}
    for row in rows:
        if row.role != "action":
            continue
        groups.setdefault(row.effect_signature, []).append(row.surface)
    return tuple(
        sorted(
            (tuple(sorted(surfaces)) for surfaces in groups.values()),
            key=lambda group: group,
        )
    )


def action_quotient_resource_comparison(
    *,
    state_count: int,
    surface_count: int,
    action_class_count: int,
    parser_bits: int,
) -> ResourceComparison:
    """Compare a flat surface transition table with an action-effect quotient.

    This is a coding comparison, not a novelty theorem.  The flat baseline stores one
    successor state for every `(state, surface)` pair.  The quotient stores one successor
    per `(state, action class)`, a surface-to-class mapping, and an executable parser.
    """

    if min(state_count, surface_count, action_class_count) < 1:
        raise ValueError("counts must be positive")
    if action_class_count > surface_count:
        raise ValueError("action classes cannot exceed surface spellings")
    if parser_bits < 0:
        raise ValueError("parser bits must be non-negative")

    state_bits = max(1, ceil(log2(state_count)))
    class_bits = 0 if action_class_count <= 1 else ceil(log2(action_class_count))
    flat = state_count * surface_count * state_bits
    quotient_transitions = state_count * action_class_count * state_bits
    surface_map = surface_count * class_bits
    total = quotient_transitions + surface_map + parser_bits
    return ResourceComparison(
        state_count,
        surface_count,
        action_class_count,
        parser_bits,
        flat,
        quotient_transitions,
        surface_map,
        total,
    )


def make_identifiable_fixture() -> FiniteRegimeTable:
    states = ("s0", "s1", "s2", "s3")
    surfaces = (
        "push-a",
        "push-b",
        "flip-a",
        "flip-b",
        "red",
        "round",
    )
    environments = ("policy-left", "policy-right")

    counts: dict[tuple[Environment, State, Surface], int] = {}
    for state_index, state in enumerate(states):
        left = {
            "push-a": 30 + state_index,
            "push-b": 20 + state_index,
            "flip-a": 5,
            "flip-b": 5,
            "red": 20,
            "round": 20,
        }
        right = {
            "push-a": 5,
            "push-b": 5,
            "flip-a": 30 + state_index,
            "flip-b": 20 + state_index,
            "red": 20,
            "round": 20,
        }
        for surface in surfaces:
            counts[("policy-left", state, surface)] = left[surface]
            counts[("policy-right", state, surface)] = right[surface]

    passive = {
        "s0": "s0",
        "s1": "s1",
        "s2": "s2",
        "s3": "s3",
    }
    successor: dict[tuple[State, Surface], State] = {}
    push_effect = {
        "s0": "s1",
        "s1": "s2",
        "s2": "s3",
        "s3": "s0",
    }
    flip_effect = {
        "s0": "s3",
        "s1": "s2",
        "s2": "s1",
        "s3": "s0",
    }
    for state in states:
        for surface in ("push-a", "push-b"):
            successor[(state, surface)] = push_effect[state]
        for surface in ("flip-a", "flip-b"):
            successor[(state, surface)] = flip_effect[state]
        for surface in ("red", "round"):
            successor[(state, surface)] = passive[state]

    return FiniteRegimeTable(
        states,
        surfaces,
        environments,
        counts,
        passive,
        successor,
    )


def make_no_policy_shift_fixture() -> FiniteRegimeTable:
    base = make_identifiable_fixture()
    counts: dict[tuple[Environment, State, Surface], int] = {}
    for state in base.states:
        for surface in base.surfaces:
            value = base.selection_counts[("policy-left", state, surface)]
            counts[("policy-left", state, surface)] = value
            counts[("policy-copy", state, surface)] = value
    return FiniteRegimeTable(
        base.states,
        base.surfaces,
        ("policy-left", "policy-copy"),
        counts,
        base.passive_successor,
        base.surface_successor,
    )


def run_theory_gate() -> dict[str, object]:
    controlled, autonomous = passive_actuation_counterexample()
    table = make_identifiable_fixture()
    evidence = classify_surface_roles(table)
    roles = {row.surface: row.role for row in evidence}
    groups = group_behavioral_action_surfaces(table, evidence)

    no_shift = make_no_policy_shift_fixture()
    no_shift_roles = {
        row.surface: row.role for row in classify_surface_roles(no_shift)
    }

    resources = action_quotient_resource_comparison(
        state_count=8,
        surface_count=64,
        action_class_count=4,
        parser_bits=64,
    )

    checks = {
        "passive_trace_is_identical": controlled.raw_trace == autonomous.raw_trace,
        "passive_actuation_assignments_disagree": (
            controlled.actuation_positions != autonomous.actuation_positions
        ),
        "policy_shift_actions_identified": all(
            roles[surface] == "action"
            for surface in ("push-a", "push-b", "flip-a", "flip-b")
        ),
        "invariant_non_effect_surfaces_identified_as_observations": (
            roles["red"] == "observation" and roles["round"] == "observation"
        ),
        "behavioral_action_spellings_quotiented": groups
        == (("flip-a", "flip-b"), ("push-a", "push-b")),
        "no_policy_shift_forces_abstention": all(
            no_shift_roles[surface] == "abstain"
            for surface in ("push-a", "push-b", "flip-a", "flip-b")
        ),
        "quotient_reduces_model_bits": (
            resources.quotient_total_bits < resources.flat_transition_bits
        ),
        "compression_is_material": resources.compression_ratio > 5.0,
    }

    return {
        "capability_id": "CAP-GEN-002-EAI-001",
        "claim": (
            "finite identifiability boundary for discovering action-like surfaces from "
            "policy shifts and invariant transition effects"
        ),
        "claim_boundary": (
            "the passive impossibility and invariance-style finite sufficiency results are "
            "known-style constructions. The unverified novelty candidate is joint raw-span "
            "segmentation, policy-regime discovery, predictive quotient acquisition, and "
            "shared executable action grammar under complete lifetime resource accounting."
        ),
        "passive_non_identifiability": {
            "raw_trace": list(controlled.raw_trace),
            "controlled_actuation_positions": sorted(controlled.actuation_positions),
            "autonomous_actuation_positions": sorted(autonomous.actuation_positions),
            "observational_views_equal": controlled.raw_trace == autonomous.raw_trace,
        },
        "identifiable_regime_fixture": {
            "roles": roles,
            "behavioral_action_classes": [list(group) for group in groups],
        },
        "no_policy_shift_fixture": {"roles": no_shift_roles},
        "resource_comparison": {
            "flat_transition_bits": resources.flat_transition_bits,
            "quotient_transition_bits": resources.quotient_transition_bits,
            "surface_to_class_bits": resources.surface_to_class_bits,
            "parser_bits": resources.parser_bits,
            "quotient_total_bits": resources.quotient_total_bits,
            "compression_ratio": resources.compression_ratio,
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_theory_gate(), ensure_ascii=False, indent=2, sort_keys=True))
