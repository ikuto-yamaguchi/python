from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Episode:
    utterance: str
    before: tuple[int, ...]
    immediate: tuple[int, ...]
    partner: tuple[int, ...]
    delayed: tuple[int, ...]


def _delta(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(b - a for a, b in zip(left, right))


def trajectory_signature(episode: Episode) -> tuple[tuple[int, ...], ...]:
    return (
        _delta(episode.before, episode.immediate),
        _delta(episode.immediate, episode.partner),
        _delta(episode.partner, episode.delayed),
    )


class ClosedLoopSemanticBinding:
    """Bind utterances only through complete interaction trajectories.

    The model does not inspect task names, topic dictionaries, answer labels,
    response candidates, or lexical similarity. A latent operation is admitted
    only when the complete immediate/partner/delayed transition signature is
    observed. This is deliberately bounded and non-neural.
    """

    def __init__(self, max_operations: int = 128, max_forms: int = 4096) -> None:
        self.max_operations = max_operations
        self.max_forms = max_forms
        self.operations: dict[tuple[tuple[int, ...], ...], int] = {}
        self.forms: dict[str, dict[int, int]] = {}
        self.reads = 0

    def observe(self, episode: Episode) -> int | None:
        signature = trajectory_signature(episode)
        if signature not in self.operations:
            if len(self.operations) >= self.max_operations:
                return None
            self.operations[signature] = len(self.operations)
        operation = self.operations[signature]
        if episode.utterance not in self.forms and len(self.forms) >= self.max_forms:
            return operation
        counts = self.forms.setdefault(episode.utterance, {})
        counts[operation] = counts.get(operation, 0) + 1
        return operation

    def infer_known(self, utterance: str) -> int | None:
        counts = self.forms.get(utterance, {})
        self.reads += len(counts)
        if not counts:
            return None
        return max(counts, key=lambda key: (counts[key], -key))

    def infer_from_trajectory(self, episode: Episode) -> int | None:
        self.reads += len(self.operations)
        return self.operations.get(trajectory_signature(episode))

    def serialized_bytes(self) -> int:
        payload = {
            "format": "closed-loop-semantic-binding-v1",
            "max_operations": self.max_operations,
            "max_forms": self.max_forms,
            "operations": [repr(key) for key in self.operations],
            "forms": self.forms,
        }
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
