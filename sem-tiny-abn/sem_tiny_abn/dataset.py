from __future__ import annotations

import random
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageFilter
from torch.utils.data import Dataset

from .utils import parse_classes


def load_gray(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("L").copy()


def resize_square(image: Image.Image, size: int) -> Image.Image:
    if image.size == (size, size):
        return image
    return image.resize((size, size), Image.Resampling.BILINEAR)


def robust_normalize(array: np.ndarray, mode: str = "percentile", low: float = 1.0, high: float = 99.0) -> np.ndarray:
    array = array.astype(np.float32)
    if mode == "none":
        return np.clip(array / 255.0, 0.0, 1.0)
    if mode == "minmax":
        lo = float(array.min())
        hi = float(array.max())
    elif mode == "percentile":
        lo, hi = np.percentile(array, [low, high]).astype(np.float32)
    else:
        raise ValueError(f"Unknown normalize_mode: {mode}")
    if hi <= lo + 1e-6:
        return np.zeros_like(array, dtype=np.float32)
    return np.clip((array - lo) / (hi - lo), 0.0, 1.0)


def parse_bool_or_auto(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return "true"
    if text in {"false", "0", "no", "off"}:
        return "false"
    if text == "auto":
        return "auto"
    raise ValueError(f"Expected true/false/auto, got: {value}")


def maybe_invert_sem(sem: torch.Tensor, design: torch.Tensor, mode: str) -> torch.Tensor:
    mode = parse_bool_or_auto(mode)
    if mode == "true":
        return 1.0 - sem
    if mode == "false":
        return sem
    sem_centered = sem - sem.mean()
    design_centered = design - design.mean()
    correlation = torch.mean(sem_centered * design_centered)
    return 1.0 - sem if float(correlation) < 0.0 else sem


def build_input_tensor(
    sem_image: Image.Image,
    design_image: Image.Image,
    image_size: int = 512,
    input_mode: str = "sem_design_posneg",
    normalize_mode: str = "percentile",
    sem_invert: str = "auto",
    design_invert: bool = False,
    design_blur_radius: float = 1.0,
    diff_tolerance_px: int = 2,
) -> torch.Tensor:
    """SEM/Designを正規化し、許容幅付き差分をメモリ上で作る。"""
    sem_image = resize_square(sem_image, image_size)
    design_image = resize_square(design_image, image_size)
    if design_blur_radius > 0:
        design_image = design_image.filter(ImageFilter.GaussianBlur(radius=design_blur_radius))

    sem_np = robust_normalize(np.asarray(sem_image), normalize_mode)
    design_np = robust_normalize(np.asarray(design_image), "minmax")
    sem = torch.from_numpy(sem_np).unsqueeze(0)
    design = torch.from_numpy(design_np).unsqueeze(0)
    if design_invert:
        design = 1.0 - design
    sem = maybe_invert_sem(sem, design, sem_invert)

    radius = max(0, int(diff_tolerance_px))
    if radius > 0:
        kernel = radius * 2 + 1
        upper = F.max_pool2d(design.unsqueeze(0), kernel, stride=1, padding=radius).squeeze(0)
        lower = -F.max_pool2d((-design).unsqueeze(0), kernel, stride=1, padding=radius).squeeze(0)
    else:
        upper = lower = design

    pos = torch.clamp(sem - upper, min=0.0, max=1.0)
    neg = torch.clamp(lower - sem, min=0.0, max=1.0)
    abs_diff = torch.clamp(pos + neg, 0.0, 1.0)

    channels = {
        "sem_design": [sem, design],
        "posneg": [pos, neg],
        "sem_design_posneg": [sem, design, pos, neg],
        "sem_design_abs_posneg": [sem, design, abs_diff, pos, neg],
    }
    if input_mode not in channels:
        raise ValueError(f"Unknown input_mode: {input_mode}")
    return torch.cat(channels[input_mode], dim=0).float()


def paired_tensor_augment(x: torch.Tensor) -> torch.Tensor:
    """全チャンネルへ同じ反転・90度回転を適用する。補間は発生しない。"""
    if random.random() < 0.5:
        x = torch.flip(x, dims=(-1,))
    if random.random() < 0.5:
        x = torch.flip(x, dims=(-2,))
    k = random.randint(0, 3)
    if k:
        x = torch.rot90(x, k, dims=(-2, -1))
    return x.contiguous()


class SEMPairDataset(Dataset):
    """位置合わせ済みSEM/Designペアの画像単位分類Dataset。"""

    def __init__(
        self,
        rows: Sequence[Dict[str, str]],
        data_root: str | Path,
        classes: Sequence[str] | str = ("OK", "NG"),
        task: str = "multiclass",
        image_size: int = 512,
        input_mode: str = "sem_design_posneg",
        normalize_mode: str = "percentile",
        sem_invert: str = "auto",
        design_invert: bool = False,
        design_blur_radius: float = 1.0,
        diff_tolerance_px: int = 2,
        augment: bool = False,
        cache_size: int = 0,
    ) -> None:
        self.rows = list(rows)
        self.data_root = Path(data_root)
        self.classes = parse_classes(classes)
        self.class_to_idx = {name: i for i, name in enumerate(self.classes)}
        self.task = task
        self.image_size = int(image_size)
        self.input_mode = input_mode
        self.normalize_mode = normalize_mode
        self.sem_invert = sem_invert
        self.design_invert = bool(design_invert)
        self.design_blur_radius = float(design_blur_radius)
        self.diff_tolerance_px = int(diff_tolerance_px)
        self.augment = augment
        self.cache_size = max(0, int(cache_size))
        self.cache: OrderedDict[int, torch.Tensor] = OrderedDict()
        if self.task not in {"multiclass", "multilabel"}:
            raise ValueError("task must be multiclass or multilabel")

    def __len__(self) -> int:
        return len(self.rows)

    @property
    def in_channels(self) -> int:
        return {
            "sem_design": 2,
            "posneg": 2,
            "sem_design_posneg": 4,
            "sem_design_abs_posneg": 5,
        }[self.input_mode]

    def resolve(self, relative: str) -> Path:
        path = Path(relative)
        return path if path.is_absolute() else self.data_root / path

    def encode_label(self, raw: str) -> torch.Tensor:
        if self.task == "multiclass":
            if raw not in self.class_to_idx:
                raise ValueError(f"Unknown label '{raw}', classes={self.classes}")
            return torch.tensor(self.class_to_idx[raw], dtype=torch.long)
        result = torch.zeros(len(self.classes), dtype=torch.float32)
        for part in raw.replace(";", "|").split("|"):
            label = part.strip()
            if not label:
                continue
            if label not in self.class_to_idx:
                raise ValueError(f"Unknown label '{label}', classes={self.classes}")
            result[self.class_to_idx[label]] = 1.0
        return result

    def load_input(self, index: int) -> torch.Tensor:
        if index in self.cache:
            value = self.cache.pop(index)
            self.cache[index] = value
            return value.clone()
        row = self.rows[index]
        value = build_input_tensor(
            load_gray(self.resolve(row["sem"])),
            load_gray(self.resolve(row["design"])),
            image_size=self.image_size,
            input_mode=self.input_mode,
            normalize_mode=self.normalize_mode,
            sem_invert=self.sem_invert,
            design_invert=self.design_invert,
            design_blur_radius=self.design_blur_radius,
            diff_tolerance_px=self.diff_tolerance_px,
        )
        if self.cache_size > 0:
            self.cache[index] = value.clone()
            while len(self.cache) > self.cache_size:
                self.cache.popitem(last=False)
        return value

    def __getitem__(self, index: int) -> Dict[str, object]:
        row = self.rows[index]
        x = self.load_input(index)
        if self.augment:
            x = paired_tensor_augment(x)
        return {
            "x": x,
            "y": self.encode_label(row["label"]),
            "sem": row["sem"],
            "design": row["design"],
            "label": row["label"],
        }
