from __future__ import annotations

import base64
import itertools
import json
import math
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .sparc_episodic import Episode, SparseEpisodicRevisionMemory, _anchors
from .sparc_language import ReplyResult
from .sparc_role_induction_v3 import SPARCHS10ModelV3
from .sparc_units import (
    Dim,
    Quantity,
    TypedExpression,
    UNIT_SPECS,
    _eval,
    _node_text,
    synthesize_typed_expression,
)
from .sparc_programs import _format_number, _literal_anchors

_SUBJECT_SLOT = "{SUBJECT}"
_UNIT_NAMES = sorted((key for key in UNIT_SPECS if key), key=len, reverse=True)
_QUANTITY_RE = re.compile(
    r"([-+]?\d+(?:\.\d+)?)\s*(" + "|".join(map(re.escape, _UNIT_NAMES)) + r")"
)


@dataclass(frozen=True)
class EvidenceQuantity:
    subject: str
    relation: str
    quantity: Quantity
    source_ids: tuple[str, ...]
    episode_ids: tuple[int, ...]


@dataclass(frozen=True)
class CrossDomainPlan:
    input_relations: tuple[str, ...]
    expression: TypedExpression
    output_symbol: str
    support: int


@dataclass(frozen=True)
class CrossDomainSchema:
    template: str
    plan_id: int
    support: int


def _parse_quantity(text: str) -> Quantity | None:
    compact = text.replace(" ", "")
    match = _QUANTITY_RE.search(compact)
    if match is None:
        return None
    value = float(match.group(1))
    symbol = match.group(2)
    prefix = compact[max(0, match.start() - 3) : match.start()]
    if prefix.endswith("時速") and symbol == "km":
        unit = UNIT_SPECS["km/h"]
    elif prefix.endswith("秒速") and symbol == "m":
        unit = UNIT_SPECS["m/s"]
    else:
        unit = UNIT_SPECS[symbol]
    return Quantity(value, unit, value * unit.scale)


def _template(question: str, subject: str) -> str:
    if subject not in question:
        raise ValueError("question does not contain inferred subject")
    return question.replace(subject, _SUBJECT_SLOT, 1)


def _template_regex(template: str) -> re.Pattern[str]:
    escaped = re.escape(template).replace(re.escape(_SUBJECT_SLOT), r"(.{1,80}?)")
    return re.compile(r"^" + escaped + r"$")


