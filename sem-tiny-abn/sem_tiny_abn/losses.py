from __future__ import annotations

from typing import Optional

import torch
import torch.nn.functional as F


def focal_cross_entropy(logits: torch.Tensor, target: torch.Tensor, weight: Optional[torch.Tensor] = None, gamma: float = 0.0) -> torch.Tensor:
    ce = F.cross_entropy(logits, target, weight=weight, reduction="none")
    if gamma <= 0:
        return ce.mean()
    pt = torch.exp(-ce).clamp(min=1e-6, max=1.0)
    return ((1.0 - pt) ** gamma * ce).mean()


def bce_multilabel(logits: torch.Tensor, target: torch.Tensor, pos_weight: Optional[torch.Tensor] = None, gamma: float = 0.0) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target.float(), pos_weight=pos_weight, reduction="none")
    if gamma <= 0:
        return bce.mean()
    prob = torch.sigmoid(logits)
    pt = torch.where(target > 0.5, prob, 1.0 - prob).clamp(min=1e-6, max=1.0)
    return ((1.0 - pt) ** gamma * bce).mean()


def compute_loss(
    out: dict,
    target: torch.Tensor,
    task: str,
    class_weight: Optional[torch.Tensor] = None,
    pos_weight: Optional[torch.Tensor] = None,
    aux_weight: float = 0.35,
    focal_gamma: float = 0.0,
) -> torch.Tensor:
    if task == "multiclass":
        main = focal_cross_entropy(out["logits"], target.long(), weight=class_weight, gamma=focal_gamma)
        if "aux_logits" in out:
            aux = focal_cross_entropy(out["aux_logits"], target.long(), weight=class_weight, gamma=focal_gamma)
            return main + aux_weight * aux
        return main
    if task == "multilabel":
        main = bce_multilabel(out["logits"], target.float(), pos_weight=pos_weight, gamma=focal_gamma)
        if "aux_logits" in out:
            aux = bce_multilabel(out["aux_logits"], target.float(), pos_weight=pos_weight, gamma=focal_gamma)
            return main + aux_weight * aux
        return main
    raise ValueError(f"Unknown task: {task}")
