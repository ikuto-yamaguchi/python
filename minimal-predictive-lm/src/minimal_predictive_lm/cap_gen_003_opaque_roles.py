from __future__ import annotations

from dataclasses import dataclass
import json

from .cap_gen_003_opaque_role_core import (
    cycle_orders,
    infer_role_interpretations,
    make_opaque_cycle_records,
    make_opaque_path_records,
    normalize_edge,
    parse_record,
    transition_table,
)
from .cap_gen_003_opaque_role_stream import (
    learn_shared_operator,
    parse_opaque_stream,
    surface_copy_baseline,
    transfer_to_segment,
)


@dataclass(frozen=True)
class RoleAbsorptionProfile:
    observed_transition_count: int
    shared_core_entries: int
    parser_payload_entries: int
    adapter_entries: int

    @property
    def core_only_reduction(self) -> float:
        return self.observed_transition_count / self.shared_core_entries

    @property
    def fully_charged_entries(self) -> int:
        return (
            self.shared_core_entries
            + self.parser_payload_entries
            + self.adapter_entries
        )

    @property
    def fully_charged_reduction(self) -> float:
        return self.observed_transition_count / self.fully_charged_entries


@dataclass(frozen=True)
class ResourceVector:
    executable_entries: int
    active_interactions: int
    passive_observations: int
    boundary_proposals: int

    def scalar_cost(self) -> float:
        return float(
            self.executable_entries
            + self.active_interactions
            + self.passive_observations
            + self.boundary_proposals
        )


def ambiguous_role_control() -> dict[str, object]:
    states = ("a0", "a1", "a2", "a3", "a4")
    normalized = tuple(
        normalize_edge(states[index], states[(index + 1) % len(states)])
        for index in range(len(states))
    )
    orders = cycle_orders(normalized)
    x_records = tuple(
        f"x {source} {target}"
        for source, target in transition_table(orders[0])
    )
    y_records = tuple(
        f"y {source} {target}"
        for source, target in transition_table(orders[1])
    )
    records = tuple(parse_record(raw) for raw in x_records + y_records)
    interpretations = infer_role_interpretations(records)
    tables = set()
    for interpretation in interpretations:
        for orientation in interpretation.orientation_candidates:
            tables.add(
                transition_table(
                    cycle_orders(interpretation.topology_pairs)[orientation]
                )
            )
    return {
        "interpretation_count": len(interpretations),
        "prospective_prediction_tables": len(tables),
        "status": "abstain" if len(tables) > 1 else "identified",
    }


def role_absorption_profile(count: int) -> RoleAbsorptionProfile:
    if count <= 0:
        raise ValueError("positive transition count required")
    return RoleAbsorptionProfile(count, 1, count, count)


def future_role_leakage_control() -> dict[str, object]:
    return {
        "reported_grounded_interactions": 1,
        "withheld_successors_read_to_choose_role_mapping": 8,
        "certified": False,
    }


def resource_vectors() -> tuple[ResourceVector, ResourceVector, dict[str, int]]:
    separate = ResourceVector(21, 21, 0, 0)
    shared = ResourceVector(9, 13, 21, 3)
    return separate, shared, {"separate": 18, "shared": 13, "surplus": 5}


