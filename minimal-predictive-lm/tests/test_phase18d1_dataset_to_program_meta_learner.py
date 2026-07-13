from minimal_predictive_lm.phase18d1_dataset_to_program_meta_learner import (
    ContinualProgramMemory,
    NoProgramError,
    NonIdentifiableProgramError,
    ambiguity_and_failure_controls,
    canonical,
    decode_value,
    evaluate_program,
    example_order_invariance,
    load_task_stream,
    run,
    synthesize_program,
    variable_rename_invariance,
)


def test_one_frozen_learner_acquires_all_data_tasks():
    for task in load_task_stream():
        program = synthesize_program(task)
        correct, total = evaluate_program(program, task["test"])
        assert correct == total


def test_post_freeze_tasks_are_data_only_and_opaque():
    tasks = load_task_stream()
    post_freeze = [task for task in tasks if task["group"] == "post_freeze"]
    assert len(post_freeze) == 11
    assert variable_rename_invariance(post_freeze[0])
    assert example_order_invariance(post_freeze[1])


def test_runtime_task_can_be_added_without_task_dispatch():
    task = {
        "id": "never-seen-by-module",
        "train": [
            {"inputs": {"red": -2, "blue": 5}, "output": 1},
            {"inputs": {"red": 0, "blue": 3}, "output": 3},
            {"inputs": {"red": 1, "blue": 4}, "output": 6},
            {"inputs": {"red": 2, "blue": -1}, "output": 3},
            {"inputs": {"red": 4, "blue": 6}, "output": 14},
        ],
        "test": [
            {"inputs": {"red": 7, "blue": 8}, "output": 22},
            {"inputs": {"red": -3, "blue": 2}, "output": -4},
        ],
    }
    program = synthesize_program(task)
    assert evaluate_program(program, task["test"]) == (2, 2)


def test_continual_learning_does_not_overwrite_old_programs():
    memory = ContinualProgramMemory()
    tasks = load_task_stream()
    development = [task for task in tasks if task["group"] == "development"]
    later = [task for task in tasks if task["group"] == "post_freeze"]
    for task in development:
        memory.learn(task)
    frozen = memory.fingerprint()
    for task in later:
        memory.learn(task)
    current = dict(memory.fingerprint())
    assert all(current[task_id] == expression for task_id, expression in frozen)


def test_insufficient_conflicting_and_outside_dsl_data_abstain():
    controls = ambiguity_and_failure_controls()
    assert all(controls.values())

    ambiguous = {
        "id": "ambiguous-direct",
        "train": [{"inputs": {"a": 2, "b": 2}, "output": 4}],
        "test": [],
    }
    try:
        synthesize_program(ambiguous)
    except NonIdentifiableProgramError:
        pass
    else:
        raise AssertionError("one ambiguous example must not choose a task program")

    impossible = {
        "id": "impossible-direct",
        "train": [
            {"inputs": {"a": 1}, "output": 2},
            {"inputs": {"a": 1}, "output": 3},
        ],
        "test": [],
    }
    try:
        synthesize_program(impossible)
    except NoProgramError:
        pass
    else:
        raise AssertionError("conflicting labels must not be memorized as a function")


def test_exact_fraction_and_heterogeneous_outputs_are_preserved():
    tasks = {task["id"]: task for task in load_task_stream()}
    quotient = synthesize_program(tasks["r1v"])
    prediction = quotient.predict({"num": 7, "den": 2})
    assert canonical(prediction) == canonical(decode_value({"fraction": [7, 2]}))

    sorting = synthesize_program(tasks["o9s"])
    assert sorting.predict({"items": [3, -1, 2]}) == (-1, 2, 3)

    uppercase = synthesize_program(tasks["u8h"])
    assert uppercase.predict({"text": "OpenAI猫"}) == "OPENAI猫"


def test_all_phase18d1_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["campaign"]["source_changes_per_post_freeze_task"] == 0
    assert payload["evaluation"]["post_freeze_correct"] == payload["evaluation"]["post_freeze_total"]
    assert payload["claim_boundary"]["arbitrary_new_primitive_discovery"] is False
    assert payload["claim_boundary"]["free_language_learning"] is False
    assert payload["claim_boundary"]["high_school_intelligence"] is False
