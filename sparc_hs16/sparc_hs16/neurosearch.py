from __future__ import annotations

import gc
import hashlib
import itertools
import json
import math
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence


def _stable_hash(text: str) -> int:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


@dataclass(frozen=True, slots=True)
class PrototypeConfig:
    name: str
    max_branch_order: int = 1
    divisive_inhibition: bool = False
    episodic_memory: bool = False
    replay_passes: int = 0
    masked_replay: bool = False
    planning_replay: bool = False


PROTOTYPE_CONFIGS: tuple[PrototypeConfig, ...] = (
    PrototypeConfig("atomic_cortex"),
    PrototypeConfig("normalized_cortex", divisive_inhibition=True),
    PrototypeConfig("dendritic_pairs", max_branch_order=2, divisive_inhibition=True),
    PrototypeConfig("dendritic_triples", max_branch_order=3, divisive_inhibition=True),
    PrototypeConfig(
        "hippocampal_one_shot",
        max_branch_order=3,
        divisive_inhibition=True,
        episodic_memory=True,
    ),
    PrototypeConfig(
        "replay",
        max_branch_order=3,
        divisive_inhibition=True,
        episodic_memory=True,
        replay_passes=2,
    ),
    PrototypeConfig(
        "masked_replay",
        max_branch_order=3,
        divisive_inhibition=True,
        episodic_memory=True,
        replay_passes=2,
        masked_replay=True,
    ),
    PrototypeConfig(
        "planning_hybrid",
        max_branch_order=3,
        divisive_inhibition=True,
        episodic_memory=True,
        replay_passes=2,
        masked_replay=True,
        planning_replay=True,
    ),
)


class QuantizedBranchCortex:
    """Fixed-memory, int8-like cortical store with dendritic branch competition.

    Each action owns a fixed byte bank. A branch key is hashed into that bank,
    so the memory ceiling is real rather than an estimate. Values are saturating
    unsigned counts; inference applies local divisive inhibition and branch
    reliability instead of a dense softmax projection.
    """

    def __init__(self, actions: Sequence[str], budget_bytes: int) -> None:
        self.actions = tuple(actions)
        if not self.actions:
            raise ValueError("actions cannot be empty")
        if budget_bytes < len(self.actions) * 1024:
            raise ValueError("budget is too small")
        self.action_index = {action: index for index, action in enumerate(self.actions)}
        self.buffer = bytearray(budget_bytes)
        self.bank_size = budget_bytes // len(self.actions)
        self.branch_stats: dict[tuple[str, ...], list[int]] = defaultdict(lambda: [0, 0])

    def _index(self, action_index: int, branch_key: str) -> int:
        return action_index * self.bank_size + _stable_hash(branch_key) % self.bank_size

    def counts(self, branch_key: str) -> list[int]:
        return [
            self.buffer[self._index(index, branch_key)]
            for index in range(len(self.actions))
        ]

    def update(self, branches: Iterable[tuple[tuple[str, ...], str]], target: str) -> None:
        target_index = self.action_index[target]
        for roles, key in branches:
            counts = self.counts(key)
            total = sum(counts)
            if total:
                predicted = max(range(len(self.actions)), key=lambda index: (counts[index], index))
                stats = self.branch_stats[roles]
                stats[1] += 1
                stats[0] += int(predicted == target_index)
            address = self._index(target_index, key)
            if self.buffer[address] < 255:
                self.buffer[address] += 1

    def scores(
        self,
        branches: Iterable[tuple[tuple[str, ...], str]],
        *,
        normalize: bool,
    ) -> list[float]:
        votes = [0.0] * len(self.actions)
        for roles, key in branches:
            counts = self.counts(key)
            total = sum(counts)
            if total < 2:
                continue
            if not normalize:
                for index, count in enumerate(counts):
                    votes[index] += count
                continue

            probabilities = [count / total for count in counts]
            entropy = -sum(
                probability * math.log(probability + 1e-12)
                for probability in probabilities
            ) / math.log(len(self.actions))
            certainty = max(0.0, 1.0 - entropy)
            correct, seen = self.branch_stats[roles]
            reliability = (correct + 2) / (seen + 3)
            specificity = 1.0 + 0.1 * (len(roles) - 1)
            weight = certainty * reliability * math.log1p(total) * specificity
            for index, probability in enumerate(probabilities):
                votes[index] += weight * probability
        return votes


