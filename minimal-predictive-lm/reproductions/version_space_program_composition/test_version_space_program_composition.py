import random

from version_space_program_composition import (
    VersionSpaceComposer,
    make_episode,
)


def trained_model():
    rng = random.Random(1)
    seqs = [make_episode(rng, renamed=i % 2 == 0, chain_len=1 + i % 4)[0] for i in range(32)]
    model = VersionSpaceComposer()
    model.fit(seqs)
    return model


def test_composes_four_unseen_surface_operations():
    model = trained_model()
    seq, answer = make_episode(random.Random(44), renamed=True, chain_len=4, demos_per_op=4)
    history = seq[: seq.index("回答") + 1]
    pred, _, _, status = model.predict(history)
    assert status == "resolved"
    assert pred == answer


def test_abstains_when_partial_demonstrations_leave_multiple_programs():
    model = trained_model()
    rng = random.Random(91)
    statuses = []
    for _ in range(64):
        seq, _ = make_episode(rng, renamed=True, chain_len=3, demos_per_op=1)
        history = seq[: seq.index("回答") + 1]
        statuses.append(model.predict(history)[3])
    assert statuses.count("ambiguous") >= 40


def test_semantically_wrong_but_functionally_consistent_demo_is_not_detectable():
    model = trained_model()
    seq, _ = make_episode(random.Random(7), renamed=True, chain_len=3, demos_per_op=4, noisy=True)
    history = seq[: seq.index("回答") + 1]
    _, _, _, status = model.predict(history)
    assert status == "resolved"
