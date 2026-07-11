from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


STAGE_C_AXES = (
    "conversation",
    "knowledge",
    "mathematics",
    "code",
    "long_context",
    "creative_writing",
)

LEVEL_DESCRIPTIONS = {
    0: "unmeasured or absent",
    1: "closed-world synthetic evidence",
    2: "held-out shift or interaction adaptation",
    3: "public open-domain benchmark evidence",
    4: "parity or better than the target open model under matched conditions",
}


@dataclass(frozen=True)
class CapabilityEvidence:
    axis: str
    level: int
    quality: float
    resource_bits: int
    evidence: str
    matched_inputs: bool = False
    public_benchmark: bool = False

    def __post_init__(self) -> None:
        if self.axis not in STAGE_C_AXES:
            raise ValueError(f"unknown Stage-C axis: {self.axis}")
        if self.level not in LEVEL_DESCRIPTIONS:
            raise ValueError(f"invalid evidence level: {self.level}")
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError("quality must be between zero and one")
        if self.resource_bits < 0:
            raise ValueError("resource_bits must be non-negative")


@dataclass(frozen=True)
class StageCScorecard:
    evidence: tuple[CapabilityEvidence, ...]

    def __post_init__(self) -> None:
        axes = [item.axis for item in self.evidence]
        if sorted(axes) != sorted(STAGE_C_AXES):
            raise ValueError("scorecard must contain each Stage-C axis exactly once")

    @property
    def level_points(self) -> int:
        return sum(item.level for item in self.evidence)

    @property
    def maximum_points(self) -> int:
        return 4 * len(STAGE_C_AXES)

    @property
    def normalized_level(self) -> float:
        return self.level_points / self.maximum_points

    @property
    def minimum_quality(self) -> float:
        return min(item.quality for item in self.evidence)

    @property
    def stage_c_ready(self) -> bool:
        return all(
            item.level == 4
            and item.matched_inputs
            and item.public_benchmark
            for item in self.evidence
        )

    @property
    def pareto_claim_allowed(self) -> bool:
        return self.stage_c_ready and all(item.resource_bits > 0 for item in self.evidence)

    @property
    def description_bits(self) -> int:
        level_bits = math.ceil(math.log2(len(LEVEL_DESCRIPTIONS)))
        return sum(
            len(item.axis.encode("utf-8")) * 8
            + len(item.evidence.encode("utf-8")) * 8
            + level_bits
            + 32
            + max(1, math.ceil(math.log2(item.resource_bits + 1)))
            + 2
            for item in self.evidence
        )

    def weakest_axes(self) -> tuple[str, ...]:
        minimum = min(item.level for item in self.evidence)
        return tuple(item.axis for item in self.evidence if item.level == minimum)


def build_scorecard(evidence: Iterable[CapabilityEvidence]) -> StageCScorecard:
    return StageCScorecard(tuple(evidence))


def choose_next_axis(
    scorecard: StageCScorecard,
    estimated_upgrade_costs: dict[str, float],
    axis_weights: dict[str, float] | None = None,
) -> str:
    weights = axis_weights or {axis: 1.0 for axis in STAGE_C_AXES}
    candidates: list[tuple[float, str]] = []
    for item in scorecard.evidence:
        remaining = 4 - item.level
        if remaining <= 0:
            continue
        cost = estimated_upgrade_costs[item.axis]
        if cost <= 0:
            raise ValueError("upgrade costs must be positive")
        value = remaining * weights.get(item.axis, 1.0) / cost
        candidates.append((value, item.axis))
    if not candidates:
        raise ValueError("all axes already satisfy Stage C")
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]
