from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader

from .dataset import build_input_tensor, load_gray
from .runtime import checkpoint_dataset_kwargs, load_checkpoint_model, make_dataset
from .utils import ensure_dir, load_yaml, read_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="誤判定を画像とHTMLギャラリーで可視化する")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--max-save", type=int, default=500)
    args = parser.parse_args()
    config = load_yaml(args.config)
    for key in ("data_root", "csv", "checkpoint", "device"):
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    if not config.get("checkpoint"):
        config["checkpoint"] = str(Path(config.get("out", "runs/sem_tiny_abn")) / "best.pt")
    if not config.get("data_root") or not config.get("csv"):
        raise ValueError("data_root と csv を設定してください")
    args.values = config
    return args


def gray_image(tensor: torch.Tensor, size: int = 320, fixed_scale: bool = True) -> Image.Image:
    array = tensor.detach().cpu().float().squeeze().numpy()
    if fixed_scale:
        array = np.clip(array, 0.0, 1.0)
    else:
        array = array - array.min()
        array = array / (array.max() + 1e-8)
    return Image.fromarray((array * 255).astype(np.uint8), mode="L").resize((size, size), Image.Resampling.NEAREST)


def attention_overlay(sem: torch.Tensor, attention: Optional[torch.Tensor], size: int = 320) -> Image.Image:
    base = gray_image(sem, size=size).convert("RGB")
    if attention is None:
        return base
    att = F.interpolate(attention.unsqueeze(0), size=sem.shape[-2:], mode="bilinear", align_corners=False).squeeze()
    att_array = np.clip(att.detach().cpu().numpy(), 0.0, 1.0)
    att_image = Image.fromarray((att_array * 255).astype(np.uint8), mode="L").resize((size, size), Image.Resampling.BILINEAR)
    red = Image.new("RGB", (size, size), (255, 0, 0))
    return Image.composite(red, base, att_image.point(lambda value: int(value * 0.55)))


def labeled_panel(image: Image.Image, label: str) -> Image.Image:
    width, height = image.size
    canvas = Image.new("RGB", (width, height + 28), "white")
    canvas.paste(image.convert("RGB"), (0, 28))
    ImageDraw.Draw(canvas).text((6, 7), label, fill=(0, 0, 0))
    return canvas


