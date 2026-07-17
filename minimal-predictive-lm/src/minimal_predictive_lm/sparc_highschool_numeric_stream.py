from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import combinations
import re
from typing import Iterable

from .sparc_highschool_document_stream import IndependentDocumentLearner
from .sparc_highschool_general import World, _clean


_INTEGER = re.compile(r"-?\d+")


@dataclass(frozen=True)
class NumericStreamResult:
    documents: int
    candidate_templates: int
    retained_templates: int
    relation_clusters: int
    values: int
    rejected_isolated_templates: int


class IndependentNumericDocumentLearner(IndependentDocumentLearner):
    """Induce numeric observation schemas from a flat independent document stream."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.numeric_document_values: dict[tuple[str, str], int] = {}
        self.numeric_document_sources: dict[tuple[str, str, int], set[str]] = {}
        self.numeric_document_patterns: dict[str, set[str]] = {}
        self.next_numeric_document_relation = 0
        self.independent_numeric_documents = 0
        self.numeric_candidate_templates = 0
        self.numeric_retained_templates = 0
        self.numeric_relation_clusters = 0
        self.numeric_rejected_isolated_templates = 0
        self.numeric_ambiguous_observations = 0

    @staticmethod
    def _normalize_number(text: str) -> tuple[str, int] | None:
        clean = _clean(text)
        matches = _INTEGER.findall(clean)
        if len(matches) != 1:
            return None
        value = int(matches[0])
        return _INTEGER.sub("<N>", clean, count=1), value

    @staticmethod
    def _derive_numeric_template(left: str, right: str) -> str | None:
        normalized_left = IndependentNumericDocumentLearner._normalize_number(left)
        normalized_right = IndependentNumericDocumentLearner._normalize_number(right)
        if normalized_left is None or normalized_right is None:
            return None
        left_text, _ = normalized_left
        right_text, _ = normalized_right
        if left_text == right_text:
            return None
        parts: list[str] = []
        variables = 0
        literal_chars = 0
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=left_text, b=right_text, autojunk=False).get_opcodes():
            if tag == "equal":
                literal = left_text[i1:i2]
                if literal:
                    parts.append(literal)
                    literal_chars += len(literal.replace("<N>", ""))
                continue
            left_value = left_text[i1:i2]
            right_value = right_text[j1:j2]
            if not left_value or not right_value or len(left_value) > 32 or len(right_value) > 32:
                return None
            parts.append("<S>")
            variables += 1
        pattern = "".join(parts)
        if variables != 1 or pattern.count("<S>") != 1 or pattern.count("<N>") != 1 or literal_chars < 3:
            return None
        return pattern

    @staticmethod
    def _specificity(pattern: str) -> int:
        return len(pattern.replace("<S>", "").replace("<N>", ""))

    @classmethod
    def _extract_numeric(cls, pattern: str, documents: tuple[tuple[str, str], ...]):
        matcher = cls._compile_numeric_observation(pattern)
        extracted: dict[int, tuple[str, int]] = {}
        for index, (text, _source) in enumerate(documents):
            match = matcher.fullmatch(_clean(text))
            if not match:
                continue
            subject = match.group("S")
            value = int(match.group("N"))
            if not subject or len(subject) > 32 or subject.isdigit():
                continue
            extracted[index] = (subject, value)
        return extracted

    def learn_independent_numeric_documents(
        self,
        records: Iterable[tuple[str, str]],
        *,
        min_support: int = 4,
        min_overlap: int = 2,
    ) -> NumericStreamResult:
        documents = tuple(records)
        candidate_patterns: set[str] = set()
        for (left, _), (right, _) in combinations(documents, 2):
            pattern = self._derive_numeric_template(left, right)
            if pattern is not None:
                candidate_patterns.add(pattern)
        self.numeric_candidate_templates += len(candidate_patterns)

        extracted = {}
        for pattern in candidate_patterns:
            rows = self._extract_numeric(pattern, documents)
            if len(set(rows.values())) >= min_support:
                extracted[pattern] = rows

        deduplicated: dict[frozenset[tuple[int, tuple[str, int]]], str] = {}
        for pattern, rows in extracted.items():
            key = frozenset(rows.items())
            current = deduplicated.get(key)
            if current is None or (self._specificity(pattern), pattern) > (self._specificity(current), current):
                deduplicated[key] = pattern
        extracted = {pattern: self._extract_numeric(pattern, documents) for pattern in deduplicated.values()}
        patterns = sorted(extracted)
        self.numeric_retained_templates += len(patterns)

        find, union = self._union_find(patterns)
        edges: dict[str, list[str]] = {pattern: [] for pattern in patterns}
        for index, left in enumerate(patterns):
            left_pairs = set(extracted[left].values())
            for right in patterns[index + 1:]:
                overlap = len(left_pairs & set(extracted[right].values()))
                if overlap < min_overlap:
                    continue
                edges[left].append(right)
                edges[right].append(left)
                union(left, right)

        components: dict[str, list[str]] = {}
        for pattern in patterns:
            components.setdefault(find(pattern), []).append(pattern)
        accepted = [sorted(component) for component in components.values() if len(component) >= 2]
        rejected = sum(len(component) for component in components.values() if len(component) < 2)
        self.numeric_rejected_isolated_templates += rejected

        metadata: dict[str, str] = {}
        for component in accepted:
            relation = f"NDR{self.next_numeric_document_relation}"
            self.next_numeric_document_relation += 1
            component_patterns = set(component)
            self.numeric_observation_patterns[relation] = component_patterns
            self.numeric_document_patterns[relation] = component_patterns
            for pattern in component:
                metadata[pattern] = relation

        new_values: dict[tuple[str, str], int] = {}
        for document_index, (_text, source) in enumerate(documents):
            candidates: list[tuple[int, str, str, int, str]] = []
            for pattern, relation in metadata.items():
                row = extracted[pattern].get(document_index)
                if row is None:
                    continue
                subject, value = row
                candidates.append((self._specificity(pattern), relation, subject, value, pattern))
            candidates.sort(key=lambda row: (-row[0], row[1], row[2], row[3], row[4]))
            if not candidates:
                continue
            top = candidates[0]
            if len(candidates) > 1 and candidates[1][0] == top[0] and candidates[1][1:4] != top[1:4]:
                self.numeric_ambiguous_observations += 1
                continue
            key = (top[2], top[1])
            existing = new_values.get(key)
            if existing is not None and existing != top[3]:
                self.numeric_ambiguous_observations += 1
                continue
            new_values[key] = top[3]
            self.numeric_document_sources.setdefault((top[2], top[1], top[3]), set()).add(source)

        self.numeric_document_values.update(new_values)
        self.independent_numeric_documents += len(documents)
        self.numeric_relation_clusters += len(accepted)
        self.text_observation_groups += len(accepted)
        return NumericStreamResult(
            documents=len(documents),
            candidate_templates=len(candidate_patterns),
            retained_templates=len(patterns),
            relation_clusters=len(accepted),
            values=len(new_values),
            rejected_isolated_templates=rejected,
        )

    def learned_numeric_world(self) -> World:
        return World.from_parts(numbers=self.numeric_document_values)

    def report(self):
        result = super().report()
        result.update({
            "independent_numeric_documents": self.independent_numeric_documents,
            "numeric_candidate_templates": self.numeric_candidate_templates,
            "numeric_retained_templates": self.numeric_retained_templates,
            "numeric_relation_clusters": self.numeric_relation_clusters,
            "numeric_rejected_isolated_templates": self.numeric_rejected_isolated_templates,
            "numeric_ambiguous_observations": self.numeric_ambiguous_observations,
            "numeric_document_values": len(self.numeric_document_values),
            "numeric_document_sources": sum(len(sources) for sources in self.numeric_document_sources.values()),
            "numeric_paraphrase_group_labels_supplied": False,
            "numeric_relation_labels_supplied": False,
            "numeric_entity_spans_supplied": False,
        })
        return result
