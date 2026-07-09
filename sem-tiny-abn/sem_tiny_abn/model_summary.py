from __future__ import annotations

import argparse

import torch

from .models import build_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="モデルのパラメータ数と簡易速度を確認する")
    p.add_argument("--model", default="tiny_abn", choices=["tiny_cnn", "tiny_abn", "tiny_freq_abn"])
    p.add_argument("--in-channels", type=int, default=4)
    p.add_argument("--num-classes", type=int, default=2)
    p.add_argument("--width", type=float, default=1.0)
    p.add_argument("--image-size", type=int, default=512)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    model = build_model(args.model, args.in_channels, args.num_classes, args.width)
    params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    x = torch.randn(1, args.in_channels, args.image_size, args.image_size)
    with torch.no_grad():
        out = model(x)
    print({
        "model": args.model,
        "width": args.width,
        "image_size": args.image_size,
        "params": params,
        "trainable_params": trainable,
        "logits_shape": tuple(out["logits"].shape),
        "attention_shape": tuple(out["attention"].shape) if "attention" in out else None,
    })


if __name__ == "__main__":
    main()
