from minimal_predictive_lm.cap_gen_003_opaque_roles import role_absorption_profile


def test_role_absorption_fails_accounting() -> None:
    profile = role_absorption_profile(12)
    assert profile.core_only_reduction == 12.0
    assert profile.fully_charged_entries == 25
    assert profile.fully_charged_reduction == 0.48
