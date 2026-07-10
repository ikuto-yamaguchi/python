from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import torch

from .dataset import SEMPairDataset
from .models import build_model


MODEL_KEYS = (
    "width",
    "depth",
    "norm",
    "block_type",
    "expansion",
    "dropout",
    "pooling",
)

DATASET_KEYS = (
    "image_size",
    "input_mode",
    "normalize_mode",
    "sem_invert",
    "design_invert",
    "design_blur_radius",
    "diff_tolerance_px",
    "cache_size",
)


def checkpoint_model_kwargs(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    config = checkpoint.get("config", {})
    return {key: config[key] for key in MODEL_KEYS if key in config}


def checkpoint_dataset_kwargs(checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    config = checkpoint.get("config", {})
    result = {key: config[key] for key in DATASET_KEYS if key in config}
    # 古いcheckpoint互換
    for key in ("image_size", "input_mode", "design_blur_radius"):
        if key not in result and key in checkpoint:
            result[key] = checkpoint[key]
    return result


def load_checkpoint_model(path: str | Path, device: torch.device) -> tuple[torch.nn.Module, Dict[str, Any]]:
    checkpoint = torch.load(path, map_location=device)
    model = build_model(
        checkpoint["model"],
        checkpoint["in_channels"],
        checkpoint["num_classes"],
        **checkpoint_model_kwargs(checkpoint),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device).eval()
    return model, checkpoint


def make_dataset(
    rows,
    data_root,
    checkpoint: Dict[str, Any],
    augment: bool = False,
) -> SEMPairDataset:
    return SEMPairDataset(
        rows,
        data_root,
        classes=checkpoint["classes"],
        task=checkpoint.get("task", "multiclass"),
        augment=augment,
        **checkpoint_dataset_kwargs(checkpoint),
    )
