from minimal_predictive_lm.english_role_compiler_v3 import EnglishRoleReferenceResolverV3


def _prompt(sentence: str, a: str, b: str, ambiguous: str = "(C) Ambiguous") -> str:
    return (
        "In the following sentences, explain the antecedent of the pronoun "
        "(which thing the pronoun refers to), or state that it is ambiguous.\n"
        f"Sentence: {sentence}\nOptions:\n(A) {a}\n(B) {b}\n{ambiguous}"
    )


def test_core_role_evidence_and_ambiguity():
    resolver = EnglishRoleReferenceResolverV3()
    assert resolver.answer(
        _prompt(
            "The guard called the cleaner and asked them to open the door.",
            "Asked the guard",
            "Asked the cleaner",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The technician told the customer that she had completed the repair.",
            "The technician completed the repair",
            "The customer completed the repair",
        )
    ).output == "(A)"
    assert resolver.answer(
        _prompt(
            "The patient was referred to the specialist because he is an expert on rare skin conditions.",
            "The patient is an expert",
            "The specialist is an expert",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The scientist collaborated with the artist, and he shared a story.",
            "The scientist shared a story",
            "The artist shared a story",
        )
    ).output == "(C)"


def test_generalized_recipient_possessor_and_causal_roles():
    resolver = EnglishRoleReferenceResolverV3()
    assert resolver.answer(
        _prompt(
            "The customer asked the salesperson if they could send the prices.",
            "The customer would send the prices",
            "The salesperson would send the prices",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The worker told the pedestrian that they should avoid the closed street.",
            "The worker should avoid it",
            "The pedestrian should avoid it",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "After meeting with the producers, Sam went to her office.",
            "It was the producers' office",
            "It was Sam's office",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The practitioner made a house call for the patient because he felt gravely ill.",
            "The practitioner felt ill",
            "The patient felt ill",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The sheriff protected the writer because he upholds the peace.",
            "The sheriff upholds the peace",
            "The writer upholds the peace",
        )
    ).output == "(A)"


def test_non_reference_prompt_abstains():
    resolver = EnglishRoleReferenceResolverV3()
    assert resolver.answer("What is 17 plus 4?").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
