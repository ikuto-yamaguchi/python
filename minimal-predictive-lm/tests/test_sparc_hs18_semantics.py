from minimal_predictive_lm.english_modifier_order import EnglishModifierOrderResolver
from minimal_predictive_lm.generic_causal_judgement import GenericCausalJudgement


def test_modifier_order_uses_semantic_classes() -> None:
    resolver = EnglishModifierOrderResolver()
    prompt = (
        "Choose the natural phrase:\n"
        "(A) wooden lovely small old red Italian box\n"
        "(B) lovely small old red Italian wooden box"
    )
    assert resolver.answer(prompt).output == "(B)"


def test_modifier_order_handles_purpose_nearest_noun() -> None:
    resolver = EnglishModifierOrderResolver()
    prompt = (
        "Options:\n"
        "(A) blue new walking shoe\n"
        "(B) new blue walking shoe"
    )
    assert resolver.answer(prompt).output == "(B)"


def test_modifier_order_does_not_intercept_clause_choices() -> None:
    resolver = EnglishModifierOrderResolver()
    prompt = (
        "Sentence: Bailey planned to meet the director at their office\n"
        "Options:\n"
        "(A) The office was the director's office\n"
        "(B) The office was Bailey's office\n"
        "(C) Ambiguous"
    )
    assert resolver.answer(prompt).output is None


def test_conjunctive_abnormal_action_is_a_cause() -> None:
    engine = GenericCausalJudgement()
    prompt = (
        "If both switches are on, the alarm sounds. Switch B is not supposed to be on. "
        "Today A and B are on, so the alarm sounds. Did switch B cause the alarm?\n"
        "Options:\n- Yes\n- No"
    )
    assert engine.answer(prompt).output == "Yes"


def test_normal_conjunct_is_not_selected_when_other_conjunct_is_abnormal() -> None:
    engine = GenericCausalJudgement()
    prompt = (
        "The device fails if both the black and red switches are on. The black switch is "
        "supposed to be on, while the red switch is not supposed to be on. Both are on and "
        "the device fails. Did the black switch cause the failure?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(prompt).output == "No"


def test_redundant_ordinary_sufficient_condition_is_not_selected() -> None:
    engine = GenericCausalJudgement()
    prompt = (
        "The lamp lights if either battery A or battery B is connected. Battery A was "
        "already connected. Sam also connected battery B and the lamp lit. Did Sam "
        "connecting battery B cause the lamp to light?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(prompt).output == "No"


def test_last_question_is_used_after_quoted_question() -> None:
    engine = GenericCausalJudgement()
    prompt = (
        "The technician asked, 'Did the machine fail yesterday?' The machine fails if two "
        "users log in. Daniel was told not to log in, but Daniel and Claire logged in and it "
        "failed. Did Daniel cause the failure?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(prompt).output == "Yes"


def test_accident_blocks_intention_not_physical_causation() -> None:
    engine = GenericCausalJudgement()
    intention = (
        "Mira aimed at the wall, but her hand slips and the ball hits the bell by accident. "
        "Did Mira intentionally hit the bell?\nOptions:\n- Yes\n- No"
    )
    physical = (
        "Mira's hand slips and the ball strikes the bell. The bell rings immediately. "
        "Did the ball cause the bell to ring?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(intention).output == "No"
    assert engine.answer(physical).output == "Yes"
