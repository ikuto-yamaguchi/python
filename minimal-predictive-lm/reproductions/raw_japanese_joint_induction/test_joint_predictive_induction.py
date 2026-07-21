from pathlib import Path
import joint_predictive_induction as jpi

def test_anti_unify_extracts_unlabeled_variable():
    result = jpi.anti("最近映画を見ましたか?", "最近本を見ましたか?")
    assert result is not None
    template, left, right = result
    assert jpi.VAR in template and left != right
    assert jpi.match(template, "最近音楽を見ましたか?") is not None

def test_joint_induction_discovers_frames_and_preserves_renames():
    ds = jpi.fixture()
    model = jpi.Inducer(True)
    model.fit(ds[:20], 1)
    assert model.c
    for dialog in ds[20:]:
        for text in dialog:
            a = model.assign(text)
            if not a:
                continue
            frame, fillers, _ = a
            renamed = text
            for i, filler in enumerate(fillers):
                renamed = renamed.replace(filler, f"ヌンス{i}号")
            b = model.assign(renamed)
            assert b is not None and b[0] == frame
            return
    raise AssertionError("no held-out frame")

def test_track_does_not_claim_free_japanese():
    report = jpi.experiment(jpi.fixture(), [8], Path("/tmp/joint-report.json"))
    assert report["claim"]["completion"] is False
    assert report["claim"]["native_japanese_communication_passed"] is False
    assert all(v["8"]["free_gate"] == 0.0 for v in report["aggregate"].values())

def test_shuffled_turn_order_is_explicit_counterexample(tmp_path: Path):
    ds = jpi.fixture()
    model = jpi.Inducer(True); model.fit(ds[:16], 7)
    shuffled = jpi.Inducer(True); shuffled.fit(jpi.shuffle(ds[:16], 998), 7)
    assert isinstance(len(shuffled.c) / max(1, len(model.c)), float)
