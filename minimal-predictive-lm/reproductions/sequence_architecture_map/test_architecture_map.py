from __future__ import annotations

import json
from pathlib import Path

import torch

from architecture_map import run_experiment
from model_registry import ARCH_CLASSES, build_model
from suite import TASKS, MixedSequenceDataset, collate
from capacity_control import run as run_capacity_control


def test_all_models_share_language_model_interface() -> None:
    tokens = torch.tensor([[1, 3, 19, 7, 25, 16]])
    for name in ARCH_CLASSES:
        model = build_model(name, target_parameters=7_000)
        logits, _ = model(tokens)
        assert logits.shape[:2] == tokens.shape
        assert logits.shape[-1] > 30


def test_recurrent_state_is_constant_but_transformer_cache_grows() -> None:
    for name in ("gru", "diag_ssm", "deltanet", "rwkv7"):
        model = build_model(name, target_parameters=7_000)
        assert model.state_bytes(32) == model.state_bytes(512)
    transformer = build_model("transformer", target_parameters=7_000)
    assert transformer.state_bytes(512) == transformer.state_bytes(32) * 16


def test_mixed_dataset_uses_one_model_across_all_tasks() -> None:
    dataset = MixedSequenceDataset(16, seed=3, held_out=False, depth=2)
    assert {example.task for example in dataset.examples} == set(TASKS)
    inputs, targets, answer_mask, task_ids = collate(dataset.examples[:8])
    assert inputs.shape == targets.shape == answer_mask.shape
    assert int(answer_mask.sum()) >= len(dataset.examples[:8])
    assert set(task_ids.tolist()).issubset(set(range(len(TASKS))))


def test_quick_reports_keep_claim_boundaries(tmp_path: Path) -> None:
    architecture_report = run_experiment(tmp_path / "architecture.json", quick=True)
    control_report = run_capacity_control(tmp_path / "controls.json", quick=True)
    assert architecture_report["claim_scope"]["completion"] is False
    assert architecture_report["claim_scope"]["highschool_level_passed"] is False
    assert control_report["completion"] is False
    assert json.loads((tmp_path / "architecture.json").read_text())["aggregate"]
