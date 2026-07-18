from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


def _stable_bucket(text: str, buckets: int) -> int:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % buckets


def _tokens(state: object) -> tuple[str, ...]:
    if isinstance(state, Mapping):
        values = [f"{key}={state[key]}" for key in sorted(state)]
    elif isinstance(state, (list, tuple, set, frozenset)):
        values = [str(item) for item in state]
    else:
        values = str(state).replace("、", " ").replace(",", " ").split()
    return tuple(sorted(dict.fromkeys(values)))


class SparseCompositionalEncoder:
    """Sparse state code made from atoms and pairwise conjunctions."""

    def __init__(self, buckets: int = 8192) -> None:
        if buckets < 128:
            raise ValueError("buckets must be >= 128")
        self.buckets = buckets

    def encode(self, state: object) -> frozenset[int]:
        atoms = _tokens(state)
        features = {f"A:{token}" for token in atoms}
        for index, left in enumerate(atoms):
            for right in atoms[index + 1 :]:
                features.add(f"P:{left}&{right}")
        return frozenset(_stable_bucket(feature, self.buckets) for feature in features)

    def to_dict(self) -> dict:
        return {"buckets": self.buckets}

    @classmethod
    def from_dict(cls, data: dict) -> "SparseCompositionalEncoder":
        return cls(buckets=int(data.get("buckets", 8192)))