def make_montage(panel_input: torch.Tensor, attention: Optional[torch.Tensor], title: str, output: Path) -> None:
    sem, design, abs_diff, pos, neg = panel_input
    panels = [
        labeled_panel(gray_image(sem), "SEM (normalized)"),
        labeled_panel(gray_image(design), "Design (soft)"),
        labeled_panel(gray_image(abs_diff), "abs diff (fixed scale)"),
        labeled_panel(gray_image(pos), "pos diff: SEM excess"),
        labeled_panel(gray_image(neg), "neg diff: SEM missing"),
        labeled_panel(attention_overlay(sem, attention), "Attention overlay"),
    ]
    panel_width, panel_height = panels[0].size
    title_height = 52
    canvas = Image.new("RGB", (panel_width * 3, panel_height * 2 + title_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 8), title[:180], fill=(0, 0, 0))
    for index, panel in enumerate(panels):
        canvas.paste(panel, ((index % 3) * panel_width, title_height + (index // 3) * panel_height))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=95)


def write_gallery(entries: List[Dict[str, str]], output_dir: Path) -> None:
    rows = []
    for entry in entries:
        relative = entry["image"]
        rows.append(
            f'<article><img src="{html.escape(relative)}" alt="誤判定可視化">'
            f'<p><b>{html.escape(entry["kind"])}</b> true={html.escape(entry["true"])} '
            f'pred={html.escape(entry["pred"])} OK確率={html.escape(entry["ok_prob"])}</p>'
            f'<p>{html.escape(entry["sem"])}</p></article>'
        )
    document = f"""<!doctype html>
<meta charset="utf-8">
<title>SEM Tiny ABN 誤判定レポート</title>
<style>
body{{font-family:sans-serif;margin:20px;background:#f5f5f5}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}}
article{{background:white;border:1px solid #ccc;padding:10px}}img{{width:100%;height:auto}}p{{overflow-wrap:anywhere}}
</style>
<h1>SEM Tiny ABN 誤判定レポート</h1><p>合計 {len(entries)} 件</p><main>{''.join(rows)}</main>"""
    (output_dir / "index.html").write_text(document, encoding="utf-8")


def main() -> None:
    args = parse_args()
    config: Dict[str, Any] = args.values
    output_dir = ensure_dir(args.out or Path(config.get("out", "runs/sem_tiny_abn")) / "error_report")
    device = torch.device(config.get("device", "cpu"))
    model, checkpoint = load_checkpoint_model(config["checkpoint"], device)
    classes: List[str] = checkpoint["classes"]
    ok_index = classes.index("OK") if "OK" in classes else 0
    threshold = float(checkpoint.get("decision_threshold", 0.5))
    non_ok_indices = [i for i in range(len(classes)) if i != ok_index]
    rows = read_annotations(config["csv"])
    dataset = make_dataset(rows, config["data_root"], checkpoint, augment=False)
    loader = DataLoader(dataset, batch_size=int(config.get("eval_batch_size", config.get("batch_size", 4))), shuffle=False, num_workers=0)
    preprocess = checkpoint_dataset_kwargs(checkpoint)
    root = Path(config["data_root"])
    entries: List[Dict[str, str]] = []
    global_index = 0
    with torch.no_grad():
        for batch in loader:
            output = model(batch["x"].to(device))
            probabilities = torch.softmax(output["logits"], dim=1).cpu()
            attention_batch = output.get("attention")
            if attention_batch is not None:
                attention_batch = attention_batch.cpu()
            for i in range(probabilities.shape[0]):
                probability = probabilities[i]
                pred_index = ok_index if float(probability[ok_index]) >= threshold else (
                    non_ok_indices[int(torch.argmax(probability[non_ok_indices]))] if non_ok_indices else int(torch.argmax(probability))
                )
                true_index = int(batch["y"][i])
                if pred_index == true_index:
                    global_index += 1
                    continue
                kind = "false_ok" if true_index != ok_index and pred_index == ok_index else "false_ng" if true_index == ok_index else "wrong_class"
                if len(entries) >= args.max_save:
                    global_index += 1
                    continue
                sem_path = Path(batch["sem"][i]); design_path = Path(batch["design"][i])
                sem_path = sem_path if sem_path.is_absolute() else root / sem_path
                design_path = design_path if design_path.is_absolute() else root / design_path
                panel_input = build_input_tensor(
                    load_gray(sem_path), load_gray(design_path), image_size=int(preprocess.get("image_size", 512)),
                    input_mode="sem_design_abs_posneg", normalize_mode=str(preprocess.get("normalize_mode", "percentile")),
                    sem_invert=str(preprocess.get("sem_invert", "auto")), design_invert=bool(preprocess.get("design_invert", False)),
                    design_blur_radius=float(preprocess.get("design_blur_radius", 1.0)), diff_tolerance_px=int(preprocess.get("diff_tolerance_px", 2)),
                )
                filename = f"{global_index:06d}_{classes[true_index]}_to_{classes[pred_index]}.png"
                relative = f"{kind}/{filename}"
                title = f"{kind} | true={classes[true_index]} pred={classes[pred_index]} OK_prob={float(probability[ok_index]):.6f} threshold={threshold:.6f} | {batch['sem'][i]}"
                make_montage(panel_input, attention_batch[i] if attention_batch is not None else None, title, output_dir / relative)
                entries.append({"kind": kind, "true": classes[true_index], "pred": classes[pred_index], "ok_prob": f"{float(probability[ok_index]):.8f}", "sem": batch["sem"][i], "design": batch["design"][i], "image": relative})
                global_index += 1
    write_gallery(entries, output_dir)
    with (output_dir / "errors.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["kind", "true", "pred", "ok_prob", "sem", "design", "image"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames); writer.writeheader(); writer.writerows(entries)
    print({"errors": len(entries), "html": str(output_dir / "index.html")})


if __name__ == "__main__":
    main()
