from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader

from .runtime import load_checkpoint_model, make_dataset
from .utils import ensure_dir, load_yaml, read_annotations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SEM Tiny ABNで推論する")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--out-csv", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--ok-threshold", type=float, default=None)
    parser.add_argument("--save-attention", default=None)
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


def save_attention(attention: torch.Tensor, path: Path, image_size: int) -> None:
    array = attention.squeeze().detach().cpu().float().numpy()
    array = np.clip(array, 0.0, 1.0)
    image = Image.fromarray((array * 255).astype(np.uint8), mode="L").resize((image_size, image_size), Image.Resampling.BILINEAR)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    args = parse_args()
    config: Dict[str, Any] = args.values
    device = torch.device(config.get("device", "cpu"))
    model, checkpoint = load_checkpoint_model(config["checkpoint"], device)
    classes: List[str] = checkpoint["classes"]
    ok_index = classes.index("OK") if "OK" in classes else 0
    threshold = float(args.ok_threshold if args.ok_threshold is not None else checkpoint.get("decision_threshold", 0.5))
    rows = read_annotations(config["csv"])
    dataset = make_dataset(rows, config["data_root"], checkpoint, augment=False)
    loader = DataLoader(dataset, batch_size=int(config.get("eval_batch_size", config.get("batch_size", 8))), shuffle=False, num_workers=0)
    attention_dir = ensure_dir(args.save_attention) if args.save_attention else None
    non_ok_indices = [i for i in range(len(classes)) if i != ok_index]
    output_rows = []
    offset = 0
    with torch.no_grad():
        for batch in loader:
            output = model(batch["x"].to(device))
            probabilities = torch.softmax(output["logits"], dim=1).cpu()
            for i in range(probabilities.shape[0]):
                probability = probabilities[i]
                if float(probability[ok_index]) >= threshold:
                    prediction_index = ok_index
                elif non_ok_indices:
                    prediction_index = non_ok_indices[int(torch.argmax(probability[non_ok_indices]))]
                else:
                    prediction_index = int(torch.argmax(probability))
                row = {
                    "sem": batch["sem"][i],
                    "design": batch["design"][i],
                    "true_label": batch["label"][i],
                    "pred": classes[prediction_index],
                    "decision_threshold": f"{threshold:.8f}",
                    "ok_prob": f"{float(probability[ok_index]):.8f}",
                }
                for class_index, class_name in enumerate(classes):
                    row[f"prob_{class_name}"] = f"{float(probability[class_index]):.8f}"
                output_rows.append(row)
                if attention_dir is not None and "attention" in output:
                    save_attention(output["attention"][i], attention_dir / f"attention_{offset+i:06d}.png", dataset.image_size)
            offset += probabilities.shape[0]
    if not output_rows:
        raise ValueError("No prediction rows")
    out_csv = Path(args.out_csv or Path(config.get("out", "runs/sem_tiny_abn")) / "predictions.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"saved: {out_csv}")


if __name__ == "__main__":
    main()
