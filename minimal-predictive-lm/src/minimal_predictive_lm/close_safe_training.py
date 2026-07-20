from __future__ import annotations

import torch

from .close_obligation_energy import (
    CloseConfig,
    ObligationSettlementEnergy,
    train_closure_head,
)


def train_closure_head_from_frozen_states(
    head: ObligationSettlementEnergy,
    open_states: torch.Tensor,
    positive_states: torch.Tensor,
    negative_states: torch.Tensor,
    cfg: CloseConfig,
) -> dict:
    """Turn inference tensors into ordinary constants before head backpropagation."""
    return train_closure_head(
        head,
        open_states.clone(),
        positive_states.clone(),
        negative_states.clone(),
        cfg,
    )
