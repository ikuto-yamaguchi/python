from __future__ import annotations

import base64
import json
import re
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .sparc_hs2 import SPARCHS2Model
from .sparc_reasoning import RelationFact, ReasoningResult


def _surface(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    text = re.sub(r"\s+", "", text)
    return text.strip("。！")


@dataclass(frozen=True)
class LearnedSchema:
    kind: str
    relation: str
    polarity: bool
    mode: str
    template: str
    slot_order: tuple[str, ...]
    support: int = 1


@dataclass(frozen=True)
class SchemaMatch:
    schema_id: int
    kind: str
    relation: str
    polarity: bool
    mode: str
    subject: str
    object: str | None
    confidence: float
    candidates_inspected: int


def _induce_template(text: str, subject: str, object_: str | None) -> tuple[str, tuple[str, ...]]:
    text = _surface(text)
    subject = _surface(subject)
    spans: list[tuple[int, int, str]] = []
    start = text.find(subject)
    if start < 0:
        raise ValueError("subject does not occur in example")
    spans.append((start, start + len(subject), "S"))
    if object_ is not None:
        object_ = _surface(object_)
        object_start = text.find(object_)
        if object_start < 0:
            raise ValueError("object does not occur in example")
        spans.append((object_start, object_start + len(object_), "O"))
    spans.sort()
    for left, right in zip(spans, spans[1:]):
        if left[1] > right[0]:
            raise ValueError("subject and object spans overlap")
    chunks: list[str] = []
    slot_order: list[str] = []
    cursor = 0
    for begin, end, slot in spans:
        chunks.append(text[cursor:begin])
        chunks.append("{" + slot + "}")
        slot_order.append(slot)
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks), tuple(slot_order)


def _literal_segments(template: str) -> tuple[str, ...]:
    return tuple(piece for piece in re.split(r"\{[SO]\}", template) if piece)


def _keys_for_literal(literal: str) -> set[str]:
    keys: set[str] = set()
    for size in (4, 3, 2):
        if len(literal) >= size:
            keys.update(literal[i : i + size] for i in range(len(literal) - size + 1))
    if literal:
        keys.add(literal)
    return keys


def _compile(schema: LearnedSchema) -> re.Pattern[str]:
    parts = re.split(r"(\{S\}|\{O\})", schema.template)
    regex: list[str] = ["^"]
    for part in parts:
        if part == "{S}":
            regex.append("(.+?)")
        elif part == "{O}":
            regex.append("(.+?)")
        elif part:
            regex.append(re.escape(part))
    regex.append("$")
    return re.compile("".join(regex))


