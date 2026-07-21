from minimal_predictive_lm.counterfactual_predicate_induction import (
    CounterfactualPredicateInducer,
    Episode,
)


def test_future_equivalent_episodes_share_predicate() -> None:
    episodes = (
        Episode(("箱を確認したい",), "color", "色を教えて？", ("表示色が確定", "塗装を選べる")),
        Episode(("端末を確認したい",), "color", "何色ですか？", ("表示色が確定", "塗装を選べる")),
        Episode(("荷物を確認したい",), "owner", "持ち主を教えて？", ("権限者が確定", "連絡先を選べる")),
    )
    model = CounterfactualPredicateInducer()
    model.fit(episodes)
    assert len(model.rows) == 2
    assert model.latent_to_signature["color"] != model.latent_to_signature["owner"]


def test_unrelated_input_is_not_magically_rejected() -> None:
    model = CounterfactualPredicateInducer()
    model.fit((Episode(("箱を確認したい",), "color", "色を教えて？", ("表示色が確定",)),))
    assert model.infer_candidates(("今日の天気を知りたい",))


def test_claim_boundary_is_not_embedded_as_success() -> None:
    model = CounterfactualPredicateInducer()
    assert model.serialized_bytes() < 1_000_000_000
