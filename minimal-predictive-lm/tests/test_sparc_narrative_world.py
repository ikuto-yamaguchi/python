from minimal_predictive_lm.sparc_narrative_world import NarrativeWorldLearner, parse_observation
from minimal_predictive_lm.sparc_narrative_world_gate import BASE, NOVEL, training_documents


def test_learns_programs_from_raw_documents_only():
    model = NarrativeWorldLearner()
    assert model.learn_documents(training_documents(BASE, 31, count_each=8), reset=True) == 6
    assert model.report()["explicit_state_maps_supplied_to_training_api"] is False


def test_multiturn_state_and_ellipsis():
    model = NarrativeWorldLearner()
    model.learn_documents(training_documents(BASE, 32, count_each=16), reset=True)
    assert model.respond("会話倉庫の在庫は30だった。") == "内容を内部状態に反映しました。"
    assert model.respond("会話倉庫は5を追加した。") == "内容を内部状態に反映しました。"
    assert model.respond("さらに3を消費した。") == "内容を内部状態に反映しました。"
    assert model.respond("会話倉庫の在庫はいくつですか？") == "会話倉庫は32です。"


def test_continual_program_growth_and_unknown_safety():
    model = NarrativeWorldLearner()
    assert model.learn_documents(training_documents(BASE, 33, count_each=12), reset=True) == 6
    assert model.learn_documents(training_documents(NOVEL, 34, count_each=12), reset=False) == 8
    model.reset_session()
    model.observe("保全庫の在庫は44だった。")
    before = dict(model.state)
    result = model.observe("保全庫は静かな夜空を眺めた。")
    assert model.state == before
    assert result.mechanism.startswith("abstain")
    restored = NarrativeWorldLearner.from_bytes(model.to_bytes())
    assert restored.state == model.state
    assert restored.report()["programs"] == 8


def test_observation_parser_does_not_mistake_events_for_state():
    assert parse_observation("青倉庫の在庫は20だった") == ("青倉庫", 20)
    assert parse_observation("青倉庫へ5を追加した") is None
