from __future__ import annotations

import importlib.util
from pathlib import Path

import torch

MODULE_PATH = Path(__file__).with_name("baseline_reproduction.py")
spec = importlib.util.spec_from_file_location("baseline_reproduction", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_models_emit_expected_shape() -> None:
    tokens = torch.tensor([[module.BOS_ID, module.TOKEN_TO_ID["記録"], module.TOKEN_TO_ID["葵"]]])
    for model in (module.TinyGRULM(), module.TinyTransformerLM()):
        logits = model(tokens)
        assert logits.shape == (1, 3, len(module.TOKENS))


def test_state_accounting_distinguishes_constant_and_growing_memory() -> None:
    gru = module.TinyGRULM()
    transformer = module.TinyTransformerLM()
    assert gru.state_elements(16) == gru.state_elements(1024)
    assert transformer.state_elements(1024) == transformer.state_elements(16) * 64


def test_dataset_has_no_answer_label_side_channel() -> None:
    dataset = module.StateTrackingDataset(8, seed=17, held_out=True, depth=5)
    for ids, answer_position in dataset:
        assert ids[answer_position].item() in [module.TOKEN_TO_ID[color] for color in module.COLORS]
        assert ids[answer_position - 1].item() == module.TOKEN_TO_ID["回答"]
