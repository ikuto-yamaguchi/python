from minimal_predictive_lm.sparc_perspective_state import SPARCHS15Model
from minimal_predictive_lm.sparc_hs15_experiment import configured_model


def test_actual_belief_reference_cause_and_persistence(tmp_path):
    model = configured_model()
    assert model.reply("実際、鍵はどこにある？").text.startswith("箱です")
    assert model.reply("健は鍵がどこにあると思っている？").text.startswith("机です")
    assert model.reply("花子は鍵がどこにあると思っている？").text.startswith("箱です")
    assert model.reply("彼はそれがどこにあると思っている？").text.startswith("箱です")
    record = model.perspective.apply_event(
        "花子がそれを戸棚へ移した。", source_id="再移動"
    )
    assert record is not None and record.object_name == "鍵"
    assert model.reply("実際、鍵はどこにある？").text.startswith("戸棚です")
    assert model.reply("健は鍵がどこにあると思っている？").text.startswith("机です")
    cause = model.reply("鍵が戸棚にある直接の原因は？")
    assert "花子がそれを戸棚へ移した" in cause.text
    path = tmp_path / "hs15.model"
    model.save(path)
    restored = SPARCHS15Model.load(path)
    assert restored.reply("健は鍵がどこにあると思っている？").text.startswith("机です")
    assert "再移動" in restored.reply("鍵が戸棚にある直接の原因は？").text


def test_no_global_scans_and_bounded_focus():
    model = configured_model()
    model.reply("花子は鍵がどこにあると思っている？")
    reply = model.reply("彼はそれがどこにあると思っている？")
    report = model.perspective.report()
    assert reply.estimated_sparse_operations <= 32
    assert report["last_focus_reads"] <= 4
    assert report["global_world_scan_used"] is False
    assert report["global_belief_scan_used"] is False
    assert report["full_history_scan_used"] is False


def test_hs14_counterexample_guard_is_retained():
    model = configured_model()
    model.base.ingest_fact("視点冬眠個体の分類は哺乳類である。", source_id="分類")
    model.base.ingest_fact("視点冬眠個体の季節状態は冬眠中である。", source_id="季節")
    reply = model.reply("視点冬眠個体の活動状態は何ですか？")
    assert reply.mechanism == "counterexample-guarded-rule"
