from __future__ import annotations

import base64
import json
import math
import re
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .sparc_cross_domain_plans import _SUBJECT_SLOT, _template_regex
from .sparc_cross_domain_plans_v2 import SPARCHS11ModelV2
from .sparc_episodic import Episode, SparseEpisodicRevisionMemory, _anchors, _strip_predicate_end
from .sparc_language import ReplyResult
from .sparc_programs import _literal_anchors


@dataclass(frozen=True)
class RelationalEvidence:
    subject: str
    relation: str
    value: str
    source_ids: tuple[str, ...]
    episode_ids: tuple[int, ...]


@dataclass(frozen=True)
class RelationalPlan:
    relations: tuple[str, ...]
    support: int


@dataclass(frozen=True)
class RelationalSchema:
    template: str
    plan_id: int
    support: int


def _answer_value(answer: str) -> str:
    text = answer.strip().strip("。！？ ")
    text = re.sub(r"^(?:答えは|結論は)", "", text)
    return _strip_predicate_end(text)


def _template(question: str, subject: str) -> str:
    if subject not in question:
        raise ValueError("question does not contain inferred subject")
    return question.replace(subject, _SUBJECT_SLOT, 1)


class SparseRelationalPlanBank:
    def __init__(
        self,
        *,
        max_plans: int = 10_000,
        max_schemas: int = 100_000,
        max_candidates: int = 32,
        max_hops: int = 5,
        max_frontier: int = 64,
    ) -> None:
        self.max_plans = max_plans
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.max_hops = max_hops
        self.max_frontier = max_frontier
        self.plans: list[RelationalPlan] = []
        self.schemas: list[RelationalSchema] = []
        self.plan_ids: dict[tuple[str, ...], int] = {}
        self.schema_ids: dict[str, int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.outgoing: dict[str, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.max_subject_chars = 0
        self.last_subject_substring_checks = 0
        self.last_plan_candidates = 0
        self.last_schema_reads = 0
        self.last_edge_reads = 0
        self.last_nodes_activated = 0
        self.last_search_states = 0
        self.last_conflict = False

    def register_episode(self, episode_id: int, episode: Episode) -> None:
        if (
            episode.claim_subject is None
            or episode.claim_relation is None
            or episode.claim_value is None
        ):
            return
        self.outgoing[episode.claim_subject][episode.claim_relation].append(episode_id)
        self.max_subject_chars = max(self.max_subject_chars, len(episode.claim_subject))

    def rebuild_index(self, episodic: SparseEpisodicRevisionMemory) -> None:
        self.outgoing.clear()
        self.max_subject_chars = 0
        for episode_id, episode in enumerate(episodic.episodes):
            self.register_episode(episode_id, episode)

    def _candidate_subjects(self, question: str) -> list[str]:
        self.last_subject_substring_checks = 0
        maximum = min(self.max_subject_chars, len(question))
        for size in range(maximum, 1, -1):
            matches: list[str] = []
            for start in range(len(question) - size + 1):
                self.last_subject_substring_checks += 1
                piece = question[start : start + size]
                if piece in self.outgoing:
                    matches.append(piece)
            if matches:
                return sorted(set(matches), key=lambda value: (-len(value), value))[:8]
        return []

    def _relation_values(
        self,
        subject: str,
        relation: str,
        episodic: SparseEpisodicRevisionMemory,
    ) -> tuple[RelationalEvidence, ...]:
        grouped: dict[str, list[tuple[int, Episode]]] = defaultdict(list)
        for episode_id in self.outgoing.get(subject, {}).get(relation, ()):
            self.last_edge_reads += 1
            episode = episodic.episodes[episode_id]
            if episode.active and episode.claim_value is not None:
                grouped[episode.claim_value].append((episode_id, episode))
        output: list[RelationalEvidence] = []
        for value, rows in grouped.items():
            sources: list[str] = []
            ids: list[int] = []
            for episode_id, episode in rows:
                ids.append(episode_id)
                if episode.source_id not in sources:
                    sources.append(episode.source_id)
            output.append(
                RelationalEvidence(
                    subject,
                    relation,
                    value,
                    tuple(sources),
                    tuple(ids),
                )
            )
        return tuple(output)

    def _paths_to_target(
        self,
        subject: str,
        target: str,
        episodic: SparseEpisodicRevisionMemory,
    ) -> set[tuple[str, ...]]:
        paths: set[tuple[str, ...]] = set()
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(subject, ())])
        seen: set[tuple[str, tuple[str, ...]]] = {(subject, ())}
        states = 0
        while queue:
            node, relations = queue.popleft()
            states += 1
            if states > 4_096:
                break
            if len(relations) >= self.max_hops:
                continue
            relation_names = sorted(self.outgoing.get(node, {}))[:32]
            for relation in relation_names:
                values = self._relation_values(node, relation, episodic)
                for evidence in values[: self.max_frontier]:
                    next_relations = relations + (relation,)
                    if evidence.value == target:
                        paths.add(next_relations)
                    state = (evidence.value, next_relations)
                    if state not in seen and len(seen) < 4_096:
                        seen.add(state)
                        queue.append(state)
        self.last_search_states = max(self.last_search_states, states)
        return paths

    def _intern_plan(self, plan: RelationalPlan) -> int:
        existing = self.plan_ids.get(plan.relations)
        if existing is not None:
            return existing
        if len(self.plans) >= self.max_plans:
            raise MemoryError("relational plan capacity reached")
        plan_id = len(self.plans)
        self.plans.append(plan)
        self.plan_ids[plan.relations] = plan_id
        return plan_id

    def _register_schema(self, template: str, plan_id: int, support: int) -> int:
        existing = self.schema_ids.get(template)
        if existing is not None:
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("relational schema capacity reached")
        schema_id = len(self.schemas)
        self.schemas.append(RelationalSchema(template, plan_id, support))
        self.schema_ids[template] = schema_id
        literal = template.replace(_SUBJECT_SLOT, "")
        for anchor in _literal_anchors(literal) or {literal}:
            self.postings[anchor].add(schema_id)
        return schema_id

    def teach(
        self,
        examples: Iterable[tuple[str, str]],
        *,
        episodic: SparseEpisodicRevisionMemory,
    ) -> RelationalPlan:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two demonstrations are required")
        common_paths: set[tuple[str, ...]] | None = None
        parsed: list[tuple[str, str]] = []
        self.last_search_states = 0
        self.last_edge_reads = 0
        for question, answer in rows:
            subjects = self._candidate_subjects(question)
            if not subjects:
                raise ValueError("could not infer a known subject from question")
            subject = max(subjects, key=len)
            paths = self._paths_to_target(subject, _answer_value(answer), episodic)
            if not paths:
                raise ValueError("no local relation path reaches demonstrated answer")
            common_paths = paths if common_paths is None else common_paths & paths
            parsed.append((question, subject))
        if not common_paths:
            raise ValueError("demonstrations share no reusable relation sequence")
        relations = min(common_paths, key=lambda path: (len(path), path))
        plan = RelationalPlan(relations, len(parsed))
        plan_id = self._intern_plan(plan)
        for question, subject in parsed:
            self._register_schema(_template(question, subject), plan_id, len(parsed))
        return self.plans[plan_id]

    def link_surface(self, question: str, subject: str, plan: RelationalPlan) -> int:
        plan_id = self._intern_plan(plan)
        return self._register_schema(_template(question, subject), plan_id, plan.support)

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
        self.last_plan_candidates = min(len(votes), self.max_candidates)
        return [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]

    def solve(
        self,
        question: str,
        *,
        episodic: SparseEpisodicRevisionMemory,
    ) -> ReplyResult | None:
        self.last_edge_reads = 0
        self.last_nodes_activated = 0
        self.last_conflict = False
        for schema_id in self._candidate_schemas(question):
            schema = self.schemas[schema_id]
            match = _template_regex(schema.template).match(question)
            if match is None:
                continue
            subject = match.group(1)
            plan = self.plans[schema.plan_id]
            frontier: dict[str, tuple[str, ...]] = {subject: ()}
            evidence_sources: list[str] = []
            evidence_text: list[str] = []
            for relation in plan.relations:
                next_frontier: dict[str, tuple[str, ...]] = {}
                for node in tuple(frontier)[: self.max_frontier]:
                    values = self._relation_values(node, relation, episodic)
                    distinct = {item.value for item in values}
                    if len(distinct) > 1:
                        self.last_conflict = True
                        return ReplyResult(
                            text=(
                                f"{node}の{relation}に矛盾する有効な資料があるため、"
                                "推論を確定できません。"
                            ),
                            confidence=0.25,
                            mechanism="relational-plan-evidence-conflict",
                            candidates_inspected=self.last_plan_candidates,
                            active_bits=self.last_nodes_activated,
                            estimated_sparse_operations=(
                                self.last_schema_reads + self.last_edge_reads
                            ),
                        )
                    for item in values:
                        next_frontier[item.value] = frontier[node] + (relation,)
                        evidence_text.append(f"{node} --{relation}→ {item.value}")
                        for source in item.source_ids:
                            if source not in evidence_sources:
                                evidence_sources.append(source)
                self.last_nodes_activated += len(frontier) + len(next_frontier)
                if not next_frontier or len(next_frontier) > self.max_frontier:
                    frontier = {}
                    break
                frontier = next_frontier
            if not frontier:
                continue
            endpoints = sorted(frontier)
            if len(endpoints) != 1:
                return ReplyResult(
                    text=(
                        f"{subject}からプランを実行すると候補が"
                        f"{len(endpoints)}件残るため、答えを一意にできません。"
                    ),
                    confidence=0.30,
                    mechanism="relational-plan-ambiguous-endpoint",
                    candidates_inspected=self.last_plan_candidates,
                    active_bits=self.last_nodes_activated,
                    estimated_sparse_operations=(
                        self.last_schema_reads + self.last_edge_reads
                        + self.last_nodes_activated
                    ),
                )
            answer = endpoints[0]
            operations = (
                self.last_schema_reads
                + self.last_edge_reads
                + self.last_nodes_activated
                + len(plan.relations)
            )
            return ReplyResult(
                text=(
                    f"{answer}です。"
                    f"{subject}から関係プラン"
                    f"{' → '.join(plan.relations)}を実行しました。"
                    f"根拠経路: {'；'.join(evidence_text)}。"
                    f"出典: {'、'.join(f'［{source}］' for source in evidence_sources)}"
                ),
                confidence=min(0.98, 0.78 + 0.04 * math.log2(plan.support + 1)),
                mechanism="learned-relational-path-plan",
                candidates_inspected=self.last_plan_candidates,
                active_bits=self.last_nodes_activated,
                estimated_sparse_operations=operations,
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-relational-plans-hs12",
            "max_plans": self.max_plans,
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "max_hops": self.max_hops,
            "max_frontier": self.max_frontier,
            "plans": [asdict(plan) for plan in self.plans],
            "schemas": [asdict(schema) for schema in self.schemas],
            "outgoing": {
                subject: {relation: ids for relation, ids in relations.items()}
                for subject, relations in self.outgoing.items()
            },
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
    def from_bytes(cls, data: bytes) -> "SparseRelationalPlanBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(
            max_plans=int(payload["max_plans"]),
            max_schemas=int(payload["max_schemas"]),
            max_candidates=int(payload["max_candidates"]),
            max_hops=int(payload["max_hops"]),
            max_frontier=int(payload["max_frontier"]),
        )
        for row in payload["plans"]:
            bank._intern_plan(
                RelationalPlan(tuple(row["relations"]), int(row["support"]))
            )
        for row in payload["schemas"]:
            bank._register_schema(
                str(row["template"]), int(row["plan_id"]), int(row["support"])
            )
        for subject, relations in payload["outgoing"].items():
            for relation, ids in relations.items():
                bank.outgoing[str(subject)][str(relation)].extend(
                    int(item) for item in ids
                )
            bank.max_subject_chars = max(bank.max_subject_chars, len(str(subject)))
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "plans": len(self.plans),
            "schemas": len(self.schemas),
            "indexed_subjects": len(self.outgoing),
            "indexed_relation_slots": sum(
                len(relations) for relations in self.outgoing.values()
            ),
            "serialized_bytes": len(self.to_bytes()),
            "last_subject_substring_checks": self.last_subject_substring_checks,
            "last_plan_candidates": self.last_plan_candidates,
            "last_schema_reads": self.last_schema_reads,
            "last_edge_reads": self.last_edge_reads,
            "last_nodes_activated": self.last_nodes_activated,
            "last_search_states": self.last_search_states,
            "last_conflict": self.last_conflict,
            "global_node_scan_used": False,
            "global_episode_scan_used": False,
            "global_relation_scan_used": False,
            "global_plan_scan_used": False,
        }


