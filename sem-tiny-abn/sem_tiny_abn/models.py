from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn


class ConvBNAct(nn.Sequential):
    def __init__(self, in_ch: int, out_ch: int, kernel: int = 3, stride: int = 1, groups: int = 1):
        padding = kernel // 2
        super().__init__(
            nn.Conv2d(in_ch, out_ch, kernel, stride=stride, padding=padding, groups=groups, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.SiLU(inplace=True),
        )


class DSConv(nn.Module):
    """Depthwise separable convolution block used by MobileNet-like tiny models."""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
        super().__init__()
        self.block = nn.Sequential(
            ConvBNAct(in_ch, in_ch, kernel=3, stride=stride, groups=in_ch),
            ConvBNAct(in_ch, out_ch, kernel=1, stride=1),
        )
        self.use_residual = stride == 1 and in_ch == out_ch

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.block(x)
        return x + y if self.use_residual else y


class TinyBackbone(nn.Module):
    def __init__(self, in_channels: int = 4, width: float = 1.0):
        super().__init__()

        def c(v: int) -> int:
            return max(8, int(round(v * width)))

        channels = [c(v) for v in (16, 24, 24, 32, 48, 64)]
        self.out_channels = channels[-1]
        self.net = nn.Sequential(
            ConvBNAct(in_channels, channels[0], kernel=3, stride=2),
            DSConv(channels[0], channels[1], stride=2),
            DSConv(channels[1], channels[2], stride=1),
            DSConv(channels[2], channels[3], stride=2),
            DSConv(channels[3], channels[4], stride=1),
            DSConv(channels[4], channels[5], stride=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SpatialAttentionBranch(nn.Module):
    def __init__(self, channels: int, num_classes: int, reduction: int = 4):
        super().__init__()
        hidden = max(8, channels // reduction)
        self.attn = nn.Sequential(
            nn.Conv2d(channels, hidden, kernel_size=1, bias=False),
            nn.BatchNorm2d(hidden),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, hidden, kernel_size=3, padding=1, groups=hidden, bias=False),
            nn.BatchNorm2d(hidden),
            nn.SiLU(inplace=True),
            nn.Conv2d(hidden, 1, kernel_size=1),
            nn.Sigmoid(),
        )
        self.aux_head = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(channels, num_classes))

    def forward(self, feat: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        attn = self.attn(feat)
        aux_logits = self.aux_head(feat)
        return attn, aux_logits


class TinyCNN(nn.Module):
    def __init__(self, in_channels: int = 4, num_classes: int = 2, width: float = 1.0):
        super().__init__()
        self.backbone = TinyBackbone(in_channels, width)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Dropout(p=0.05),
            nn.Linear(self.backbone.out_channels, num_classes),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.backbone(x)
        logits = self.head(feat)
        return {"logits": logits, "features": feat}


class TinyABN(nn.Module):
    """TinyCNN with an ABN-style attention branch.

    Attention is intentionally low-resolution and cheap. The perception branch uses
    ABN's stable `(1 + attention) * features` style gating.
    """

    def __init__(self, in_channels: int = 4, num_classes: int = 2, width: float = 1.0):
        super().__init__()
        self.backbone = TinyBackbone(in_channels, width)
        c = self.backbone.out_channels
        self.attention = SpatialAttentionBranch(c, num_classes)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Dropout(p=0.05),
            nn.Linear(c, num_classes),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.backbone(x)
        attn, aux_logits = self.attention(feat)
        attended = feat * (1.0 + attn)
        logits = self.head(attended)
        return {"logits": logits, "aux_logits": aux_logits, "attention": attn, "features": feat}


class TinyFreqABN(nn.Module):
    """Low/high split attention variant.

    This is a lightweight approximation of frequency-aware ABN. It splits feature
    channels into two groups. Inspect `attention_low` for coarse morphology and
    `attention_high` for fine edge/detail response.
    """

    def __init__(self, in_channels: int = 4, num_classes: int = 2, width: float = 1.0):
        super().__init__()
        self.backbone = TinyBackbone(in_channels, width)
        c = self.backbone.out_channels
        c_low = c // 2
        self.c_low = c_low
        self.low_attention = SpatialAttentionBranch(c_low, num_classes)
        self.high_attention = SpatialAttentionBranch(c - c_low, num_classes)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Dropout(p=0.05),
            nn.Linear(c, num_classes),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.backbone(x)
        low, high = torch.split(feat, [self.c_low, feat.shape[1] - self.c_low], dim=1)
        attn_low, aux_low = self.low_attention(low)
        attn_high, aux_high = self.high_attention(high)
        low = low * (1.0 + attn_low)
        high = high * (1.0 + attn_high)
        logits = self.head(torch.cat([low, high], dim=1))
        aux_logits = 0.5 * (aux_low + aux_high)
        return {
            "logits": logits,
            "aux_logits": aux_logits,
            "attention_low": attn_low,
            "attention_high": attn_high,
            "attention": 0.5 * (attn_low + attn_high),
            "features": feat,
        }


def build_model(name: str, in_channels: int, num_classes: int, width: float = 1.0) -> nn.Module:
    name = name.lower()
    if name == "tiny_cnn":
        return TinyCNN(in_channels=in_channels, num_classes=num_classes, width=width)
    if name == "tiny_abn":
        return TinyABN(in_channels=in_channels, num_classes=num_classes, width=width)
    if name == "tiny_freq_abn":
        return TinyFreqABN(in_channels=in_channels, num_classes=num_classes, width=width)
    raise ValueError(f"Unknown model: {name}")
