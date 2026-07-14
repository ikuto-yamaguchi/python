from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Mapping, Sequence

from .cap_gen_003_cross_domain_operational_transfer import (
    InteractionDomain,
    cycle_fixture,
    exact_accuracy,
    learn_shared_cycle_operator,
    transfer_operator,
)


State = str
Transition = tuple[State, State]


@dataclass(frozen=True)
class DeterministicDomain:
    name: str
    states: tuple[State, ...]
    transitions: tuple[Transition, ...]

    def validate(self) -> None:
        if not self.states:
            raise ValueError("domain must contain states")
        if len(set(self.states)) != len(self.states):
            raise ValueError("states must be unique")
        table = dict(self.transitions)
        if len(table) != len(self.transitions):
            raise ValueError("each source may have only one successor")
        if set(table) != set(self.states):
            raise ValueError("a complete deterministic domain needs one transition per state")
        if any(target not in set(self.states) for target in table.values()):
            raise ValueError("transition target must be a domain state")

    @property
    def table(self) -> dict[State, State]:
        self.validate()
        return dict(self.transitions)


@dataclass(frozen=True)
class LookupAdapter:
    domain_name: str
    entries: tuple[Transition, ...]
    grounded_sources: tuple[State, ...]

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def grounded_interactions(self) -> int:
        return len(self.grounded_sources)

    @property
    def future_active_successors_used(self) -> int:
        return len(set(dict(self.entries)) - set(self.grounded_sources))

    def predict(self, state: State) -> State | None:
        return dict(self.entries).get(state)


@dataclass(frozen=True)
class AbsorptionResult:
    domain_count: int
    transition_count: int
    shared_core_entries: int
    adapter_entries: int
    exact_training_accuracy: float

    @property
    def core_only_reduction(self) -> float:
        return self.transition_count / self.shared_core_entries

    @property
    def fully_charged_reduction(self) -> float:
        return self.transition_count / (self.shared_core_entries + self.adapter_entries)


@dataclass(frozen=True)
class ReuseProfile:
    name: str
    heldout_state_count: int
    shared_core_entries: int
    heldout_adapter_entries: int
    heldout_grounded_interactions: int
    heldout_exact_accuracy: float
    future_active_successors_used: int

    @property
    def heldout_storage_savings(self) -> int:
        return self.heldout_state_count - self.heldout_adapter_entries

    @property
    def heldout_interaction_savings(self) -> int:
        return self.heldout_state_count - self.heldout_grounded_interactions

    @property
    def certified_operational_reuse(self) -> bool:
        return (
            self.heldout_exact_accuracy == 1.0
            and self.future_active_successors_used == 0
            and self.heldout_storage_savings > 0
            and self.heldout_interaction_savings > 0
        )


def exact_table_accuracy(
    predictions: Mapping[State, State],
    truth: Mapping[State, State],
) -> float:
    if not truth:
        return 0.0
    return sum(predictions.get(source) == target for source, target in truth.items()) / len(truth)


def universal_lookup_predictions(
    adapter: LookupAdapter,
    states: Iterable[State],
) -> dict[State, State]:
    predictions: dict[State, State] = {}
    for state in states:
        target = adapter.predict(state)
        if target is not None:
            predictions[state] = target
    return predictions


def fully_absorbed_adapter(domain: DeterministicDomain) -> LookupAdapter:
    """Encode the complete domain transition table in a per-domain adapter."""

    return LookupAdapter(
        domain_name=domain.name,
        entries=domain.transitions,
        grounded_sources=domain.states,
    )


def absorb_arbitrary_domains(domains: Sequence[DeterministicDomain]) -> AbsorptionResult:
    """Fit arbitrary deterministic systems with one universal lookup interpreter.

    The shared core is constant-size, but every transition is copied into an adapter.
    This obtains zero execution error without learning transferable dynamics.
    """

    if not domains:
        raise ValueError("at least one domain is required")
    adapters = tuple(fully_absorbed_adapter(domain) for domain in domains)
    accuracies = []
    for domain, adapter in zip(domains, adapters):
        predictions = universal_lookup_predictions(adapter, domain.states)
        accuracies.append(exact_table_accuracy(predictions, domain.table))
    transition_count = sum(len(domain.transitions) for domain in domains)
    return AbsorptionResult(
        domain_count=len(domains),
        transition_count=transition_count,
        shared_core_entries=1,
        adapter_entries=sum(adapter.entry_count for adapter in adapters),
        exact_training_accuracy=sum(accuracies) / len(accuracies),
    )


