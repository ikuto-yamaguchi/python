from __future__ import annotations

from typing import Mapping, Protocol

from .orbit_learner_types import MechanismOrbit
from .orbit_operator import (
    AffineOperator,
    Prediction,
    TransitionEpisode,
    ordered_roles,
    parse_control,
    surface_pattern,
)


class LearnerState(Protocol):
    orbits: dict[AffineOperator, MechanismOrbit]
    surface_operators: dict[str, AffineOperator]
    surface_orbits: dict[str, str]
    transport_attempts: int
    transport_successes: int


def ground_surface_once(state: LearnerState, episode: TransitionEpisode) -> str | None:
    pattern = surface_pattern(episode.text, episode.before)
    roles = ordered_roles(episode.text, episode.before, episode.after)
    values = tuple(int(episode.before[role]) for role in roles)
    targets = tuple(int(episode.after[role]) for role in roles)
    control = parse_control(episode.text, episode.before)
    matches: list[tuple[MechanismOrbit, AffineOperator]] = []
    for orbit in state.orbits.values():
        if orbit.operator.arity != len(roles):
            continue
        variants = [orbit.operator]
        if len(roles) == 2:
            variants.append(orbit.operator.permute((1, 0)))
        for variant in variants:
            state.transport_attempts += 1
            if variant.apply_values(values, control) == targets:
                state.transport_successes += 1
                matches.append((orbit, variant))
    unique = {
        (orbit.orbit_id, operator.rows): (orbit, operator)
        for orbit, operator in matches
    }
    if len({key[0] for key in unique}) != 1:
        return None
    orbit, operator = next(iter(unique.values()))
    state.surface_operators[pattern] = operator
    state.surface_orbits[pattern] = orbit.orbit_id
    orbit.surfaces.add(pattern)
    orbit.support += 1
    return orbit.orbit_id


def predict(state: LearnerState, text: str, before: Mapping[str, int]) -> Prediction:
    pattern = surface_pattern(text, before)
    operator = state.surface_operators.get(pattern)
    if operator is None:
        return Prediction(None, None, 0, False)
    roles = ordered_roles(text, before)
    if len(roles) != operator.arity:
        return Prediction(None, None, 1, False)
    values = tuple(int(before[role]) for role in roles)
    outputs = operator.apply_values(values, parse_control(text, before))
    after = {str(key): int(value) for key, value in before.items()}
    for role, value in zip(roles, outputs, strict=True):
        after[role] = value
    return Prediction(after, state.surface_orbits.get(pattern), 1, True)
