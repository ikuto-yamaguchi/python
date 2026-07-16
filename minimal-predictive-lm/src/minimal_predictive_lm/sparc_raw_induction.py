from __future__ import annotations

import base64
import hashlib
import json
import re
import zlib
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .sparc_language import ReplyResult
from .sparc_reasoning import RelationFact, SparseRelationalCortex
from .sparc_schema import SPARCHS3Model


_MARKERS = tuple(
    sorted(
        {
            "に分類されます",
            "に分類される",
            "によって",
            "により",
            "につながります",
            "につながる",
            "ではありません",
            "ではない",
            "である",
            "です",
            "ます",
            "より",
            "から",
            "まで",
            "として",
            "について",
            "は",
            "が",
            "の",
            "を",
            "に",
            "で",
            "へ",
            "と",
            "も",
            "だ",
        },
        key=lambda value: (-len(value), value),
    )
)
_MARKER_RE = re.compile("(" + "|".join(re.escape(value) for value in _MARKERS) + ")")
_MARKER_SET = set(_MARKERS)


def _normalise(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    text = re.sub(r"\s+", "", text)
    return text.strip("。！")


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(piece for piece in _MARKER_RE.split(_normalise(text)) if piece)


def _latent_id(template: str) -> str:
    digest = hashlib.blake2b(template.encode("utf-8"), digest_size=8).hexdigest()
    return "latent:" + digest


@dataclass(frozen=True)
class RawRelationSchema:
    relation: str
    template: str
    slot_positions: tuple[int, int]
    support: int
    example_sentence: str
    example_subject: str
    example_object: str


@dataclass(frozen=True)
class RawMiningReport:
    sentences: int
    clusters: int
    schemas: int
    facts: int
    rejected_clusters: int


class LearnedRelationalCortex(SparseRelationalCortex):
    def __init__(self, profile: str = "ci") -> None:
        super().__init__(profile)
        self.learned_transitive: set[str] = set()

    def mark_transitive(self, relation: str) -> None:
        self.learned_transitive.add(relation)

    def _transitive(self, relation: str) -> bool:
        return relation in self.learned_transitive or super()._transitive(relation)


class RawPatternMiner:
    """Discover repeated two-slot relations from unlabeled Japanese sentences."""

    def __init__(self, min_support: int = 3, max_schemas: int = 100_000) -> None:
        self.min_support = min_support
        self.max_schemas = max_schemas
        self.schemas: list[RawRelationSchema] = []
        self.facts: list[RelationFact] = []
        self.report = RawMiningReport(0, 0, 0, 0, 0)

    def fit(self, sentences: Iterable[str]) -> "RawPatternMiner":
        rows = [(_normalise(sentence), _tokens(sentence)) for sentence in sentences]
        groups: dict[tuple[object, ...], list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
        for sentence, tokens in rows:
            marker_signature = tuple(
                (index, token)
                for index, token in enumerate(tokens)
                if token in _MARKER_SET
            )
            groups[(len(tokens), marker_signature)].append((sentence, tokens))

        self.schemas.clear()
        self.facts.clear()
        rejected = 0
        clusters = 0

        def emit(group: list[tuple[str, tuple[str, ...]]]) -> bool:
            nonlocal rejected, clusters
            if len(group) < self.min_support or len(self.schemas) >= self.max_schemas:
                return False
            clusters += 1
            width = len(group[0][1])
            columns = [
                set(tokens[index] for _sentence, tokens in group)
                for index in range(width)
            ]
            variable = tuple(index for index, values in enumerate(columns) if len(values) > 1)
            if len(variable) == 2:
                left, right = variable
                if any(
                    tokens[left] in _MARKER_SET or tokens[right] in _MARKER_SET
                    for _sentence, tokens in group
                ):
                    rejected += 1
                    return False
                template_tokens = list(group[0][1])
                template_tokens[left] = "{S}"
                template_tokens[right] = "{O}"
                template = "".join(template_tokens)
                relation = _latent_id(template)
                first_sentence, first_tokens = group[0]
                self.schemas.append(
                    RawRelationSchema(
                        relation=relation,
                        template=template,
                        slot_positions=(left, right),
                        support=len(group),
                        example_sentence=first_sentence,
                        example_subject=first_tokens[left],
                        example_object=first_tokens[right],
                    )
                )
                for _sentence, tokens in group:
                    self.facts.append(RelationFact(tokens[left], relation, tokens[right]))
                return True

            if len(variable) > 2:
                best: tuple[int, int, int, int] | None = None
                best_groups: dict[str, list[tuple[str, tuple[str, ...]]]] | None = None
                for position in variable:
                    if any(tokens[position] in _MARKER_SET for _sentence, tokens in group):
                        continue
                    buckets: dict[str, list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
                    for row in group:
                        buckets[row[1][position]].append(row)
                    supported = {
                        value: rows_for_value
                        for value, rows_for_value in buckets.items()
                        if len(rows_for_value) >= self.min_support
                    }
                    if not supported:
                        continue
                    coverage = sum(len(rows_for_value) for rows_for_value in supported.values())
                    largest = max(len(rows_for_value) for rows_for_value in supported.values())
                    score = (coverage, len(supported), -largest, -position)
                    if best is None or score > best:
                        best = score
                        best_groups = supported
                if best_groups is not None:
                    emitted = False
                    for subgroup in best_groups.values():
                        emitted = emit(subgroup) or emitted
                        if len(self.schemas) >= self.max_schemas:
                            break
                    return emitted

            rejected += 1
            return False

        for group in groups.values():
            emit(group)
            if len(self.schemas) >= self.max_schemas:
                break

        self.report = RawMiningReport(
            sentences=len(rows),
            clusters=clusters,
            schemas=len(self.schemas),
            facts=len(self.facts),
            rejected_clusters=rejected,
        )
        return self


class RawCurriculumModel:
    """HS3 model whose schemas and facts are induced from raw sentence groups."""

    def __init__(
        self,
        *,
        reasoning_profile: str = "ci",
        min_support: int = 3,
        max_schemas: int = 100_000,
    ) -> None:
        self.model = SPARCHS3Model()
        self.model.base.reasoning = LearnedRelationalCortex(reasoning_profile)
        self.miner = RawPatternMiner(min_support=min_support, max_schemas=max_schemas)
        self.qa_alignments = 0

    @property
    def cortex(self) -> LearnedRelationalCortex:
        assert isinstance(self.model.base.reasoning, LearnedRelationalCortex)
        return self.model.base.reasoning

    def fit_raw(self, sentences: Iterable[str]) -> "RawCurriculumModel":
        self.miner.fit(sentences)
        for schema in self.miner.schemas:
            self.model.teach_statement(
                schema.example_sentence,
                schema.example_subject,
                schema.relation,
                schema.example_object,
            )
        for fact in self.miner.facts:
            self.cortex.add_fact(fact)
            self.cortex.add_fact(RelationFact(fact.object, fact.relation + "~inverse", fact.subject))
        self._learn_transitivity_from_closure()
        return self

    def _learn_transitivity_from_closure(self) -> None:
        by_relation: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for fact in self.miner.facts:
            by_relation[fact.relation].add((fact.subject, fact.object))
        for relation, edges in by_relation.items():
            outgoing: dict[str, set[str]] = defaultdict(set)
            for source, target in edges:
                outgoing[source].add(target)
            chains = 0
            closures = 0
            for source, middles in outgoing.items():
                for middle in middles:
                    for target in outgoing.get(middle, ()):
                        chains += 1
                        if (source, target) in edges:
                            closures += 1
            if chains >= 2 and closures / chains >= 0.5:
                self.cortex.mark_transitive(relation)

    def _entities_in(self, text: str) -> list[str]:
        text = _normalise(text)
        matches = [
            (text.find(label), -len(label), label)
            for label in self.cortex.labels
            if label and label in text
        ]
        matches.sort()
        selected: list[tuple[int, int, str]] = []
        for start, neg_length, label in matches:
            end = start - neg_length
            if any(
                not (end <= other_start or start >= other_end)
                for other_start, other_end, _label in selected
            ):
                continue
            selected.append((start, end, label))
        selected.sort(key=lambda row: row[0])
        return [label for _start, _end, label in selected[:4]]

    def align_qa(self, question: str, answer: str) -> bool:
        question = _normalise(question)
        answer = _normalise(answer)
        entities = self._entities_in(question)
        answer_id = self.cortex.entities.get(answer)
        if answer not in {"はい", "いいえ"} and answer_id is not None:
            for key in entities:
                key_id = self.cortex.entities[key]
                for (source, relation, polarity), targets in self.cortex.outgoing.items():
                    if not polarity or source != key_id or answer_id not in targets:
                        continue
                    self.model.teach_query(question, key, relation, None, mode="lookup")
                    self.model.renderer.teach(relation, positive="{O}です。")
                    self.qa_alignments += 1
                    return True
        if answer == "はい" and len(entities) >= 2:
            for subject in entities:
                for object_ in entities:
                    if subject == object_:
                        continue
                    relations = {
                        relation
                        for source, relation, polarity in self.cortex.outgoing
                        if polarity and source == self.cortex.entities[subject]
                    }
                    for relation in relations:
                        found, _path, _nodes, _edges, _bounded = self.cortex._search(
                            subject, relation, object_
                        )
                        if found:
                            self.model.teach_query(
                                question, subject, relation, object_, mode="yesno"
                            )
                            self.model.renderer.teach(
                                relation,
                                positive="{S}は{O}の関係にあります。",
                                negative="{S}は{O}の関係にはありません。",
                                evidence="{S}→{O}",
                            )
                            self.qa_alignments += 1
                            return True
        return False

    def reply(self, text: str):
        normalised = _normalise(text)
        if text.strip().endswith(("?", "？")):
            query = self.model.schemas.match(normalised, "query")
            if query is not None:
                result = self.model._answer_schema_query(query)
                if result is not None:
                    return result
                return ReplyResult(
                    text="まだその答えを学習できていません。教えてください。",
                    confidence=0.0,
                    mechanism="calibrated-unknown",
                    candidates_inspected=self.model.schemas.last_candidates_inspected,
                    active_bits=0,
                    estimated_sparse_operations=self.model.schemas.last_anchor_reads,
                )
            reasoning = self.cortex.answer(normalised)
            if reasoning is not None:
                return reasoning
            return self.model.base.language.reply(normalised)
        return self.model.reply(normalised)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs4-raw",
            "model": base64.b85encode(self.model.to_bytes()).decode("ascii"),
            "transitive": sorted(self.cortex.learned_transitive),
            "miner_report": asdict(self.miner.report),
            "qa_alignments": self.qa_alignments,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "RawCurriculumModel":
        payload = json.loads(zlib.decompress(data))
        result = cls()
        result.model = SPARCHS3Model.from_bytes(base64.b85decode(payload["model"]))
        old = result.model.base.reasoning
        cortex = LearnedRelationalCortex(old.profile.name)
        cortex.__dict__.update(old.__dict__)
        cortex.learned_transitive = set(payload["transitive"])
        result.model.base.reasoning = cortex
        result.miner.report = RawMiningReport(**payload["miner_report"])
        result.qa_alignments = int(payload["qa_alignments"])
        return result

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "RawCurriculumModel":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "raw_mining": asdict(self.miner.report),
            "qa_alignments": self.qa_alignments,
            "learned_transitive_relations": len(self.cortex.learned_transitive),
            "model": self.model.report(),
            "serialized_bytes": len(self.to_bytes()),
            "structured_subject_object_labels_required_for_raw_fit": False,
            "raw_global_sentence_scan_at_query": False,
        }
