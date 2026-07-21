from pathlib import Path
import random
import tempfile

from interference_bounded_consolidation import Memory, episode, feat, run


def test_stable_feature_is_deterministic():
    history = ["<bos>", "記録", "葵", "は", "赤"]
    a = feat(history)
    b = feat(history)
    assert a.shape == (64,)
    assert (a == b).all()


def test_all_families_generate_answer():
    rng = random.Random(1)
    for family in ("memory", "arithmetic", "causal", "plan"):
        seq = episode(rng, family, depth=2)
        assert seq[0] == "<bos>"
        assert seq[-1] == "<eos>"
        assert "回答" in seq


def test_interference_method_tracks_rejections():
    m = Memory("interference_bounded")
    x = feat(["<bos>", "質問", "葵"])
    for y in range(8):
        m.observe(x, y)
    assert m.proposed == 8
    assert m.accepted + m.rejected == 8


def test_full_report_keeps_claim_boundary():
    with tempfile.TemporaryDirectory() as d:
        report = run(Path(d) / "report.json")
    assert report["claim"]["completion"] is False
    assert report["claim"]["highschool_level_passed"] is False
    assert set(report["aggregate"]) == {"immediate", "surprise", "interference_bounded"}