class BrainPrototype:
    """One task-independent brain-inspired learner under a strict memory budget."""

    def __init__(
        self,
        config: PrototypeConfig,
        budget_mb: int,
        actions: Sequence[str] = ("A", "B", "C"),
    ) -> None:
        if budget_mb <= 0:
            raise ValueError("budget_mb must be positive")
        self.config = config
        self.actions = tuple(actions)
        self.budget_bytes = int(budget_mb) * 1024 * 1024
        # 75% cortex, 25% reserved for hippocampus, transition graph and metadata.
        cortex_bytes = max(len(self.actions) * 1024, int(self.budget_bytes * 0.75))
        self.cortex = QuantizedBranchCortex(self.actions, cortex_bytes)
        self.episodes: deque[tuple[tuple[tuple[tuple[str, ...], str], ...], str]] = deque(
            maxlen=max(128, budget_mb * 64)
        )
        self.transitions: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.state_rewards: dict[str, float] = defaultdict(float)
        self.q_values: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def branches(self, state: Mapping[str, object]) -> tuple[tuple[tuple[str, ...], str], ...]:
        items = tuple((str(key), str(value)) for key, value in sorted(state.items()))
        output: list[tuple[tuple[str, ...], str]] = []
        for order in range(1, min(self.config.max_branch_order, len(items)) + 1):
            for combination in itertools.combinations(items, order):
                roles = tuple(key for key, _ in combination)
                branch_key = "|".join(f"{key}={value}" for key, value in combination)
                output.append((roles, branch_key))
        return tuple(output)

    def predict(self, state: Mapping[str, object]) -> str:
        branches = self.branches(state)
        votes = self.cortex.scores(
            branches,
            normalize=self.config.divisive_inhibition,
        )
        if self.config.episodic_memory and self.episodes:
            query = {key for _, key in branches}
            for saved, target in reversed(self.episodes):
                candidate = {key for _, key in saved}
                similarity = len(query & candidate) / max(1, len(query | candidate))
                if similarity >= 0.98:
                    votes[self.actions.index(target)] += 25.0
                    break
        return self.actions[
            max(range(len(self.actions)), key=lambda index: (votes[index], index))
        ]

    def learn(self, state: Mapping[str, object], target: str) -> None:
        branches = self.branches(state)
        self.cortex.update(branches, target)
        if self.config.episodic_memory:
            self.episodes.append((branches, target))

    def consolidate(self) -> None:
        if self.config.replay_passes <= 0:
            return
        rows = list(self.episodes)
        for _ in range(self.config.replay_passes):
            for branches, target in reversed(rows):
                self.cortex.update(branches, target)
                if not self.config.masked_replay:
                    continue
                roles = sorted({role for subset, _ in branches for role in subset})
                for dropped_role in roles:
                    counterfactual = [
                        branch for branch in branches if dropped_role not in branch[0]
                    ]
                    self.cortex.update(counterfactual, target)

    @staticmethod
    def _state_key(state: Mapping[str, object]) -> str:
        return json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def observe_transition(
        self,
        state: Mapping[str, object],
        action: str,
        next_state: Mapping[str, object],
        *,
        reward: float = 0.0,
        terminal: bool = False,
    ) -> None:
        state_key = self._state_key(state)
        next_key = self._state_key(next_state)
        self.transitions[(state_key, action)][next_key] += 1
        if reward or terminal:
            self.state_rewards[next_key] = max(self.state_rewards[next_key], float(reward))

    def replay_plan(self, passes: int = 20, gamma: float = 0.95) -> None:
        if not self.config.planning_replay:
            return
        for _ in range(max(0, passes)):
            for (state_key, action), next_states in list(self.transitions.items()):
                total = sum(next_states.values())
                expected = 0.0
                for next_key, count in next_states.items():
                    future = max(self.q_values[next_key].values(), default=0.0)
                    expected += (count / total) * (
                        self.state_rewards.get(next_key, 0.0) + gamma * future
                    )
                self.q_values[state_key][action] = expected

    def planned_action(
        self,
        state: Mapping[str, object],
        actions: Sequence[str] = ("GO", "WAIT"),
    ) -> str:
        if not self.config.planning_replay:
            return actions[-1]
        state_key = self._state_key(state)
        return max(actions, key=lambda action: (self.q_values[state_key].get(action, 0.0), action))

    @property
    def allocated_cortex_bytes(self) -> int:
        return len(self.cortex.buffer)


@dataclass(frozen=True, slots=True)
class PrototypeResult:
    name: str
    budget_mb: int
    compositional_accuracy: float
    retention_accuracy: float
    one_shot_accuracy: float
    delayed_planning_accuracy: float
    composite_score: float
    allocated_cortex_bytes: int
    total_budget_bytes: int

    def to_dict(self) -> dict:
        return asdict(self)


