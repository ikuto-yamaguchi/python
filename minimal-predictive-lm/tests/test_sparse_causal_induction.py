from minimal_predictive_lm.english_causal_compiler_v4 import EnglishCausalResolverV4
from minimal_predictive_lm.sparse_causal_curriculum import build_sparse_causal_curriculum
from minimal_predictive_lm.sparse_causal_routing import (
    train_routed_sparse_causal_prototypes,
)


def test_sparse_prototypes_generalize_to_new_generated_entities_and_phrasings():
    model = train_routed_sparse_causal_prototypes(
        build_sparse_causal_curriculum(seed=2100, variants_per_pattern=24)
    )
    heldout = build_sparse_causal_curriculum(seed=2101, variants_per_pattern=6)
    predictions = [model.predict(row.prompt) for row in heldout]
    correct = sum(prediction.answer == row.answer for prediction, row in zip(predictions, heldout))
    answered = sum(prediction.answer is not None for prediction in predictions)
    mean_candidates = sum(prediction.candidates for prediction in predictions) / len(predictions)
    assert correct / len(heldout) >= 0.85
    assert answered / len(heldout) >= 0.85
    assert mean_candidates <= 8.0
    assert len(model.prototypes) <= 24


def test_learned_committee_handles_paraphrased_unseen_scenarios():
    resolver = EnglishCausalResolverV4()
    accident = (
        "Mira hoped to score, but the instrument escaped her grip without control and "
        "struck the center. Did Mira intentionally strike the center?"
    )
    duty = (
        "Noah was responsible for keeping coolant in a device. He saw the coolant was "
        "missing and did not refill it. The device failed. Did the device fail because "
        "Noah did not refill the coolant?"
    )
    redundant = (
        "A signal sounds if either sensor is active. Sensor one was already active. "
        "Later, Imani activated sensor two, and the signal sounded. Did the signal "
        "sound because Imani activated sensor two?"
    )
    assert resolver.answer(accident).output == "No"
    assert resolver.answer(duty).output == "Yes"
    assert resolver.answer(redundant).output == "No"


def test_deliberate_maintenance_is_not_collapsed_into_passive_nonaction():
    resolver = EnglishCausalResolverV4()
    passive = (
        "A service sends a reward when a client is subscribed. The client was already "
        "subscribed and did not change the status. The reward arrived. Did the reward "
        "arrive because the client did not change the subscription status?"
    )
    deliberate = (
        "A service sends a reward when a client is subscribed. The client checked the "
        "account, saw that it was subscribed, and deliberately left the status unchanged. "
        "The account remained subscribed and the reward arrived. Did the reward arrive "
        "because the client did not change the subscription status?"
    )
    assert resolver.answer(passive).output == "No"
    assert resolver.answer(deliberate).output == "Yes"


def test_learned_override_cannot_erase_high_confidence_control_evidence():
    resolver = EnglishCausalResolverV4()
    controlled = (
        "An engineer knew that activating the device would also destroy the sample. "
        "The engineer did not care and deliberately activated it. The sample was "
        "destroyed. Did the engineer intentionally destroy the sample?"
    )
    accidental = (
        "An engineer wanted to test a device, but lost balance and the control slipped "
        "from her hand. The device activated and destroyed the sample unexpectedly. "
        "Did the engineer intentionally destroy the sample?"
    )
    assert resolver.answer(controlled).output == "Yes"
    assert resolver.answer(accidental).output == "No"


def test_model_is_local_sparse_and_has_no_benchmark_task_router():
    resolver = EnglishCausalResolverV4()
    prediction = resolver.model.predict(
        "A device fails if both parts move. One prohibited operator moves a part. "
        "Did the operator cause the failure?"
    )
    assert prediction.candidates <= 8
    assert resolver.benchmark_task_name_branches == 0
    assert resolver.domain_specific_handlers == 0
