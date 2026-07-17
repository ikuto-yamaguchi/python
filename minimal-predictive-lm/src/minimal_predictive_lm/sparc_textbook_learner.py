from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import pickle
import re
import zlib
from typing import Mapping

_QUOTE_RE = re.compile(r"「([^」]{1,48})」")
_PUNCT_RE = re.compile(r"[\s、。！？；：・（）()「」『』【】\[\]]+")


def _clean(text: str) -> str:
    return _PUNCT_RE.sub("", text)


def _ngrams(text: str, lo: int = 2, hi: int = 5) -> Counter[str]:
    text = _clean(text)
    return Counter(
        text[index : index + width]
        for width in range(lo, hi + 1)
        for index in range(max(0, len(text) - width + 1))
    )


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


@dataclass(frozen=True)
class TextAnswer:
    value: str | None
    confidence: float
    sources: tuple[str, ...]
    proof: tuple[tuple[str, str, str], ...]
    mechanism: str


class SparseTextbookLearner:
    """Sparse relation and rule induction from Japanese text.

    Relation names and the relation inventory are not supplied. A paragraph that
    repeats one fact in multiple phrasings connects those surfaces into one
    latent relation. Redundant direct conclusions then supervise compact
    two-edge graph rules.
    """

    def __init__(
        self,
        *,
        relation_threshold: float = 0.75,
        relation_margin: float = 0.08,
        query_threshold: float = 0.65,
        query_margin: float = 0.08,
        max_candidates: int = 16,
        max_depth: int = 4,
    ) -> None:
        self.relation_threshold = relation_threshold
        self.relation_margin = relation_margin
        self.query_threshold = query_threshold
        self.query_margin = query_margin
        self.max_candidates = max_candidates
        self.max_depth = max_depth
        self.entities: set[str] = set()
        self.pattern_to_relation: dict[str, str] = {}
        self.relation_patterns: dict[str, set[str]] = {}
        self.next_relation = 0
        self.facts: dict[tuple[str, str, str], set[str]] = {}
        self.out_index: dict[str, dict[str, set[str]]] = {}
        self.query_patterns: dict[tuple[str, str, str], set[str]] = {}
        self.rules: dict[tuple[str, str], str] = {}
        self.rule_stats: dict[tuple[str, str, str], tuple[int, float]] = {}
        self.last_candidates = 0
        self.last_feature_reads = 0
        self.training_paragraphs = 0
        self.qa_demonstrations = 0

    def _extract_entities(self, text: str) -> list[str]:
        quoted = _QUOTE_RE.findall(text)
        if quoted:
            self.entities.update(quoted)
            unique: list[str] = []
            for item in quoted:
                if item not in unique:
                    unique.append(item)
            return unique

        occupied: list[tuple[int, int]] = []
        found: list[tuple[int, str]] = []
        for entity in sorted(self.entities, key=lambda value: (-len(value), value)):
            start = text.find(entity)
            if start < 0:
                continue
            end = start + len(entity)
            if any(not (end <= left or start >= right) for left, right in occupied):
                continue
            occupied.append((start, end))
            found.append((start, entity))
        return [entity for _, entity in sorted(found)]

    @staticmethod
    def _abstract(text: str, first: str, second: str | None = None) -> str:
        replacements = [(first, "<A>")]
        if second is not None:
            replacements.append((second, "<B>"))
        for value, marker in sorted(replacements, key=lambda row: -len(row[0])):
            text = text.replace(f"「{value}」", marker)
            text = text.replace(value, marker)
        return _clean(text)

    def _new_relation(self) -> str:
        relation = f"R{self.next_relation}"
        self.next_relation += 1
        self.relation_patterns[relation] = set()
        return relation

    def _rebuild_index(self) -> None:
        index: dict[str, dict[str, set[str]]] = {}
        for subject, relation, obj in self.facts:
            index.setdefault(subject, {}).setdefault(relation, set()).add(obj)
        self.out_index = index

    def _merge_relations(self, keep: str, drop: str) -> str:
        if keep == drop:
            return keep
        self.relation_patterns.setdefault(keep, set()).update(
            self.relation_patterns.pop(drop, set())
        )
        for pattern, relation in list(self.pattern_to_relation.items()):
            if relation == drop:
                self.pattern_to_relation[pattern] = keep

        merged_facts: dict[tuple[str, str, str], set[str]] = {}
        for (subject, relation, obj), sources in self.facts.items():
            relation = keep if relation == drop else relation
            merged_facts.setdefault((subject, relation, obj), set()).update(sources)
        self.facts = merged_facts

        merged_queries: dict[tuple[str, str, str], set[str]] = {}
        for (relation, direction, mode), patterns in self.query_patterns.items():
            relation = keep if relation == drop else relation
            merged_queries.setdefault((relation, direction, mode), set()).update(patterns)
        self.query_patterns = merged_queries

        merged_rules: dict[tuple[str, str], str] = {}
        for (left, right), head in self.rules.items():
            left = keep if left == drop else left
            right = keep if right == drop else right
            head = keep if head == drop else head
            merged_rules[(left, right)] = head
        self.rules = merged_rules
        self._rebuild_index()
        return keep

    def learn_fact_paragraph(self, text: str, source_id: str) -> str:
        sentences = [
            row.strip()
            for row in re.split(r"(?<=[。！？])", text)
            if row.strip()
        ] or [text.strip()]
        first_entities = self._extract_entities(sentences[0])
        if len(first_entities) < 2:
            raise ValueError("paragraph must introduce two quoted entities")
        first, second = first_entities[:2]

        patterns: list[str] = []
        for sentence in sentences:
            self._extract_entities(sentence)
            if first in sentence and second in sentence:
                patterns.append(self._abstract(sentence, first, second))
        if not patterns:
            raise ValueError("paragraph yielded no relation surfaces")

        existing = sorted(
            {
                self.pattern_to_relation[pattern]
                for pattern in patterns
                if pattern in self.pattern_to_relation
            }
        )
        relation = existing[0] if existing else self._new_relation()
        for other in existing[1:]:
            relation = self._merge_relations(relation, other)

        for pattern in patterns:
            self.pattern_to_relation[pattern] = relation
            self.relation_patterns.setdefault(relation, set()).add(pattern)
        self.facts.setdefault((first, relation, second), set()).add(source_id)
        self.entities.update((first, second))
        self.training_paragraphs += 1
        self._rebuild_index()
        return relation

    def _rank_relation(self, pattern: str) -> list[tuple[float, str]]:
        query = _ngrams(pattern)
        rows: list[tuple[float, str]] = []
        reads = 0
        for relation, patterns in self.relation_patterns.items():
            best = 0.0
            for stored in patterns:
                vector = _ngrams(stored)
                reads += min(len(query), len(vector))
                best = max(best, _cosine(query, vector))
            rows.append((best, relation))
        rows.sort(key=lambda row: (-row[0], row[1]))
        self.last_candidates = min(len(rows), self.max_candidates)
        self.last_feature_reads = reads
        return rows[: self.max_candidates]

    def read_sentence(self, text: str, source_id: str) -> tuple[bool, str]:
        entities = self._extract_entities(text)
        if len(entities) < 2:
            return False, "abstain-missing-entities"

        choices: list[tuple[float, str, str, str]] = []
        for first, second in ((entities[0], entities[1]), (entities[1], entities[0])):
            pattern = self._abstract(text, first, second)
            exact = self.pattern_to_relation.get(pattern)
            if exact is not None:
                choices.append((1.0, exact, first, second))
                continue
            ranked = self._rank_relation(pattern)
            if ranked:
                choices.append((ranked[0][0], ranked[0][1], first, second))

        choices.sort(key=lambda row: (-row[0], row[1], row[2], row[3]))
        if not choices or choices[0][0] < self.relation_threshold:
            return False, "abstain-unknown-relation"
        if (
            len(choices) > 1
            and choices[0][0] - choices[1][0] < self.relation_margin
            and choices[0][1:] != choices[1][1:]
        ):
            return False, "abstain-ambiguous-relation"

        _, relation, first, second = choices[0]
        self.facts.setdefault((first, relation, second), set()).add(source_id)
        self.entities.update((first, second))
        self._rebuild_index()
        return True, relation

    def _direct_proofs(
        self,
        subject: str,
        relation: str,
    ) -> list[tuple[str, tuple[str, ...], tuple[tuple[str, str, str], ...]]]:
        rows = []
        for obj in self.out_index.get(subject, {}).get(relation, set()):
            sources = tuple(sorted(self.facts[(subject, relation, obj)]))
            rows.append((obj, sources, ((subject, relation, obj),)))
        return rows

    def _prove(
        self,
        subject: str,
        target_relation: str,
        depth: int | None = None,
        visited: set[tuple[str, str, int]] | None = None,
    ) -> list[tuple[str, tuple[str, ...], tuple[tuple[str, str, str], ...]]]:
        depth = self.max_depth if depth is None else depth
        visited = set() if visited is None else visited
        state = (subject, target_relation, depth)
        if state in visited:
            return []
        visited.add(state)

        rows = self._direct_proofs(subject, target_relation)
        if depth <= 0:
            return rows

        for (left_relation, right_relation), head in self.rules.items():
            if head != target_relation:
                continue
            for middle in self.out_index.get(subject, {}).get(left_relation, set()):
                left_sources = tuple(
                    sorted(self.facts[(subject, left_relation, middle)])
                )
                for obj, right_sources, right_proof in self._prove(
                    middle,
                    right_relation,
                    depth - 1,
                    visited.copy(),
                ):
                    rows.append(
                        (
                            obj,
                            tuple(sorted(set(left_sources) | set(right_sources))),
                            ((subject, left_relation, middle),) + right_proof,
                        )
                    )

        unique: dict[
            tuple[str, int],
            tuple[str, tuple[str, ...], tuple[tuple[str, str, str], ...]],
        ] = {}
        for row in rows:
            unique.setdefault((row[0], len(row[2])), row)
        return list(unique.values())

    def learn_question(
        self,
        question: str,
        answer: str,
        *,
        mode: str = "direct",
    ) -> bool:
        entities = self._extract_entities(question)
        self.entities.add(answer)
        if not entities:
            return False
        subject = entities[0]
        candidates: list[tuple[str, str, str]] = []

        if mode == "direct":
            for subject0, relation, obj in self.facts:
                if subject0 == subject and obj == answer:
                    candidates.append((relation, "forward", "direct"))
                elif obj == subject and subject0 == answer:
                    candidates.append((relation, "reverse", "direct"))
        elif mode == "closure":
            for relation in self.relation_patterns:
                if any(
                    obj == answer and len(proof) > 1
                    for obj, _, proof in self._prove(subject, relation)
                ):
                    candidates.append((relation, "forward", "closure"))
        else:
            raise ValueError(f"unknown question mode: {mode}")

        candidates = sorted(set(candidates))
        if len(candidates) != 1:
            return False
        pattern = self._abstract(question, subject)
        self.query_patterns.setdefault(candidates[0], set()).add(pattern)
        self.qa_demonstrations += 1
        return True

    def induce_rules(
        self,
        *,
        min_support: int = 5,
        min_precision: float = 0.95,
        preserve_existing: bool = True,
    ) -> dict[tuple[str, str], str]:
        triples = list(self.facts)
        outgoing: dict[str, list[tuple[str, str]]] = {}
        for subject, relation, obj in triples:
            outgoing.setdefault(subject, []).append((relation, obj))

        body_counts: Counter[tuple[str, str]] = Counter()
        head_counts: Counter[tuple[str, str, str]] = Counter()
        for first, left_relation, middle in triples:
            for right_relation, last in outgoing.get(middle, []):
                body_counts[(left_relation, right_relation)] += 1
                for head_relation, candidate in outgoing.get(first, []):
                    if candidate == last:
                        head_counts[(left_relation, right_relation, head_relation)] += 1

        proposed: dict[tuple[str, str], tuple[str, int, float]] = {}
        for (left, right, head), support in head_counts.items():
            total = body_counts[(left, right)]
            precision = support / total if total else 0.0
            if support < min_support or precision < min_precision:
                continue
            current = proposed.get((left, right))
            if current is None or (support, precision, head) > (
                current[1],
                current[2],
                current[0],
            ):
                proposed[(left, right)] = (head, support, precision)

        if not preserve_existing:
            self.rules.clear()
        for body, (head, support, precision) in proposed.items():
            self.rules[body] = head
            self.rule_stats[(body[0], body[1], head)] = (support, precision)
        return dict(self.rules)

    def ask(self, question: str) -> TextAnswer:
        entities = self._extract_entities(question)
        if not entities:
            return TextAnswer(None, 0.0, (), (), "abstain-missing-subject")
        subject = entities[0]
        pattern = self._abstract(question, subject)
        query = _ngrams(pattern)

        scores: list[tuple[float, tuple[str, str, str]]] = []
        reads = 0
        for key, patterns in self.query_patterns.items():
            best = 0.0
            for stored in patterns:
                vector = _ngrams(stored)
                reads += min(len(query), len(vector))
                best = max(best, _cosine(query, vector))
            scores.append((best, key))
        scores.sort(key=lambda row: (-row[0], row[1]))
        self.last_candidates = min(len(scores), self.max_candidates)
        self.last_feature_reads = reads

        if not scores or scores[0][0] < self.query_threshold:
            return TextAnswer(None, 0.0, (), (), "abstain-unknown-question")
        if (
            len(scores) > 1
            and scores[0][0] - scores[1][0] < self.query_margin
            and scores[0][1] != scores[1][1]
        ):
            return TextAnswer(
                None,
                scores[0][0],
                (),
                (),
                "abstain-ambiguous-question",
            )

        confidence, (relation, direction, mode) = scores[0]
        if direction == "reverse":
            proofs = [
                (
                    candidate,
                    tuple(sorted(sources)),
                    ((candidate, rel, obj),),
                )
                for (candidate, rel, obj), sources in self.facts.items()
                if rel == relation and obj == subject
            ]
        elif mode == "direct":
            proofs = self._direct_proofs(subject, relation)
        else:
            proofs = self._prove(subject, relation)
            if proofs:
                longest = max(len(proof) for _, _, proof in proofs)
                proofs = [row for row in proofs if len(row[2]) == longest]

        by_value: dict[
            str,
            tuple[str, tuple[str, ...], tuple[tuple[str, str, str], ...]],
        ] = {}
        for row in proofs:
            by_value.setdefault(row[0], row)
        proofs = list(by_value.values())
        if len(proofs) != 1:
            return TextAnswer(
                None,
                confidence,
                (),
                (),
                "abstain-answer-cardinality",
            )

        value, sources, proof = proofs[0]
        return TextAnswer(
            value,
            confidence,
            sources,
            proof,
            "latent-relation-proof",
        )

    def explain(self, question: str) -> str:
        result = self.ask(question)
        if result.value is None:
            return "根拠を一意に特定できないため、回答を控えます。"
        source_text = "、".join(result.sources)
        return f"答えは「{result.value}」です。根拠資料は {source_text} です。"

    def report(self) -> dict[str, object]:
        return {
            "latent_relations": len(self.relation_patterns),
            "relation_surfaces": sum(
                len(patterns) for patterns in self.relation_patterns.values()
            ),
            "facts": len(self.facts),
            "rules": len(self.rules),
            "query_schemas": len(self.query_patterns),
            "entities": len(self.entities),
            "training_paragraphs": self.training_paragraphs,
            "qa_demonstrations": self.qa_demonstrations,
            "operation_names_supplied": False,
            "relation_inventory_supplied": False,
            "whitespace_tokenizer_used": False,
            "morphological_dictionary_used": False,
            "serialized_bytes": len(self.to_bytes()),
        }

    def to_bytes(self) -> bytes:
        return zlib.compress(pickle.dumps(self, protocol=5), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseTextbookLearner":
        model = pickle.loads(zlib.decompress(data))
        if not isinstance(model, cls):
            raise TypeError("invalid sparse textbook model")
        return model
