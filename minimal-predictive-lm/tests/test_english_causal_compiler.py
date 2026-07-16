from minimal_predictive_lm.english_causal_compiler_v2 import EnglishCausalResolverV2


def test_conjunctive_normality_selects_abnormal_contributor():
    resolver = EnglishCausalResolverV2()
    prompt = (
        "A machine will short circuit if both the black wire and the red wire touch "
        "the battery at the same time. The black wire is supposed to touch the "
        "battery, while the red wire is supposed to remain elsewhere. One day, "
        "the black wire and the red wire both end up touching the battery. "
    )
    assert resolver.answer(prompt + "Did the black wire cause the short circuit?").output == "No"
    assert resolver.answer(prompt + "Did the red wire cause the short circuit?").output == "Yes"


def test_intent_separates_accident_goal_and_foreseen_side_effect():
    resolver = EnglishCausalResolverV2()
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
    balance_loss = (
        "A contestant wants to win, but loses his balance. The dart slips out of his "
        "hand and wobbles toward the board, landing in the high point region. "
        "Did the contestant intentionally hit the high point region?"
    )
    expert = (
        "An expert marksman decided to shoot the target, pulled the trigger, and "
        "directly hit it. Did the marksman intentionally shoot the target?"
    )
    assert resolver.answer(accidental).output == "No"
    assert resolver.answer(foreseen).output == "Yes"
    assert resolver.answer(balance_loss).output == "No"
    assert resolver.answer(expert).output == "Yes"


def test_proximate_and_specific_paths_outrank_background_conditions():
    resolver = EnglishCausalResolverV2()
    story = (
        "John had incurable lung cancer after exposure to asbestos at his job and was "
        "certain to die. A nurse administered the wrong medication. He died minutes "
        "after the medication was administered. "
    )
    assert resolver.answer(story + "Did misadministration of medication cause John's premature death?").output == "Yes"
    assert resolver.answer(story + "Did John's job cause his premature death?").output == "No"
    assert resolver.answer(story + "Did exposure to asbestos cause John's lung cancer?").output == "Yes"


def test_prescriptive_violation_statistical_unusualness_and_state_maintenance_differ():
    resolver = EnglishCausalResolverV2()
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


def test_omission_duty_awareness_and_determiner_safe_actor_extraction():
    resolver = EnglishCausalResolverV2()
    responsible = (
        "The worker is responsible for putting oil in a machine. The worker forgot to "
        "put oil in it, and the machine broke down. "
        "Did the worker not putting oil cause the machine to break down?"
    )
    unaware = (
        "The worker is not responsible for putting oil in a machine. The worker did "
        "not notice that another worker forgot the oil. The machine broke down. "
        "Did the worker not putting oil cause the machine to break down?"
    )
    noticed = (
        "Kate noticed that Janet did not put oil in the machine, but Kate also did not "
        "put oil in it. The machine broke down. "
        "Did the machine break down because Kate did not put oil in it?"
    )
    assert resolver.answer(responsible).output == "Yes"
    assert resolver.answer(unaware).output == "No"
    assert resolver.answer(noticed).output == "Yes"


def test_temporal_preemption_hidden_mechanism_and_intervening_agent():
    resolver = EnglishCausalResolverV2()
    preemption = (
        "A team wins if either a three-pointer or a layup is scored. They scored a "
        "three-pointer right at the beginning and a layup right at the end. "
        "Did the later layup cause the team to win?"
    )
    hidden = (
        "Unbeknownst to everybody, if two people are logged in at the same time an "
        "email is sent. Alice and Zoe logged in. Did Zoe cause the email to be sent?"
    )
    prohibited = (
        "A computer will only crash if two people are logged in at once. Claire told "
        "Daniel, please don't log on. Claire and Daniel logged in and it crashed. "
        "Did Daniel cause the computer crash?"
    )
    intervening = (
        "Joe stopped to help someone, delaying pickup. A neighbor drove Joe's son, "
        "and a drunk driver struck the car. Did Joe cause his son's injury?"
    )
    assert resolver.answer(preemption).output == "No"
    assert resolver.answer(hidden).output == "No"
    assert resolver.answer(prohibited).output == "Yes"
    assert resolver.answer(intervening).output == "No"


def test_question_extraction_handles_quotes_and_abbreviations():
    resolver = EnglishCausalResolverV2()
    prompt = (
        "Prof. Smith said, \"The program will increase profit, but it will also harm "
        "the environment.\" The board knew this and the program was implemented. "
        "Did the board intentionally harm the environment?\nOptions:\n- Yes\n- No"
    )
    assert resolver.answer(prompt).output == "Yes"


def test_noncausal_prompt_abstains_and_has_no_task_branch():
    resolver = EnglishCausalResolverV2()
    assert resolver.answer("What is 17 plus 4?").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
