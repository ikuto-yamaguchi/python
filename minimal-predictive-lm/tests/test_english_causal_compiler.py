from minimal_predictive_lm.english_causal_compiler import EnglishCausalResolver


def test_conjunctive_normality_selects_abnormal_contributor():
    resolver = EnglishCausalResolver()
    prompt = (
        "A machine will short circuit if both the black wire and the red wire touch "
        "the battery at the same time. The black wire is supposed to touch the "
        "battery, while the red wire is supposed to remain elsewhere. One day, "
        "the black wire and the red wire both end up touching the battery. "
    )
    assert resolver.answer(prompt + "Did the black wire cause the short circuit?").output == "No"
    assert resolver.answer(prompt + "Did the red wire cause the short circuit?").output == "Yes"


def test_intent_separates_accident_goal_and_foreseen_side_effect():
    resolver = EnglishCausalResolver()
    accidental = (
        "Jake desperately wants to win. He presses the trigger, but his hand slips "
        "and the shot goes wild. Nonetheless the bullet hits the bullseye. "
        "Did Jake intentionally hit the bullseye?"
    )
    foreseen = (
        "The hunter realizes that if he shoots the deer, the bullet will definitely "
        "hit a birdwatcher. He does not care and shoots. "
        "Did the man intentionally shoot the birdwatcher?"
    )
    assert resolver.answer(accidental).output == "No"
    assert resolver.answer(foreseen).output == "Yes"


def test_proximate_path_outranks_background_condition():
    resolver = EnglishCausalResolver()
    story = (
        "John had incurable cancer from asbestos at his job and was certain to die. "
        "A nurse administered the wrong medication. He died minutes after the "
        "medication was administered. "
    )
    assert resolver.answer(story + "Did misadministration of medication cause John's premature death?").output == "Yes"
    assert resolver.answer(story + "Did John's job cause his premature death?").output == "No"


def test_prescriptive_violation_statistical_unusualness_and_omission_are_distinct():
    resolver = EnglishCausalResolver()
    violation = (
        "The motion detector is triggered if at least one person appears. Suzy was "
        "told to arrive. Billy was told: do not come in tomorrow. Both Billy and "
        "Suzy arrive. Did Billy cause the motion detector to go off?"
    )
    unusual = (
        "The coffee shop makes a profit if anyone orders coffee. Drew doesn't usually "
        "order coffee. This Tuesday, unexpectedly, Drew ordered coffee. Kylie and "
        "Oliver also ordered. Did Drew ordering coffee cause the shop to make a profit?"
    )
    omission = (
        "The guitar plays if either channel A is selected or the mixer is on. Channel A "
        "is selected and the mixer is on. Sara did not turn off the mixer. "
        "Did the guitar play because Sara did not turn off the mixer?"
    )
    redundant_addition = (
        "The boat starts if either the gear is in neutral or the motor is in lock. "
        "The gear is in neutral. Ned changed the position of the motor and put it in "
        "lock. Did the boat start because Ned changed the position of the motor?"
    )
    assert resolver.answer(violation).output == "Yes"
    assert resolver.answer(unusual).output == "No"
    assert resolver.answer(omission).output == "Yes"
    assert resolver.answer(redundant_addition).output == "No"


def test_noncausal_prompt_abstains_and_has_no_task_branch():
    resolver = EnglishCausalResolver()
    assert resolver.answer("What is 17 plus 4?").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
