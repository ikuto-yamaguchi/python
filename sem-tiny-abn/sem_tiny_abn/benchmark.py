from __future__ import annotations

import argparse
import time

import torch

from .models import build_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark SEM Tiny ABN latency")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--iters", type=int, default=300)
    p.add_argument("--warmup", type=int, default=30)
    p.add_argument("--device", default="cpu")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    ckpt = torch.load(args.checkpoint, map_location=device)
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    x = torch.randn(args.batch_size, ckpt["in_channels"], ckpt["image_size"], ckpt["image_size"], device=device)
    with torch.no_grad():
        for _ in range(args.warmup):
            _ = model(x)["logits"]
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(args.iters):
            _ = model(x)["logits"]
        if device.type == "cuda":
            torch.cuda.synchronize()
        t1 = time.perf_counter()
    total_ms = (t1 - t0) * 1000.0
    per_batch = total_ms / args.iters
    per_image = per_batch / args.batch_size
    print({"per_batch_ms": per_batch, "per_image_ms": per_image, "batch_size": args.batch_size})


if __name__ == "__main__":
    main()