def partial_lookup_adapter(
    domain: DeterministicDomain,
    grounded_sources: Sequence[State],
    *,
    leak_future: bool = False,
) -> LookupAdapter:
    table = domain.table
    grounded = tuple(grounded_sources)
    unknown = set(grounded) - set(domain.states)
    if unknown:
        raise ValueError("grounded source is not in the domain")
    entries = domain.transitions if leak_future else tuple((source, table[source]) for source in grounded)
    return LookupAdapter(domain.name, entries, grounded)


def reuse_profile_from_lookup(
    name: str,
    domain: DeterministicDomain,
    adapter: LookupAdapter,
) -> ReuseProfile:
    predictions = universal_lookup_predictions(adapter, domain.states)
    return ReuseProfile(
        name=name,
        heldout_state_count=len(domain.states),
        shared_core_entries=1,
        heldout_adapter_entries=adapter.entry_count,
        heldout_grounded_interactions=adapter.grounded_interactions,
        heldout_exact_accuracy=exact_table_accuracy(predictions, domain.table),
        future_active_successors_used=adapter.future_active_successors_used,
    )


def common_guaranteed_transitions(
    worlds: Sequence[DeterministicDomain],
) -> tuple[Transition, ...]:
    """Return transitions that are identical in every observationally possible world."""

    if not worlds:
        return ()
    state_set = set(worlds[0].states)
    if any(set(world.states) != state_set for world in worlds[1:]):
        raise ValueError("worlds must share the same observable state set")
    tables = [world.table for world in worlds]
    output = []
    for state in sorted(state_set):
        targets = {table[state] for table in tables}
        if len(targets) == 1:
            output.append((state, targets.pop()))
    return tuple(output)


def cycle_reuse_profile() -> ReuseProfile:
    """Positive control from COT-001, now evaluated by the anti-absorption gate."""

    alpha, _ = cycle_fixture(
        "alpha",
        ("amber", "birch", "cedar", "dune", "ember"),
        orientation_index=0,
    )
    beta, _ = cycle_fixture(
        "beta",
        ("q7", "m2", "z9", "a4", "t1", "k8", "c3"),
        orientation_index=1,
    )
    heldout_full, heldout_truth = cycle_fixture(
        "heldout",
        ("north", "violet", "copper", "echo", "jade", "lima", "orbit", "piano", "quartz"),
        orientation_index=1,
    )
    truth = dict(heldout_truth)
    source = heldout_full.states[0]
    heldout = InteractionDomain(
        name=heldout_full.name,
        states=heldout_full.states,
        passive_edges=heldout_full.passive_edges,
        active_transitions=((source, truth[source]),),
    )
    certificate = learn_shared_cycle_operator((alpha, beta))
    transfer = transfer_operator(certificate, heldout)
    accuracy = exact_accuracy(transfer.predictions, heldout_truth)
    return ReuseProfile(
        name="certified-shared-cycle-operator",
        heldout_state_count=len(heldout.states),
        shared_core_entries=1,
        heldout_adapter_entries=1,
        heldout_grounded_interactions=1,
        heldout_exact_accuracy=accuracy,
        future_active_successors_used=0,
    )


def arbitrary_domain(
    name: str,
    prefix: str,
    target_indices: Sequence[int],
) -> DeterministicDomain:
    states = tuple(f"{prefix}{index}" for index in range(len(target_indices)))
    if any(index < 0 or index >= len(states) for index in target_indices):
        raise ValueError("target index out of range")
    return DeterministicDomain(
        name=name,
        states=states,
        transitions=tuple(
            (state, states[target_indices[index]])
            for index, state in enumerate(states)
        ),
    )


