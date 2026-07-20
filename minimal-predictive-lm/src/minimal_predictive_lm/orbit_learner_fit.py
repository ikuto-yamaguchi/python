from __future__ import annotations

from collections import defaultdict
import hashlib
from typing import Protocol, Sequence

from .orbit_learner_types import MechanismOrbit
from .orbit_operator import AffineOperator, TransitionEpisode, fit_operator, surface_pattern


class LearnerState(Protocol):
    minimum_support: int
    minimum_fraction: float
    orbits: dict[AffineOperator, MechanismOrbit]
    surface_operators: dict[str, AffineOperator]
    surface_orbits: dict[str, str]


def fit_orbits(state: LearnerState, episodes: Sequence[TransitionEpisode]) -> int:
    groups: dict[str, list[TransitionEpisode]] = defaultdict(list)
    for episode in episodes:
        groups[surface_pattern(episode.text, episode.before)].append(episode)
    for pattern, rows in groups.items():
        fit = fit_operator(rows, state.minimum_support, state.minimum_fraction)
        if fit.operator is None:
            continue
        canonical, _ = fit.operator.canonical()
        orbit = state.orbits.get(canonical)
        if orbit is None:
            digest = hashlib.blake2s(
                repr(canonical.rows).encode(), digest_size=8
            ).hexdigest()
            orbit = MechanismOrbit(f"orbit:{digest}", canonical)
            state.orbits[canonical] = orbit
        orbit.support += fit.support
        orbit.residuals += fit.residuals
        orbit.surfaces.add(pattern)
        state.surface_operators[pattern] = fit.operator
        state.surface_orbits[pattern] = orbit.orbit_id
    return len(state.orbits)
