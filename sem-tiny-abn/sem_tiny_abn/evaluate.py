from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score
from torch.utils.data import DataLoader

from .metrics import binary_gate_metrics
from .runtime import load_checkpoint_model, make_dataset
from .utils import load_yaml, read_annotations, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SEM Tiny ABNを評価する")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()
    config = load_yaml(args.config)
    for key in ("data_root", "csv", "checkpoint", "device"):
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    if args.batch_size is not None:
        config["eval_batch_size"] = args.batch_size
    if not config.get("checkpoint"):
        config["checkpoint"] = str(Path(config.get("out", "runs/sem_tiny_abn")) / "best.pt")
    if not config.get("data_root") or not config.get("csv"):
        raise ValueError("data_root と csv を設定してください")
    args.values = config
    return args


def main() -> None:
    args = parse_args()
    config: Dict[str, Any] = args.values
    device = torch.device(config.get("device", "cpu"))
    model, checkpoint = load_checkpoint_model(config["checkpoint"], device)
    classes: List[str] = checkpoint["classes"]
    rows = read_annotations(config["csv"])
    dataset = make_dataset(rows, config["data_root"], checkpoint, augment=False)
    loader = DataLoader(dataset, batch_size=int(config.get("eval_batch_size", config.get("batch_size", 8))), shuffle=False, num_workers=0)

    y_true: List[int] = []
    probability_rows: List[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            logits = model(batch["x"].to(device))["logits"]
            probability_rows.extend(torch.softmax(logits, dim=1).cpu().numpy())
            y_true.extend(batch["y"].cpu().tolist())
    probabilities = np.asarray(probability_rows)
    if probabilities.size == 0:
        raise ValueError("評価データが空です")
    argmax_pred = probabilities.argmax(axis=1)
    ok_index = classes.index("OK") if "OK" in classes else 0
    threshold = float(checkpoint.get("decision_threshold", 0.5))
    gate = binary_gate_metrics(y_true, probabilities[:, ok_index], ok_index, threshold)
    gated_pred = argmax_pred.copy()
    non_ok = [i for i in range(len(classes)) if i != ok_index]
    for i in range(len(gated_pred)):
        if probabilities[i, ok_index] >= threshold:
            gated_pred[i] = ok_index
        elif gated_pred[i] == ok_index and non_ok:
            gated_pred[i] = non_ok[int(np.argmax(probabilities[i, non_ok]))]

    result: Dict[str, Any] = {
        "classes": classes,
        "samples": len(y_true),
        "decision_threshold": threshold,
        "argmax_accuracy": float(np.mean(argmax_pred == np.asarray(y_true))),
        "argmax_balanced_accuracy": float(balanced_accuracy_score(y_true, argmax_pred)),
        "gated_accuracy": float(np.mean(gated_pred == np.asarray(y_true))),
        "gated_balanced_accuracy": float(balanced_accuracy_score(y_true, gated_pred)),
        "confusion_matrix_argmax": confusion_matrix(y_true, argmax_pred, labels=list(range(len(classes)))).tolist(),
        "confusion_matrix_gated": confusion_matrix(y_true, gated_pred, labels=list(range(len(classes)))).tolist(),
        "classification_report_gated": classification_report(
            y_true, gated_pred, labels=list(range(len(classes))), target_names=classes, zero_division=0, output_dict=True
        ),
        **gate,
    }
    if len(classes) == 2 and len(set(y_true)) == 2:
        true_ok = (np.asarray(y_true) == ok_index).astype(np.int64)
        result["roc_auc_ok"] = float(roc_auc_score(true_ok, probabilities[:, ok_index]))
    print(result)
    out_json = args.out_json or str(Path(config.get("out", "runs/sem_tiny_abn")) / "evaluation.json")
    save_json(result, out_json)


if __name__ == "__main__":
    main()
