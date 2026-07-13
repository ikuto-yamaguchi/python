from minimal_predictive_lm.cap_gen_002_predictive_state_lower_bound import (
    DeterministicPredictor,
    lifetime_resource_objective,
    minimal_predictive_quotient,
)


def test_equivalent_implementation_states_collapse_to_one_predictive_state():
    machine = DeterministicPredictor(
        states=("a", "b", "c"),
        alphabet=(0, 1),
        transitions={
            ("a", 0): "a",
            ("a", 1): "c",
            ("b", 0): "b",
            ("b", 1): "c",
            ("c", 0): "c",
            ("c", 1): "c",
        },
        outputs={"a": 0, "b": 0, "c": 1},
    )
    quotient = minimal_predictive_quotient(machine)
    assert quotient.state_count == 2
    assert quotient.minimum_persistent_state_bits == 1
    assert quotient.block_of("a") == quotient.block_of("b")
    assert quotient.block_of("a") != quotient.block_of("c")


def test_future_distinguishable_states_cannot_be_merged_even_with_same_output():
    machine = DeterministicPredictor(
        states=(0, 1, 2, 3),
        alphabet=("tick",),
        transitions={
            (0, "tick"): 1,
            (1, "tick"): 2,
            (2, "tick"): 3,
            (3, "tick"): 3,
        },
        outputs={0: 0, 1: 0, 2: 0, 3: 1},
    )
    quotient = minimal_predictive_quotient(machine)
    assert quotient.state_count == 4
    assert quotient.minimum_persistent_state_bits == 2


def test_resource_objective_penalizes_hidden_runtime_and_memory():
    compact = lifetime_resource_objective(
        executable_bits=1_000,
        persistent_state_bits=16,
        training_operations=10_000,
        inference_operations=100,
        peak_working_bits=256,
        prediction_loss_bits=50.0,
    )
    apparently_small_but_hidden_runtime = lifetime_resource_objective(
        executable_bits=1_000,
        persistent_state_bits=16,
        training_operations=10_000,
        inference_operations=100,
        peak_working_bits=8_192,
        prediction_loss_bits=50.0,
    )
    assert compact < apparently_small_but_hidden_runtime


def test_api_contains_no_task_or_benchmark_identifier():
    names = set(minimal_predictive_quotient.__code__.co_varnames)
    assert "task_id" not in names
    assert "benchmark" not in names
    assert "domain" not in names
