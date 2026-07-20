from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
import hashlib, json
from typing import Mapping, Sequence
from .orbit_operator import AffineOperator, Prediction, TransitionEpisode, fit_operator, ordered_roles, parse_control, surface_pattern

@dataclass
class MechanismOrbit:
    orbit_id: str
    operator: AffineOperator
    support: int = 0
    residuals: int = 0
    surfaces: set[str] = field(default_factory=set)

class OrbitLearner:
    """Induce mechanism identity only after exact intervention transport."""
    def __init__(self, *, minimum_support: int = 3, minimum_fraction: float = 0.75) -> None:
        self.minimum_support, self.minimum_fraction = minimum_support, minimum_fraction
        self.orbits: dict[AffineOperator, MechanismOrbit] = {}
        self.surface_operators: dict[str, AffineOperator] = {}
        self.surface_orbits: dict[str, str] = {}
        self.transport_attempts = self.transport_successes = 0

    def fit(self, episodes: Sequence[TransitionEpisode]) -> int:
        groups: dict[str, list[TransitionEpisode]] = defaultdict(list)
        for episode in episodes:
            groups[surface_pattern(episode.text, episode.before)].append(episode)
        for pattern, rows in groups.items():
            fit = fit_operator(rows, self.minimum_support, self.minimum_fraction)
            if fit.operator is None:
                continue
            canonical, _ = fit.operator.canonical()
            orbit = self.orbits.get(canonical)
            if orbit is None:
                digest = hashlib.blake2s(repr(canonical.rows).encode(), digest_size=8).hexdigest()
                orbit = self.orbits[canonical] = MechanismOrbit(f"orbit:{digest}", canonical)
            orbit.support += fit.support
            orbit.residuals += fit.residuals
            orbit.surfaces.add(pattern)
            self.surface_operators[pattern] = fit.operator
            self.surface_orbits[pattern] = orbit.orbit_id
        return len(self.orbits)

    def ground_surface_once(self, episode: TransitionEpisode) -> str | None:
        pattern = surface_pattern(episode.text, episode.before)
        roles = ordered_roles(episode.text, episode.before, episode.after)
        values = tuple(int(episode.before[role]) for role in roles)
        targets = tuple(int(episode.after[role]) for role in roles)
        control = parse_control(episode.text, episode.before)
        matches: list[tuple[MechanismOrbit, AffineOperator]] = []
        for orbit in self.orbits.values():
            if orbit.operator.arity != len(roles):
                continue
            variants = [orbit.operator] + ([orbit.operator.permute((1, 0))] if len(roles) == 2 else [])
            for variant in variants:
                self.transport_attempts += 1
                if variant.apply_values(values, control) == targets:
                    self.transport_successes += 1
                    matches.append((orbit, variant))
        unique = {(orbit.orbit_id, operator.rows): (orbit, operator) for orbit, operator in matches}
        if len({key[0] for key in unique}) != 1:
            return None
        orbit, operator = next(iter(unique.values()))
        self.surface_operators[pattern], self.surface_orbits[pattern] = operator, orbit.orbit_id
        orbit.surfaces.add(pattern); orbit.support += 1
        return orbit.orbit_id

    def predict(self, text: str, before: Mapping[str, int]) -> Prediction:
        pattern = surface_pattern(text, before); operator = self.surface_operators.get(pattern)
        if operator is None:
            return Prediction(None, None, 0, False)
        roles = ordered_roles(text, before)
        if len(roles) != operator.arity:
            return Prediction(None, None, 1, False)
        outputs = operator.apply_values(tuple(int(before[r]) for r in roles), parse_control(text, before))
        after = {str(k): int(v) for k, v in before.items()}
        for role, value in zip(roles, outputs, strict=True): after[role] = value
        return Prediction(after, self.surface_orbits.get(pattern), 1, True)

    def to_bytes(self) -> bytes:
        payload = {"orbits": [{"id": o.orbit_id, "arity": o.operator.arity, "operator": o.operator.rows, "support": o.support, "residuals": o.residuals, "surfaces": sorted(o.surfaces)} for o in sorted(self.orbits.values(), key=lambda x: x.orbit_id)], "surface_operators": {p: {"arity": op.arity, "rows": op.rows, "orbit": self.surface_orbits[p]} for p, op in sorted(self.surface_operators.items())}}
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
