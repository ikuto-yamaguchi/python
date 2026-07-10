from __future__ import annotations

import argparse
import math
import time
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from torch.utils.data import DataLoader
from tqdm import tqdm

from .dataset import SEMPairDataset
from .losses import compute_loss
from .metrics import calibrate_ok_threshold
from .models import build_model
from .utils import (
    class_counts, compute_class_weights, ensure_dir, load_yaml, parse_classes,
    read_annotations, save_json, seed_everything, split_rows, validate_paths,
)

DEFAULTS: Dict[str, Any] = {
    "data_root": None, "csv": None, "out": "runs/sem_tiny_abn",
    "classes": "OK,NG", "task": "multiclass", "model": "tiny_abn",
    "input_mode": "sem_design_posneg", "image_size": 512,
    "normalize_mode": "percentile", "sem_invert": "auto", "design_invert": False,
    "design_blur_radius": 1.0, "diff_tolerance_px": 2, "cache_size": 0,
    "width": 1.0, "depth": 1, "norm": "group", "block_type": "standard",
    "expansion": 2.0, "dropout": 0.1, "pooling": "avgmax",
    "epochs": 60, "batch_size": 4, "lr": 1e-3, "weight_decay": 1e-4,
    "optimizer": "adamw", "momentum": 0.9, "warmup_epochs": 3,
    "aux_weight": 1.0, "focal_gamma": 0.0, "label_smoothing": 0.0,
    "class_weight_mode": "none", "grad_clip_norm": 5.0, "val_ratio": 0.2,
    "target_false_ok_rate": 0.0, "early_stopping_patience": 15,
    "num_workers": 0, "device": "cpu", "cpu_threads": 0, "seed": 42,
    "deterministic": False, "amp": False, "channels_last": False, "resume": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SEM Tiny ABNを設定ファイルから学習する")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--resume", default=None)
    cli = parser.parse_args()
    config = {**DEFAULTS, **load_yaml(cli.config)}
    for key in ("data_root", "csv", "out", "device", "resume"):
        value = getattr(cli, key)
        if value is not None:
            config[key] = value
    if not config["data_root"] or not config["csv"]:
        raise ValueError("data_root と csv を設定ファイルに記載してください")
    cli.config_values = config
    return cli


def make_optimizer(model: torch.nn.Module, config: Dict[str, Any]) -> torch.optim.Optimizer:
    name = str(config["optimizer"]).lower()
    if name == "adamw":
        return torch.optim.AdamW(model.parameters(), lr=config["lr"], weight_decay=config["weight_decay"])
    if name == "sgd":
        return torch.optim.SGD(model.parameters(), lr=config["lr"], momentum=config["momentum"], weight_decay=config["weight_decay"], nesterov=True)
    raise ValueError(f"Unknown optimizer: {name}")


