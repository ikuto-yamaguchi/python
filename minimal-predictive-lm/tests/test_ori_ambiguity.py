from minimal_predictive_lm.cap_gen_003_opaque_roles import (
    ambiguous_role_control,
    future_role_leakage_control,
)


def test_ambiguous_roles_abstain() -> None:
    result = ambiguous_role_control()
    assert result["interpretation_count"] == 2
    assert result["prospective_prediction_tables"] == 2
    assert result["status"] == "abstain"


def test_future_role_leakage_rejected() -> None:
    result = future_role_leakage_control()
    assert result["withheld_successors_read_to_choose_role_mapping"] == 8
    assert result["certified"] is False
