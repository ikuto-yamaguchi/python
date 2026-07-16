from minimal_predictive_lm.english_causal_compiler_v3_runtime import (
    EnglishCausalResolverV3Runtime,
)


def test_foreseen_side_effect_and_accidental_path_use_same_intent_lattice():
    resolver = EnglishCausalResolverV3Runtime()
    foreseen = (
        "A hunter realizes that firing will definitely hit a bystander. He does not "
        "care and shoots the target. Did the hunter intentionally hit the bystander?"
    )
    accidental = (
        "A player wants to win but loses his balance. The dart slips out of his hand "
        "and wobbles into the target. Did the player intentionally hit the target?"
    )
    board = (
        "The board was told that a program will increase profits but will also harm "
        "the environment. The board decided to implement the program, and it harmed "
        "the environment. Did the board intentionally harm the environment?"
    )
    assert resolver.answer(foreseen).output == "Yes"
    assert resolver.answer(accidental).output == "No"
    assert resolver.answer(board).output == "Yes"


def test_generic_participant_conjunction_prefers_abnormal_agent():
    resolver = EnglishCausalResolverV3Runtime()
    story = (
        "A bridge collapses if two trains enter at the same time. Billy is not "
        "supposed to enter, while Suzy is supposed to enter. Billy ignores his signal "
        "and Suzy follows her signal. Both trains enter and the bridge collapses. "
    )
    assert resolver.answer(story + "Did Billy cause the bridge to collapse?").output == "Yes"
    assert resolver.answer(story + "Did Suzy cause the bridge to collapse?").output == "No"


def test_redundant_addition_equal_status_and_passive_state_are_distinct():
    resolver = EnglishCausalResolverV3Runtime()
    redundant = (
        "A device activates if either the safety switch is off or knob A is on. The "
        "safety switch is off and knob A is off. Tom changed knob A to on. The device "
        "activated. Did the device activate because Tom changed the position of knob A?"
    )
    equal = (
        "A shop makes a profit if anyone orders coffee. Only one order is needed. As "
        "usual, Drew ordered coffee, and two other regular customers also ordered. "
        "Did Drew ordering coffee cause the shop to make a profit?"
    )
    passive = (
        "A company sends a sample if a client is on its list. The client is already "
        "subscribed and did not change the subscription status. The sample arrived. "
        "Did the client receive the sample because the client did not change the "
        "subscription status?"
    )
    assert resolver.answer(redundant).output == "No"
    assert resolver.answer(equal).output == "Yes"
    assert resolver.answer(passive).output == "No"


def test_duty_omission_and_choice_invariance():
    resolver = EnglishCausalResolverV3Runtime()
    omission = (
        "Janet is responsible for putting oil in a machine. Janet did not put oil in "
        "it and the machine broke down. Did Janet not putting oil cause the machine "
        "to break down?"
    )
    choice = (
        "A diner chose dish B instead of dish A. Unknown to the diner, both of these "
        "dishes were made with wine sauce, which caused an allergic reaction. Did the "
        "diner's choice of dish cause the reaction?"
    )
    assert resolver.answer(omission).output == "Yes"
    assert resolver.answer(choice).output == "No"


def test_noncausal_input_still_abstains_without_task_name_routing():
    resolver = EnglishCausalResolverV3Runtime()
    assert resolver.answer("Sort these words alphabetically.").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
