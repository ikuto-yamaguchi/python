from __future__ import annotations

import argparse
import time
from typing import Dict

import torch
import torch.nn as nn

from .models import build_model


def count_macs(model: nn.Module, x: torch.Tensor) -> int:
    total = 0
    hooks = []
    def conv_hook(module: nn.Conv2d, inputs, output):
        nonlocal total
        batch, out_channels, out_h, out_w = output.shape
        kernel_ops = module.kernel_size[0] * module.kernel_size[1] * (module.in_channels // module.groups)
        total += int(batch * out_channels * out_h * out_w * kernel_ops)
    def linear_hook(module: nn.Linear, inputs, output):
        nonlocal total
        total += int(output.numel() * module.in_features)
    for module in model.modules():
        if isinstance(module, nn.Conv2d): hooks.append(module.register_forward_hook(conv_hook))
        elif isinstance(module, nn.Linear): hooks.append(module.register_forward_hook(linear_hook))
    with torch.no_grad(): model(x)
    for hook in hooks: hook.remove()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="モデル規模・MACs・PyTorch CPU速度を測る")
    parser.add_argument("--model", default="tiny_abn", choices=["tiny_cnn", "tiny_abn", "tiny_freq_abn"])
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--width", type=float, default=1.0)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--block-type", default="standard", choices=["standard", "mobile"])
    parser.add_argument("--norm", default="group", choices=["group", "batch", "none"])
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=50)
    args = parser.parse_args()
    torch.set_num_threads(max(1, args.threads))
    model = build_model(args.model, 4, 2, width=args.width, depth=args.depth, block_type=args.block_type, norm=args.norm).eval()
    x = torch.randn(1, 4, args.image_size, args.image_size)
    parameters = sum(parameter.numel() for parameter in model.parameters())
    macs = count_macs(model, x)
    with torch.no_grad():
        for _ in range(10): model(x)
        start = time.perf_counter()
        for _ in range(args.iterations): model(x)
        elapsed = time.perf_counter() - start
    output: Dict[str, object] = {
        "model": args.model, "block_type": args.block_type, "width": args.width, "depth": args.depth,
        "image_size": args.image_size, "parameters": parameters, "macs": macs, "macs_million": macs / 1_000_000,
        "pytorch_cpu_ms_per_image": elapsed * 1000 / args.iterations, "threads": args.threads,
    }
    print(output)


if __name__ == "__main__": main()