def run_experiment() -> dict[str, object]:
    training_domains = (
        arbitrary_domain("pair-swaps", "p", (1, 0, 3, 2, 5, 4)),
        arbitrary_domain("mixed-map", "m", (2, 0, 1, 3, 5, 4)),
        arbitrary_domain("long-cycle", "c", (1, 2, 3, 4, 5, 0)),
    )
    absorption = absorb_arbitrary_domains(training_domains)

    heldout = arbitrary_domain("heldout-arbitrary", "h", (1, 0, 3, 2, 5, 4, 7, 6))
    one_source = (heldout.states[0],)
    partial = reuse_profile_from_lookup(
        "lawful-one-entry-lookup",
        heldout,
        partial_lookup_adapter(heldout, one_source),
    )
    leaked = reuse_profile_from_lookup(
        "future-leaking-lookup",
        heldout,
        partial_lookup_adapter(heldout, one_source, leak_future=True),
    )
    full = reuse_profile_from_lookup(
        "fully-grounded-lookup",
        heldout,
        fully_absorbed_adapter(heldout),
    )
    shared = cycle_reuse_profile()

    world_a = arbitrary_domain("world-a", "w", (1, 0, 3, 2, 5, 4, 7, 6))
    world_b = arbitrary_domain("world-b", "w", (1, 2, 0, 3, 4, 5, 6, 7))
    common = common_guaranteed_transitions((world_a, world_b))

    result = {
        "capability_id": "CAP-GEN-003-AAF-001",
        "strategic_purpose": (
            "reject fake cross-domain reuse where adapters absorb transition knowledge; "
            "require prospective held-out savings and no future-successor leakage"
        ),
        "adapter_absorption": {
            "domain_count": absorption.domain_count,
            "transition_count": absorption.transition_count,
            "shared_core_entries": absorption.shared_core_entries,
            "adapter_entries": absorption.adapter_entries,
            "exact_training_accuracy": absorption.exact_training_accuracy,
            "core_only_reduction": absorption.core_only_reduction,
            "fully_charged_reduction": absorption.fully_charged_reduction,
        },
        "heldout_lookup_controls": {
            "lawful_partial": {
                "accuracy": partial.heldout_exact_accuracy,
                "storage_savings": partial.heldout_storage_savings,
                "interaction_savings": partial.heldout_interaction_savings,
                "certified": partial.certified_operational_reuse,
            },
            "future_leaking": {
                "accuracy": leaked.heldout_exact_accuracy,
                "future_active_successors_used": leaked.future_active_successors_used,
                "certified": leaked.certified_operational_reuse,
            },
            "fully_grounded": {
                "accuracy": full.heldout_exact_accuracy,
                "storage_savings": full.heldout_storage_savings,
                "interaction_savings": full.heldout_interaction_savings,
                "certified": full.certified_operational_reuse,
            },
        },
        "indistinguishable_worlds": {
            "state_count": len(world_a.states),
            "common_transition_count": len(common),
            "common_coverage": len(common) / len(world_a.states),
            "same_one_anchor_evidence": common[0] == world_a.transitions[0] == world_b.transitions[0],
            "full_transfer_without_structure_guaranteed": len(common) == len(world_a.states),
        },
        "positive_control": {
            "name": shared.name,
            "accuracy": shared.heldout_exact_accuracy,
            "storage_savings": shared.heldout_storage_savings,
            "interaction_savings": shared.heldout_interaction_savings,
            "future_active_successors_used": shared.future_active_successors_used,
            "certified": shared.certified_operational_reuse,
        },
        "passed": (
            absorption.exact_training_accuracy == 1.0
            and absorption.core_only_reduction == 18.0
            and absorption.fully_charged_reduction < 1.0
            and partial.heldout_exact_accuracy == 0.125
            and not partial.certified_operational_reuse
            and leaked.heldout_exact_accuracy == 1.0
            and leaked.future_active_successors_used == 7
            and not leaked.certified_operational_reuse
            and full.heldout_exact_accuracy == 1.0
            and full.heldout_storage_savings == 0
            and full.heldout_interaction_savings == 0
            and not full.certified_operational_reuse
            and len(common) == 1
            and shared.certified_operational_reuse
            and shared.heldout_storage_savings == 8
            and shared.heldout_interaction_savings == 8
        ),
        "claim_boundary": (
            "MDP homomorphisms, action equivariance, representation non-identifiability, "
            "domain-adaptation counterexamples, MDL, and meta-learning memorization are prior art. "
            "AAF-001 is a project-specific anti-shortcut theorem gate and accounting rule. "
            "It is not raw-stream learning, public benchmark progress, or human-level intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
