from minimal_predictive_lm.english_role_compiler import EnglishRoleReferenceResolver


def _prompt(sentence: str, a: str, b: str, ambiguous: str = "(C) Ambiguous") -> str:
    return (
        "In the following sentences, explain the antecedent of the pronoun "
        "(which thing the pronoun refers to), or state that it is ambiguous.\n"
        f"Sentence: {sentence}\nOptions:\n(A) {a}\n(B) {b}\n{ambiguous}"
    )


def test_object_control_subject_continuity_semantics_and_ambiguity():
    resolver = EnglishRoleReferenceResolver()
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


def test_non_reference_prompt_abstains():
    resolver = EnglishRoleReferenceResolver()
    assert resolver.answer("What is 17 plus 4?").output is None
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
