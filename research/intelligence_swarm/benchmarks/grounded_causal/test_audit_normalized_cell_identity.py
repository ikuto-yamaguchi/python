#!/usr/bin/env python3
from audit_normalized_cell_identity import audit


def row(instance_id, domain="rtfm", condition="entity_holdout"):
    return {
        "instance_id": instance_id,
        "domain": domain,
        "seed": 1,
        "split": "test",
        "condition": condition,
        "utterance": "x",
        "state_before": {},
        "gold_action": 0,
        "gold_state_after": {},
    }


def test_distinct_cells_pass():
    result = audit([
        row("a", domain="rtfm", condition="entity_holdout"),
        row("b", domain="silg", condition="dynamics_holdout"),
    ])
    assert result["valid"], result


def test_unicode_case_domain_alias_fails():
    result = audit([
        row("a", domain="RTFM"),
        row("b", domain="ＲＴＦＭ"),
    ])
    assert not result["valid"]
    assert result["classification"] == "initial_reproduction_failure"
    assert any(f["field"] == "domain" for f in result["findings"])


def test_invisible_space_domain_alias_fails():
    result = audit([
        row("a", domain="dark world"),
        row("b", domain="dark\u200bworld"),
    ])
    assert not result["valid"]


def test_condition_order_and_separator_alias_fails():
    result = audit([
        row("a", condition="entity_holdout+dynamics_holdout"),
        row("b", condition="DYNAMICS_HOLDOUT | ENTITY_HOLDOUT"),
    ])
    assert not result["valid"]
    assert any(f["field"] == "condition" for f in result["findings"])


def test_empty_after_normalization_fails():
    result = audit([row("a", domain="\u200b \t")])
    assert not result["valid"]


if __name__ == "__main__":
    test_distinct_cells_pass()
    test_unicode_case_domain_alias_fails()
    test_invisible_space_domain_alias_fails()
    test_condition_order_and_separator_alias_fails()
    test_empty_after_normalization_fails()
    print("normalized cell identity audit tests passed")
