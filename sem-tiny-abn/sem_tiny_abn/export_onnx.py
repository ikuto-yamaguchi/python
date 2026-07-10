from __future__ import annotations

import argparse
from pathlib import Path

import torch

from .runtime import load_checkpoint_model


class ExportWrapper(torch.nn.Module):
    def __init__(self, model: torch.nn.Module, include_attention: bool) -> None:
        super().__init__(); self.model = model; self.include_attention = include_attention
    def forward(self, x: torch.Tensor):
        output = self.model(x)
        if self.include_attention and "attention" in output:
            return output["logits"], output["attention"]
        return output["logits"]


def main() -> None:
    parser = argparse.ArgumentParser(description="学習済みモデルをONNXへ変換する")
    parser.add_argument("--checkpoint", required=True); parser.add_argument("--out", required=True)
    parser.add_argument("--opset", type=int, default=17); parser.add_argument("--include-attention", action="store_true")
    args = parser.parse_args()
    model, checkpoint = load_checkpoint_model(args.checkpoint, torch.device("cpu"))
    image_size = int(checkpoint.get("config", {}).get("image_size", checkpoint.get("image_size", 512)))
    dummy = torch.randn(1, checkpoint["in_channels"], image_size, image_size)
    wrapper = ExportWrapper(model, args.include_attention).eval()
    output_names = ["logits", "attention"] if args.include_attention and checkpoint["model"] != "tiny_cnn" else ["logits"]
    dynamic_axes = {"input": {0: "batch"}, "logits": {0: "batch"}}
    if "attention" in output_names: dynamic_axes["attention"] = {0: "batch"}
    output_path = Path(args.out); output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(wrapper, dummy, output_path.as_posix(), opset_version=args.opset, input_names=["input"], output_names=output_names, dynamic_axes=dynamic_axes, do_constant_folding=True)
    print(f"saved: {output_path}")


if __name__ == "__main__": main()
