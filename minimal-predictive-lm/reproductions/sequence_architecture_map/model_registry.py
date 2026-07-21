from __future__ import annotations

from models_baselines import DiagonalSSMLM, GRULM, TransformerLM
from models_memory import DeltaNetLM, RWKV7ProbeLM
from suite import TOKENS

ARCH_CLASSES = {
    "gru": GRULM,
    "diag_ssm": DiagonalSSMLM,
    "deltanet": DeltaNetLM,
    "rwkv7": RWKV7ProbeLM,
    "transformer": TransformerLM,
}


def build_model(name: str, target_parameters: int = 10_000):
    candidates = []
    for dim in (8, 12, 16, 20, 24, 28, 32, 40, 48):
        if name in ("deltanet", "rwkv7") and dim % 8:
            continue
        if name == "transformer" and dim % 2:
            continue
        try:
            model = ARCH_CLASSES[name](len(TOKENS), dim)
        except ValueError:
            continue
        parameters = sum(parameter.numel() for parameter in model.parameters())
        candidates.append((abs(parameters - target_parameters), model))
    if not candidates:
        raise ValueError(name)
    return min(candidates, key=lambda row: row[0])[1]
