import torch

from model_registry import build_model
from optimizer_coupling import CompositeOptimizer, zeropower_via_newtonschulz5, train_one


def test_newton_schulz_preserves_shape_and_finite_values():
    matrix = torch.randn(12, 8)
    result = zeropower_via_newtonschulz5(matrix)
    assert result.shape == matrix.shape
    assert torch.isfinite(result).all()


def test_muon_updates_all_architecture_families():
    for architecture in ("gru", "transformer", "rwkv7", "deltanet"):
        model = build_model(architecture)
        optimizer = CompositeOptimizer(model, "muon")
        before = [parameter.detach().clone() for parameter in model.parameters()]
        loss = sum(parameter.square().mean() for parameter in model.parameters())
        loss.backward()
        optimizer.step()
        assert any(not torch.equal(old, new) for old, new in zip(before, model.parameters()))


def test_quick_training_returns_bounded_metrics():
    metric = train_one("gru", "adamw", seed=1, train_examples=64, epochs=1)
    assert 0.0 <= metric.answer_accuracy <= 1.0
    assert 0.0 <= metric.stress_accuracy <= 1.0
    assert metric.parameters > 0
    assert metric.model_bytes < 1_000_000_000
    assert metric.candidate_count > 1
    assert metric.gradient_steps > 0
