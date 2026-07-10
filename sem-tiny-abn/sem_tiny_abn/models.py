from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


def round_channels(value: int, width: float, divisor: int = 8) -> int:
    return max(divisor, int(value * width + divisor / 2) // divisor * divisor)


def make_norm(channels: int, norm: str = "group") -> nn.Module:
    norm = norm.lower()
    if norm == "batch":
        return nn.BatchNorm2d(channels)
    if norm == "group":
        groups = min(8, channels)
        while channels % groups != 0 and groups > 1:
            groups -= 1
        return nn.GroupNorm(groups, channels)
    if norm == "none":
        return nn.Identity()
    raise ValueError(f"Unknown norm: {norm}")


class ConvNormAct(nn.Sequential):
    def __init__(
        self,
        in_ch: int,
        out_ch: int,
        kernel: int = 3,
        stride: int = 1,
        groups: int = 1,
        dilation: int = 1,
        norm: str = "group",
        activate: bool = True,
    ) -> None:
        padding = dilation * (kernel // 2)
        layers: list[nn.Module] = [
            nn.Conv2d(
                in_ch,
                out_ch,
                kernel,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
                bias=False,
            ),
            make_norm(out_ch, norm),
        ]
        if activate:
            layers.append(nn.SiLU(inplace=True))
        super().__init__(*layers)


class ResidualBlock(nn.Module):
    """CPUで最適化されやすい通常3x3 Convの小型Residual block。"""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1, dilation: int = 1, norm: str = "group") -> None:
        super().__init__()
        self.conv1 = ConvNormAct(in_ch, out_ch, 3, stride=stride, dilation=dilation, norm=norm)
        self.conv2 = ConvNormAct(out_ch, out_ch, 3, dilation=dilation, norm=norm, activate=False)
        self.skip = (
            nn.Identity()
            if stride == 1 and in_ch == out_ch
            else ConvNormAct(in_ch, out_ch, 1, stride=stride, norm=norm, activate=False)
        )
        self.act = nn.SiLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.conv2(self.conv1(x)) + self.skip(x))


class MobileBlock(nn.Module):
    """パラメータ削減用のinverted residual block。

    CPUでは通常Convより遅い環境もあるため、デフォルトにはしていない。
    """

    def __init__(
        self,
        in_ch: int,
        out_ch: int,
        stride: int = 1,
        dilation: int = 1,
        norm: str = "group",
        expansion: float = 2.0,
    ) -> None:
        super().__init__()
        hidden = round_channels(int(in_ch * expansion), 1.0)
        layers: list[nn.Module] = []
        if hidden != in_ch:
            layers.append(ConvNormAct(in_ch, hidden, 1, norm=norm))
        layers.extend(
            [
                ConvNormAct(hidden, hidden, 3, stride=stride, groups=hidden, dilation=dilation, norm=norm),
                ConvNormAct(hidden, out_ch, 1, norm=norm, activate=False),
            ]
        )
        self.block = nn.Sequential(*layers)
        self.use_residual = stride == 1 and in_ch == out_ch
        self.act = nn.SiLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.block(x)
        return self.act(x + y) if self.use_residual else self.act(y)


def make_block(
    block_type: str,
    in_ch: int,
    out_ch: int,
    stride: int,
    dilation: int,
    norm: str,
    expansion: float,
) -> nn.Module:
    if block_type == "standard":
        return ResidualBlock(in_ch, out_ch, stride=stride, dilation=dilation, norm=norm)
    if block_type == "mobile":
        return MobileBlock(
            in_ch,
            out_ch,
            stride=stride,
            dilation=dilation,
            norm=norm,
            expansion=expansion,
        )
    raise ValueError(f"Unknown block_type: {block_type}")


def make_stage(
    block_type: str,
    in_ch: int,
    out_ch: int,
    repeats: int,
    stride: int,
    norm: str,
    expansion: float,
    dilation: int = 1,
) -> nn.Sequential:
    layers = [make_block(block_type, in_ch, out_ch, stride, 1, norm, expansion)]
    for _ in range(max(0, repeats - 1)):
        layers.append(make_block(block_type, out_ch, out_ch, 1, dilation, norm, expansion))
    return nn.Sequential(*layers)


