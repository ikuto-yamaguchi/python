from __future__ import annotations

import csv
import json
import random
import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import yaml

SEM_COLUMNS = ("sem", "sem_path", "sem_image", "image_sem")
DESIGN_COLUMNS = ("design", "design_path", "pattern", "design_image", "image_design")
LABEL_COLUMNS = ("label", "target", "class")
GROUP_COLUMNS = ("group", "group_id", "pattern_id", "wafer", "wafer_id", "lot", "lot_id", "fov_group")
SPLIT_COLUMNS = ("split", "subset", "set")


def seed_everything(seed: int, deterministic: bool = False) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.use_deterministic_algorithms(True, warn_only=True)
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True


def load_yaml(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def save_json(data: Dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def parse_classes(classes: str | Sequence[str]) -> List[str]:
    if isinstance(classes, str):
        result = [item.strip() for item in classes.split(",") if item.strip()]
    else:
        result = [str(item).strip() for item in classes if str(item).strip()]
    if not result:
        raise ValueError("At least one class is required")
    if len(set(result)) != len(result):
        raise ValueError(f"Duplicate classes: {result}")
    return result


def find_column(fieldnames: Iterable[str], candidates: Sequence[str], required: bool = True) -> Optional[str]:
    names = list(fieldnames)
    lower_to_actual = {name.lower(): name for name in names}
    for candidate in candidates:
        if candidate.lower() in lower_to_actual:
            return lower_to_actual[candidate.lower()]
    if required:
        raise ValueError(f"Could not find any of columns {candidates}; available={names}")
    return None


def read_annotations(csv_path: str | Path) -> List[Dict[str, str]]:
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        sem_col = find_column(reader.fieldnames, SEM_COLUMNS)
        design_col = find_column(reader.fieldnames, DESIGN_COLUMNS)
        label_col = find_column(reader.fieldnames, LABEL_COLUMNS)
        group_col = find_column(reader.fieldnames, GROUP_COLUMNS, required=False)
        split_col = find_column(reader.fieldnames, SPLIT_COLUMNS, required=False)
        rows: List[Dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            sem = (row.get(sem_col or "") or "").strip()
            design = (row.get(design_col or "") or "").strip()
            label = (row.get(label_col or "") or "").strip()
            if not sem or not design or not label:
                raise ValueError(f"Missing sem/design/label at row {row_number}: {row}")
            item = {"sem": sem, "design": design, "label": label}
            if group_col:
                item["group"] = (row.get(group_col) or "").strip()
            if split_col:
                item["split"] = (row.get(split_col) or "").strip().lower()
            rows.append(item)
    if not rows:
        raise ValueError(f"CSV has no rows: {path}")
    return rows


def _class_distribution(rows: Sequence[Dict[str, str]]) -> Dict[str, float]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
    total = max(1, len(rows))
    return {label: count / total for label, count in counts.items()}


def _stratified_image_split(rows, val_ratio: float, seed: int):
    rng = random.Random(seed)
    by_label: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        by_label.setdefault(row["label"], []).append(row)
    train, val = [], []
    for label_rows in by_label.values():
        label_rows = list(label_rows)
        rng.shuffle(label_rows)
        n_val = max(1, int(round(len(label_rows) * val_ratio))) if len(label_rows) > 1 else 0
        val.extend(label_rows[:n_val])
        train.extend(label_rows[n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def _group_split(rows, val_ratio: float, seed: int):
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for index, row in enumerate(rows):
        group = row.get("group") or f"__ungrouped_{index}"
        grouped.setdefault(group, []).append(row)
    groups = list(grouped)
    if len(groups) < 2:
        raise ValueError("Group split requires at least two distinct groups")
    overall = _class_distribution(rows)
    labels = sorted(overall)
    target_count = len(rows) * val_ratio
    best = None
    for attempt in range(256):
        rng = random.Random(seed + attempt)
        shuffled = list(groups)
        rng.shuffle(shuffled)
        selected, count = [], 0
        for group in shuffled:
            if count < target_count or not selected:
                selected.append(group)
                count += len(grouped[group])
        selected_set = set(selected)
        val = [row for group in selected for row in grouped[group]]
        train = [row for group in groups if group not in selected_set for row in grouped[group]]
        if not train or not val:
            continue
        if len(labels) > 1 and ({row["label"] for row in train} != set(labels) or {row["label"] for row in val} != set(labels)):
            continue
        val_dist = _class_distribution(val)
        score = abs(len(val) - target_count) / max(1, len(rows))
        score += sum(abs(val_dist.get(label, 0.0) - overall.get(label, 0.0)) for label in labels)
        if best is None or score < best[0]:
            best = (score, selected)
    if best is None:
        raise ValueError("Could not create a group-aware split containing all classes")
    selected_set = set(best[1])
    return (
        [row for group in groups if group not in selected_set for row in grouped[group]],
        [row for group in best[1] for row in grouped[group]],
    )


def split_rows(rows, val_ratio: float, seed: int):
    rows = list(rows)
    explicit_train = [row for row in rows if row.get("split") in {"train", "training"}]
    explicit_val = [row for row in rows if row.get("split") in {"val", "valid", "validation"}]
    has_any_split = any(bool(row.get("split")) for row in rows)
    if has_any_split:
        unknown = [row.get("split") for row in rows if row.get("split") not in {"train", "training", "val", "valid", "validation"}]
        if unknown or not explicit_train or not explicit_val or len(explicit_train) + len(explicit_val) != len(rows):
            raise ValueError("split列を使う場合は全行をtrainまたはvalで明示してください")
        return explicit_train, explicit_val, {"mode": "explicit_split_column", "train_count": len(explicit_train), "val_count": len(explicit_val)}
    if any(bool(row.get("group")) for row in rows):
        train, val = _group_split(rows, val_ratio, seed)
        train_groups = {row.get("group") for row in train if row.get("group")}
        val_groups = {row.get("group") for row in val if row.get("group")}
        if train_groups & val_groups:
            raise RuntimeError("Group leakage detected after split")
        return train, val, {"mode": "group_aware", "train_count": len(train), "val_count": len(val), "train_groups": len(train_groups), "val_groups": len(val_groups)}
    warnings.warn("CSVにgroup列またはsplit列がありません。同一パターン/ウェハ由来画像がtrain/valへ跨ると精度が水増しされます。", RuntimeWarning)
    train, val = _stratified_image_split(rows, val_ratio, seed)
    return train, val, {"mode": "stratified_image_level_WARNING_LEAKAGE_POSSIBLE", "train_count": len(train), "val_count": len(val)}


def class_counts(rows, classes):
    counts = {name: 0 for name in classes}
    for row in rows:
        if row["label"] in counts:
            counts[row["label"]] += 1
    return counts


def compute_class_weights(rows, classes) -> torch.Tensor:
    counts = class_counts(rows, classes)
    values = np.array([counts[name] for name in classes], dtype=np.float32)
    if np.any(values == 0):
        raise ValueError(f"Training split lacks classes: {counts}")
    return torch.tensor(values.sum() / (len(values) * values), dtype=torch.float32)


def validate_paths(rows, data_root: str | Path) -> None:
    root = Path(data_root)
    missing, duplicates, seen = [], set(), set()
    for row in rows:
        pair = (row["sem"], row["design"])
        if pair in seen:
            duplicates.add(pair)
        seen.add(pair)
        for key in ("sem", "design"):
            path = Path(row[key])
            path = path if path.is_absolute() else root / path
            if not path.is_file():
                missing.append(str(path))
    if missing:
        raise FileNotFoundError(f"Missing image files ({len(missing)}):\n" + "\n".join(missing[:20]))
    if duplicates:
        warnings.warn(f"Duplicate SEM/Design pairs found: {len(duplicates)}", RuntimeWarning)


def ensure_dir(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output