class SparseSchemaInducer:
    """Few-shot surface-schema memory with sparse anchor routing."""

    def __init__(self, max_schemas: int = 200_000, max_candidates: int = 64) -> None:
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.schemas: list[LearnedSchema] = []
        self.schema_key_to_id: dict[tuple[object, ...], int] = {}
        self.postings: dict[tuple[str, str], set[int]] = defaultdict(set)
        self._compiled: dict[int, re.Pattern[str]] = {}
        self.last_candidates_inspected = 0
        self.last_anchor_reads = 0

    def teach(
        self,
        *,
        kind: str,
        sentence: str,
        subject: str,
        relation: str,
        object_: str | None = None,
        polarity: bool = True,
        mode: str = "yesno",
    ) -> int:
        template, slots = _induce_template(sentence, subject, object_)
        key = (kind, relation, polarity, mode, template, slots)
        existing = self.schema_key_to_id.get(key)
        if existing is not None:
            previous = self.schemas[existing]
            self.schemas[existing] = LearnedSchema(**{**asdict(previous), "support": previous.support + 1})
            return existing
        if len(self.schemas) >= self.max_schemas:
            raise MemoryError("schema capacity reached")
        schema_id = len(self.schemas)
        schema = LearnedSchema(kind, relation, polarity, mode, template, slots)
        self.schemas.append(schema)
        self.schema_key_to_id[key] = schema_id
        keys: set[str] = set()
        for literal in _literal_segments(template):
            keys.update(_keys_for_literal(literal))
        if not keys:
            keys.add(template)
        for anchor in keys:
            self.postings[(kind, anchor)].add(schema_id)
        return schema_id

    def _candidate_ids(self, text: str, kind: str) -> list[int]:
        text = _surface(text)
        votes: Counter[int] = Counter()
        reads = 0
        routed = sorted(
            ((len(self.postings.get((kind, key), ())), key) for key in _keys_for_literal(text) if self.postings.get((kind, key))),
            key=lambda row: (row[0], -len(row[1]), row[1]),
        )
        used_routes = 0
        for posting_size, key in routed:
            if votes and posting_size > self.max_candidates * 4:
                break
            for schema_id in self.postings[(kind, key)]:
                votes[schema_id] += len(key) * len(key) / max(1, posting_size)
                reads += 1
            used_routes += 1
            if used_routes >= 8 or (len(votes) >= self.max_candidates and posting_size > 1):
                break
        self.last_anchor_reads = reads
        if not votes:
            self.last_candidates_inspected = 0
            return []
        candidates = [schema_id for schema_id, _score in votes.most_common(self.max_candidates)]
        self.last_candidates_inspected = len(candidates)
        return candidates

    def match(self, text: str, kind: str) -> SchemaMatch | None:
        text = _surface(text)
        candidates = self._candidate_ids(text, kind)
        best: tuple[float, SchemaMatch] | None = None
        inspected = 0
        for schema_id in candidates:
            schema = self.schemas[schema_id]
            pattern = self._compiled.setdefault(schema_id, _compile(schema))
            matched = pattern.fullmatch(text)
            inspected += 1
            if not matched:
                continue
            values = matched.groups()
            slots = dict(zip(schema.slot_order, values))
            literal_chars = sum(len(piece) for piece in _literal_segments(schema.template))
            confidence = min(1.0, 0.55 + literal_chars / max(1, len(text)) * 0.35 + min(schema.support, 5) * 0.02)
            result = SchemaMatch(
                schema_id=schema_id,
                kind=kind,
                relation=schema.relation,
                polarity=schema.polarity,
                mode=schema.mode,
                subject=slots["S"],
                object=slots.get("O"),
                confidence=confidence,
                candidates_inspected=inspected,
            )
            score = confidence + schema.support * 0.001
            if best is None or score > best[0]:
                best = (score, result)
        self.last_candidates_inspected = inspected
        return None if best is None else best[1]

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-schema-hs3",
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "schemas": [asdict(schema) for schema in self.schemas],
        }
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseSchemaInducer":
        payload = json.loads(zlib.decompress(data))
        model = cls(int(payload["max_schemas"]), int(payload["max_candidates"]))
        for row in payload["schemas"]:
            model.teach(
                kind=row["kind"],
                sentence=row["template"].replace("{S}", "主体").replace("{O}", "対象"),
                subject="主体",
                object_="対象" if "O" in row["slot_order"] else None,
                relation=row["relation"],
                polarity=bool(row["polarity"]),
                mode=row["mode"],
            )
            schema_id = len(model.schemas) - 1
            schema = model.schemas[schema_id]
            model.schemas[schema_id] = LearnedSchema(**{**asdict(schema), "support": int(row["support"])})
        return model

    def report(self) -> dict[str, int | bool]:
        return {
            "schemas": len(self.schemas),
            "anchor_posting_edges": sum(len(ids) for ids in self.postings.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates_inspected": self.last_candidates_inspected,
            "last_anchor_reads": self.last_anchor_reads,
            "global_schema_scan_used": False,
        }


class CompositionalJapaneseRenderer:
    def __init__(self) -> None:
        self.positive: dict[str, str] = {}
        self.negative: dict[str, str] = {}
        self.evidence: dict[str, str] = {}

    def teach(self, relation: str, *, positive: str, negative: str | None = None, evidence: str | None = None) -> None:
        self.positive[relation] = positive
        if negative is not None:
            self.negative[relation] = negative
        if evidence is not None:
            self.evidence[relation] = evidence

    @staticmethod
    def _fill(template: str, subject: str, object_: str) -> str:
        return template.replace("{S}", subject).replace("{O}", object_)

    def render(
        self,
        subject: str,
        relation: str,
        object_: str,
        *,
        positive: bool,
        path: tuple[RelationFact, ...] = (),
    ) -> str:
        template = (
            self.positive.get(relation, "{S}と{O}の関係を確認できました。")
            if positive
            else self.negative.get(relation, "{S}と{O}の関係は確認できません。")
        )
        answer = self._fill(template, subject, object_)
        if positive and len(path) > 1:
            evidence_template = self.evidence.get(relation, "{S}→{O}")
            steps = [self._fill(evidence_template, fact.subject, fact.object) for fact in path]
            answer += " 根拠は" + "、".join(steps) + "です。"
        return answer

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {"positive": self.positive, "negative": self.negative, "evidence": self.evidence}

    @classmethod
    def from_dict(cls, row: dict[str, dict[str, str]]) -> "CompositionalJapaneseRenderer":
        renderer = cls()
        renderer.positive.update(row.get("positive", {}))
        renderer.negative.update(row.get("negative", {}))
        renderer.evidence.update(row.get("evidence", {}))
        return renderer


class SPARCHS3Model:
    """HS2 reasoning plus learned surface schemas and compositional answers."""

    def __init__(self, base: SPARCHS2Model | None = None) -> None:
        self.base = base or SPARCHS2Model()
        self.schemas = SparseSchemaInducer()
        self.renderer = CompositionalJapaneseRenderer()

    def teach_statement(
        self,
        sentence: str,
        subject: str,
        relation: str,
        object_: str,
        *,
        polarity: bool = True,
    ) -> int:
        return self.schemas.teach(
            kind="statement",
            sentence=sentence,
            subject=subject,
            relation=relation,
            object_=object_,
            polarity=polarity,
            mode="learn",
        )

    def teach_query(
        self,
        sentence: str,
        subject: str,
        relation: str,
        object_: str | None,
        *,
        mode: str = "yesno",
    ) -> int:
        return self.schemas.teach(
            kind="query",
            sentence=sentence,
            subject=subject,
            relation=relation,
            object_=object_,
            mode=mode,
        )

    def learn(self, text: str) -> str:
        matched = self.schemas.match(text, "statement")
        if matched is None or matched.object is None:
            return self.base.learn(text)
        self.base.reasoning.add_fact(
            RelationFact(matched.subject, matched.relation, matched.object, matched.polarity, matched.confidence)
        )
        return f"学習済みスキーマ{matched.schema_id}で関係を覚えました。"

    def _answer_schema_query(self, matched: SchemaMatch) -> ReasoningResult | None:
        if matched.mode == "lookup":
            source = self.base.reasoning.entities.get(matched.subject)
            if source is None:
                return None
            targets = self.base.reasoning.outgoing.get((source, matched.relation, True), Counter())
            if not targets:
                return None
            target, _count = targets.most_common(1)[0]
            object_ = self.base.reasoning.labels[target]
            text = self.renderer.render(matched.subject, matched.relation, object_, positive=True)
            return ReasoningResult(text, matched.confidence, "learned-schema-lookup", (RelationFact(matched.subject, matched.relation, object_),), 2, len(targets), False)
        if matched.object is None:
            return None
        found, path, nodes, edges, bounded = self.base.reasoning._search(
            matched.subject, matched.relation, matched.object
        )
        if found:
            text = self.renderer.render(
                matched.subject, matched.relation, matched.object, positive=True, path=path
            )
            return ReasoningResult(
                text,
                min(0.99, matched.confidence + 0.08),
                "learned-schema-compositional-reasoning",
                path,
                nodes,
                edges,
                bounded,
            )
        source = self.base.reasoning.entities.get(matched.subject)
        target = self.base.reasoning.entities.get(matched.object)
        if source is not None and target is not None and self.base.reasoning._direct_negative(source, matched.relation, target):
            text = self.renderer.render(matched.subject, matched.relation, matched.object, positive=False)
            fact = RelationFact(matched.subject, matched.relation, matched.object, False)
            return ReasoningResult(text, 0.98, "learned-schema-negative", (fact,), 2, 1, False)
        return None

    def reply(self, text: str):
        query = self.schemas.match(text, "query")
        if query is not None:
            result = self._answer_schema_query(query)
            if result is not None:
                return result
        statement = self.schemas.match(text, "statement")
        if statement is not None and statement.object is not None:
            self.base.reasoning.add_fact(
                RelationFact(statement.subject, statement.relation, statement.object, statement.polarity, statement.confidence)
            )
            return ReasoningResult(
                f"分かりました。{statement.subject}と{statement.object}の関係を覚えました。",
                statement.confidence,
                "learned-surface-schema",
                (RelationFact(statement.subject, statement.relation, statement.object, statement.polarity),),
                2,
                1,
                False,
            )
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs3",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "schemas": base64.b85encode(self.schemas.to_bytes()).decode("ascii"),
            "renderer": self.renderer.to_dict(),
        }
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS3Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS2Model.from_bytes(base64.b85decode(payload["base"])))
        model.schemas = SparseSchemaInducer.from_bytes(base64.b85decode(payload["schemas"]))
        model.renderer = CompositionalJapaneseRenderer.from_dict(payload["renderer"])
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS3Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "base": self.base.report(),
            "schemas": self.schemas.report(),
            "combined_serialized_bytes": len(self.to_bytes()),
            "whole_response_retrieval_required_for_schema_answers": False,
            "compositional_renderer": True,
        }
