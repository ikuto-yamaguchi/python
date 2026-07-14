from __future__ import annotations

from minimal_predictive_lm.cap_gen_003_opaque_role_core import (
    make_opaque_cycle_records,
    parse_record,
)
from minimal_predictive_lm.cap_gen_003_opaque_role_stream import (
    parse_opaque_stream,
    surface_copy_baseline,
)
from minimal_predictive_lm.cap_gen_003_opaque_roles import run_experiment


def test_semantic_labels_are_forbidden() -> None:
    for raw in ("EDGE a b", "STEP a b", "RESET a b", "FREEZE a b"):
        try:
            parse_record(raw)
        except ValueError:
            pass
        else:
            raise AssertionError(raw)


def test_local_role_mapping_can_flip_across_contexts() -> None:
    alpha, _ = make_opaque_cycle_records(
        ("a0", "a1", "a2", "a3", "a4"),
        topology_tag="ka",
        action_tag="zu",
        orientation=0,
    )
    beta, _ = make_opaque_cycle_records(
        ("b0", "b1", "b2", "b3", "b4", "b5", "b6"),
        topology_tag="zu",
        action_tag="ka",
        orientation=1,
    )
    parsed = parse_opaque_stream(
        tuple(parse_record(item) for item in alpha + beta)
    )
    assert len(parsed.segments) == 2
    assert all(len(segment.interpretations) == 1 for segment in parsed.segments)
    assert parsed.segments[0].interpretations[0].topology_tag == "ka"
    assert parsed.segments[1].interpretations[0].topology_tag == "zu"
    assert surface_copy_baseline(
        parsed.segments[0], parsed.segments[1]
    ) == "contradiction"


def test_role_and_boundary_inference_is_causal_and_unlabeled() -> None:
    stream = run_experiment()["stream"]
    assert stream["reset_tokens_used"] == 0
    assert stream["semantic_role_tokens_used"] == 0
    assert stream["domain_label_tokens_used"] == 0
    assert stream["all_boundaries_causal"] is True
    assert stream["segment_count"] == 4


def test_one_anchor_transfers_all_heldout_transitions() -> None:
    transfer = run_experiment()["positive_transfer"]
    assert transfer["status"] == "transferred"
    assert transfer["exact_accuracy"] == 1.0
    assert transfer["predictions"] == 9
    assert transfer["grounded_interactions"] == 1
    assert transfer["future_successors_used"] == 0


def test_zero_anchor_abstains_and_path_is_rejected() -> None:
    transfer = run_experiment()["positive_transfer"]
    assert transfer["zero_anchor_status"] == "abstain"
    assert transfer["zero_anchor_orientation_candidates"] == 2
    assert transfer["unsupported_status"] == "unsupported"
