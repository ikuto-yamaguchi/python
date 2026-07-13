from fractions import Fraction

import pytest

from minimal_predictive_lm.phase18d10_primitive_core import IndexAffinePrimitive
from minimal_predictive_lm.phase18d12_multiple_ungrouped_primitives import (
    ElementAffinePrimitive,
    NoPromotablePrimitiveError,
    ResidualRow,
    hidden_future_accuracy,
    load_dataset,
    negative_controls,
    online_learn,
    parameter_recovery_controls,
    run,
    select_next_primitive,
)


def test_two_heterogeneous_primitives_are_invented_without_groups():
    payload = load_dataset()
    result = online_learn(payload["stream"])
    assert len(result.promotions) == 2
    assert tuple(p.position for p in result.promotions) == (15, 20)
    assert isinstance(result.library[0], IndexAffinePrimitive)
    assert (
        result.library[0].multiplier,
        result.library[0].offset,
    ) == (1, 1)
    assert isinstance(result.library[1], ElementAffinePrimitive)
    assert (
        result.library[1].scale,
        result.library[1].offset,
    ) == (1, 1)


def test_each_promotion_has_cross_type_disjoint_positive_support():
    payload = load_dataset()
    result = online_learn(payload["stream"])
    support_sets = [
        set(promotion.support_positions)
        for promotion in result.promotions
    ]
    assert all(
        set(promotion.support_types) == {"string", "number_list"}
        for promotion in result.promotions
    )
    assert all(promotion.mdl_gain_bits > 0 for promotion in result.promotions)
    assert support_sets[0].isdisjoint(support_sets[1])
    assert all(
        payload["audit_labels"][position].startswith("HIDDEN")
        for support in support_sets
        for position in support
    )


def test_future_hidden_records_are_all_explained_after_invention():
    payload = load_dataset()
    result = online_learn(payload["stream"])
    correct, total = hidden_future_accuracy(
        result,
        payload["stream"],
        payload["audit_labels"],
    )
    assert total == 21
    assert correct == total


def test_future_suffix_cannot_change_prefix_learning():
    payload = load_dataset()
    full = online_learn(payload["stream"])
    prefix_length = 35
    prefix = online_learn(payload["stream"][:prefix_length])
    assert full.predictions[:prefix_length] == prefix.predictions
    assert full.observed_operations[:prefix_length] == prefix.observed_operations
    assert tuple(
        p.primitive.render() for p in full.promotions
        if p.position < prefix_length
    ) == tuple(p.primitive.render() for p in prefix.promotions)


def test_ambiguous_noise_and_duplicate_controls_reject():
    assert all(negative_controls().values())


def test_different_parameters_are_recovered_by_same_search():
    assert all(parameter_recovery_controls().values())


def test_under_supported_cluster_abstains():
    index = IndexAffinePrimitive(1, 1)
    rows = (
        ResidualRow(0, "abcd", index.apply("abcd")),
        ResidualRow(
            1,
            tuple(Fraction(x) for x in (1, 2, 3, 4)),
            index.apply(tuple(Fraction(x) for x in (1, 2, 3, 4))),
        ),
        ResidualRow(2, "lamp", index.apply("lamp")),
        ResidualRow(
            3,
            tuple(Fraction(x) for x in (5, 6, 7, 8)),
            index.apply(tuple(Fraction(x) for x in (5, 6, 7, 8))),
        ),
        ResidualRow(4, "quiet", index.apply("quiet")),
    )
    with pytest.raises(NoPromotablePrimitiveError):
        select_next_primitive(rows)


def test_all_phase18d12_theorem_checks_pass():
    payload = run()
    assert payload["all_theorem_checks_pass"]
    assert all(payload["theorem_checks"].values())
    assert payload["claim_boundary"]["candidate_meta_grammar_human_designed"]
    assert not payload["claim_boundary"]["llm_like_general_learning"]
    assert not payload["claim_boundary"]["high_school_intelligence"]
