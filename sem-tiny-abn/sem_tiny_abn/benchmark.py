from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch

from .dataset import build_input_tensor, load_gray
from .runtime import checkpoint_dataset_kwargs, load_checkpoint_model
from .utils import load_yaml, read_annotations


def main() -> None:
    parser = argparse.ArgumentParser(description="PyTorch推論と前処理の時間を測る")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--with-preprocess", action="store_true")
    args = parser.parse_args()
    config = load_yaml(args.config)
    checkpoint_path = args.checkpoint or config.get("checkpoint") or str(Path(config.get("out", "runs/sem_tiny_abn")) / "best.pt")
    device = torch.device(args.device or config.get("device", "cpu"))
    if device.type == "cpu": torch.set_num_threads(max(1, args.threads))
    model, checkpoint = load_checkpoint_model(checkpoint_path, device)
    preprocess = checkpoint_dataset_kwargs(checkpoint)
    image_size = int(preprocess.get("image_size", 512))
    x = torch.randn(1, checkpoint["in_channels"], image_size, image_size, device=device)
    with torch.no_grad():
        for _ in range(args.warmup): model(x)
        if device.type == "cuda": torch.cuda.synchronize()
        start = time.perf_counter()
        for _ in range(args.iterations): model(x)
        if device.type == "cuda": torch.cuda.synchronize()
        model_ms = (time.perf_counter() - start) * 1000 / args.iterations
    result = {"model_ms_per_image": model_ms, "device": str(device), "threads": args.threads}
    if args.with_preprocess:
        rows = read_annotations(config["csv"])
        root = Path(config["data_root"]); row = rows[0]
        sem_path = Path(row["sem"]); design_path = Path(row["design"])
        sem_path = sem_path if sem_path.is_absolute() else root / sem_path
        design_path = design_path if design_path.is_absolute() else root / design_path
        sem = load_gray(sem_path); design = load_gray(design_path)
        count = min(args.iterations, 20); start = time.perf_counter()
        for _ in range(count):
            build_input_tensor(
                sem, design, image_size=image_size, input_mode=str(preprocess.get("input_mode", "sem_design_posneg")),
                normalize_mode=str(preprocess.get("normalize_mode", "percentile")), sem_invert=str(preprocess.get("sem_invert", "auto")),
                design_invert=bool(preprocess.get("design_invert", False)), design_blur_radius=float(preprocess.get("design_blur_radius", 1.0)),
                diff_tolerance_px=int(preprocess.get("diff_tolerance_px", 2)),
            )
        result["preprocess_ms_per_pair"] = (time.perf_counter() - start) * 1000 / count
        result["estimated_end_to_end_ms"] = result["model_ms_per_image"] + result["preprocess_ms_per_pair"]
    print(result)


if __name__ == "__main__": main()