class HybridPool(nn.Module):
    """全体形態の平均情報と、微小局所異常の最大応答を両方残す。"""

    def __init__(self, mode: str = "avgmax") -> None:
        super().__init__()
        self.mode = mode

    @property
    def output_multiplier(self) -> int:
        return 2 if self.mode == "avgmax" else 1

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg = F.adaptive_avg_pool2d(x, 1).flatten(1)
        if self.mode == "avg":
            return avg
        max_value = F.adaptive_max_pool2d(x, 1).flatten(1)
        if self.mode == "max":
            return max_value
        if self.mode == "avgmax":
            return torch.cat([avg, max_value], dim=1)
        raise ValueError(f"Unknown pooling: {self.mode}")


class TinyFeatureExtractor(nn.Module):
    """ABN用にshared trunkとperception tailを明示的に分離したbackbone。"""

    def __init__(
        self,
        in_channels: int = 4,
        width: float = 1.0,
        depth: int = 1,
        norm: str = "group",
        block_type: str = "standard",
        expansion: float = 2.0,
    ) -> None:
        super().__init__()
        c0, c1, c2, c3, c4 = [round_channels(v, width) for v in (16, 24, 32, 48, 64)]
        repeats = max(1, int(depth))
        self.shared_channels = c2
        self.out_channels = c4

        self.shared = nn.Sequential(
            ConvNormAct(in_channels, c0, 3, stride=2, norm=norm),
            make_stage(block_type, c0, c1, repeats, 2, norm, expansion),
            make_stage(block_type, c1, c2, repeats, 2, norm, expansion),
        )

        self.tail = nn.Sequential(
            make_stage(block_type, c2, c3, repeats + 1, 2, norm, expansion),
            make_stage(block_type, c3, c4, repeats, 1, norm, expansion, dilation=2),
        )


class ABNAttentionBranch(nn.Module):
    """本家ABNに近い、補助分類とAttention生成が結合されたbranch。"""

    def __init__(
        self,
        channels: int,
        num_classes: int,
        depth: int = 1,
        norm: str = "group",
        block_type: str = "standard",
        expansion: float = 2.0,
    ) -> None:
        super().__init__()
        self.refine = make_stage(
            block_type,
            channels,
            channels,
            max(1, depth),
            1,
            norm,
            expansion,
        )
        self.class_maps = nn.Conv2d(channels, num_classes, kernel_size=1, bias=True)
        self.attention_from_classes = nn.Conv2d(num_classes, 1, kernel_size=3, padding=1, bias=True)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        class_maps = self.class_maps(self.refine(x))
        aux_logits = F.adaptive_avg_pool2d(class_maps, 1).flatten(1)
        attention = torch.sigmoid(self.attention_from_classes(class_maps))
        return attention, aux_logits, class_maps


class TinyCNN(nn.Module):
    def __init__(
        self,
        in_channels: int = 4,
        num_classes: int = 2,
        width: float = 1.0,
        depth: int = 1,
        norm: str = "group",
        block_type: str = "standard",
        expansion: float = 2.0,
        dropout: float = 0.1,
        pooling: str = "avgmax",
    ) -> None:
        super().__init__()
        self.features = TinyFeatureExtractor(in_channels, width, depth, norm, block_type, expansion)
        self.pool = HybridPool(pooling)
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.features.out_channels * self.pool.output_multiplier, num_classes),
        )
        self.apply(init_weights)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        shared = self.features.shared(x)
        feat = self.features.tail(shared)
        logits = self.head(self.pool(feat))
        return {"logits": logits, "features": feat}