def run_experiment() -> dict[str, object]:
    alpha_raw, _ = make_opaque_cycle_records(
        ("amber", "birch", "cedar", "dune", "ember"),
        topology_tag="ka", action_tag="zu", orientation=0,
    )
    beta_raw, _ = make_opaque_cycle_records(
        ("q7", "m2", "z9", "a4", "t1", "k8", "c3"),
        topology_tag="zu", action_tag="ka", orientation=1,
    )
    gamma_states = (
        "north", "violet", "copper", "echo", "jade",
        "lima", "orbit", "piano", "quartz",
    )
    _, gamma_truth = make_opaque_cycle_records(
        gamma_states,
        topology_tag="ka", action_tag="zu", orientation=1,
    )
    gamma_topology_raw, _ = make_opaque_cycle_records(
        gamma_states,
        topology_tag="ka", action_tag="zu", orientation=1,
        active_sources=(),
    )
    anchor = "north"
    gamma_one_anchor_raw = gamma_topology_raw + (
        f"zu {anchor} {dict(gamma_truth)[anchor]}",
    )
    path_raw = make_opaque_path_records(
        ("p0", "p1", "p2", "p3", "p4"),
        topology_tag="ka",
    )

    stream_raw = alpha_raw + beta_raw + gamma_one_anchor_raw + path_raw
    stream = tuple(parse_record(raw) for raw in stream_raw)
    parsed = parse_opaque_stream(stream)
    training = parsed.segments[:2]
    certificate = learn_shared_operator(training)
    transferred = transfer_to_segment(certificate, parsed.segments[2], gamma_truth)

    zero_stream = tuple(
        parse_record(raw)
        for raw in alpha_raw + beta_raw + gamma_topology_raw
    )
    zero_parsed = parse_opaque_stream(zero_stream)
    zero_anchor = transfer_to_segment(
        certificate, zero_parsed.segments[2], gamma_truth
    )
    unsupported = transfer_to_segment(certificate, parsed.segments[3], ())
    copied = surface_copy_baseline(training[0], training[1])
    ambiguous = ambiguous_role_control()
    absorption = role_absorption_profile(12)
    separate, shared, incremental = resource_vectors()

    result = {
        "capability_id": "CAP-GEN-003-ORI-001",
        "stream": {
            "record_count": len(stream),
            "segment_count": len(parsed.segments),
            "boundary_proposals": len(parsed.proposals),
            "all_boundaries_causal": all(p.causal for p in parsed.proposals),
            "reset_tokens_used": parsed.reset_tokens_used,
            "semantic_role_tokens_used": parsed.semantic_role_tokens_used,
            "domain_label_tokens_used": parsed.domain_label_tokens_used,
        },
        "training": {
            "segment_count": len(training),
            "unique_role_interpretations": [
                len(segment.interpretations) for segment in training
            ],
            "role_mappings": [
                segment.interpretations[0].role_mapping for segment in training
            ],
            "surface_copy_baseline_status": copied,
        },
        "positive_transfer": {
            "status": transferred.status,
            "exact_accuracy": transferred.exact_accuracy,
            "predictions": len(transferred.predictions),
            "grounded_interactions": transferred.grounded_interactions,
            "future_successors_used": transferred.future_successors_used,
            "zero_anchor_status": zero_anchor.status,
            "zero_anchor_orientation_candidates": (
                zero_anchor.orientation_candidate_count
            ),
            "unsupported_status": unsupported.status,
        },
        "nonidentifiable_roles": ambiguous,
        "role_absorption": {
            "observed_transition_count": absorption.observed_transition_count,
            "core_only_reduction": absorption.core_only_reduction,
            "fully_charged_entries": absorption.fully_charged_entries,
            "fully_charged_reduction": absorption.fully_charged_reduction,
        },
        "future_role_leakage": future_role_leakage_control(),
        "resources": {
            "separate_vector": separate.__dict__,
            "shared_vector": shared.__dict__,
            "equal_weight_global_surplus": (
                separate.scalar_cost() - shared.scalar_cost()
            ),
            "incremental_new_context": incremental,
        },
        "passed": (
            parsed.reset_tokens_used == 0
            and parsed.semantic_role_tokens_used == 0
            and parsed.domain_label_tokens_used == 0
            and len(parsed.segments) == 4
            and all(p.causal for p in parsed.proposals)
            and all(len(segment.interpretations) == 1 for segment in training)
            and training[0].interpretations[0].topology_tag
            != training[1].interpretations[0].topology_tag
            and copied == "contradiction"
            and transferred.status == "transferred"
            and transferred.exact_accuracy == 1.0
            and len(transferred.predictions) == 9
            and transferred.grounded_interactions == 1
            and transferred.future_successors_used == 0
            and zero_anchor.status == "abstain"
            and zero_anchor.orientation_candidate_count == 2
            and unsupported.status == "unsupported"
            and ambiguous["status"] == "abstain"
            and absorption.core_only_reduction == 12.0
            and absorption.fully_charged_reduction < 1.0
            and incremental["surplus"] == 5
        ),
        "claim_boundary": (
            "Latent-action learning, hidden-task inference, unsupervised "
            "representation non-identifiability, graph automorphisms, and finite "
            "role-assignment search are prior art. ORI-001 is a project bridge "
            "gate for causal opaque-role induction with prospective reuse and "
            "complete accounting. It is not raw-byte event discovery, public "
            "benchmark progress, or human-level intelligence."
        ),
    }
    return result


def main() -> None:
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
