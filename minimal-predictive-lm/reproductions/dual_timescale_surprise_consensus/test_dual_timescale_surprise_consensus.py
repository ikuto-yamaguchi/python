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
    # Conflicting observations keep the stream surprising after the replay
    # buffer matures, so the test actually exercises accept/reject decisions.
    for index in range(24):
        target = 1 + (index % 4)
        counter_target = 1 + ((index + 1) % 4)
        m.observe(x, target, (x, counter_target))
    assert m.proposed > 0
    assert m.accepted + m.rejected > 0
    assert m.accepted + m.rejected <= m.proposed


def test_full_report_claim_boundary():
    with tempfile.TemporaryDirectory() as d:
        report = run(Path(d) / "report.json")
    assert report["claim"]["completion"] is False
    assert report["claim"]["highschool_level_passed"] is False
    assert set(report["aggregate"]) == {"immediate", "surprise", "delayed_consensus"}
