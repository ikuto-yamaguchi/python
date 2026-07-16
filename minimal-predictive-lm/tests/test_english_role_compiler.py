from minimal_predictive_lm.english_role_compiler_v4 import EnglishRoleReferenceResolverV4


def _prompt(sentence: str, a: str, b: str, ambiguous: str = "(C) Ambiguous") -> str:
    return (
        "In the following sentences, explain the antecedent of the pronoun "
        "(which thing the pronoun refers to), or state that it is ambiguous.\n"
        f"Sentence: {sentence}\nOptions:\n(A) {a}\n(B) {b}\n{ambiguous}"
    )


def test_core_role_evidence_and_ambiguity():
    resolver = EnglishRoleReferenceResolverV4()
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


def test_recipient_possessor_and_causal_roles():
    resolver = EnglishRoleReferenceResolverV4()
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
            "After meeting with the producers, Sam went to their office.",
            "It was the producers' office",
            "It was Sam's office",
        )
    ).output == "(C)"
    assert resolver.answer(
        _prompt(
            "The practitioner made a house call for the patient because he felt gravely ill.",
            "The practitioner felt ill",
            "The patient felt ill",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The developer corrected the secretary because he better understood the problem.",
            "The developer understood the problem",
            "The secretary understood the problem",
        )
    ).output == "(A)"


def test_complement_roles_and_possessive_subjects():
    resolver = EnglishRoleReferenceResolverV4()
    assert resolver.answer(
        _prompt(
            "The patient disclosed to the counselor that they had a history of substance abuse.",
            "The patient had a history",
            "The counselor had a history",
        )
    ).output == "(A)"
    assert resolver.answer(
        _prompt(
            "The physician told the baker that they had cancer.",
            "The physician had cancer",
            "The baker had cancer",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The engineer informed the client that they would need to make future payments on time.",
            "The engineer should make payments",
            "The client should make payments",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "The chief told the counselor that he took the day off.",
            "The chief took the day off",
            "The counselor took the day off",
        )
    ).output == "(A)"
    assert resolver.answer(
        _prompt(
            "The secretary came to the analyst's office and helped her to book a flight.",
            "Helped the secretary book a flight",
            "Helped the analyst book a flight",
        )
    ).output == "(B)"
    assert resolver.answer(
        _prompt(
            "My cousin called her boss for more information",
            "They were my cousin's boss",
            "They were the boss's boss",
        )
    ).output == "(A)"


def test_non_reference_prompt_abstains():
    resolver = EnglishRoleReferenceResolverV4()
    assert resolver.answer("What is 17 plus 4?").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
