from fractions import Fraction
from itertools import product

from minimal_predictive_lm.cap_gen_002_resource_theory import (
    AffineMap,
    MacroReplacement,
    ResourcePoint,
    affine_word_value,
    conjugate_latent_system,
    downstream_error_bound,
    fixed_length_program_count,
    flat_boolean_factor_entries,
    observed_affine_trajectory,
    program_code_bits,
    resource_frontier_dominates,
    resource_objective_delta,
    suffix_lipschitz_products,
)


def test_flat_factor_cost_is_exponential():
    assert flat_boolean_factor_entries(0) == 1
    assert flat_boolean_factor_entries(10) == 1024
    assert flat_boolean_factor_entries(20) == 1_048_576


def test_fixed_length_generator_words_are_distinguishable_on_affine_probe():
    generator_count = 3
    depth = 6
    words = tuple(product(range(generator_count), repeat=depth))
    values = {affine_word_value(word, generator_count) for word in words}
    assert len(words) == fixed_length_program_count(generator_count, depth)
    assert len(values) == len(words)
    assert program_code_bits(generator_count, depth) == 12


def test_latent_generators_are_not_identifiable_under_coordinate_conjugacy():
    initial = Fraction(1, 3)
    generators = (
        AffineMap.build(2, 1),
        AffineMap.build(-1, 3),
    )
    decoder = AffineMap.build(5, -2)
    coordinate_change = AffineMap.build(3, 7)
    word = (0, 1, 0, 0, 1, 1)

    transformed_initial, transformed_generators, transformed_decoder = (
        conjugate_latent_system(
            initial,
            generators,
            decoder,
            coordinate_change,
        )
    )
    original_observations = observed_affine_trajectory(
        initial,
        word,
        generators,
        decoder,
    )
    transformed_observations = observed_affine_trajectory(
        transformed_initial,
        word,
        transformed_generators,
        transformed_decoder,
    )

    assert transformed_generators != generators
    assert transformed_decoder != decoder
    assert transformed_initial != initial
    assert transformed_observations == original_observations


def test_macro_boundaries_are_not_identifiable_from_aggregate_map_alone():
    outer = AffineMap.build(2, 1)
    inner = AffineMap.build(3, -2)
    hidden_change = AffineMap.build(5, 4)

    original = outer.compose(inner)
    alternative_outer = outer.compose(hidden_change.inverse())
    alternative_inner = hidden_change.compose(inner)
    alternative = alternative_outer.compose(alternative_inner)

    assert alternative_outer != outer
    assert alternative_inner != inner
    assert alternative == original
    for probe in (Fraction(-2), Fraction(0), Fraction(7, 3)):
        assert alternative.apply(probe) == original.apply(probe)


def test_lipschitz_suffix_bound_matches_explicit_linear_error():
    constants = (2.0, 3.0, 5.0)
    suffixes = suffix_lipschitz_products(constants)
    assert suffixes == (15.0, 5.0, 1.0)
    assert downstream_error_bound((0.1, 0.2), (15.0, 5.0)) == 2.5


def test_macro_is_accepted_only_when_total_resource_code_decreases():
    replacement = MacroReplacement(
        repetitions=20,
        original_bits_per_copy=40,
        macro_definition_bits=120,
        call_bits_per_use=4,
        original_operations_per_copy=12,
        macro_operations_per_use=5,
        lookup_operations_per_use=1,
    )
    assert replacement.saved_bits == 600
    assert replacement.saved_operations == 120
    assert resource_objective_delta(
        replacement,
        predictive_extra_bits=10,
        bit_weight=1.0,
        operation_weight=0.1,
    ) < 0
    assert resource_objective_delta(
        replacement,
        predictive_extra_bits=700,
        bit_weight=1.0,
        operation_weight=0.1,
    ) > 0


def test_resource_dominance_requires_a_strict_improvement():
    compact = ResourcePoint(100, 50, 20)
    equal = ResourcePoint(100, 50, 20)
    larger = ResourcePoint(101, 50, 20)
    assert resource_frontier_dominates(compact, larger)
    assert not resource_frontier_dominates(compact, equal)
