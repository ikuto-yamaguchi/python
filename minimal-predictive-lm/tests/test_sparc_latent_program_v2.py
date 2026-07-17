import random
from minimal_predictive_lm.sparc_latent_program_v2 import (
    BASE, NOVEL, Learner, StateInducer, apply, derive, narratives,
    rows_for, state_sequence,
)


def test_generic_programs_execute() -> None:
    rng = random.Random(2102)
    rows = rows_for((*BASE, *NOVEL), True, rng)
    assert len({derive(row) for row in rows}) == 8
    assert all(apply(derive(row), row.text, row.before) == row.after for row in rows)


def test_continual_unseen_surface_transfer_and_restore() -> None:
    rng = random.Random(2102)
    base_train = rows_for(BASE, True, rng); base_test = rows_for(BASE, False, rng)
    novel_train = rows_for(NOVEL, True, rng); novel_test = rows_for(NOVEL, False, rng)
    model = Learner(); model.fit_corpus(narratives())
    before = model.learn(base_train, True)
    assert all(model.infer(row.text, row.before).after == row.after for row in base_test)
    after = model.learn(novel_train)
    assert (before, after) == (6, 8)
    restored = Learner.from_bytes(model.to_bytes())
    assert all(restored.infer(row.text, row.before).after == row.after for row in (*base_test, *novel_test))


def test_query_and_three_state_memory_are_discovered() -> None:
    sequence = state_sequence(211, ("春印", "夏印", "冬印"), ("暖答", "暑答", "寒答"), "照会", ("雑音甲", "雑音乙", "雑音丙"))
    result = StateInducer().fit(sequence)
    assert result.query == "照会"
    assert set(result.cues) == {"春印", "夏印", "冬印"}
    assert result.cardinality == 3
    assert result.gain_bits >= 500