def make_scheduler(optimizer: torch.optim.Optimizer, epochs: int, warmup_epochs: int):
    def scale(epoch: int) -> float:
        if warmup_epochs > 0 and epoch < warmup_epochs:
            return max(1e-3, (epoch + 1) / warmup_epochs)
        progress = (epoch - warmup_epochs) / max(1, epochs - warmup_epochs)
        return 0.5 * (1.0 + math.cos(math.pi * min(max(progress, 0.0), 1.0)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, scale)


def build_dataset(rows, config: Dict[str, Any], classes: List[str], augment: bool) -> SEMPairDataset:
    return SEMPairDataset(
        rows, config["data_root"], classes=classes, task=config["task"],
        image_size=config["image_size"], input_mode=config["input_mode"],
        normalize_mode=config["normalize_mode"], sem_invert=config["sem_invert"],
        design_invert=config["design_invert"], design_blur_radius=config["design_blur_radius"],
        diff_tolerance_px=config["diff_tolerance_px"], augment=augment, cache_size=config["cache_size"],
    )


def build_network(config: Dict[str, Any], in_channels: int, num_classes: int) -> torch.nn.Module:
    return build_model(
        config["model"], in_channels, num_classes, width=config["width"], depth=config["depth"],
        norm=config["norm"], block_type=config["block_type"], expansion=config["expansion"],
        dropout=config["dropout"], pooling=config["pooling"],
    )


def move_input(x: torch.Tensor, device: torch.device, channels_last: bool) -> torch.Tensor:
    x = x.to(device, non_blocking=device.type == "cuda")
    return x.contiguous(memory_format=torch.channels_last) if channels_last else x


def train_one_epoch(model, loader, optimizer, scaler, device, config, class_weight) -> Dict[str, float]:
    model.train()
    total_loss = total_main = total_aux = 0.0
    total_items = 0
    for batch in tqdm(loader, desc="train", leave=False):
        x = move_input(batch["x"], device, config["channels_last"])
        y = batch["y"].to(device, non_blocking=device.type == "cuda")
        optimizer.zero_grad(set_to_none=True)
        amp_enabled = bool(config["amp"] and device.type == "cuda")
        with torch.autocast(device_type=device.type, enabled=amp_enabled):
            output = model(x)
            loss, parts = compute_loss(
                output, y, task=config["task"], class_weight=class_weight,
                aux_weight=config["aux_weight"], focal_gamma=config["focal_gamma"],
                label_smoothing=config["label_smoothing"],
            )
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        if config["grad_clip_norm"] and config["grad_clip_norm"] > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["grad_clip_norm"]))
        scaler.step(optimizer)
        scaler.update()
        count = x.shape[0]
        total_items += count
        total_loss += float(loss.detach()) * count
        total_main += parts["main_loss"] * count
        total_aux += parts["aux_loss"] * count
    return {
        "train_loss": total_loss / max(1, total_items),
        "train_main_loss": total_main / max(1, total_items),
        "train_aux_loss": total_aux / max(1, total_items),
    }


@torch.no_grad()
def validate(model, loader, device, config, classes, class_weight) -> Dict[str, Any]:
    model.eval()
    total_loss = 0.0
    total_items = 0
    y_true: List[int] = []
    probabilities: List[np.ndarray] = []
    for batch in tqdm(loader, desc="val", leave=False):
        x = move_input(batch["x"], device, config["channels_last"])
        y = batch["y"].to(device)
        output = model(x)
        loss, _ = compute_loss(
            output, y, task=config["task"], class_weight=class_weight,
            aux_weight=config["aux_weight"], focal_gamma=config["focal_gamma"],
            label_smoothing=config["label_smoothing"],
        )
        probability = torch.softmax(output["logits"], dim=1)
        total_loss += float(loss) * x.shape[0]
        total_items += x.shape[0]
        y_true.extend(y.cpu().tolist())
        probabilities.extend(probability.cpu().numpy())
    if not probabilities:
        raise ValueError("Validation split is empty")
    probability_array = np.asarray(probabilities)
    predictions = probability_array.argmax(axis=1)
    ok_index = classes.index("OK") if "OK" in classes else 0
    threshold_metrics = calibrate_ok_threshold(y_true, probability_array[:, ok_index], ok_index, config["target_false_ok_rate"])
    metrics: Dict[str, Any] = {
        "val_loss": total_loss / max(1, total_items),
        "argmax_accuracy": float(np.mean(predictions == np.asarray(y_true))),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        **threshold_metrics,
    }
    if len(classes) == 2 and len(set(y_true)) == 2:
        true_ok = (np.asarray(y_true) == ok_index).astype(np.int64)
        metrics["roc_auc_ok"] = float(roc_auc_score(true_ok, probability_array[:, ok_index]))
    return metrics


def checkpoint_payload(model, optimizer, scheduler, scaler, epoch, best_key, config, classes, dataset, threshold, split_info):
    return {
        "epoch": epoch, "model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
        "scheduler_state": scheduler.state_dict(), "scaler_state": scaler.state_dict(), "best_key": best_key,
        "model": config["model"], "classes": classes, "task": config["task"],
        "in_channels": dataset.in_channels, "num_classes": len(classes),
        "decision_threshold": float(threshold), "config": config, "split_info": split_info,
    }


