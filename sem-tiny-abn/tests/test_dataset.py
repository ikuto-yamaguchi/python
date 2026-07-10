import numpy as np
import torch
from PIL import Image

from sem_tiny_abn.dataset import build_input_tensor


def image_from_array(array):
    return Image.fromarray((array * 255).astype(np.uint8), mode="L")


def test_tolerance_band_reduces_small_edge_shift_diff():
    design = np.zeros((64, 64), dtype=np.float32); design[20:44, 20:44] = 1.0
    sem = np.zeros_like(design); sem[20:44, 21:45] = 1.0
    no_tolerance = build_input_tensor(image_from_array(sem), image_from_array(design), image_size=64, input_mode="posneg", normalize_mode="minmax", sem_invert="false", design_blur_radius=0, diff_tolerance_px=0)
    tolerance = build_input_tensor(image_from_array(sem), image_from_array(design), image_size=64, input_mode="posneg", normalize_mode="minmax", sem_invert="false", design_blur_radius=0, diff_tolerance_px=2)
    assert float(tolerance.sum()) < float(no_tolerance.sum())


def test_auto_polarity_matches_design():
    design = np.zeros((32, 32), dtype=np.float32); design[8:24, 8:24] = 1.0
    tensor = build_input_tensor(image_from_array(1.0 - design), image_from_array(design), image_size=32, input_mode="sem_design", normalize_mode="minmax", sem_invert="auto", design_blur_radius=0, diff_tolerance_px=0)
    correlation = torch.mean((tensor[0] - tensor[0].mean()) * (tensor[1] - tensor[1].mean()))
    assert float(correlation) > 0
