from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import yaml

SEM_COLUMNS = ("sem", "sem_path", "sem_image", "image_sem")
DESIGN_COLUMNS = ("design", "design_path", "pattern", "design_image", "image_design")
LABEL_COLUMNS = ("label", "target", "class")


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_yaml(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def save_json(data: Dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_classes(classes: str | Sequence[str]) -> List[str]:
    if isinstance(classes, str):
        out = [c.strip() for c in classes.split(",") if c.strip()]
    else:
        out = [str(c).strip() for c in classes if str(c).strip()]
    if not out:
        raise ValueError("At least one class is required")
    return out


def find_column(fieldnames: Iterable[str], candidates: Sequence[str]) -> str:
    names = list(fieldnames)
    lower_to_actual = {n.lower(): n for n in names}
    for cand in candidates:
        if cand.lower() in lower_to_actual:
            return lower_to_actual[cand.lower()]
    raise ValueError(f"Could not find any of columns {candidates}; available={names}")


def read_annotations(csv_path: str | Path) -> List[Dict[str, str]]:
    csv_path = Path(csv_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")
        sem_col = find_column(reader.fieldnames, SEM_COLUMNS)
        design_col = find_column(reader.fieldnames, DESIGN_COLUMNS)
        label_col = find_column(reader.fieldnames, LABEL_COLUMNS)
        rows: List[Dict[str, str]] = []
        for i, row in enumerate(reader):
            sem = (row.get(sem_col) or "").strip()
            design = (row.get(design_col) or "").strip()
            label = (row.get(label_col) or "").strip()
            if not sem or not design or not label:
                raise ValueError(f"Missing sem/design/label at row {i + 2}: {row}")
            rows.append({"sem": sem, "design": design, "label": label})
    if not rows:
        raise ValueError(f"CSV has no rows: {csv_path}")
    return rows


def split_rows(rows: Sequence[Dict[str, str]], val_ratio: float, seed: int) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    rows = list(rows)
    rng = random.Random(seed)
    by_label: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        by_label.setdefault(r["label"], []).append(r)
    train: List[Dict[str, str]] = []
    val: List[Dict[str, str]] = []
    for label_rows in by_label.values():
        rng.shuffle(label_rows)
        n_val = max(1, int(round(len(label_rows) * val_ratio))) if len(label_rows) > 1 else 0
        val.extend(label_rows[:n_val])
        train.extend(label_rows[n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def class_counts(rows: Sequence[Dict[str, str]], classes: Sequence[str]) -> Dict[str, int]:
    counts = {c: 0 for c in classes}
    for r in rows:
        label = r["label"]
        if label in counts:
            counts[label] += 1
    return counts


def compute_class_weights(rows: Sequence[Dict[str, str]], classes: Sequence[str]) -> torch.Tensor:
    counts = class_counts(rows, classes)
    values = np.array([counts[c] for c in classes], dtype=np.float32)
    values = np.maximum(values, 1.0)
    weights = values.sum() / (len(values) * values)
    return torch.tensor(weights, dtype=torch.float32)


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
