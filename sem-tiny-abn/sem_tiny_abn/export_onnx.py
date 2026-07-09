from __future__ import annotations

import argparse
from pathlib import Path

import torch

from .models import build_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export SEM Tiny ABN to ONNX")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--opset", type=int, default=17)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ckpt = torch.load(args.checkpoint, map_location="cpu")
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    dummy = torch.randn(1, ckpt["in_channels"], ckpt["image_size"], ckpt["image_size"])

    class Wrapper(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            return self.m(x)["logits"]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        Wrapper(model), dummy, out_path.as_posix(), opset_version=args.opset,
        input_names=["input"], output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    )
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
