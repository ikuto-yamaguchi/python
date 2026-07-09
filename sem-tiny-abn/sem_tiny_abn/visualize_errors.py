from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader

from .dataset import SEMPairDataset
from .models import build_model
from .utils import ensure_dir, read_annotations


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="誤判定をSEM/Design/差分/Attentionの俯瞰画像として保存する")
    p.add_argument("--data-root", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", default="runs/sem_tiny_abn/error_report")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--device", default="cpu")
    p.add_argument("--max-save", type=int, default=200)
    return p.parse_args()


def load_model(path: str, device: torch.device):
    ckpt = torch.load(path, map_location=device)
    model = build_model(ckpt["model"], ckpt["in_channels"], ckpt["num_classes"], ckpt.get("width", 1.0))
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, ckpt


def to_u8(t: torch.Tensor) -> Image.Image:
    arr = t.detach().cpu().float().squeeze().numpy()
    arr = arr - arr.min()
    arr = arr / (arr.max() + 1e-8)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="L")


def tile_with_label(img: Image.Image, label: str, size: int = 256) -> Image.Image:
    img = img.resize((size, size), Image.BILINEAR).convert("L")
    canvas = Image.new("RGB", (size, size + 24), "white")
    canvas.paste(img.convert("RGB"), (0, 24))
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 5), label, fill=(0, 0, 0))
    return canvas


def make_montage(x: torch.Tensor, attention: Optional[torch.Tensor], title: str, out_path: Path) -> None:
    channels = [x[i] if i < x.shape[0] else torch.zeros_like(x[0]) for i in range(max(5, x.shape[0]))]
    sem = channels[0]
    design = channels[1] if x.shape[0] >= 2 else torch.zeros_like(sem)
    if x.shape[0] >= 4:
        pos = channels[2]
        neg = channels[3]
        abs_diff = torch.clamp(pos + neg, 0, 1)
    elif x.shape[0] >= 2:
        pos = torch.clamp(sem - design, min=0)
        neg = torch.clamp(design - sem, min=0)
        abs_diff = torch.clamp(pos + neg, 0, 1)
    else:
        pos = neg = abs_diff = torch.zeros_like(sem)

    if attention is not None:
        attn = F.interpolate(attention.unsqueeze(0), size=sem.shape[-2:], mode="bilinear", align_corners=False).squeeze(0).squeeze(0)
    else:
        attn = torch.zeros_like(sem)

    panels = [
        tile_with_label(to_u8(sem), "SEM"),
        tile_with_label(to_u8(design), "Design/soft_design"),
        tile_with_label(to_u8(pos), "pos_diff: SEM側に余計"),
        tile_with_label(to_u8(neg), "neg_diff: SEM側で不足"),
        tile_with_label(to_u8(abs_diff), "abs_diff"),
        tile_with_label(to_u8(attn), "Attention"),
    ]
    w, h = panels[0].size
    title_h = 34
    canvas = Image.new("RGB", (w * 3, h * 2 + title_h), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 9), title, fill=(0, 0, 0))
    for i, panel in enumerate(panels):
        x0 = (i % 3) * w
        y0 = title_h + (i // 3) * h
        canvas.paste(panel, (x0, y0))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.out)
    device = torch.device(args.device)
    model, ckpt = load_model(args.checkpoint, device)
    classes: List[str] = ckpt["classes"]
    rows = read_annotations(args.csv)
    eval_crop_mode = "center_crop" if ckpt.get("crop_mode") == "random_tile" else ckpt.get("crop_mode", "resize")
    ds = SEMPairDataset(
        rows,
        args.data_root,
        classes=classes,
        task=ckpt["task"],
        image_size=ckpt["image_size"],
        input_mode=ckpt["input_mode"],
        design_blur_radius=ckpt["design_blur_radius"],
        augment=False,
        crop_mode=eval_crop_mode,
        tile_size=ckpt.get("tile_size", ckpt.get("image_size", 512)),
    )
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    ok_idx = classes.index("OK") if "OK" in classes else 0
    saved = false_ok = false_ng = 0
    index = 0
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            out = model(x)
            prob = torch.softmax(out["logits"], dim=1).cpu()
            pred = prob.argmax(dim=1).cpu()
            y = batch["y"].cpu()
            attn = out.get("attention")
            if attn is not None:
                attn = attn.cpu()
            for b in range(x.size(0)):
                t = int(y[b].item())
                p = int(pred[b].item())
                if t == p:
                    index += 1
                    continue
                kind = "false_ok" if (t != ok_idx and p == ok_idx) else "false_ng" if (t == ok_idx and p != ok_idx) else "wrong"
                false_ok += int(kind == "false_ok")
                false_ng += int(kind == "false_ng")
                if saved < args.max_save:
                    title = f"{kind} | true={classes[t]} pred={classes[p]} conf={float(prob[b, p]):.4f} | sem={batch['sem'][b]}"
                    make_montage(
                        x=batch["x"][b].cpu(),
                        attention=attn[b] if attn is not None else None,
                        title=title,
                        out_path=out_dir / kind / f"{index:06d}_{classes[t]}_to_{classes[p]}.png",
                    )
                    saved += 1
                index += 1
    print({"saved": saved, "false_ok": false_ok, "false_ng": false_ng, "out": str(out_dir)})


if __name__ == "__main__":
    main()