class SparseCrossDomainPlanBank:
    def __init__(
        self,
        *,
        max_plans: int = 10_000,
        max_schemas: int = 100_000,
        max_candidates: int = 32,
    ) -> None:
        self.max_plans = max_plans
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.plans: list[CrossDomainPlan] = []
        self.schemas: list[CrossDomainSchema] = []
        self.plan_ids: dict[str, int] = {}
        self.schema_ids: dict[str, int] = {}
        self.postings: dict[str, set[int]] = defaultdict(set)
        self.subject_relations: dict[str, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.subject_postings: dict[str, set[str]] = defaultdict(set)
        self.last_plan_candidates = 0
        self.last_anchor_reads = 0
        self.last_fact_reads = 0
        self.last_expression_cost = 0
        self.last_search_attempts = 0
        self.last_conflict = False

    def register_episode(self, episode_id: int, episode: Episode) -> None:
        if (
            episode.claim_subject is None
            or episode.claim_relation is None
            or episode.claim_value is None
            or _parse_quantity(episode.claim_value) is None
        ):
            return
        self.subject_relations[episode.claim_subject][episode.claim_relation].append(
            episode_id
        )
        for anchor in _anchors(episode.claim_subject):
            self.subject_postings[anchor].add(episode.claim_subject)

    def rebuild_fact_index(self, episodic: SparseEpisodicRevisionMemory) -> None:
        self.subject_relations.clear()
        self.subject_postings.clear()
        for episode_id, episode in enumerate(episodic.episodes):
            self.register_episode(episode_id, episode)

    def _candidate_subjects(self, question: str) -> list[str]:
        routes = sorted(
            (
                len(self.subject_postings.get(anchor, ())),
                -len(anchor),
                anchor,
            )
            for anchor in _anchors(question)
            if self.subject_postings.get(anchor)
        )
        votes: Counter[str] = Counter()
        reads = 0
        for posting_size, negative_length, anchor in routes[:8]:
            weight = (-negative_length) ** 2 / max(1, posting_size)
            for subject in self.subject_postings[anchor]:
                if subject in question:
                    votes[subject] += weight
                reads += 1
                if reads >= 128:
                    break
            if reads >= 128:
                break
        self.last_anchor_reads = reads
        return [subject for subject, _score in votes.most_common(8)]

    def _evidence_quantity(
        self,
        subject: str,
        relation: str,
        episodic: SparseEpisodicRevisionMemory,
    ) -> EvidenceQuantity | None:
        episode_ids = self.subject_relations.get(subject, {}).get(relation, ())
        active: list[tuple[int, Episode, Quantity]] = []
        for episode_id in episode_ids:
            self.last_fact_reads += 1
            episode = episodic.episodes[episode_id]
            if not episode.active or episode.claim_value is None:
                continue
            quantity = _parse_quantity(episode.claim_value)
            if quantity is not None:
                active.append((episode_id, episode, quantity))
        if not active:
            return None
        values = {
            (round(item[2].base_value, 10), item[2].unit.dimension) for item in active
        }
        if len(values) > 1:
            self.last_conflict = True
            return None
        latest = max(active, key=lambda row: row[1].timestamp)
        source_ids: list[str] = []
        ids: list[int] = []
        for episode_id, episode, _quantity in active:
            ids.append(episode_id)
            if episode.source_id not in source_ids:
                source_ids.append(episode.source_id)
        return EvidenceQuantity(
            subject,
            relation,
            latest[2],
            tuple(source_ids),
            tuple(ids),
        )

    def _available_relations(
        self,
        subject: str,
        episodic: SparseEpisodicRevisionMemory,
    ) -> dict[str, EvidenceQuantity]:
        output: dict[str, EvidenceQuantity] = {}
        for relation in self.subject_relations.get(subject, {}):
            evidence = self._evidence_quantity(subject, relation, episodic)
            if evidence is not None:
                output[relation] = evidence
        return output

    def _intern_plan(self, plan: CrossDomainPlan) -> int:
        key = json.dumps(
            [
                plan.input_relations,
                plan.expression.node,
                plan.expression.input_dimensions,
                plan.expression.output_dimension,
                plan.output_symbol,
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        existing = self.plan_ids.get(key)
        if existing is not None:
            return existing
        if len(self.plans) >= self.max_plans:
            raise MemoryError("cross-domain plan capacity reached")
        plan_id = len(self.plans)
        self.plans.append(plan)
        self.plan_ids[key] = plan_id
        return plan_id

    def _register_schema(self, template: str, plan_id: int, support: int) -> int:
        existing = self.schema_ids.get(template)
        if existing is not None:
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("cross-domain schema capacity reached")
        schema_id = len(self.schemas)
        self.schemas.append(CrossDomainSchema(template, plan_id, support))
        self.schema_ids[template] = schema_id
        literal = template.replace(_SUBJECT_SLOT, "")
        for anchor in _literal_anchors(literal) or {literal}:
            self.postings[anchor].add(schema_id)
        return schema_id

    def teach(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        episodic: SparseEpisodicRevisionMemory,
        max_relations: int = 3,
        max_cost: int = 9,
    ) -> CrossDomainPlan:
        rows = list(examples)
        if len(rows) < 2:
            raise ValueError("at least two examples are required")
        parsed: list[
            tuple[str, str, str | float | int, dict[str, EvidenceQuantity], Quantity]
        ] = []
        common_relations: set[str] | None = None
        for question, answer in rows:
            subjects = self._candidate_subjects(question)
            if not subjects:
                raise ValueError("could not infer a known subject from question")
            subject = max(subjects, key=len)
            available = self._available_relations(subject, episodic)
            answer_quantity = _parse_quantity(str(answer))
            if answer_quantity is None:
                raise ValueError("answer must include a supported unit")
            parsed.append((question, subject, answer, available, answer_quantity))
            relations = set(available)
            common_relations = relations if common_relations is None else common_relations & relations
        candidates = sorted(common_relations or ())[:8]
        if not candidates:
            raise ValueError("demonstrations share no typed evidence relations")

        best: tuple[float, tuple[str, ...], TypedExpression, str] | None = None
        self.last_search_attempts = 0
        for width in range(1, min(max_relations, len(candidates)) + 1):
            for relation_order in itertools.permutations(candidates, width):
                self.last_search_attempts += 1
                typed_rows: list[
                    tuple[tuple[float, ...], tuple[Dim, ...], float, Dim]
                ] = []
                output_symbol = parsed[0][4].unit.symbol
                compatible = True
                for _question, _subject, _answer, available, answer_quantity in parsed:
                    evidence = [available.get(relation) for relation in relation_order]
                    if any(item is None for item in evidence):
                        compatible = False
                        break
                    typed_rows.append(
                        (
                            tuple(item.quantity.base_value for item in evidence if item),
                            tuple(item.quantity.unit.dimension for item in evidence if item),
                            answer_quantity.base_value,
                            answer_quantity.unit.dimension,
                        )
                    )
                    if answer_quantity.unit.symbol != output_symbol:
                        compatible = False
                        break
                if not compatible:
                    continue
                try:
                    expression = synthesize_typed_expression(
                        typed_rows,
                        max_cost=max_cost,
                        max_states=20_000,
                        backward_budget=10_000,
                    )
                except (ValueError, RuntimeError):
                    continue
                score = expression.cost + 0.25 * len(relation_order)
                if best is None or score < best[0]:
                    best = (score, relation_order, expression, output_symbol)
            if best is not None:
                break
        if best is None:
            raise ValueError("no evidence-to-calculation plan matched demonstrations")
        _score, relation_order, expression, output_symbol = best
        plan = CrossDomainPlan(
            tuple(relation_order), expression, output_symbol, len(parsed)
        )
        plan_id = self._intern_plan(plan)
        for question, subject, _answer, _available, _answer_quantity in parsed:
            self._register_schema(_template(question, subject), plan_id, len(parsed))
        self.last_expression_cost = expression.cost
        return self.plans[plan_id]

    def link_surface(self, question: str, subject: str, plan: CrossDomainPlan) -> int:
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
        self.last_plan_candidates = min(len(votes), self.max_candidates)
        self.last_anchor_reads = reads
        return [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]

    def solve(
        self,
        question: str,
        *,
        episodic: SparseEpisodicRevisionMemory,
    ) -> ReplyResult | None:
        self.last_fact_reads = 0
        self.last_conflict = False
        for schema_id in self._candidate_schemas(question):
            schema = self.schemas[schema_id]
            match = _template_regex(schema.template).match(question)
            if match is None:
                continue
            subject = match.group(1)
            plan = self.plans[schema.plan_id]
            evidence: list[EvidenceQuantity] = []
            for relation in plan.input_relations:
                item = self._evidence_quantity(subject, relation, episodic)
                if item is None:
                    if self.last_conflict:
                        return ReplyResult(
                            text=(
                                f"{subject}の{relation}には矛盾する有効な資料があるため、"
                                "計算を確定できません。"
                            ),
                            confidence=0.25,
                            mechanism="cross-domain-evidence-conflict",
                            candidates_inspected=self.last_plan_candidates,
                            active_bits=0,
                            estimated_sparse_operations=(
                                self.last_anchor_reads + self.last_fact_reads
                            ),
                        )
                    break
                evidence.append(item)
            if len(evidence) != len(plan.input_relations):
                continue
            value_base = _eval(
                plan.expression.node,
                tuple(item.quantity.base_value for item in evidence),
            )
            output_unit = UNIT_SPECS[plan.output_symbol]
            value = value_base / output_unit.scale
            sources: list[str] = []
            for item in evidence:
                for source in item.source_ids:
                    if source not in sources:
                        sources.append(source)
            relation_text = "、".join(
                f"{item.relation}={_format_number(item.quantity.raw_value)}{item.quantity.unit.symbol}"
                for item in evidence
            )
            operations = (
                self.last_anchor_reads
                + self.last_fact_reads
                + self.last_plan_candidates
                + plan.expression.cost
            )
            self.last_expression_cost = plan.expression.cost
            return ReplyResult(
                text=(
                    f"{_format_number(value)}{plan.output_symbol}です。"
                    f"{subject}について{relation_text}を使い、"
                    f"式{_node_text(plan.expression.node)}で求めました。"
                    f"根拠: {'、'.join(f'［{source}］' for source in sources)}"
                ),
                confidence=min(0.98, 0.78 + 0.04 * math.log2(plan.support + 1)),
                mechanism="learned-cross-domain-plan",
                candidates_inspected=self.last_plan_candidates,
                active_bits=len(evidence),
                estimated_sparse_operations=operations,
            )
        return None

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-cross-domain-plans-hs11",
            "max_plans": self.max_plans,
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "plans": [
                {
                    "input_relations": plan.input_relations,
                    "expression": asdict(plan.expression),
                    "output_symbol": plan.output_symbol,
                    "support": plan.support,
                }
                for plan in self.plans
            ],
            "schemas": [asdict(schema) for schema in self.schemas],
            "subject_relations": {
                subject: {relation: ids for relation, ids in relations.items()}
                for subject, relations in self.subject_relations.items()
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
    def from_bytes(cls, data: bytes) -> "SparseCrossDomainPlanBank":
        payload = json.loads(zlib.decompress(data))
        bank = cls(
            max_plans=int(payload["max_plans"]),
            max_schemas=int(payload["max_schemas"]),
            max_candidates=int(payload["max_candidates"]),
        )

        def tuples(value):
            if isinstance(value, list):
                return tuple(tuples(item) for item in value)
            return value

        for row in payload["plans"]:
            expression_row = row["expression"]
            expression = TypedExpression(
                tuples(expression_row["node"]),
                int(expression_row["cost"]),
                tuples(expression_row["input_dimensions"]),
                tuples(expression_row["output_dimension"]),
                int(expression_row["semantic_states"]),
                int(expression_row["candidates_generated"]),
            )
            bank._intern_plan(
                CrossDomainPlan(
                    tuple(row["input_relations"]),
                    expression,
                    str(row["output_symbol"]),
                    int(row["support"]),
                )
            )
        for row in payload["schemas"]:
            bank._register_schema(
                str(row["template"]), int(row["plan_id"]), int(row["support"])
            )
        for subject, relations in payload["subject_relations"].items():
            for relation, ids in relations.items():
                bank.subject_relations[str(subject)][str(relation)].extend(
                    int(item) for item in ids
                )
            for anchor in _anchors(str(subject)):
                bank.subject_postings[anchor].add(str(subject))
        return bank

    def report(self) -> dict[str, int | bool]:
        return {
            "plans": len(self.plans),
            "schemas": len(self.schemas),
            "indexed_subjects": len(self.subject_relations),
            "indexed_relation_slots": sum(
                len(relations) for relations in self.subject_relations.values()
            ),
            "serialized_bytes": len(self.to_bytes()),
            "last_plan_candidates": self.last_plan_candidates,
            "last_anchor_reads": self.last_anchor_reads,
            "last_fact_reads": self.last_fact_reads,
            "last_expression_cost": self.last_expression_cost,
            "last_search_attempts": self.last_search_attempts,
            "last_conflict": self.last_conflict,
            "global_subject_scan_used": False,
            "global_episode_scan_used": False,
            "global_plan_scan_used": False,
        }


class SPARCHS11Model:
    def __init__(self, base: SPARCHS10ModelV3 | None = None) -> None:
        self.base = base or SPARCHS10ModelV3()
        self.plans = SparseCrossDomainPlanBank()

    @property
    def episodic(self) -> SparseEpisodicRevisionMemory:
        return self.base.base.base.episodic

    def ingest_fact(self, text: str, *, source_id: str, revision: bool = False) -> tuple[int, ...]:
        inserted = self.base.base.base.ingest(
            text, source_id=source_id, revision=revision
        )
        for episode_id in inserted:
            self.plans.register_episode(episode_id, self.episodic.episodes[episode_id])
        return inserted

    def teach_plan(
        self,
        examples: Iterable[tuple[str, str | float | int]],
        *,
        max_relations: int = 3,
        max_cost: int = 9,
    ) -> CrossDomainPlan:
        return self.plans.teach(
            examples,
            episodic=self.episodic,
            max_relations=max_relations,
            max_cost=max_cost,
        )

    def link_plan_surface(
        self, question: str, subject: str, plan: CrossDomainPlan
    ) -> int:
        return self.plans.link_surface(question, subject, plan)

    def reply(self, text: str) -> ReplyResult:
        planned = self.plans.solve(text, episodic=self.episodic)
        if planned is not None:
            return planned
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs11",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "plans": base64.b85encode(self.plans.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS11Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS10ModelV3.from_bytes(base64.b85decode(payload["base"])))
        model.plans = SparseCrossDomainPlanBank.from_bytes(
            base64.b85decode(payload["plans"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS11Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS11",
            "base": self.base.report(),
            "plans": self.plans.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
