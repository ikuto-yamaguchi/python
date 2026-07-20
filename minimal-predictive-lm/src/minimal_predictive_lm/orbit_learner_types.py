from __future__ import annotations

from dataclasses import dataclass, field

from .orbit_operator import AffineOperator


@dataclass
class MechanismOrbit:
    orbit_id: str
    operator: AffineOperator
    support: int = 0
    residuals: int = 0
    surfaces: set[str] = field(default_factory=set)
