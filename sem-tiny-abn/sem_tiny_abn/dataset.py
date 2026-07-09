from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, Sequence, Tuple

import numpy as np
import torch
from PIL import Image, ImageFilter
from torch.utils.data import Dataset

from .utils import parse_classes


def _load_gray(path: Path) -> Image.Image:
    """画像をモノクロで読み込む。SEMもDesignも1ch画像として扱う。"""
    return Image.open(path).convert("L")


def _pil_to_tensor(img: Image.Image) -> torch.Tensor:
    """PIL画像を 0.0〜1.0 の PyTorch Tensor に変換する。"""
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def _resize(img: Image.Image, size: int) -> Image.Image:
    """512/1024画像を学習用サイズへ縮小する。"""
    return img.resize((size, size), Image.BILINEAR)


def _paired_augment(sem: Image.Image, design: Image.Image) -> Tuple[Image.Image, Image.Image]:
    """SEMとDesignに同じ回転・反転をかける。

    片方だけ変換すると位置合わせ関係が壊れるので、必ず同じ変換にする。
    """
    if random.random() < 0.5:
        sem = sem.transpose(Image.FLIP_LEFT_RIGHT)
        design = design.transpose(Image.FLIP_LEFT_RIGHT)
    if random.random() < 0.5:
        sem = sem.transpose(Image.FLIP_TOP_BOTTOM)
        design = design.transpose(Image.FLIP_TOP_BOTTOM)
    k = random.randint(0, 3)
    if k:
        sem = sem.rotate(90 * k, expand=True)
        design = design.rotate(90 * k, expand=True)
    return sem, design


class SEMPairDataset(Dataset):
    """SEM画像とDesign画像のペアを読むDataset。

    差分画像はPNGなどに保存しない。
    __getitem__ の中でメモリ上に pos_diff / neg_diff を作る。
    """

    def __init__(
        self,
        rows: Sequence[Dict[str, str]],
        data_root: str | Path,
        classes: Sequence[str] | str = ("OK", "NG"),
        task: str = "multiclass",
        image_size: int = 128,
        input_mode: str = "sem_design_posneg",
        design_blur_radius: float = 1.2,
        augment: bool = False,
    ) -> None:
        self.rows = list(rows)
        self.data_root = Path(data_root)
        self.classes = parse_classes(classes)
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.task = task
        self.image_size = int(image_size)
        self.input_mode = input_mode
        self.design_blur_radius = float(design_blur_radius)
        self.augment = augment
        if self.task not in {"multiclass", "multilabel"}:
            raise ValueError("task must be 'multiclass' or 'multilabel'")

    def __len__(self) -> int:
        return len(self.rows)

    @property
    def in_channels(self) -> int:
        """input_modeごとの入力チャンネル数。"""
        return {
            "sem_design": 2,
            "posneg": 2,
            "sem_design_posneg": 4,
            "sem_design_abs_posneg": 5,
        }[self.input_mode]

    def _resolve(self, rel: str) -> Path:
        p = Path(rel)
        if p.is_absolute():
            return p
        return self.data_root / p

    def _label(self, raw: str) -> torch.Tensor:
        if self.task == "multiclass":
            if raw not in self.class_to_idx:
                raise ValueError(f"Unknown label '{raw}'. classes={self.classes}")
            return torch.tensor(self.class_to_idx[raw], dtype=torch.long)
        out = torch.zeros(len(self.classes), dtype=torch.float32)
        for part in raw.replace(";", "|").split("|"):
            part = part.strip()
            if not part:
                continue
            if part not in self.class_to_idx:
                raise ValueError(f"Unknown label '{part}'. classes={self.classes}")
            out[self.class_to_idx[part]] = 1.0
        return out

    def _make_input(self, sem_img: Image.Image, design_img: Image.Image) -> torch.Tensor:
        if self.augment:
            sem_img, design_img = _paired_augment(sem_img, design_img)
        sem_img = _resize(sem_img, self.image_size)
        design_img = _resize(design_img, self.image_size)

        # Designを少しぼかす。
        # 理由: Designの硬いエッジとSEMのぼけたエッジを直接比べると、
        # 小さなエッジ位置ずれに過敏になりやすいから。
        if self.design_blur_radius > 0:
            design_soft_img = design_img.filter(ImageFilter.GaussianBlur(radius=self.design_blur_radius))
        else:
            design_soft_img = design_img

        sem = _pil_to_tensor(sem_img)
        design = _pil_to_tensor(design_soft_img)

        # SEM側に余計に出ている差分。太り・余計な接続・bridge寄り。
        pos = torch.clamp(sem - design, min=0.0)

        # DesignにはあるのにSEM側で足りない差分。細り・欠け・break寄り。
        neg = torch.clamp(design - sem, min=0.0)
        abs_diff = pos + neg

        if self.input_mode == "sem_design":
            return torch.cat([sem, design], dim=0)
        if self.input_mode == "posneg":
            return torch.cat([pos, neg], dim=0)
        if self.input_mode == "sem_design_posneg":
            return torch.cat([sem, design, pos, neg], dim=0)
        if self.input_mode == "sem_design_abs_posneg":
            return torch.cat([sem, design, abs_diff, pos, neg], dim=0)
        raise ValueError(f"Unknown input_mode: {self.input_mode}")

    def __getitem__(self, idx: int):
        row = self.rows[idx]
        sem_img = _load_gray(self._resolve(row["sem"]))
        design_img = _load_gray(self._resolve(row["design"]))
        x = self._make_input(sem_img, design_img)
        y = self._label(row["label"])
        return {"x": x, "y": y, "sem": row["sem"], "design": row["design"], "label": row["label"]}
