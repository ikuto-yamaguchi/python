from minimal_predictive_lm.cap_gen_003_opaque_roles import resource_vectors


def test_resource_vector_is_not_global_victory() -> None:
    separate, shared, incremental = resource_vectors()
    assert separate.scalar_cost() - shared.scalar_cost() == -4
    assert incremental == {"separate": 18, "shared": 13, "surplus": 5}
