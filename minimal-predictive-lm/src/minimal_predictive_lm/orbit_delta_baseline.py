from __future__ import annotations

from typing import Mapping

from .orbit_operator import TransitionEpisode, ordered_roles, surface_pattern


class ExactDeltaBaseline:
    """Surface memory that freezes the numeric delta from its last example."""

    def __init__(self) -> None:
        self.memory: dict[str, tuple[int, ...]] = {}

    def observe(self, episode: TransitionEpisode) -> None:
        pattern = surface_pattern(episode.text, episode.before)
        roles = ordered_roles(episode.text, episode.before, episode.after)
        self.memory[pattern] = tuple(
            int(episode.after[role]) - int(episode.before[role])
            for role in roles
        )

    def predict(self, text: str, before: Mapping[str, int]) -> dict[str, int] | None:
        pattern = surface_pattern(text, before)
        delta = self.memory.get(pattern)
        if delta is None:
            return None
        roles = ordered_roles(text, before)
        if len(delta) != len(roles):
            return None
        after = {str(key): int(value) for key, value in before.items()}
        for role, amount in zip(roles, delta, strict=True):
            after[role] += amount
        return after
