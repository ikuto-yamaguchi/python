from __future__ import annotations

import base64
import json
import math
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .sparc_cross_domain_plans import _SUBJECT_SLOT, _template_regex
from .sparc_episodic import SparseEpisodicRevisionMemory, _strip_predicate_end
from .sparc_language import ReplyResult
from .sparc_programs import _literal_anchors
from .sparc_relational_plans import SPARCHS12Model, SparseRelationalPlanBank


@dataclass(frozen=True)
class GoalRule:
    head_relation: str
    body_relations: tuple[str, ...]
    support: int


@dataclass(frozen=True)
class GoalRuleSchema:
    template: str
    head_relation: str
    support: int


@dataclass(frozen=True)
class DerivedValue:
    value: str
    source_ids: tuple[str, ...]
    proof_steps: tuple[str, ...]


def _answer_value(answer: str) -> str:
    text = answer.strip().strip("。！？ ")
    text = text.removeprefix("答えは").removeprefix("結論は")
    return _strip_predicate_end(text)


def _template(question: str, subject: str) -> str:
    if subject not in question:
        raise ValueError("question does not contain inferred subject")
    return question.replace(subject, _SUBJECT_SLOT, 1)


class SparseGoalRuleBank:
    def __init__(
        self,
        *,
        max_rules: int = 10_000,
        max_schemas: int = 100_000,
        max_candidates: int = 32,
        max_rule_depth: int = 4,
        max_frontier: int = 32,
    ) -> None:
        self.max_rules = max_rules
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.max_rule_depth = max_rule_depth
        self.max_frontier = max_frontier
        self.rules: list[GoalRule] = []
        self.schemas: list[GoalRuleSchema] = []
        self.rule_ids: dict[tuple[str, tuple[str, ...]], int] = {}
        self.rules_by_head: dict[str, list[int]] = defaultdict(list)
        self.schema_ids: dict[str, int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.last_schema_reads = 0
        self.last_rule_reads = 0
        self.last_edge_reads = 0
        self.last_nodes_activated = 0
        self.last_recursive_goals = 0
        self.last_induction_states = 0
        self.last_rule_candidates = 0
        self.last_conflict = False

    @staticmethod
    def _direct_values(
        subject: str,
        relation: str,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
        counter: list[int],
    ) -> tuple[DerivedValue, ...]:
        grouped: dict[str, list[tuple[int, object]]] = defaultdict(list)
        for episode_id in graph.outgoing.get(subject, {}).get(relation, ()):
            counter[0] += 1
            episode = episodic.episodes[episode_id]
            if episode.active and episode.claim_value is not None:
                grouped[episode.claim_value].append((episode_id, episode))
        output: list[DerivedValue] = []
        for value, rows in grouped.items():
            sources: list[str] = []
            for _episode_id, episode in rows:
                if episode.source_id not in sources:
                    sources.append(episode.source_id)
            output.append(
                DerivedValue(
                    value,
                    tuple(sources),
                    (f"{subject} --{relation}→ {value}",),
                )
            )
        return tuple(output)

    def _paths_to_target_excluding_head(
        self,
        subject: str,
        target: str,
        head_relation: str,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> set[tuple[str, ...]]:
        paths: set[tuple[str, ...]] = set()
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(subject, ())])
        seen: set[tuple[str, tuple[str, ...]]] = {(subject, ())}
        edge_counter = [0]
        states = 0
        while queue:
            node, relations = queue.popleft()
            states += 1
            if states > 4_096 or len(relations) >= 5:
                continue
            for relation in sorted(graph.outgoing.get(node, {}))[:32]:
                if node == subject and relation == head_relation:
                    continue
                values = self._direct_values(
                    node,
                    relation,
                    graph=graph,
                    episodic=episodic,
                    counter=edge_counter,
                )
                for item in values[: self.max_frontier]:
                    next_path = relations + (relation,)
                    if item.value == target:
                        paths.add(next_path)
                    state = (item.value, next_path)
                    if state not in seen and len(seen) < 4_096:
                        seen.add(state)
                        queue.append(state)
        self.last_edge_reads += edge_counter[0]
        self.last_induction_states = max(self.last_induction_states, states)
        return paths

    def _direct_head_relations(
        self,
        subject: str,
        target: str,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> set[str]:
        output: set[str] = set()
        edge_counter = [0]
        for relation in graph.outgoing.get(subject, {}):
            values = self._direct_values(
                subject,
                relation,
                graph=graph,
                episodic=episodic,
                counter=edge_counter,
            )
            if any(item.value == target for item in values):
                output.add(relation)
        self.last_edge_reads += edge_counter[0]
        return output

    def _intern_rule(self, rule: GoalRule) -> int:
        key = (rule.head_relation, rule.body_relations)
        existing = self.rule_ids.get(key)
        if existing is not None:
            return existing
        if len(self.rules) >= self.max_rules:
            raise MemoryError("goal rule capacity reached")
        rule_id = len(self.rules)
        self.rules.append(rule)
        self.rule_ids[key] = rule_id
        self.rules_by_head[rule.head_relation].append(rule_id)
        return rule_id

    def _register_schema(
        self, template: str, head_relation: str, support: int
    ) -> int:
        existing = self.schema_ids.get(template)
        if existing is not None:
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("goal rule schema capacity reached")
        schema_id = len(self.schemas)
        self.schemas.append(GoalRuleSchema(template, head_relation, support))
        self.schema_ids[template] = schema_id
        literal = template.replace(_SUBJECT_SLOT, "")
        for anchor in _literal_anchors(literal) or {literal}:
            self.postings[anchor].add(schema_id)
        return schema_id

    def teach(
        self,
        examples: Iterable[tuple[str, str]],
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> GoalRule:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two demonstrations are required")
        common: set[tuple[str, tuple[str, ...]]] | None = None
        parsed: list[tuple[str, str]] = []
        self.last_edge_reads = 0
        self.last_induction_states = 0
        for question, answer in rows:
            subjects = graph._candidate_subjects(question)
            if not subjects:
                raise ValueError("could not infer a known subject from question")
            subject = max(subjects, key=len)
            target = _answer_value(answer)
            candidates: set[tuple[str, tuple[str, ...]]] = set()
            for head in self._direct_head_relations(
                subject, target, graph=graph, episodic=episodic
            ):
                for body in self._paths_to_target_excluding_head(
                    subject,
                    target,
                    head,
                    graph=graph,
                    episodic=episodic,
                ):
                    candidates.add((head, body))
            if not candidates:
                raise ValueError("no redundant conclusion and support path found")
            common = candidates if common is None else common & candidates
            parsed.append((question, subject))
        if not common:
            raise ValueError("demonstrations share no variable-binding rule")
        head, body = min(common, key=lambda item: (len(item[1]), item[0], item[1]))
        rule = GoalRule(head, body, len(parsed))
        self._intern_rule(rule)
        for question, subject in parsed:
            self._register_schema(_template(question, subject), head, len(parsed))
        return rule

    def link_surface(
        self, question: str, subject: str, head_relation: str, support: int = 1
    ) -> int:
        return self._register_schema(
            _template(question, subject), head_relation, support
        )

    def _candidate_schemas(self, question: str) -> list[int]:
        routes = sorted(
            (
                len(self.postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _literal_anchors(question)
            if self.postings.get(anchor)
        )
        votes: Counter[int] = Counter()
        reads = 0
        for posting_size, negative_length, anchor in routes[:8]:
            if votes and posting_size > self.max_candidates * 4:
                break
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for schema_id in self.postings[anchor]:
                votes[schema_id] += weight
                reads += 1
            if len(votes) >= self.max_candidates:
                break
        self.last_schema_reads = reads
        return [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]

    @staticmethod
    def _merge_sources(*groups: tuple[str, ...]) -> tuple[str, ...]:
        output: list[str] = []
        for group in groups:
            for source in group:
                if source not in output:
                    output.append(source)
        return tuple(output)

    def _resolve(
        self,
        subject: str,
        relation: str,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
        depth: int,
        visited: frozenset[tuple[str, str]],
    ) -> tuple[DerivedValue, ...]:
        self.last_recursive_goals += 1
        goal = (subject, relation)
        if goal in visited or depth > self.max_rule_depth:
            return ()
        next_visited = visited | {goal}
        edge_counter = [0]
        direct = self._direct_values(
            subject,
            relation,
            graph=graph,
            episodic=episodic,
            counter=edge_counter,
        )
        self.last_edge_reads += edge_counter[0]
        if direct:
            if len({item.value for item in direct}) > 1:
                self.last_conflict = True
            return direct

        results: list[DerivedValue] = []
        rule_ids = self.rules_by_head.get(relation, ())[:8]
        self.last_rule_candidates = max(self.last_rule_candidates, len(rule_ids))
        for rule_id in rule_ids:
            self.last_rule_reads += 1
            rule = self.rules[rule_id]
            frontier: dict[str, DerivedValue] = {
                subject: DerivedValue(subject, (), ())
            }
            for body_relation in rule.body_relations:
                next_frontier: dict[str, DerivedValue] = {}
                for node, accumulated in tuple(frontier.items())[: self.max_frontier]:
                    values = self._resolve(
                        node,
                        body_relation,
                        graph=graph,
                        episodic=episodic,
                        depth=depth + 1,
                        visited=next_visited,
                    )
                    if self.last_conflict:
                        return ()
                    for item in values[: self.max_frontier]:
                        next_frontier[item.value] = DerivedValue(
                            item.value,
                            self._merge_sources(
                                accumulated.source_ids, item.source_ids
                            ),
                            accumulated.proof_steps + item.proof_steps,
                        )
                self.last_nodes_activated += len(frontier) + len(next_frontier)
                if not next_frontier or len(next_frontier) > self.max_frontier:
                    frontier = {}
                    break
                frontier = next_frontier
            for item in frontier.values():
                results.append(
                    DerivedValue(
                        item.value,
                        item.source_ids,
                        (
                            f"rule {rule.head_relation}(x,z) <- "
                            + " -> ".join(rule.body_relations),
                        )
                        + item.proof_steps,
                    )
                )
        unique: dict[tuple[str, tuple[str, ...]], DerivedValue] = {}
        for item in results:
            unique[(item.value, item.source_ids)] = item
        return tuple(unique.values())

    def solve(
        self,
        question: str,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> ReplyResult | None:
        self.last_rule_reads = 0
        self.last_edge_reads = 0
        self.last_nodes_activated = 0
        self.last_recursive_goals = 0
        self.last_rule_candidates = 0
        self.last_conflict = False
        for schema_id in self._candidate_schemas(question):
            schema = self.schemas[schema_id]
            match = _template_regex(schema.template).match(question)
            if match is None:
                continue
            subject = match.group(1)
            values = self._resolve(
                subject,
                schema.head_relation,
                graph=graph,
                episodic=episodic,
                depth=0,
                visited=frozenset(),
            )
            if self.last_conflict:
                return ReplyResult(
                    text=(
                        f"{subject}の{schema.head_relation}に必要な資料が矛盾しているため、"
                        "規則推論を確定できません。"
                    ),
                    confidence=0.25,
                    mechanism="goal-rule-evidence-conflict",
                    candidates_inspected=self.last_rule_candidates,
                    active_bits=self.last_nodes_activated,
                    estimated_sparse_operations=(
                        self.last_schema_reads
                        + self.last_rule_reads
                        + self.last_edge_reads
                        + self.last_nodes_activated
                    ),
                )
            endpoints = sorted({item.value for item in values})
            if not endpoints:
                continue
            if len(endpoints) > 1:
                return ReplyResult(
                    text=(
                        f"{subject}の{schema.head_relation}は候補が{len(endpoints)}件あり、"
                        "一意に確定できません。"
                    ),
                    confidence=0.30,
                    mechanism="goal-rule-ambiguous-endpoint",
                    candidates_inspected=self.last_rule_candidates,
                    active_bits=self.last_nodes_activated,
                    estimated_sparse_operations=(
                        self.last_schema_reads
                        + self.last_rule_reads
                        + self.last_edge_reads
                        + self.last_nodes_activated
                    ),
                )
            answer = endpoints[0]
            selected = next(item for item in values if item.value == answer)
            operations = (
                self.last_schema_reads
                + self.last_rule_reads
                + self.last_edge_reads
                + self.last_nodes_activated
                + self.last_recursive_goals
            )
            return ReplyResult(
                text=(
                    f"{answer}です。目標{schema.head_relation}を逆向きに解き、"
                    f"証明: {'；'.join(selected.proof_steps)}。"
                    f"出典: {'、'.join(f'［{source}］' for source in selected.source_ids)}"
                ),
                confidence=min(0.98, 0.78 + 0.04 * math.log2(schema.support + 1)),
                mechanism="goal-directed-learned-rule",
                candidates_inspected=max(1, self.last_rule_candidates),
                active_bits=self.last_nodes_activated,
                estimated_sparse_operations=operations,
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-goal-rules-hs13",
            "max_rules": self.max_rules,
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "max_rule_depth": self.max_rule_depth,
            "max_frontier": self.max_frontier,
            "rules": [asdict(rule) for rule in self.rules],
            "schemas": [asdict(schema) for schema in self.schemas],
        }
        return zlib.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseGoalRuleBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(
            max_rules=int(payload["max_rules"]),
            max_schemas=int(payload["max_schemas"]),
            max_candidates=int(payload["max_candidates"]),
            max_rule_depth=int(payload["max_rule_depth"]),
            max_frontier=int(payload["max_frontier"]),
        )
        for row in payload["rules"]:
            bank._intern_rule(
                GoalRule(
                    str(row["head_relation"]),
                    tuple(row["body_relations"]),
                    int(row["support"]),
                )
            )
        for row in payload["schemas"]:
            bank._register_schema(
                str(row["template"]),
                str(row["head_relation"]),
                int(row["support"]),
            )
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "rules": len(self.rules),
            "schemas": len(self.schemas),
            "head_predicates": len(self.rules_by_head),
            "serialized_bytes": len(self.to_bytes()),
            "last_schema_reads": self.last_schema_reads,
            "last_rule_reads": self.last_rule_reads,
            "last_edge_reads": self.last_edge_reads,
            "last_nodes_activated": self.last_nodes_activated,
            "last_recursive_goals": self.last_recursive_goals,
            "last_induction_states": self.last_induction_states,
            "last_rule_candidates": self.last_rule_candidates,
            "last_conflict": self.last_conflict,
            "forward_materialisation_used": False,
            "global_entity_scan_used": False,
            "global_edge_scan_used": False,
            "global_rule_scan_used": False,
        }


class SPARCHS13Model:
    def __init__(self, base: SPARCHS12Model | None = None) -> None:
        self.base = base or SPARCHS12Model()
        self.goal_rules = SparseGoalRuleBank()

    @property
    def episodic(self) -> SparseEpisodicRevisionMemory:
        return self.base.episodic

    @property
    def graph(self) -> SparseRelationalPlanBank:
        return self.base.relational_plans

    def ingest_fact(
        self, text: str, *, source_id: str, revision: bool = False
    ) -> tuple[int, ...]:
        return self.base.ingest_fact(text, source_id=source_id, revision=revision)

    def teach_rule(self, examples: Iterable[tuple[str, str]]) -> GoalRule:
        return self.goal_rules.teach(
            examples, graph=self.graph, episodic=self.episodic
        )

    def link_rule_surface(
        self, question: str, subject: str, head_relation: str, support: int = 1
    ) -> int:
        return self.goal_rules.link_surface(
            question, subject, head_relation, support
        )

    def reply(self, text: str) -> ReplyResult:
        ruled = self.goal_rules.solve(
            text, graph=self.graph, episodic=self.episodic
        )
        if ruled is not None:
            return ruled
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs13",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "rules": base64.b85encode(self.goal_rules.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS13Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS12Model.from_bytes(base64.b85decode(payload["base"])))
        model.goal_rules = SparseGoalRuleBank.from_bytes(
            base64.b85decode(payload["rules"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS13Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS13",
            "base": self.base.report(),
            "goal_rules": self.goal_rules.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
