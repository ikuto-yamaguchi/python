from pathlib import Path
import sys

import pytest

torch = pytest.importorskip("torch")
sys.path.insert(0, str(Path(__file__).parent))
from rwkv7_reproduction import (  # noqa: E402
    TinyRWKV7LM,
    TOKENS,
    state_size_invariance,
    streaming_equivalence,
)


def test_streaming_matches_unsplit_recurrence():
    assert streaming_equivalence() < 1e-6


def test_recurrent_state_is_context_length_invariant():
    sizes = state_size_invariance()
    assert len(set(sizes.values())) == 1
    assert next(iter(sizes.values())) < 1_000_000


def test_delta_and_no_delta_have_identical_parameter_budget():
    full = TinyRWKV7LM(len(TOKENS), delta_enabled=True)
    ablated = TinyRWKV7LM(len(TOKENS), delta_enabled=False)
    assert sum(p.numel() for p in full.parameters()) == sum(p.numel() for p in ablated.parameters())


def test_forward_shapes_and_finite_values():
    model = TinyRWKV7LM(len(TOKENS), dim=24, n_layer=2, head_size=8)
    tokens = torch.randint(0, len(TOKENS), (3, 11))
    logits, state = model(tokens)
    assert logits.shape == (3, 11, len(TOKENS))
    assert torch.isfinite(logits).all()
    assert len(state) == 2
