from __future__ import annotations

import json
from typing import Protocol

from .orbit_learner_types import MechanismOrbit
from .orbit_operator import AffineOperator


class LearnerState(Protocol):
    orbits: dict[AffineOperator, MechanismOrbit]
    surface_operators: dict[str, AffineOperator]
    surface_orbits: dict[str, str]


def serialize(state: LearnerState) -> bytes:
    payload = {
        "orbits": [
            {
                "id": orbit.orbit_id,
                "arity": orbit.operator.arity,
                "operator": orbit.operator.rows,
                "support": orbit.support,
                "residuals": orbit.residuals,
                "surfaces": sorted(orbit.surfaces),
            }
            for orbit in sorted(state.orbits.values(), key=lambda row: row.orbit_id)
        ],
        "surface_operators": {
            pattern: {
                "arity": operator.arity,
                "rows": operator.rows,
                "orbit": state.surface_orbits[pattern],
            }
            for pattern, operator in sorted(state.surface_operators.items())
        },
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
