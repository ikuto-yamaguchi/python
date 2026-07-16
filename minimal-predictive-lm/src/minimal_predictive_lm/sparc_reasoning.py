from __future__ import annotations

import json
import re
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RelationFact:
    subject: str
    relation: str
    object: str
    polarity: bool = True
    confidence: float = 1.0


@dataclass(frozen=True)
class ReasoningResult:
    text: str
    confidence: float
    mechanism: str
    path: tuple[RelationFact, ...]
    nodes_activated: int
    edges_inspected: int
    bounded: bool


@dataclass(frozen=True)
class ReasoningProfile:
    name: str
    max_entities: int
    max_edges: int
    max_hops: int
    max_activations: int
    max_edges_per_query: int


REASONING_PROFILES = {
    "ci": ReasoningProfile("ci", 100_000, 1_000_000, 8, 128, 512),
    "desktop-large": ReasoningProfile("desktop-large", 2_000_000, 32_000_000, 12, 256, 2048),
    "desktop-xl": ReasoningProfile("desktop-xl", 8_000_000, 128_000_000, 16, 512, 8192),
}


def _norm(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    text = re.sub(r"\s+", "", text)
    return text.strip("。！")


def _entity(text: str) -> str:
    return _norm(text).strip("、,「」『』\"'")


_DIMENSION = {
    "高い": "height",
    "低い": "height",
    "大きい": "size",
    "小さい": "size",
    "速い": "speed",
    "遅い": "speed",
    "重い": "weight",
    "軽い": "weight",
    "長い": "length",
    "短い": "length",
    "多い": "amount",
    "少ない": "amount",
    "強い": "strength",
    "弱い": "strength",
}
_GREATER_WORDS = {"高い", "大きい", "速い", "重い", "長い", "多い", "強い"}


class SparseRelationalCortex:
    """Event-driven relational cortex with bounded local propagation.

    Knowledge capacity can grow, but a query only activates the subgraph reached
    from its subject within fixed hop, node and edge budgets. Contradictory
    negative evidence is stored separately and blocks unsupported positive paths.
    """

    def __init__(self, profile: str | ReasoningProfile = "ci") -> None:
        self.profile = REASONING_PROFILES[profile] if isinstance(profile, str) else profile
        self.entities: dict[str, int] = {}
        self.labels: list[str] = []
        self.outgoing: dict[tuple[int, str, bool], Counter[int]] = defaultdict(Counter)
        self.incoming: dict[tuple[int, str, bool], Counter[int]] = defaultdict(Counter)
        self.edge_count = 0
        self.observations = 0
        self.surprise_writes = 0
        self.last_nodes_activated = 0
        self.last_edges_inspected = 0

    def _intern(self, label: str) -> int:
        label = _entity(label)
        found = self.entities.get(label)
        if found is not None:
            return found
        if len(self.labels) >= self.profile.max_entities:
            raise MemoryError("entity capacity reached")
        idx = len(self.labels)
        self.entities[label] = idx
        self.labels.append(label)
        return idx

    def add_fact(self, fact: RelationFact) -> bool:
        source = self._intern(fact.subject)
        target = self._intern(fact.object)
        key = (source, fact.relation, fact.polarity)
        existed = self.outgoing[key][target] > 0
        self.observations += 1
        self.outgoing[key][target] += 1
        self.incoming[(target, fact.relation, fact.polarity)][source] += 1
        if not existed:
            if self.edge_count >= self.profile.max_edges:
                self.outgoing[key][target] -= 1
                self.incoming[(target, fact.relation, fact.polarity)][source] -= 1
                raise MemoryError("edge capacity reached")
            self.edge_count += 1
            self.surprise_writes += 1
        return not existed

    def parse_statement(self, text: str) -> tuple[RelationFact, ...]:
        text = _norm(text)
        match = re.match(r"^(.+?)の原因は(.+?)(?:です|だ|である)?$", text)
        if match:
            effect, cause = map(_entity, match.groups())
            return (RelationFact(cause, "causes", effect),)
        match = re.match(r"^(.+?)が原因で(.+?)(?:です|だ|である)?$", text)
        if match:
            cause, effect = map(_entity, match.groups())
            return (RelationFact(cause, "causes", effect),)
        match = re.match(r"^(.+?)は(.+?)より(高い|低い|大きい|小さい|速い|遅い|重い|軽い|長い|短い|多い|少ない|強い|弱い)(?:です)?$", text)
        if match:
            left, right, word = match.groups()
            relation = ("greater:" if word in _GREATER_WORDS else "less:") + _DIMENSION[word]
            return (RelationFact(_entity(left), relation, _entity(right)),)
        match = re.match(r"^(.+?)の([^は]+?)は(.+?)(?:です|だ|である)?$", text)
        if match:
            subject, prop, value = map(_entity, match.groups())
            return (RelationFact(subject, f"property:{prop}", value),)
        match = re.match(r"^(.+?)は(.+?)(?:ではありません|ではない|じゃありません|じゃない)$", text)
        if match:
            return (RelationFact(_entity(match.group(1)), "isa", _entity(match.group(2)), False),)
        match = re.match(r"^(?:すべての)?(.+?)は(.+?)(?:です|だ|である)$", text)
        if match:
            return (RelationFact(_entity(match.group(1)), "isa", _entity(match.group(2))),)
        return ()

    def learn_text(self, text: str) -> tuple[RelationFact, ...]:
        facts = self.parse_statement(text)
        for fact in facts:
            self.add_fact(fact)
        return facts

    @staticmethod
    def _transitive(relation: str) -> bool:
        return relation in {"isa", "located_in", "causes"} or relation.startswith("greater:") or relation.startswith("less:")

    @staticmethod
    def _inverse_relation(relation: str) -> str | None:
        if relation.startswith("greater:"):
            return "less:" + relation.split(":", 1)[1]
        if relation.startswith("less:"):
            return "greater:" + relation.split(":", 1)[1]
        return None

    def _direct_negative(self, source: int, relation: str, target: int) -> bool:
        return self.outgoing.get((source, relation, False), Counter()).get(target, 0) > 0

    def _search(self, subject: str, relation: str, target: str) -> tuple[bool, tuple[RelationFact, ...], int, int, bool]:
        source = self.entities.get(_entity(subject))
        goal = self.entities.get(_entity(target))
        if source is None or goal is None:
            return False, (), 0, 0, False
        if self._direct_negative(source, relation, goal):
            return False, (RelationFact(subject, relation, target, False),), 1, 1, False
        queue = deque([(source, tuple())])
        visited = {source}
        edges = 0
        bounded = False
        while queue:
            node, path = queue.popleft()
            if len(path) >= self.profile.max_hops:
                bounded = True
                continue
            targets = self.outgoing.get((node, relation, True), Counter())
            for nxt, count in targets.items():
                edges += 1
                fact = RelationFact(self.labels[node], relation, self.labels[nxt], True, min(1.0, count / 3.0 + 0.66))
                candidate_path = path + (fact,)
                if nxt == goal:
                    self.last_nodes_activated = len(visited) + (0 if nxt in visited else 1)
                    self.last_edges_inspected = edges
                    return True, candidate_path, self.last_nodes_activated, edges, bounded
                if self._transitive(relation) and nxt not in visited:
                    if len(visited) >= self.profile.max_activations or edges >= self.profile.max_edges_per_query:
                        bounded = True
                        self.last_nodes_activated = len(visited)
                        self.last_edges_inspected = edges
                        return False, (), len(visited), edges, bounded
                    visited.add(nxt)
                    queue.append((nxt, candidate_path))
            inverse = self._inverse_relation(relation)
            if inverse is not None:
                reverse_sources = self.incoming.get((node, inverse, True), Counter())
                for nxt, count in reverse_sources.items():
                    edges += 1
                    fact = RelationFact(self.labels[node], relation, self.labels[nxt], True, min(1.0, count / 3.0 + 0.66))
                    candidate_path = path + (fact,)
                    if nxt == goal:
                        self.last_nodes_activated = len(visited) + (0 if nxt in visited else 1)
                        self.last_edges_inspected = edges
                        return True, candidate_path, self.last_nodes_activated, edges, bounded
                    if nxt not in visited:
                        if len(visited) >= self.profile.max_activations or edges >= self.profile.max_edges_per_query:
                            bounded = True
                            break
                        visited.add(nxt)
                        queue.append((nxt, candidate_path))
        self.last_nodes_activated = len(visited)
        self.last_edges_inspected = edges
        return False, (), len(visited), edges, bounded

    def _explain(self, path: tuple[RelationFact, ...]) -> str:
        clauses = []
        for fact in path:
            if fact.relation == "isa":
                clauses.append(f"{fact.subject}は{fact.object}")
            elif fact.relation == "causes":
                clauses.append(f"{fact.subject}が{fact.object}の原因")
            elif fact.relation.startswith("greater:"):
                clauses.append(f"{fact.subject}は{fact.object}より大きい側")
            elif fact.relation.startswith("less:"):
                clauses.append(f"{fact.subject}は{fact.object}より小さい側")
            else:
                clauses.append(f"{fact.subject}と{fact.object}に{fact.relation}関係がある")
        return "、".join(clauses)

    def answer(self, text: str) -> ReasoningResult | None:
        text = _norm(text)
        match = re.match(r"^(.+?)の(.+?)は(?:何|なに|誰)(?:ですか|なの|だ)?？?$", text)
        if match:
            subject, prop = map(_entity, match.groups())
            source = self.entities.get(subject)
            relation = f"property:{prop}"
            if source is None:
                return None
            values = self.outgoing.get((source, relation, True), Counter())
            self.last_nodes_activated = 1
            self.last_edges_inspected = len(values)
            if not values:
                return None
            target, count = values.most_common(1)[0]
            value = self.labels[target]
            return ReasoningResult(f"{subject}の{prop}は{value}です。", min(1.0, 0.7 + count / 10), "direct-property", (RelationFact(subject, relation, value),), 2, len(values), False)
        match = re.match(r"^(.+?)の原因は(?:何|なに)(?:ですか)?？?$", text)
        if match:
            effect = _entity(match.group(1))
            target = self.entities.get(effect)
            if target is None:
                return None
            causes = self.incoming.get((target, "causes", True), Counter())
            self.last_nodes_activated = 1 + len(causes)
            self.last_edges_inspected = len(causes)
            if not causes:
                return None
            source, count = causes.most_common(1)[0]
            cause = self.labels[source]
            return ReasoningResult(f"{cause}が原因です。", min(1.0, 0.7 + count / 10), "causal-recall", (RelationFact(cause, "causes", effect),), 2, len(causes), False)
        match = re.match(r"^(.+?)は(.+?)の原因(?:ですか|なの|か)？?$", text)
        if match:
            subject, target = map(_entity, match.groups())
            found, path, nodes, edges, bounded = self._search(subject, "causes", target)
            if found:
                return ReasoningResult(f"はい。{self._explain(path)}ためです。", 0.92, "bounded-causal-chain", path, nodes, edges, bounded)
            return ReasoningResult("その因果関係は確認できません。", 0.55, "bounded-causal-chain", path, nodes, edges, bounded)
        match = re.match(r"^(.+?)と(.+?)ではどちらが(高い|大きい|速い|重い|長い|多い|強い)(?:ですか)?？?$", text)
        if match:
            left, right, word = match.groups()
            relation = "greater:" + _DIMENSION[word]
            found, path, nodes, edges, bounded = self._search(_entity(left), relation, _entity(right))
            if found:
                return ReasoningResult(f"{_entity(left)}の方が{word}です。{self._explain(path)}ためです。", 0.9, "bounded-comparison-chain", path, nodes, edges, bounded)
            reverse, rpath, rnodes, redges, rbounded = self._search(_entity(right), relation, _entity(left))
            if reverse:
                return ReasoningResult(f"{_entity(right)}の方が{word}です。{self._explain(rpath)}ためです。", 0.9, "bounded-comparison-chain", rpath, rnodes, redges, rbounded)
            return None
        match = re.match(r"^(.+?)は(.+?)(?:ですか|なの|か)？?$", text)
        if match:
            subject, target = map(_entity, match.groups())
            found, path, nodes, edges, bounded = self._search(subject, "isa", target)
            if found:
                return ReasoningResult(f"はい。{self._explain(path)}ので、{subject}は{target}です。", 0.94, "bounded-relational-microprogram", path, nodes, edges, bounded)
            source_id = self.entities.get(subject)
            target_id = self.entities.get(target)
            if source_id is not None and target_id is not None and self._direct_negative(source_id, "isa", target_id):
                fact = RelationFact(subject, "isa", target, False)
                return ReasoningResult(f"いいえ。{subject}は{target}ではないと学習しています。", 0.98, "explicit-negative-evidence", (fact,), 2, 1, False)
            return None
        return None

    def to_bytes(self) -> bytes:
        rows = []
        for (source, relation, polarity), targets in self.outgoing.items():
            for target, count in targets.items():
                rows.append((source, relation, polarity, target, count))
        payload = {
            "format": "sparc-reasoning-hs2",
            "profile": asdict(self.profile),
            "labels": self.labels,
            "edges": rows,
            "observations": self.observations,
            "surprise_writes": self.surprise_writes,
        }
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseRelationalCortex":
        payload = json.loads(zlib.decompress(data))
        model = cls(ReasoningProfile(**payload["profile"]))
        for label in payload["labels"]:
            model._intern(label)
        for source, relation, polarity, target, count in payload["edges"]:
            model.outgoing[(int(source), str(relation), bool(polarity))][int(target)] = int(count)
            model.incoming[(int(target), str(relation), bool(polarity))][int(source)] = int(count)
            model.edge_count += 1
        model.observations = int(payload["observations"])
        model.surprise_writes = int(payload["surprise_writes"])
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SparseRelationalCortex":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, int | float | str | bool]:
        return {
            "profile": self.profile.name,
            "entities": len(self.labels),
            "relation_edges": self.edge_count,
            "observations": self.observations,
            "surprise_writes": self.surprise_writes,
            "write_fraction": self.surprise_writes / self.observations if self.observations else 0.0,
            "serialized_bytes": len(self.to_bytes()),
            "max_hops": self.profile.max_hops,
            "max_activations": self.profile.max_activations,
            "max_edges_per_query": self.profile.max_edges_per_query,
            "last_nodes_activated": self.last_nodes_activated,
            "last_edges_inspected": self.last_edges_inspected,
            "full_history_attention_used": False,
            "growing_kv_cache_used": False,
            "dense_global_graph_scan_used": False,
        }
