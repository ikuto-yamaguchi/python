from __future__ import annotations
import hashlib
import itertools
import json
import math
import re
from array import array
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable, Iterator, Mapping, Sequence
_TOKEN_RE = re.compile('[A-Za-z]+\\d*|\\d+|[一-龥々〆ヵヶ]+|[ぁ-んー]+|[ァ-ヶー]+|[^\\s]')

def stable_hash(text: str) -> int:
    value = int.from_bytes(hashlib.blake2b(text.encode('utf-8'), digest_size=8).digest(), 'little')
    return value or 1

def tokenize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text))

class DistributionalRoleInducer:

    def __init__(self, *, min_count: int=8, min_followers: int=2, cluster_threshold: float=0.75) -> None:
        self.min_count = min_count
        self.min_followers = min_followers
        self.cluster_threshold = cluster_threshold
        self.anchor_to_role: dict[str, str] = {}
        self.role_members: dict[str, tuple[str, ...]] = {}

    def fit(self, texts: Iterable[str]) -> 'DistributionalRoleInducer':
        followers: dict[str, Counter[str]] = defaultdict(Counter)
        predecessors: dict[str, Counter[str]] = defaultdict(Counter)
        counts: Counter[str] = Counter()
        starts: Counter[str] = Counter()
        documents = 0
        for text in texts:
            tokens = tokenize(text)
            documents += 1
            if tokens:
                starts[tokens[0]] += 1
            for index, token in enumerate(tokens):
                counts[token] += 1
                if index:
                    predecessors[token][tokens[index - 1]] += 1
                if index + 1 < len(tokens):
                    followers[token][tokens[index + 1]] += 1
        lexical_candidates = [token for token in followers if counts[token] >= self.min_count and len(followers[token]) >= self.min_followers and (not any((character.isdigit() for character in token)))]
        strong_anchors = [token for token in lexical_candidates if len(predecessors[token]) >= 3 or starts[token] >= max(3, documents // 50)]
        anchors = set(strong_anchors)
        for token in lexical_candidates:
            support = set(followers[token])
            if any((len(support & set(followers[anchor])) / max(1, len(support | set(followers[anchor]))) >= self.cluster_threshold for anchor in strong_anchors)):
                anchors.add(token)
        clusters: list[tuple[set[str], list[str]]] = []
        for anchor in sorted(anchors):
            support = set(followers[anchor])
            best_index = -1
            best_score = 0.0
            for index, (union_support, _members) in enumerate(clusters):
                score = len(support & union_support) / max(1, len(support | union_support))
                if score > best_score:
                    best_score = score
                    best_index = index
            if best_index >= 0 and best_score >= self.cluster_threshold:
                clusters[best_index][0].update(support)
                clusters[best_index][1].append(anchor)
            else:
                clusters.append((set(support), [anchor]))
        self.anchor_to_role.clear()
        self.role_members.clear()
        for index, (_support, members) in enumerate(clusters):
            role = f'R{index}'
            self.role_members[role] = tuple(members)
            for anchor in members:
                self.anchor_to_role[anchor] = role
        return self

    def bindings(self, text: str) -> tuple[tuple[str, str], ...]:
        tokens = tokenize(text)
        bindings = {(self.anchor_to_role[token], tokens[index + 1]) for index, token in enumerate(tokens[:-1]) if token in self.anchor_to_role}
        return tuple(sorted(bindings))

    def to_dict(self) -> dict:
        return {'anchor_to_role': dict(self.anchor_to_role), 'role_members': {role: list(members) for role, members in self.role_members.items()}}

class ContextGateInducer:

    def __init__(self, *, min_purity: float=0.98, min_coverage: int=100) -> None:
        self.min_purity = min_purity
        self.min_coverage = min_coverage
        self.schemas: dict[tuple[str, str], tuple[str, str, float, int]] = {}

    def fit(self, role_inducer: DistributionalRoleInducer, examples: Iterable[tuple[str, str]], actions: Sequence[str]) -> 'ContextGateInducer':
        action_index = {action: index for index, action in enumerate(actions)}
        statistics: dict[tuple[str, str, str, str], dict[tuple[str, str], list[int]]] = defaultdict(lambda: defaultdict(lambda: [0] * len(actions)))
        for text, target in examples:
            bindings = dict(role_inducer.bindings(text))
            target_index = action_index[target]
            roles = sorted(bindings)
            for context_role in roles:
                context_value = bindings[context_role]
                other_roles = [role for role in roles if role != context_role]
                for left_role, right_role in itertools.combinations(other_roles, 2):
                    row = statistics[context_role, context_value, left_role, right_role][bindings[left_role], bindings[right_role]]
                    row[target_index] += 1
        candidates_by_context: dict[tuple[str, str], list[tuple[float, int, str, str]]] = defaultdict(list)
        for (context_role, context_value, left_role, right_role), rows in statistics.items():
            repeated_rows = [row for row in rows.values() if sum(row) >= 3]
            if not repeated_rows:
                continue
            total = sum((sum(row) for row in repeated_rows))
            purity = sum((max(row) for row in repeated_rows)) / total
            coverage = len(repeated_rows)
            candidates_by_context[context_role, context_value].append((purity, coverage, left_role, right_role))
        self.schemas.clear()
        for context, candidates in candidates_by_context.items():
            candidates.sort(reverse=True)
            purity, coverage, left_role, right_role = candidates[0]
            if purity >= self.min_purity and coverage >= self.min_coverage:
                self.schemas[context] = (left_role, right_role, purity, coverage)
        return self

    def features(self, bindings: Iterable[tuple[str, str]]) -> tuple[int, ...]:
        values = dict(bindings)
        output: list[int] = []
        for (context_role, context_value), (left_role, right_role, _purity, _coverage) in self.schemas.items():
            if values.get(context_role) == context_value and left_role in values and (right_role in values):
                output.append(stable_hash(f'G:{context_role}={context_value}|{left_role}={values[left_role]}|{right_role}={values[right_role]}'))
        return tuple(output)

    def serialized_bytes(self) -> int:
        payload = {f'{role}={value}': list(schema) for (role, value), schema in self.schemas.items()}
        return len(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))

class FastCandidateStore:

    def __init__(self, action_count: int, budget_bytes: int) -> None:
        self.action_count = action_count
        self.slots = max(128, budget_bytes // (8 + action_count))
        self.fingerprints = array('Q', [0]) * self.slots
        self.counts = bytearray(self.slots * action_count)
        self.collisions = 0

    def update(self, fingerprint: int, target_index: int) -> bytes:
        position = fingerprint % self.slots
        offset = position * self.action_count
        if self.fingerprints[position] != fingerprint:
            if self.fingerprints[position]:
                self.collisions += 1
            self.fingerprints[position] = fingerprint
            self.counts[offset:offset + self.action_count] = bytes(self.action_count)
        count_index = offset + target_index
        if self.counts[count_index] < 255:
            self.counts[count_index] += 1
        return bytes(self.counts[offset:offset + self.action_count])

    def clear(self, fingerprint: int) -> None:
        position = fingerprint % self.slots
        if self.fingerprints[position] != fingerprint:
            return
        self.fingerprints[position] = 0
        offset = position * self.action_count
        self.counts[offset:offset + self.action_count] = bytes(self.action_count)

    @property
    def storage_bytes(self) -> int:
        return self.fingerprints.itemsize * len(self.fingerprints) + len(self.counts)

class PackedCorticalStore:

    def __init__(self, action_count: int, budget_bytes: int, *, max_probe: int=16) -> None:
        self.action_count = action_count
        self.max_probe = max_probe
        self.slots = max(128, budget_bytes // (8 + action_count + 1))
        self.fingerprints = array('Q', [0]) * self.slots
        self.counts = bytearray(self.slots * action_count)
        self.age = bytearray(self.slots)
        self.occupied = 0
        self.replacements = 0
        self.clock = 0
        self.lookup_count = 0
        self.probe_count = 0

    def _positions(self, fingerprint: int) -> Iterator[int]:
        position = fingerprint % self.slots
        step = (fingerprint >> 32 | 1) % self.slots or 1
        for _ in range(self.max_probe):
            yield position
            position = (position + step) % self.slots

    def read(self, fingerprint: int) -> bytes | None:
        self.lookup_count += 1
        for position in self._positions(fingerprint):
            self.probe_count += 1
            current = self.fingerprints[position]
            if current == fingerprint:
                offset = position * self.action_count
                return bytes(self.counts[offset:offset + self.action_count])
            if current == 0:
                return None
        return None

    def promote(self, fingerprint: int, evidence: bytes) -> None:
        self.clock = self.clock + 1 & 255
        empty_position: int | None = None
        candidates: list[int] = []
        for position in self._positions(fingerprint):
            current = self.fingerprints[position]
            if current == fingerprint:
                offset = position * self.action_count
                for index, value in enumerate(evidence):
                    self.counts[offset + index] = min(255, self.counts[offset + index] + value)
                self.age[position] = self.clock
                return
            if current == 0 and empty_position is None:
                empty_position = position
            candidates.append(position)
        if empty_position is not None:
            position = empty_position
            self.occupied += 1
        else:
            position = min(candidates, key=lambda candidate: (sum(self.counts[candidate * self.action_count:candidate * self.action_count + self.action_count]), self.age[candidate]))
            self.replacements += 1
        self.fingerprints[position] = fingerprint
        offset = position * self.action_count
        self.counts[offset:offset + self.action_count] = evidence
        self.age[position] = self.clock

    @property
    def average_probes(self) -> float:
        return self.probe_count / max(1, self.lookup_count)

    @property
    def storage_bytes(self) -> int:
        return self.fingerprints.itemsize * len(self.fingerprints) + len(self.counts) + len(self.age)

class RawCausalSchemaModel:

    def __init__(self, *, budget_mb: int, actions: Sequence[str]=('A', 'B', 'C'), schema_fraction: float=0.03) -> None:
        if budget_mb <= 0:
            raise ValueError('budget_mb must be positive')
        if not 0.0 < schema_fraction < 1.0:
            raise ValueError('schema_fraction must be between zero and one')
        self.actions = tuple(actions)
        self.budget_bytes = budget_mb * 1024 * 1024
        self.schema_fraction = schema_fraction
        schema_bytes = int(self.budget_bytes * schema_fraction)
        candidate_bytes = schema_bytes // 3
        cortical_bytes = schema_bytes - candidate_bytes
        self.roles = DistributionalRoleInducer()
        self.gate = ContextGateInducer()
        self.candidate_store = FastCandidateStore(len(self.actions), candidate_bytes)
        self.cortical_store = PackedCorticalStore(len(self.actions), cortical_bytes)
        used = self.candidate_store.storage_bytes + self.cortical_store.storage_bytes
        self.reserved_storage = bytearray(max(0, self.budget_bytes - used))
        self.prediction_count = 0
        self.feature_count = 0

    def fit_roles(self, texts: Iterable[str]) -> None:
        self.roles.fit(texts)

    def fit_context_gates(self, examples: Iterable[tuple[str, str]]) -> None:
        self.gate.fit(self.roles, examples, self.actions)

    def _features(self, text: str) -> tuple[int, ...]:
        bindings = self.roles.bindings(text)
        gated = self.gate.features(bindings)
        if gated:
            return gated
        output: list[int] = []
        for order in range(1, min(3, len(bindings)) + 1):
            for combination in itertools.combinations(bindings, order):
                output.append(stable_hash(f'O{order}:' + '|'.join((f'{role}={value}' for role, value in combination))))
        return tuple(output)

    def learn(self, text: str, target: str) -> None:
        target_index = self.actions.index(target)
        for fingerprint in self._features(text):
            evidence = self.candidate_store.update(fingerprint, target_index)
            total = sum(evidence)
            if total >= 3 and max(evidence) == total:
                self.cortical_store.promote(fingerprint, evidence)
                self.candidate_store.clear(fingerprint)

    def predict(self, text: str) -> str:
        votes = [0.0] * len(self.actions)
        features = self._features(text)
        self.prediction_count += 1
        self.feature_count += len(features)
        for fingerprint in features:
            evidence = self.cortical_store.read(fingerprint)
            if not evidence:
                continue
            total = sum(evidence)
            if total < 2:
                continue
            probabilities = [value / total for value in evidence]
            entropy = -sum((probability * math.log(probability + 1e-12) for probability in probabilities)) / math.log(len(evidence))
            certainty = max(0.0, 1.0 - entropy)
            weight = certainty * math.log1p(total)
            for index, probability in enumerate(probabilities):
                votes[index] += weight * probability
        return self.actions[max(range(len(votes)), key=lambda index: (votes[index], -index))]

    @property
    def managed_storage_bytes(self) -> int:
        return self.candidate_store.storage_bytes + self.cortical_store.storage_bytes + len(self.reserved_storage)

    @property
    def average_features_per_prediction(self) -> float:
        return self.feature_count / max(1, self.prediction_count)

    @property
    def estimated_active_storage_bytes_per_prediction(self) -> float:
        return self.average_features_per_prediction * self.cortical_store.average_probes * (8 + len(self.actions))

class SurfaceNgramBaseline:

    def __init__(self, *, budget_mb: int, actions: Sequence[str]=('A', 'B', 'C'), table_fraction: float=0.03) -> None:
        self.actions = tuple(actions)
        self.budget_bytes = budget_mb * 1024 * 1024
        table_bytes = int(self.budget_bytes * table_fraction)
        self.table = PackedCorticalStore(len(self.actions), table_bytes)
        self.reserve = bytearray(max(0, self.budget_bytes - self.table.storage_bytes))

    @staticmethod
    def _features(text: str) -> tuple[int, ...]:
        tokens = tokenize(text)
        output: list[int] = []
        for order in (1, 2, 3):
            for index in range(len(tokens) - order + 1):
                output.append(stable_hash('N:' + ' '.join(tokens[index:index + order])))
        return tuple(output)

    def learn(self, text: str, target: str) -> None:
        target_index = self.actions.index(target)
        evidence = bytes((1 if index == target_index else 0 for index in range(len(self.actions))))
        for fingerprint in self._features(text):
            self.table.promote(fingerprint, evidence)

    def predict(self, text: str) -> str:
        votes = [0] * len(self.actions)
        for fingerprint in self._features(text):
            evidence = self.table.read(fingerprint)
            if not evidence:
                continue
            for index, value in enumerate(evidence):
                votes[index] += value
        return self.actions[max(range(len(votes)), key=lambda index: (votes[index], -index))]
_TEMPLATES = ('世界 {world} 基準 {mode} 横値 {x} 縦値 {y} 噂 {hint}', '噂 {hint} 世界 {world} では 横値 {x} 縦値 {y} 基準 {mode}', '横値 {x} と 縦値 {y} 世界 {world} 判断基準 {mode} 参考 {hint}', '判断基準 {mode} 参考 {hint} 縦値 {y} 世界 {world} 横値 {x}')
_ACTIONS = ('A', 'B', 'C')

def _target(world: int, mode: str, value: int) -> str:
    return _ACTIONS[stable_hash(f'{world}|{mode}|{value}') % len(_ACTIONS)]

def _sentence(world: int, mode: str, x_value: int, y_value: int, hint: str, template_index: int) -> str:
    return _TEMPLATES[template_index].format(world=f'W{world}', mode=mode, x=f'X{x_value}', y=f'Y{y_value}', hint=hint)

def role_calibration_texts(worlds: int=256) -> Iterator[str]:
    for world in range(worlds):
        for mode in ('横', '縦'):
            for value in range(4):
                hint = _ACTIONS[stable_hash(f'calibration|{world}|{mode}|{value}') % len(_ACTIONS)]
                yield _sentence(world, mode, value, (value * 3 + world) % 4, hint, value % 3)

def training_examples(worlds: int) -> Iterator[tuple[str, str]]:
    for world in range(worlds):
        for mode in ('横', '縦'):
            for value in range(4):
                target = _target(world, mode, value)
                for repetition in range(3):
                    if mode == '横':
                        x_value = value
                        y_value = (value + repetition) % 4
                    else:
                        x_value = (value + repetition) % 4
                        y_value = value
                    hint = _ACTIONS[stable_hash(f'hint|{world}|{mode}|{value}|{repetition}') % len(_ACTIONS)]
                    yield (_sentence(world, mode, x_value, y_value, hint, (world + value + repetition) % 3), target)

def hidden_examples(worlds: int, *, start: int, count: int=500) -> Iterator[tuple[str, str]]:
    for world in range(start, min(worlds, start + count)):
        for mode in ('横', '縦'):
            for value in range(4):
                if mode == '横':
                    x_value = value
                    y_value = (value + 3) % 4
                else:
                    x_value = (value + 3) % 4
                    y_value = value
                hint = _ACTIONS[stable_hash(f'hidden-hint|{world}|{mode}|{value}') % len(_ACTIONS)]
                yield (_sentence(world, mode, x_value, y_value, hint, 3), _target(world, mode, value))

@dataclass(frozen=True, slots=True)
class BudgetEvaluation:
    budget_mb: int
    early_accuracy: float
    middle_accuracy: float
    late_accuracy: float
    overall_accuracy: float
    p95_latency_ms: float
    training_seconds: float
    managed_storage_bytes: int
    cortical_slots: int
    cortical_occupied: int
    cortical_utilization: float
    cortical_replacements: int
    candidate_collisions: int
    average_features_per_query: float
    average_lookup_probes: float
    estimated_active_storage_bytes_per_query: float
    learned_context_gates: int
    gate_serialized_bytes: int

    def to_dict(self) -> dict:
        return asdict(self)
