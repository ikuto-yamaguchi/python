from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn.functional as F
from PIL import Image

from .dataset import _load_gray, make_input_tensor
from .models import build_model
from .utils import read_annotations


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="高解像度画像をタイル走査してOK/NG判定する")
    p.add_argument("--data-root", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out-csv", default="tile_predictions.csv")
    p.add_argument("--tile-size", type=int, default=None)
    p.add_argument("--stride", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--device", default="cpu")
    p.add_argument("--ng-threshold", type=float, default=0.5)
    return p.parse_args()


def load_model(path: str, device: torch.device):
    ckpt = torch.load(path, map_location=device)
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt


def resolve(root: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else root / p


def tile_positions(h: int, w: int, tile: int, stride: int) -> List[Tuple[int, int]]:
    ys = list(range(0, max(h - tile, 0) + 1, stride))
    xs = list(range(0, max(w - tile, 0) + 1, stride))
    if not ys or ys[-1] != max(h - tile, 0):
        ys.append(max(h - tile, 0))
    if not xs or xs[-1] != max(w - tile, 0):
        xs.append(max(w - tile, 0))
    return [(y, x) for y in ys for x in xs]


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    model, ckpt = load_model(args.checkpoint, device)
    classes: List[str] = ckpt["classes"]
    ok_idx = classes.index("OK") if "OK" in classes else 0
    ng_indices = [i for i, c in enumerate(classes) if c != "OK"]
    tile = args.tile_size or ckpt.get("tile_size", ckpt.get("model_input_size", 256))
    stride = args.stride or max(1, tile // 2)
    root = Path(args.data_root)
    rows = read_annotations(args.csv)
    out_rows = []

    with torch.no_grad():
        for row in rows:
            sem = _load_gray(resolve(root, row["sem"]))
            design = _load_gray(resolve(root, row["design"]))
            full = make_input_tensor(
                sem,
                design,
                image_size=ckpt["image_size"],
                input_mode=ckpt["input_mode"],
                design_blur_radius=ckpt["design_blur_radius"],
            )
            c, h, w = full.shape
            positions = tile_positions(h, w, tile, stride)
            probs = []
            best_tile = (0, 0)
            best_ng = -1.0
            for start in range(0, len(positions), args.batch_size):
                batch_pos = positions[start : start + args.batch_size]
                tiles = []
                for y, x in batch_pos:
                    patch = full[:, y : y + tile, x : x + tile]
                    if patch.shape[-2:] != (tile, tile):
                        patch = F.pad(patch, (0, tile - patch.shape[-1], 0, tile - patch.shape[-2]))
                    tiles.append(patch)
                x_batch = torch.stack(tiles, dim=0).to(device)
                prob = torch.softmax(model(x_batch)["logits"], dim=1).cpu()
                probs.append(prob)
                if ng_indices:
                    ng_score_batch = prob[:, ng_indices].max(dim=1).values
                    local_best = int(ng_score_batch.argmax().item())
                    if float(ng_score_batch[local_best]) > best_ng:
                        best_ng = float(ng_score_batch[local_best])
                        best_tile = batch_pos[local_best]
            all_prob = torch.cat(probs, dim=0)
            if ng_indices:
                ng_score = float(all_prob[:, ng_indices].max().item())
                pred = "NG" if ng_score >= args.ng_threshold else "OK"
                ok_score = 1.0 - ng_score
            else:
                best_prob, best_idx = all_prob.max(dim=1)
                i = int(best_prob.argmax().item())
                pred = classes[int(best_idx[i].item())]
                ok_score = float(all_prob[i, ok_idx])
                ng_score = 0.0
            out_rows.append({
                "sem": row["sem"],
                "design": row["design"],
                "true_label": row["label"],
                "pred": pred,
                "ok_score": f"{ok_score:.6f}",
                "ng_score": f"{ng_score:.6f}",
                "best_tile_y": best_tile[0],
                "best_tile_x": best_tile[1],
                "tile_size": tile,
                "stride": stride,
                "num_tiles": len(positions),
            })
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
