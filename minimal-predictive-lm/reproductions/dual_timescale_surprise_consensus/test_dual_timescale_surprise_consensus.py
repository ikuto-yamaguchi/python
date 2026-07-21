from pathlib import Path
import tempfile
from dual_timescale_surprise_consensus import Memory, feat, make_episode, run
import random


def test_feature_shape_and_episode():
    assert feat(["<bos>", "記録"]).shape == (64,)
    seq = make_episode(random.Random(1), depth=2)
    assert seq[0] == "<bos>" and seq[-1] == "<eos>"


def test_delayed_consensus_tracks_decisions():
    m = Memory("delayed_consensus")
    x = feat(["<bos>", "質問", "葵"])
    for _ in range(20):
        m.observe(x, 1, (x, 1))
    assert m.proposed > 0
    assert m.accepted + m.rejected > 0


def test_full_report_claim_boundary():
    with tempfile.TemporaryDirectory() as d:
        report = run(Path(d) / "report.json")
    assert report["claim"]["completion"] is False
    assert report["claim"]["highschool_level_passed"] is False
    assert set(report["aggregate"]) == {"immediate", "surprise", "delayed_consensus"}
