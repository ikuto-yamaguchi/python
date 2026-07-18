from minimal_predictive_lm.generic_causal_judgement_v3 import GenericCausalJudgementV3


def test_intentional_harm_differs_from_unwanted_benefit() -> None:
    engine = GenericCausalJudgementV3()
    harm = (
        "The manager knows the project will harm the river. He does not care and decides "
        "to start it. The river is harmed. Did the manager intentionally harm the river?\n"
        "Options:\n- Yes\n- No"
    )
    benefit = (
        "The manager knows the project will also help the park. He does not care about "
        "helping it and starts the project for profit. Did the manager intentionally help "
        "the park?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(harm).output == "Yes"
    assert engine.answer(benefit).output == "No"


def test_late_second_contributor_is_selected() -> None:
    engine = GenericCausalJudgementV3()
    prompt = (
        "If two users are logged in, an email is sent. Alice logs in at 9:00. Zoe logs in "
        "at 9:30 when Alice is already logged in. Immediately an email is sent. Did Zoe "
        "cause the email to be sent?\nOptions:\n- Yes\n- No"
    )
    assert engine.answer(prompt).output == "Yes"


def test_probability_changes_normal_causal_selection() -> None:
    engine = GenericCausalJudgementV3()
    unlikely = (
        "Joe wins iff he draws green from the first box and blue from the second. It is "
        "unlikely that he gets green from the first box. He draws both and wins. Did Joe's "
        "first choice cause him to win?\nOptions:\n- Yes\n- No"
    )
    likely = unlikely.replace("unlikely", "very likely")
    assert engine.answer(unlikely).output == "Yes"
    assert engine.answer(likely).output == "No"


def test_normal_and_abnormal_fertilizers_are_distinguished() -> None:
    engine = GenericCausalJudgementV3()
    story = (
        "Plants dry if both chemical A and chemical B are applied. Alex followed the "
        "instructions and used only A. Benni used B instead even though the instruction "
        "was to use only A. Both were applied and the plants dried. "
    )
    alex = story + "Did the fertilization by Alex cause the plants to dry?\nOptions:\n- Yes\n- No"
    benni = story + "Did the fertilization by Benni cause the plants to dry?\nOptions:\n- Yes\n- No"
    assert engine.answer(alex).output == "No"
    assert engine.answer(benni).output == "Yes"
