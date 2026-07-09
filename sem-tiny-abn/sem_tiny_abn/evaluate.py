from __future__ import annotations

import argparse
from typing import List

import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader

from .dataset import SEMPairDataset
from .models import build_model
from .utils import read_annotations


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate SEM Tiny ABN checkpoint")
    p.add_argument("--data-root", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--device", default="cpu")
    return p.parse_args()


def load_model(path: str, device: torch.device):
    ckpt = torch.load(path, map_location=device)
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    model, ckpt = load_model(args.checkpoint, device)
    classes: List[str] = ckpt["classes"]
    rows = read_annotations(args.csv)
    ds = SEMPairDataset(rows, args.data_root, classes=classes, task=ckpt["task"], image_size=ckpt["image_size"], input_mode=ckpt["input_mode"], design_blur_radius=ckpt["design_blur_radius"], augment=False)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)
    y_true, y_pred = [], []
    ok_idx = classes.index("OK") if "OK" in classes else 0
    with torch.no_grad():
        for batch in loader:
            logits = model(batch["x"].to(device))["logits"]
            y_pred.extend(logits.argmax(dim=1).cpu().tolist())
            y_true.extend(batch["y"].cpu().tolist())
    print("classes:", classes)
    print("confusion_matrix:")
    print(confusion_matrix(y_true, y_pred, labels=list(range(len(classes)))))
    print(classification_report(y_true, y_pred, labels=list(range(len(classes))), target_names=classes, zero_division=0))
    false_ok = sum(1 for t, p in zip(y_true, y_pred) if t != ok_idx and p == ok_idx)
    false_ng = sum(1 for t, p in zip(y_true, y_pred) if t == ok_idx and p != ok_idx)
    print({"false_ok": false_ok, "false_ng": false_ng, "total": len(y_true)})


if __name__ == "__main__":
    main()
