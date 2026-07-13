from functools import lru_cache

import minimal_predictive_lm.phase18d11_ungrouped_online_residual as m


@lru_cache(maxsize=1)
def fixture():
    payload = m.load_dataset()
    records = tuple(payload["stream"])
    result = m.online_learn(records)
    return payload, records, result


def test_stream_has_no_task_or_group_fields():
    _, records, _ = fixture()
    assert all(set(row) == {"input", "output"} for row in records)


def test_cross_type_primitive_is_promoted_from_ungrouped_residuals():
    payload, _, result = fixture()
    assert result.promotion is not None
    assert result.promotion.position == 16
    assert result.promotion.candidates_evaluated == 170
    assert set(result.promotion.support_types) == {"string", "number_list"}
    assert all(
        payload["audit_labels"][position] == "HIDDEN"
        for position in result.promotion.support_positions
    )
    assert isinstance(result.primitive, m.IndexAffinePrimitive)
    assert (result.primitive.multiplier, result.primitive.offset) == (1, 1)


def test_primitive_generalizes_to_every_future_hidden_record():
    payload, records, result = fixture()
    correct, total = m._invented_future_accuracy(
        result,
        records,
        payload["audit_labels"],
    )
    assert total == 10
    assert correct == total


def test_online_errors_are_confined_to_change_regret_or_noise():
    payload, records, result = fixture()
    labels = payload["audit_labels"]
    changes = {
        index
        for index in range(1, len(labels))
        if labels[index] != labels[index - 1]
    }
    allowed = (
        changes
        | {index + 1 for index in changes}
        | {
            index
            for index, label in enumerate(labels)
            if label == "NOISE"
        }
    )
    wrong = set()
    for index, (prediction, row) in enumerate(
        zip(result.predictions, records)
    ):
        if (
            prediction is not None
            and m.canonical(prediction)
            != m.canonical(m.decode(row["output"]))
        ):
            wrong.add(index)
    assert wrong <= allowed


def test_noise_and_competing_behaviors_do_not_promote():
    _, records, _ = fixture()
    assert all(m.negative_controls(records).values())


def test_all_phase18d11_theorem_checks_pass():
    result = m.run()
    assert result["all_theorem_checks_pass"]
    assert all(result["theorem_checks"].values())
    assert result["claim_boundary"]["raw_byte_stream"] is False
    assert result["claim_boundary"]["meta_grammar_human_designed"] is True
    assert result["claim_boundary"]["llm_like_general_learning"] is False