def build_compositional_benchmark(
    worlds: int = 12,
) -> tuple[list[tuple[dict[str, object], str]], list[tuple[dict[str, object], str]]]:
    """Create hidden combinations with a deliberately non-causal distractor.

    The hint is only 50% correct in training and always wrong in the hidden set.
    Solvers that memorize superficial correlations fail; context branches must
    recover the world/mode/value relation.
    """

    actions = ("A", "B", "C")
    training: list[tuple[dict[str, object], str]] = []
    hidden: list[tuple[dict[str, object], str]] = []
    for world in range(worlds):
        xs = [f"x{index}" for index in range(4)]
        ys = [f"y{index}" for index in range(4)]
        x_map = {value: actions[(index + world) % 3] for index, value in enumerate(xs)}
        y_map = {value: actions[(2 * index + world) % 3] for index, value in enumerate(ys)}
        held_pairs = {(0, 1), (1, 2), (2, 3), (3, 0)}
        for mode_index, mode in enumerate(("axis-x", "axis-y")):
            for x_index, x_value in enumerate(xs):
                for y_index, y_value in enumerate(ys):
                    target = x_map[x_value] if mode_index == 0 else y_map[y_value]
                    target_index = actions.index(target)
                    hint = (
                        target
                        if (x_index + y_index + world) % 2
                        else actions[(target_index + 1) % 3]
                    )
                    state: dict[str, object] = {
                        "world": world,
                        "mode": mode,
                        "x": x_value,
                        "y": y_value,
                        "hint": hint,
                    }
                    is_hidden = (
                        (x_index, y_index) in held_pairs
                        if mode_index == 0
                        else (y_index, x_index) in held_pairs
                    )
                    if is_hidden:
                        test = dict(state)
                        test["hint"] = actions[(target_index + 1) % 3]
                        hidden.append((test, target))
                    else:
                        training.append((state, target))
    return training, hidden


def evaluate_prototype(
    config: PrototypeConfig,
    budget_mb: int,
    *,
    epochs: int = 3,
) -> PrototypeResult:
    training, hidden = build_compositional_benchmark()
    model = BrainPrototype(config, budget_mb)
    for _ in range(epochs):
        for state, target in training:
            model.learn(state, target)
    model.consolidate()

    compositional = sum(model.predict(state) == target for state, target in hidden) / len(hidden)

    exceptions: list[tuple[dict[str, object], str]] = []
    for index in range(30):
        state: dict[str, object] = {
            "world": "exception",
            "mode": "axis-x",
            "x": f"novel{index}",
            "y": "y0",
            "hint": "C",
            "exception": index,
        }
        target = model.actions[index % len(model.actions)]
        model.learn(state, target)
        exceptions.append((state, target))
    one_shot = sum(model.predict(state) == target for state, target in exceptions) / len(exceptions)

    for position in range(12):
        state = {"position": position}
        next_state = {"position": position + 1}
        model.observe_transition(
            state,
            "GO",
            next_state,
            reward=1.0 if position == 11 else 0.0,
            terminal=position == 11,
        )
        model.observe_transition(state, "WAIT", state, reward=-0.1)
    model.replay_plan(30)
    planning = sum(
        model.planned_action({"position": position}) == "GO"
        for position in range(12)
    ) / 12

    retention = sum(model.predict(state) == target for state, target in hidden) / len(hidden)
    composite = 0.45 * compositional + 0.20 * retention + 0.20 * one_shot + 0.15 * planning
    result = PrototypeResult(
        name=config.name,
        budget_mb=budget_mb,
        compositional_accuracy=compositional,
        retention_accuracy=retention,
        one_shot_accuracy=one_shot,
        delayed_planning_accuracy=planning,
        composite_score=composite,
        allocated_cortex_bytes=model.allocated_cortex_bytes,
        total_budget_bytes=model.budget_bytes,
    )
    del model
    gc.collect()
    return result


def successive_halving_search(
    stages: Sequence[tuple[int, int]] = ((16, 8), (64, 4), (256, 2)),
) -> dict:
    candidates = list(PROTOTYPE_CONFIGS)
    stage_reports: list[dict] = []
    final_rows: list[PrototypeResult] = []
    for budget_mb, survivors in stages:
        rows = [evaluate_prototype(config, budget_mb) for config in candidates]
        rows.sort(key=lambda result: (result.composite_score, result.name), reverse=True)
        stage_reports.append(
            {
                "budget_mb": budget_mb,
                "evaluated": [result.to_dict() for result in rows],
                "survivors": [result.name for result in rows[:survivors]],
            }
        )
        final_rows = rows
        survivor_names = {result.name for result in rows[:survivors]}
        candidates = [config for config in candidates if config.name in survivor_names]

    winner = max(final_rows, key=lambda result: (result.composite_score, result.name))
    atomic_rows = [
        result
        for stage in stage_reports
        for result in stage["evaluated"]
        if result["name"] == "atomic_cortex"
    ]
    atomic_score = atomic_rows[0]["composite_score"] if atomic_rows else 0.0
    return {
        "experiment": "SPARC-HS18 256MB neuroscience-mechanism prototype search",
        "stages": stage_reports,
        "winner": winner.to_dict(),
        "winner_advantage_over_atomic_points": 100.0 * (winner.composite_score - atomic_score),
        "candidate_architecture_found": (
            winner.name == "planning_hybrid"
            and winner.one_shot_accuracy == 1.0
            and winner.delayed_planning_accuracy == 1.0
            and winner.composite_score - atomic_score >= 0.25
        ),
        "actual_256mb_budget_tested": any(stage["budget_mb"] == 256 for stage in stage_reports),
        "same_learning_code_all_prototypes": True,
        "task_specific_solver_inside_model": False,
        "transformer_used": False,
        "backpropagation_used": False,
        "raw_language_concept_learning_passed": False,
        "general_intelligence_discovered": False,
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
    }