def main() -> None:
    args = parse_args()
    config: Dict[str, Any] = args.config_values
    if int(config["cpu_threads"]) > 0:
        torch.set_num_threads(int(config["cpu_threads"]))
    seed_everything(int(config["seed"]), bool(config["deterministic"]))
    out_dir = ensure_dir(config["out"])
    device = torch.device(config["device"])
    classes = parse_classes(config["classes"])
    if config["task"] != "multiclass":
        raise NotImplementedError("厳密な閾値校正を行う現行版はmulticlassを対象とします")

    rows = read_annotations(config["csv"])
    validate_paths(rows, config["data_root"])
    train_rows, val_rows, split_info = split_rows(rows, float(config["val_ratio"]), int(config["seed"]))
    train_dataset = build_dataset(train_rows, config, classes, augment=True)
    val_dataset = build_dataset(val_rows, config, classes, augment=False)
    loader_kwargs = dict(num_workers=int(config["num_workers"]), pin_memory=device.type == "cuda", persistent_workers=int(config["num_workers"]) > 0)
    train_loader = DataLoader(train_dataset, batch_size=int(config["batch_size"]), shuffle=True, **loader_kwargs)
    val_loader = DataLoader(val_dataset, batch_size=int(config["batch_size"]), shuffle=False, **loader_kwargs)

    model = build_network(config, train_dataset.in_channels, len(classes)).to(device)
    if config["channels_last"]:
        model = model.to(memory_format=torch.channels_last)
    optimizer = make_optimizer(model, config)
    scheduler = make_scheduler(optimizer, int(config["epochs"]), int(config["warmup_epochs"]))
    scaler = torch.cuda.amp.GradScaler(enabled=bool(config["amp"] and device.type == "cuda"))
    class_weight: Optional[torch.Tensor] = None
    if str(config["class_weight_mode"]).lower() == "balanced":
        class_weight = compute_class_weights(train_rows, classes).to(device)

    start_epoch = 1
    best_key = (-float("inf"), -float("inf"), -float("inf"))
    if config.get("resume"):
        resume = torch.load(config["resume"], map_location=device)
        model.load_state_dict(resume["model_state"])
        optimizer.load_state_dict(resume["optimizer_state"])
        scheduler.load_state_dict(resume["scheduler_state"])
        if resume.get("scaler_state"):
            scaler.load_state_dict(resume["scaler_state"])
        start_epoch = int(resume["epoch"]) + 1
        best_key = tuple(resume.get("best_key", best_key))

    run_info = {
        "device": str(device), "parameter_count": sum(p.numel() for p in model.parameters()),
        "classes": classes, "class_counts_all": class_counts(rows, classes),
        "class_counts_train": class_counts(train_rows, classes), "class_counts_val": class_counts(val_rows, classes),
        "split_info": split_info, "config": config,
    }
    save_json(run_info, out_dir / "run_info.json")
    print(run_info)

    history: List[Dict[str, Any]] = []
    epochs_without_improvement = 0
    for epoch in range(start_epoch, int(config["epochs"]) + 1):
        start = time.perf_counter()
        train_metrics = train_one_epoch(model, train_loader, optimizer, scaler, device, config, class_weight)
        val_metrics = validate(model, val_loader, device, config, classes, class_weight)
        scheduler.step()
        epoch_metrics = {
            "epoch": epoch, "lr": optimizer.param_groups[0]["lr"],
            "seconds": time.perf_counter() - start, **train_metrics, **val_metrics,
        }
        history.append(epoch_metrics)
        save_json({"history": history}, out_dir / "train_log.json")
        print(epoch_metrics)

        current_key = (-float(epoch_metrics["false_ok_rate"]), -float(epoch_metrics["false_ng_rate"]), float(epoch_metrics["argmax_accuracy"]))
        payload = checkpoint_payload(model, optimizer, scheduler, scaler, epoch, max(best_key, current_key), config, classes, train_dataset, epoch_metrics["threshold"], split_info)
        torch.save(payload, out_dir / "last.pt")
        if current_key > best_key:
            best_key = current_key
            payload["best_key"] = best_key
            torch.save(payload, out_dir / "best.pt")
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
        if int(config["early_stopping_patience"]) > 0 and epochs_without_improvement >= int(config["early_stopping_patience"]):
            print(f"Early stopping at epoch {epoch}")
            break
    print(f"best checkpoint: {out_dir / 'best.pt'}")


if __name__ == "__main__":
    main()
