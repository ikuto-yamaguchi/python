from __future__ import annotations

from typing import Optional

import torch
import torch.nn.functional as F


def focal_cross_entropy(
    logits: torch.Tensor,
    target: torch.Tensor,
    weight: Optional[torch.Tensor] = None,
    gamma: float = 0.0,
    label_smoothing: float = 0.0,
) -> torch.Tensor:
    raw_ce = F.cross_entropy(logits, target, reduction="none", label_smoothing=label_smoothing)
    sample_weight = weight.gather(0, target.long()) if weight is not None else torch.ones_like(raw_ce)
    if gamma > 0:
        pt = torch.exp(-raw_ce).clamp(min=1e-6, max=1.0)
        raw_ce = ((1.0 - pt) ** gamma) * raw_ce
    return (raw_ce * sample_weight).mean()


def bce_multilabel(
    logits: torch.Tensor,
    target: torch.Tensor,
    pos_weight: Optional[torch.Tensor] = None,
    gamma: float = 0.0,
) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target.float(), pos_weight=pos_weight, reduction="none")
    if gamma > 0:
        probability = torch.sigmoid(logits)
        pt = torch.where(target > 0.5, probability, 1.0 - probability).clamp(min=1e-6, max=1.0)
        bce = ((1.0 - pt) ** gamma) * bce
    return bce.mean()


def _single_loss(logits, target, task, class_weight, pos_weight, focal_gamma, label_smoothing):
    if task == "multiclass":
        return focal_cross_entropy(logits, target.long(), class_weight, focal_gamma, label_smoothing)
    if task == "multilabel":
        return bce_multilabel(logits, target.float(), pos_weight, focal_gamma)
    raise ValueError(f"Unknown task: {task}")


def compute_loss(
    output: dict,
    target: torch.Tensor,
    task: str,
    class_weight: Optional[torch.Tensor] = None,
    pos_weight: Optional[torch.Tensor] = None,
    aux_weight: float = 1.0,
    focal_gamma: float = 0.0,
    label_smoothing: float = 0.0,
) -> tuple[torch.Tensor, dict[str, float]]:
    main = _single_loss(output["logits"], target, task, class_weight, pos_weight, focal_gamma, label_smoothing)
    auxiliary_logits = []
    if "aux_logits_low" in output and "aux_logits_high" in output:
        auxiliary_logits.extend([output["aux_logits_low"], output["aux_logits_high"]])
    elif "aux_logits" in output:
        auxiliary_logits.append(output["aux_logits"])
    if auxiliary_logits:
        auxiliary = torch.stack([
            _single_loss(logits, target, task, class_weight, pos_weight, focal_gamma, label_smoothing)
            for logits in auxiliary_logits
        ]).mean()
        total = main + float(aux_weight) * auxiliary
    else:
        auxiliary = torch.zeros((), device=main.device)
        total = main
    return total, {"main_loss": float(main.detach()), "aux_loss": float(auxiliary.detach())}
