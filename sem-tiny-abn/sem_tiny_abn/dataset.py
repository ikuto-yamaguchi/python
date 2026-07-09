from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, Sequence, Tuple

import numpy as np
import torch
import torch.nn.functional as F
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
    """画像を学習/推論用サイズへ縮小または拡大する。"""
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


def _pad_to_min_size(x: torch.Tensor, min_size: int) -> torch.Tensor:
    """画像Tensorを最低 min_size x min_size まで右下方向へゼロパディングする。"""
    _, h, w = x.shape
    pad_h = max(0, min_size - h)
    pad_w = max(0, min_size - w)
    if pad_h == 0 and pad_w == 0:
        return x
    return F.pad(x, (0, pad_w, 0, pad_h), mode="constant", value=0.0)


def _crop_tensor(x: torch.Tensor, top: int, left: int, size: int) -> torch.Tensor:
    x = _pad_to_min_size(x, size)
    return x[:, top : top + size, left : left + size]


def make_input_tensor(
    sem_img: Image.Image,
    design_img: Image.Image,
    image_size: int = 512,
    input_mode: str = "sem_design_posneg",
    design_blur_radius: float = 1.2,
) -> torch.Tensor:
    """SEM/Designからモデル入力チャンネルを作る。

    差分画像は保存せず、この関数内でメモリ上に作る。
    """
    sem_img = _resize(sem_img, image_size)
    design_img = _resize(design_img, image_size)

    # Designを少しぼかす。
    # 理由: Designの硬いエッジとSEMのぼけたエッジを直接比べると、
    # 小さなエッジ位置ずれに過敏になりやすいから。
    if design_blur_radius > 0:
        design_soft_img = design_img.filter(ImageFilter.GaussianBlur(radius=design_blur_radius))
    else:
        design_soft_img = design_img

    sem = _pil_to_tensor(sem_img)
    design = _pil_to_tensor(design_soft_img)

    # SEM側に余計に出ている差分。太り・余計な接続・bridge寄り。
    pos = torch.clamp(sem - design, min=0.0)

    # DesignにはあるのにSEM側で足りない差分。細り・欠け・break寄り。
    neg = torch.clamp(design - sem, min=0.0)
    abs_diff = pos + neg

    if input_mode == "sem_design":
        return torch.cat([sem, design], dim=0)
    if input_mode == "posneg":
        return torch.cat([pos, neg], dim=0)
    if input_mode == "sem_design_posneg":
        return torch.cat([sem, design, pos, neg], dim=0)
    if input_mode == "sem_design_abs_posneg":
        return torch.cat([sem, design, abs_diff, pos, neg], dim=0)
    raise ValueError(f"Unknown input_mode: {input_mode}")


class SEMPairDataset(Dataset):
    """SEM画像とDesign画像のペアを読むDataset。

    crop_mode:
      resize      : 画像全体を image_size x image_size にして使う。
      center_crop : image_sizeにしたあと、中央 tile_size だけを切る。確認用。

    OK/NGの画像単位ラベルだけでランダムタイル学習をすると、NG画像内の正常領域までNG扱いになり、
    ラベルノイズで精度が落ちる可能性があるため、このDatasetからは外しています。
    タイルは推論時の探索用 `tile_predict.py` または、将来パッチ単位ラベルがある場合に使います。
    """

    def __init__(
        self,
        rows: Sequence[Dict[str, str]],
        data_root: str | Path,
        classes: Sequence[str] | str = ("OK", "NG"),
        task: str = "multiclass",
        image_size: int = 512,
        input_mode: str = "sem_design_posneg",
        design_blur_radius: float = 1.2,
        augment: bool = False,
        crop_mode: str = "resize",
        tile_size: int = 256,
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
        self.crop_mode = crop_mode
        self.tile_size = int(tile_size)
        if self.task not in {"multiclass", "multilabel"}:
            raise ValueError("task must be 'multiclass' or 'multilabel'")
        if self.crop_mode not in {"resize", "center_crop"}:
            raise ValueError("crop_mode must be resize or center_crop")

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

    @property
    def model_input_size(self) -> int:
        return self.tile_size if self.crop_mode == "center_crop" else self.image_size

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

    def _apply_crop(self, x: torch.Tensor) -> torch.Tensor:
        if self.crop_mode == "resize":
            return x
        x = _pad_to_min_size(x, self.tile_size)
        _, h, w = x.shape
        max_top = max(0, h - self.tile_size)
        max_left = max(0, w - self.tile_size)
        top = max_top // 2
        left = max_left // 2
        return _crop_tensor(x, top, left, self.tile_size)

    def _make_input(self, sem_img: Image.Image, design_img: Image.Image) -> torch.Tensor:
        if self.augment:
            sem_img, design_img = _paired_augment(sem_img, design_img)
        x = make_input_tensor(
            sem_img=sem_img,
            design_img=design_img,
            image_size=self.image_size,
            input_mode=self.input_mode,
            design_blur_radius=self.design_blur_radius,
        )
        return self._apply_crop(x)

    def __getitem__(self, idx: int):
        row = self.rows[idx]
        sem_img = _load_gray(self._resolve(row["sem"]))
        design_img = _load_gray(self._resolve(row["design"]))
        x = self._make_input(sem_img, design_img)
        y = self._label(row["label"])
        return {"x": x, "y": y, "sem": row["sem"], "design": row["design"], "label": row["label"]}