class SPARCHS12Model:
    def __init__(self, base: SPARCHS11ModelV2 | None = None) -> None:
        self.base = base or SPARCHS11ModelV2()
        self.relational_plans = SparseRelationalPlanBank()
        self.relational_plans.rebuild_index(self.episodic)

    @property
    def episodic(self) -> SparseEpisodicRevisionMemory:
        return self.base.episodic

    def ingest_fact(
        self, text: str, *, source_id: str, revision: bool = False
    ) -> tuple[int, ...]:
        inserted = self.base.ingest_fact(text, source_id=source_id, revision=revision)
        for episode_id in inserted:
            self.relational_plans.register_episode(
                episode_id, self.episodic.episodes[episode_id]
            )
        return inserted

    def teach_relational_plan(
        self, examples: Iterable[tuple[str, str]]
    ) -> RelationalPlan:
        return self.relational_plans.teach(examples, episodic=self.episodic)

    def link_relational_surface(
        self, question: str, subject: str, plan: RelationalPlan
    ) -> int:
        return self.relational_plans.link_surface(question, subject, plan)

    def reply(self, text: str) -> ReplyResult:
        relational = self.relational_plans.solve(text, episodic=self.episodic)
        if relational is not None:
            return relational
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs12",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "relational": base64.b85encode(self.relational_plans.to_bytes()).decode(
                "ascii"
            ),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS12Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS11ModelV2.from_bytes(base64.b85decode(payload["base"])))
        model.relational_plans = SparseRelationalPlanBank.from_bytes(
            base64.b85decode(payload["relational"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS12Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS12",
            "base": self.base.report(),
            "relational_plans": self.relational_plans.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
