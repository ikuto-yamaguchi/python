from __future__ import annotations

import argparse
from typing import Any, Dict, List

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .dataset import SEMPairDataset
from .losses import compute_loss
from .models import build_model
from .utils import compute_class_weights, ensure_dir, load_yaml, parse_classes, read_annotations, save_json, seed_everything, split_rows


def _apply_config(args: argparse.Namespace, defaults: Dict[str, Any]) -> argparse.Namespace:
    """設定ファイル中心で動かすための上書き処理。

    CLIで指定された値はCLIを優先し、未指定のものだけYAMLから埋める。
    """
    cfg = load_yaml(args.config)
    for k, v in {**defaults, **cfg}.items():
        key = k.replace("-", "_")
        if hasattr(args, key) and getattr(args, key) is None:
            setattr(args, key, v)
    return args


def parse_args() -> argparse.Namespace:
    defaults: Dict[str, Any] = {
        "data_root": None,
        "csv": None,
        "out": "runs/sem_tiny_abn",
        "classes": "OK,NG",
        "task": "multiclass",
        "model": "tiny_abn",
        "input_mode": "sem_design_posneg",
        "image_size": 512,
        "crop_mode": "resize",
        "tile_size": 256,
        "design_blur_radius": 1.2,
        "width": 1.0,
        "epochs": 30,
        "batch_size": 8,
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "aux_weight": 0.35,
        "focal_gamma": 1.5,
        "val_ratio": 0.2,
        "num_workers": 0,
        "device": "cpu",
        "seed": 42,
        "amp": False,
        "compile_model": False,
    }
    p = argparse.ArgumentParser(description="Train TinyCNN/TinyABN for SEM-design OK/NG judgement")
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--data-root", default=None)
    p.add_argument("--csv", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--classes", default=None)
    p.add_argument("--task", default=None, choices=["multiclass", "multilabel"])
    p.add_argument("--model", default=None, choices=["tiny_cnn", "tiny_abn", "tiny_freq_abn"])
    p.add_argument("--input-mode", default=None, choices=["sem_design", "posneg", "sem_design_posneg", "sem_design_abs_posneg"])
    p.add_argument("--image-size", type=int, default=None)
    p.add_argument("--crop-mode", default=None, choices=["resize", "center_crop", "random_tile"])
    p.add_argument("--tile-size", type=int, default=None)
    p.add_argument("--design-blur-radius", type=float, default=None)
    p.add_argument("--width", type=float, default=None)
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=None)
    p.add_argument("--lr", type=float, default=None)
    p.add_argument("--weight-decay", type=float, default=None)
    p.add_argument("--aux-weight", type=float, default=None)
    p.add_argument("--focal-gamma", type=float, default=None)
    p.add_argument("--val-ratio", type=float, default=None)
    p.add_argument("--num-workers", type=int, default=None)
    p.add_argument("--device", default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--amp", action="store_true", default=None, help="CUDA時のみAMPを使う")
    p.add_argument("--compile-model", action="store_true", default=None, help="PyTorch 2系のtorch.compileを使う。CPUでは環境により遅くなる場合あり")
    args = _apply_config(p.parse_args(), defaults)
    if args.data_root is None or args.csv is None:
        raise ValueError("data_root と csv は設定ファイルかCLIで指定してください")
    return args


@torch.no_grad()
def evaluate(model, loader, device, task: str, class_names: List[str]) -> Dict[str, float]:
    model.eval()
    total = correct = false_ok = false_ng = 0
    ok_idx = class_names.index("OK") if "OK" in class_names else 0
    ng_indices = [i for i, c in enumerate(class_names) if c != "OK"]
    for batch in loader:
        x = batch["x"].to(device)
        y = batch["y"].to(device)
        logits = model(x)["logits"]
        if task == "multiclass":
            pred = logits.argmax(dim=1)
            total += y.numel()
            correct += (pred == y).sum().item()
            false_ok += ((pred == ok_idx) & (y != ok_idx)).sum().item()
            false_ng += ((pred != ok_idx) & (y == ok_idx)).sum().item()
        else:
            prob = torch.sigmoid(logits)
            pred = prob > 0.5
            total += y.numel()
            correct += (pred == (y > 0.5)).sum().item()
            if ng_indices:
                is_true_ng = (y[:, ng_indices] > 0.5).any(dim=1)
                is_pred_ok = pred[:, ok_idx] & ~pred[:, ng_indices].any(dim=1)
                false_ok += (is_true_ng & is_pred_ok).sum().item()
                false_ng += ((y[:, ok_idx] > 0.5) & ~is_pred_ok).sum().item()
    return {"accuracy": correct / max(total, 1), "false_ok": float(false_ok), "false_ng": float(false_ng)}


def main() -> None:
    args = parse_args()
    seed_everything(int(args.seed))
    out_dir = ensure_dir(args.out)
    device = torch.device(args.device)
    classes = parse_classes(args.classes)
    rows = read_annotations(args.csv)
    train_rows, val_rows = split_rows(rows, float(args.val_ratio), int(args.seed))

    train_ds = SEMPairDataset(
        train_rows,
        args.data_root,
        classes=classes,
        task=args.task,
        image_size=args.image_size,
        input_mode=args.input_mode,
        design_blur_radius=args.design_blur_radius,
        augment=True,
        crop_mode=args.crop_mode,
        tile_size=args.tile_size,
    )
    val_ds = SEMPairDataset(
        val_rows,
        args.data_root,
        classes=classes,
        task=args.task,
        image_size=args.image_size,
        input_mode=args.input_mode,
        design_blur_radius=args.design_blur_radius,
        augment=False,
        crop_mode="center_crop" if args.crop_mode == "random_tile" else args.crop_mode,
        tile_size=args.tile_size,
    )
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory=device.type == "cuda")
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=device.type == "cuda")

    model = build_model(args.model, in_channels=train_ds.in_channels, num_classes=len(classes), width=args.width).to(device)
    if args.compile_model and hasattr(torch, "compile"):
        model = torch.compile(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))
    class_weight = compute_class_weights(train_rows, classes).to(device) if args.task == "multiclass" else None
    scaler = torch.cuda.amp.GradScaler(enabled=bool(args.amp and device.type == "cuda"))
    best = -1.0
    history = []

    print({
        "model": args.model,
        "classes": classes,
        "image_size": args.image_size,
        "crop_mode": args.crop_mode,
        "tile_size": args.tile_size,
        "model_input_size": train_ds.model_input_size,
        "batch_size": args.batch_size,
        "device": str(device),
    })

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for batch in tqdm(train_loader, desc=f"epoch {epoch}/{args.epochs}"):
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.cuda.amp.autocast(enabled=bool(args.amp and device.type == "cuda")):
                out = model(x)
                loss = compute_loss(out, y, task=args.task, class_weight=class_weight, aux_weight=args.aux_weight, focal_gamma=args.focal_gamma)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            running += float(loss.item()) * x.size(0)
        scheduler.step()
        metrics = evaluate(model, val_loader, device, args.task, classes)
        metrics["train_loss"] = running / max(len(train_ds), 1)
        metrics["epoch"] = epoch
        history.append(metrics)
        print(metrics)
        score = metrics["accuracy"] - 0.01 * metrics["false_ok"]
        if score > best:
            best = score
            raw_model = getattr(model, "_orig_mod", model)
            torch.save({
                "model_state": raw_model.state_dict(),
                "model": args.model,
                "classes": classes,
                "task": args.task,
                "input_mode": args.input_mode,
                "image_size": args.image_size,
                "crop_mode": args.crop_mode,
                "tile_size": args.tile_size,
                "model_input_size": train_ds.model_input_size,
                "design_blur_radius": args.design_blur_radius,
                "width": args.width,
                "in_channels": train_ds.in_channels,
                "num_classes": len(classes),
            }, out_dir / "best.pt")
    save_json({"history": history, "classes": classes, "args": vars(args)}, out_dir / "train_log.json")
    print(f"saved: {out_dir / 'best.pt'}")


if __name__ == "__main__":
    main()
