import numpy as np

from minimal_predictive_lm.sacs_core import (
    FullHistoryAttentionMemory,
    SelectiveAssociativeState,
)


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def test_sacs_state_is_fixed_and_delta_updates() -> None:
    memory = SelectiveAssociativeState(
        key_dim=16,
        value_dim=8,
        blocks=8,
        top_k=1,
        decays=[1.0] * 8,
        seed=3,
    )
    before = memory.report().total_bytes
    key = _unit(np.arange(1, 17, dtype=np.float32))
    value = _unit(np.arange(1, 9, dtype=np.float32))
    first_loss = memory.update(key, value)
    second_loss = memory.update(key, value)
    prediction = memory.read(key)
    after = memory.report().total_bytes
    assert after == before
    assert second_loss < first_loss
    assert float(prediction @ value) > 0.9


def test_full_history_cache_grows_but_sacs_does_not() -> None:
    sacs = SelectiveAssociativeState(
        key_dim=16,
        value_dim=8,
        blocks=4,
        top_k=1,
        decays=[1.0] * 4,
    )
    full = FullHistoryAttentionMemory(16, 8)
    fixed_bytes = sacs.report().total_bytes
    for index in range(100):
        key = _unit(np.roll(np.arange(1, 17, dtype=np.float32), index % 16))
        value = _unit(np.roll(np.arange(1, 9, dtype=np.float32), index % 8))
        sacs.write(key, value)
        full.write(key, value)
    assert sacs.report().total_bytes == fixed_bytes
    assert full.total_bytes > 100 * 16


def test_route_is_sparse() -> None:
    memory = SelectiveAssociativeState(key_dim=32, value_dim=8, blocks=16, top_k=2)
    selected = memory.route(np.ones(32, dtype=np.float32))
    assert len(selected) == 2
    assert len(set(int(index) for index in selected)) == 2