class TinyABN(nn.Module):
    def __init__(
        self,
        in_channels: int = 4,
        num_classes: int = 2,
        width: float = 1.0,
        depth: int = 1,
        norm: str = "group",
        block_type: str = "standard",
        expansion: float = 2.0,
        dropout: float = 0.1,
        pooling: str = "avgmax",
    ) -> None:
        super().__init__()
        self.features = TinyFeatureExtractor(in_channels, width, depth, norm, block_type, expansion)
        self.attention_branch = ABNAttentionBranch(
            self.features.shared_channels,
            num_classes,
            depth=max(1, depth),
            norm=norm,
            block_type=block_type,
            expansion=expansion,
        )
        self.pool = HybridPool(pooling)
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.features.out_channels * self.pool.output_multiplier, num_classes),
        )
        self.apply(init_weights)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        shared = self.features.shared(x)
        attention, aux_logits, class_maps = self.attention_branch(shared)
        attended = shared * (1.0 + attention)
        feat = self.features.tail(attended)
        logits = self.head(self.pool(feat))
        return {
            "logits": logits,
            "aux_logits": aux_logits,
            "attention": attention,
            "class_maps": class_maps,
            "features": feat,
        }


class TinyFreqABN(nn.Module):
    """固定low-passとhigh residualによる軽量周波数分離版。

    藤吉研究室の再構成Loss付きFrequency-Aware ABNそのものではない。
    チャンネルを任意に二分する旧実装と違い、空間周波数としてlow/highを明示的に分ける。
    """

    def __init__(
        self,
        in_channels: int = 4,
        num_classes: int = 2,
        width: float = 1.0,
        depth: int = 1,
        norm: str = "group",
        block_type: str = "standard",
        expansion: float = 2.0,
        dropout: float = 0.1,
        pooling: str = "avgmax",
        frequency_kernel: int = 5,
    ) -> None:
        super().__init__()
        if frequency_kernel % 2 == 0:
            raise ValueError("frequency_kernel must be odd")
        self.frequency_kernel = frequency_kernel
        self.features = TinyFeatureExtractor(in_channels, width, depth, norm, block_type, expansion)
        branch_kwargs = dict(
            channels=self.features.shared_channels,
            num_classes=num_classes,
            depth=max(1, depth),
            norm=norm,
            block_type=block_type,
            expansion=expansion,
        )
        self.low_branch = ABNAttentionBranch(**branch_kwargs)
        self.high_branch = ABNAttentionBranch(**branch_kwargs)
        self.pool = HybridPool(pooling)
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.features.out_channels * self.pool.output_multiplier, num_classes),
        )
        self.apply(init_weights)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        shared = self.features.shared(x)
        k = self.frequency_kernel
        low = F.avg_pool2d(shared, kernel_size=k, stride=1, padding=k // 2)
        high = shared - low
        attention_low, aux_low, class_maps_low = self.low_branch(low)
        attention_high, aux_high, class_maps_high = self.high_branch(high)
        attention = 0.5 * (attention_low + attention_high)
        feat = self.features.tail(shared * (1.0 + attention))
        logits = self.head(self.pool(feat))
        return {
            "logits": logits,
            "aux_logits": 0.5 * (aux_low + aux_high),
            "aux_logits_low": aux_low,
            "aux_logits_high": aux_high,
            "attention": attention,
            "attention_low": attention_low,
            "attention_high": attention_high,
            "class_maps_low": class_maps_low,
            "class_maps_high": class_maps_high,
            "features": feat,
        }


def init_weights(module: nn.Module) -> None:
    if isinstance(module, nn.Conv2d):
        nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, (nn.BatchNorm2d, nn.GroupNorm)):
        if module.weight is not None:
            nn.init.ones_(module.weight)
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, nn.Linear):
        nn.init.normal_(module.weight, mean=0.0, std=0.01)
        if module.bias is not None:
            nn.init.zeros_(module.bias)


def build_model(
    name: str,
    in_channels: int,
    num_classes: int,
    width: float = 1.0,
    depth: int = 1,
    norm: str = "group",
    block_type: str = "standard",
    expansion: float = 2.0,
    dropout: float = 0.1,
    pooling: str = "avgmax",
) -> nn.Module:
    kwargs = dict(
        in_channels=in_channels,
        num_classes=num_classes,
        width=width,
        depth=depth,
        norm=norm,
        block_type=block_type,
        expansion=expansion,
        dropout=dropout,
        pooling=pooling,
    )
    name = name.lower()
    if name == "tiny_cnn":
        return TinyCNN(**kwargs)
    if name == "tiny_abn":
        return TinyABN(**kwargs)
    if name == "tiny_freq_abn":
        return TinyFreqABN(**kwargs)
    raise ValueError(f"Unknown model: {name}")
