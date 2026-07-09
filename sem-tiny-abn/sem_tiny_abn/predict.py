from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader

from .dataset import SEMPairDataset
from .models import build_model
from .utils import ensure_dir, read_annotations


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Predict with SEM Tiny ABN")
    p.add_argument("--data-root", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out-csv", default="predictions.csv")
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--device", default="cpu")
    p.add_argument("--ok-threshold", type=float, default=0.98, help="Only call OK when OK probability is above this")
    p.add_argument("--save-attention", default=None, help="Optional directory to save attention PNGs")
    return p.parse_args()


def load_model(path: str, device: torch.device):
    ckpt = torch.load(path, map_location=device)
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt


def save_attention_png(attn: torch.Tensor, out_path: Path) -> None:
    arr = attn.squeeze().detach().cpu().float().numpy()
    arr = arr - arr.min()
    arr = arr / (arr.max() + 1e-8)
    arr = (arr * 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="L").resize((256, 256), Image.BILINEAR)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    model, ckpt = load_model(args.checkpoint, device)
    classes: List[str] = ckpt["classes"]
    ok_idx = classes.index("OK") if "OK" in classes else 0
    rows = read_annotations(args.csv)
    ds = SEMPairDataset(rows, args.data_root, classes=classes, task=ckpt["task"], image_size=ckpt["image_size"], input_mode=ckpt["input_mode"], design_blur_radius=ckpt["design_blur_radius"], augment=False)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    out_rows = []
    attn_dir = ensure_dir(args.save_attention) if args.save_attention else None
    with torch.no_grad():
        global_i = 0
        for batch in loader:
            out = model(batch["x"].to(device))
            prob = F.softmax(out["logits"], dim=1).cpu()
            pred_idx = prob.argmax(dim=1).tolist()
            for b in range(prob.size(0)):
                p = prob[b]
                best = pred_idx[b]
                label = classes[best]
                if best == ok_idx and float(p[ok_idx]) < args.ok_threshold:
                    label = "REVIEW" if "REVIEW" in classes else "NG"
                item = {"sem": batch["sem"][b], "design": batch["design"][b], "true_label": batch["label"][b], "pred": label, "raw_pred": classes[best], "confidence": f"{float(p[best]):.6f}", "ok_prob": f"{float(p[ok_idx]):.6f}"}
                for ci, cname in enumerate(classes):
                    item[f"prob_{cname}"] = f"{float(p[ci]):.6f}"
                out_rows.append(item)
                if attn_dir is not None and "attention" in out:
                    save_attention_png(out["attention"][b], attn_dir / f"attn_{global_i:06d}.png")
                if attn_dir is not None and "attention_low" in out:
                    save_attention_png(out["attention_low"][b], attn_dir / f"attn_low_{global_i:06d}.png")
                    save_attention_png(out["attention_high"][b], attn_dir / f"attn_high_{global_i:06d}.png")
                global_i += 1
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