@dataclass(frozen=True, slots=True)
class Episode:
    state: tuple[int, ...]
    action: str
    reward: float
    next_state: tuple[int, ...]
    terminal: bool

    def to_dict(self) -> dict:
        return {
            "state": list(self.state),
            "action": self.action,
            "reward": self.reward,
            "next_state": list(self.next_state),
            "terminal": self.terminal,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        return cls(
            state=tuple(int(value) for value in data["state"]),
            action=str(data["action"]),
            reward=float(data["reward"]),
            next_state=tuple(int(value) for value in data["next_state"]),
            terminal=bool(data["terminal"]),
        )


class HippocampalEpisodeStore:
    """Bounded one-shot episodic store with sparse pattern completion."""

    def __init__(self, capacity: int = 4096) -> None:
        self.capacity = capacity
        self.episodes: list[Episode] = []

    def remember(self, episode: Episode) -> None:
        self.episodes.append(episode)
        overflow = len(self.episodes) - self.capacity
        if overflow > 0:
            del self.episodes[:overflow]

    def action_values(self, state: frozenset[int], actions: Sequence[str]) -> dict[str, float]:
        if not state or not self.episodes:
            return {action: 0.0 for action in actions}
        scored: dict[str, list[tuple[float, float]]] = {action: [] for action in actions}
        for episode in reversed(self.episodes):
            if episode.action not in scored:
                continue
            candidate = set(episode.state)
            union = len(state | candidate)
            similarity = len(state & candidate) / union if union else 0.0
            if similarity >= 0.5:
                scored[episode.action].append((similarity, episode.reward))
        output: dict[str, float] = {}
        for action, rows in scored.items():
            if not rows:
                output[action] = 0.0
                continue
            rows.sort(reverse=True)
            top = rows[:8]
            total_weight = sum(score for score, _ in top)
            output[action] = sum(score * reward for score, reward in top) / total_weight
        return output

    def to_dict(self) -> dict:
        return {"capacity": self.capacity, "episodes": [episode.to_dict() for episode in self.episodes]}

    @classmethod
    def from_dict(cls, data: dict) -> "HippocampalEpisodeStore":
        store = cls(capacity=int(data.get("capacity", 4096)))
        store.episodes = [Episode.from_dict(row) for row in data.get("episodes", [])]
        return store


class PredictiveCortex:
    """Sparse linear value predictor updated by local prediction error."""

    def __init__(self, alpha: float = 0.25, gamma: float = 0.9) -> None:
        self.alpha = alpha
        self.gamma = gamma
        self.bias: dict[str, float] = defaultdict(float)
        self.weights: dict[str, dict[int, float]] = defaultdict(dict)

    def value(self, features: frozenset[int], action: str) -> float:
        if not features:
            return self.bias.get(action, 0.0)
        weights = self.weights.get(action, {})
        return self.bias.get(action, 0.0) + sum(
            weights.get(feature, 0.0) for feature in features
        ) / math.sqrt(len(features))

    def values(self, features: frozenset[int], actions: Sequence[str]) -> dict[str, float]:
        return {action: self.value(features, action) for action in actions}

    def update(self, state: frozenset[int], action: str, target: float) -> float:
        prediction = self.value(state, action)
        error = target - prediction
        self.bias[action] = self.bias.get(action, 0.0) + self.alpha * error * 0.1
        if state:
            step = self.alpha * error / math.sqrt(len(state))
            row = self.weights.setdefault(action, {})
            for feature in state:
                row[feature] = row.get(feature, 0.0) + step
                if abs(row[feature]) < 1e-12:
                    row.pop(feature, None)
        return error

    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "bias": dict(self.bias),
            "weights": {
                action: {str(feature): weight for feature, weight in row.items()}
                for action, row in self.weights.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PredictiveCortex":
        cortex = cls(alpha=float(data.get("alpha", 0.25)), gamma=float(data.get("gamma", 0.9)))
        cortex.bias = defaultdict(float, {str(key): float(value) for key, value in data.get("bias", {}).items()})
        cortex.weights = defaultdict(
            dict,
            {
                str(action): {int(feature): float(weight) for feature, weight in row.items()}
                for action, row in data.get("weights", {}).items()
            },
        )
        return cortex


class CorticalTransitionModel:
    """Predict sparse next-state features from current features and an action."""

    def __init__(self) -> None:
        self.observations: dict[str, dict[int, int]] = defaultdict(dict)
        self.links: dict[str, dict[int, dict[int, int]]] = defaultdict(dict)

    def update(self, state: frozenset[int], action: str, next_state: frozenset[int]) -> float:
        predicted = self.predict(state, action)
        union = len(predicted | next_state)
        similarity = len(predicted & next_state) / union if union else 1.0
        observations = self.observations.setdefault(action, {})
        links = self.links.setdefault(action, {})
        for feature in state:
            observations[feature] = observations.get(feature, 0) + 1
            row = links.setdefault(feature, {})
            for next_feature in next_state:
                row[next_feature] = row.get(next_feature, 0) + 1
        return 1.0 - similarity

    def predict(self, state: frozenset[int], action: str) -> frozenset[int]:
        observations = self.observations.get(action, {})
        links = self.links.get(action, {})
        evidence: dict[int, float] = defaultdict(float)
        normalizer = 0.0
        for feature in state:
            seen = observations.get(feature, 0)
            if not seen:
                continue
            normalizer += 1.0
            for next_feature, count in links.get(feature, {}).items():
                evidence[next_feature] += count / seen
        if normalizer == 0.0:
            return frozenset()
        return frozenset(
            feature for feature, score in evidence.items() if score / normalizer >= 0.34
        )

    def to_dict(self) -> dict:
        return {
            "observations": {
                action: {str(feature): count for feature, count in row.items()}
                for action, row in self.observations.items()
            },
            "links": {
                action: {
                    str(feature): {
                        str(next_feature): count for next_feature, count in next_row.items()
                    }
                    for feature, next_row in row.items()
                }
                for action, row in self.links.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CorticalTransitionModel":
        model = cls()
        model.observations = defaultdict(
            dict,
            {
                str(action): {int(feature): int(count) for feature, count in row.items()}
                for action, row in data.get("observations", {}).items()
            },
        )
        model.links = defaultdict(
            dict,
            {
                str(action): {
                    int(feature): {
                        int(next_feature): int(count) for next_feature, count in next_row.items()
                    }
                    for feature, next_row in row.items()
                }
                for action, row in data.get("links", {}).items()
            },
        )
        return model


class BasalGangliaGate:
    """Select an action by combining cortical prediction and episodic recall."""

    def __init__(self, episodic_weight: float = 0.35) -> None:
        self.episodic_weight = episodic_weight

    def choose(
        self,
        actions: Sequence[str],
        cortical: Mapping[str, float],
        episodic: Mapping[str, float],
    ) -> str:
        if not actions:
            raise ValueError("at least one action is required")
        return max(
            actions,
            key=lambda action: (
                cortical.get(action, 0.0) + self.episodic_weight * episodic.get(action, 0.0),
                action,
            ),
        )

    def to_dict(self) -> dict:
        return {"episodic_weight": self.episodic_weight}

    @classmethod
    def from_dict(cls, data: dict) -> "BasalGangliaGate":
        return cls(episodic_weight=float(data.get("episodic_weight", 0.35)))


class CorticoHippocampalLoop:
    """Sparse online learner shared by every task.

    It combines cortical prediction-error learning, one-shot episodic memory,
    basal-ganglia-like action gating and offline replay. There are no task
    names, task formulas or task-specific solvers in this class.
    """

    def __init__(
        self,
        actions: Iterable[str],
        *,
        buckets: int = 8192,
        episode_capacity: int = 4096,
        alpha: float = 0.25,
        gamma: float = 0.9,
    ) -> None:
        self.actions = tuple(sorted(dict.fromkeys(str(action) for action in actions)))
        if not self.actions:
            raise ValueError("actions cannot be empty")
        self.encoder = SparseCompositionalEncoder(buckets)
        self.hippocampus = HippocampalEpisodeStore(episode_capacity)
        self.cortex = PredictiveCortex(alpha, gamma)
        self.transition_model = CorticalTransitionModel()
        self.gate = BasalGangliaGate()

    def act(self, state: object, actions: Sequence[str] | None = None) -> str:
        candidates = tuple(actions or self.actions)
        features = self.encoder.encode(state)
        return self.gate.choose(
            candidates,
            self.cortex.values(features, candidates),
            self.hippocampus.action_values(features, candidates),
        )

    def learn(
        self,
        state: object,
        action: str,
        reward: float,
        next_state: object,
        *,
        terminal: bool = False,
    ) -> float:
        current = self.encoder.encode(state)
        following = self.encoder.encode(next_state)
        next_value = 0.0 if terminal else max(self.cortex.values(following, self.actions).values())
        target = float(reward) + self.cortex.gamma * next_value
        value_error = self.cortex.update(current, str(action), target)
        self.transition_model.update(current, str(action), following)
        self.hippocampus.remember(
            Episode(tuple(sorted(current)), str(action), float(reward), tuple(sorted(following)), terminal)
        )
        return value_error

    def replay(self, passes: int = 4) -> None:
        if passes < 0:
            raise ValueError("passes must be non-negative")
        for _ in range(passes):
            for episode in reversed(self.hippocampus.episodes):
                current = frozenset(episode.state)
                following = frozenset(episode.next_state)
                next_value = 0.0 if episode.terminal else max(
                    self.cortex.values(following, self.actions).values()
                )
                target = episode.reward + self.cortex.gamma * next_value
                self.cortex.update(current, episode.action, target)

    def to_dict(self) -> dict:
        return {
            "format": "cortico-hippocampal-loop-v1",
            "actions": list(self.actions),
            "encoder": self.encoder.to_dict(),
            "hippocampus": self.hippocampus.to_dict(),
            "cortex": self.cortex.to_dict(),
            "transition_model": self.transition_model.to_dict(),
            "gate": self.gate.to_dict(),
            "architecture": {
                "sparse_event_code": True,
                "prediction_error_learning": True,
                "one_shot_episodic_memory": True,
                "offline_replay": True,
                "action_gating": True,
                "transformer_used": False,
                "backpropagation_used": False,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CorticoHippocampalLoop":
        if data.get("format") != "cortico-hippocampal-loop-v1":
            raise ValueError("unsupported format")
        loop = cls(
            data["actions"],
            buckets=int(data.get("encoder", {}).get("buckets", 8192)),
            episode_capacity=int(data.get("hippocampus", {}).get("capacity", 4096)),
            alpha=float(data.get("cortex", {}).get("alpha", 0.25)),
            gamma=float(data.get("cortex", {}).get("gamma", 0.9)),
        )
        loop.encoder = SparseCompositionalEncoder.from_dict(data.get("encoder", {}))
        loop.hippocampus = HippocampalEpisodeStore.from_dict(data.get("hippocampus", {}))
        loop.cortex = PredictiveCortex.from_dict(data.get("cortex", {}))
        loop.transition_model = CorticalTransitionModel.from_dict(data.get("transition_model", {}))
        loop.gate = BasalGangliaGate.from_dict(data.get("gate", {}))
        return loop

    def serialized_bytes(self) -> int:
        return len(
            json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
