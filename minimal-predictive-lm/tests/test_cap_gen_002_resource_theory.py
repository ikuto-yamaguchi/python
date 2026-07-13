from itertools import product

from minimal_predictive_lm.cap_gen_002_resource_theory import (
    MacroReplacement,
    ResourcePoint,
    affine_word_value,
    downstream_error_bound,
    fixed_length_program_count,
    flat_boolean_factor_entries,
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
