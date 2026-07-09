from __future__ import annotations

import torch

from sem_tiny_abn.models import build_model


def test_tiny_abn_forward():
    model = build_model("tiny_abn", in_channels=4, num_classes=2, width=0.5)
    x = torch.randn(2, 4, 128, 128)
    out = model(x)
    assert out["logits"].shape == (2, 2)
    assert out["attention"].ndim == 4


def test_tiny_freq_abn_forward():
    model = build_model("tiny_freq_abn", in_channels=4, num_classes=2, width=0.5)
    x = torch.randn(2, 4, 128, 128)
    out = model(x)
    assert out["logits"].shape == (2, 2)
    assert out["attention_low"].ndim == 4
    assert out["attention_high"].ndim == 4
