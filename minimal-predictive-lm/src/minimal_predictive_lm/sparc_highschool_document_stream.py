from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import combinations
import re
from typing import Iterable

from .sparc_highschool_general import Edit, Program, World, _clean
from .sparc_highschool_text_observation import TextObservationLearner


_DOC_SLOT = re.compile(r"<X(\d+)>")


@dataclass(frozen=True)
class DocumentStreamResult:
    documents: int
    candidate_templates: int
    retained_templates: int
    relation_clusters: int
    facts: int
    rejected_isolated_templates: int


class IndependentDocumentLearner(TextObservationLearner):
    """Induce opaque relation schemas from a flat, ungrouped document stream.

    No paraphrase bundle, relation label, entity span, task name, or internal world is
    supplied. Candidate two-slot frames are proposed from repeated alignment across
    independent sentences. Frames become one relation only when their extracted
    entity pairs agree across documents (possibly in reversed textual order).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_facts: set[tuple[str, str, str]] = set()
        self.document_sources: dict[tuple[str, str, str], set[str]] = {}
        self.document_patterns: dict[str, set[str]] = {}
        self.next_document_relation = 0
        self.independent_documents = 0
        self.document_candidate_templates = 0
        self.document_retained_templates = 0
        self.document_relation_clusters = 0
        self.document_rejected_isolated_templates = 0

    @staticmethod
    def _derive_template(left: str, right: str) -> str | None:
        left = _clean(left)
        right = _clean(right)
        if not left or not right or left == right:
            return None
        parts: list[str] = []
        variables = 0
        literal_chars = 0
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=left, b=right, autojunk=False).get_opcodes():
            if tag == "equal":
                literal = left[i1:i2]
                if literal:
                    parts.append(literal)
                    literal_chars += len(literal)
                continue
            left_value = left[i1:i2]
            right_value = right[j1:j2]
            if not left_value or not right_value:
                return None
            if len(left_value) > 32 or len(right_value) > 32:
                return None
            parts.append(f"<X{variables}>")
            variables += 1
        if variables != 2 or literal_chars < 3:
            return None
        return "".join(parts)

    @staticmethod
    def _compile_template(pattern: str) -> re.Pattern[str]:
        output = ""
        seen: set[int] = set()
        for part in re.split(r"(<X\d+>)", pattern):
            match = _DOC_SLOT.fullmatch(part)
            if not match:
                output += re.escape(part)
                continue
            index = int(match.group(1))
            if index in seen:
                output += rf"(?P=X{index})"
            else:
                output += rf"(?P<X{index}>.+?)"
                seen.add(index)
        return re.compile("^" + output + "$")

    @staticmethod
    def _swap_slots(pattern: str) -> str:
        return pattern.replace("<X0>", "<TMP>").replace("<X1>", "<X0>").replace("<TMP>", "<X1>")

    @staticmethod
    def _specificity(pattern: str) -> int:
        return len(_DOC_SLOT.sub("", pattern))

    @classmethod
    def _extract(cls, pattern: str, documents: tuple[tuple[str, str], ...]) -> dict[int, tuple[str, str]]:
        matcher = cls._compile_template(pattern)
        extracted: dict[int, tuple[str, str]] = {}
        for index, (text, _source) in enumerate(documents):
            match = matcher.fullmatch(_clean(text))
            if not match:
                continue
            left = match.group("X0")
            right = match.group("X1")
            if (
                not left
                or not right
                or left == right
                or len(left) > 32
                or len(right) > 32
                or left.isdigit()
                or right.isdigit()
            ):
                continue
            extracted[index] = (left, right)
        return extracted

    @staticmethod
    def _union_find(items: list[str]):
        parent = {item: item for item in items}

        def find(item: str) -> str:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        return parent, find, union

    def learn_independent_documents(
        self,
        records: Iterable[tuple[str, str]],
        *,
        min_support: int = 3,
        min_overlap: int = 2,
    ) -> DocumentStreamResult:
        documents = tuple(records)
        if len(documents) < min_support * 2:
            raise ValueError("independent document induction requires a small corpus")

        candidate_patterns: set[str] = set()
        for (left, _), (right, _) in combinations(documents, 2):
            pattern = self._derive_template(left, right)
            if pattern is not None:
                candidate_patterns.add(pattern)
        self.document_candidate_templates += len(candidate_patterns)

        extracted: dict[str, dict[int, tuple[str, str]]] = {}
        for pattern in candidate_patterns:
            rows = self._extract(pattern, documents)
            if len(set(rows.values())) >= min_support:
                extracted[pattern] = rows

        # Pairwise alignment can produce several equivalent frames. Keep the most
        # specific frame for an identical document->binding mapping.
        deduplicated: dict[frozenset[tuple[int, tuple[str, str]]], str] = {}
        for pattern, rows in extracted.items():
            key = frozenset(rows.items())
            current = deduplicated.get(key)
            if current is None or (self._specificity(pattern), pattern) > (self._specificity(current), current):
                deduplicated[key] = pattern
        extracted = {pattern: self._extract(pattern, documents) for pattern in deduplicated.values()}
        patterns = sorted(extracted)
        self.document_retained_templates += len(patterns)

        parent, find, union = self._union_find(patterns)
        edges: dict[str, list[tuple[str, int]]] = {pattern: [] for pattern in patterns}
        for index, left in enumerate(patterns):
            left_pairs = set(extracted[left].values())
            for right in patterns[index + 1:]:
                right_pairs = set(extracted[right].values())
                direct = len(left_pairs & right_pairs)
                reversed_overlap = len(left_pairs & {(obj, subject) for subject, obj in right_pairs})
                if max(direct, reversed_overlap) < min_overlap or direct == reversed_overlap:
                    continue
                sign = 1 if direct > reversed_overlap else -1
                edges[left].append((right, sign))
                edges[right].append((left, sign))
                union(left, right)

        components: dict[str, list[str]] = {}
        for pattern in patterns:
            components.setdefault(find(pattern), []).append(pattern)

        accepted_components = [sorted(component) for component in components.values() if len(component) >= 2]
        self.document_rejected_isolated_templates += sum(len(component) for component in components.values() if len(component) < 2)

        all_new_facts: set[tuple[str, str, str]] = set()
        for component in accepted_components:
            orientation: dict[str, int] = {component[0]: 1}
            queue = [component[0]]
            while queue:
                current = queue.pop()
                for neighbor, sign in edges[current]:
                    if neighbor not in component:
                        continue
                    proposed = orientation[current] * sign
                    if neighbor not in orientation:
                        orientation[neighbor] = proposed
                        queue.append(neighbor)
                    elif orientation[neighbor] != proposed:
                        raise ValueError("inconsistent document-frame orientation")

            relation = f"DR{self.next_document_relation}"
            self.next_document_relation += 1
            canonical_patterns: set[str] = set()
            facts: set[tuple[str, str, str]] = set()
            for pattern in component:
                sign = orientation.get(pattern, 1)
                canonical_patterns.add(pattern if sign == 1 else self._swap_slots(pattern))
                for document_index, pair in extracted[pattern].items():
                    subject, obj = pair if sign == 1 else (pair[1], pair[0])
                    fact = (subject, relation, obj)
                    facts.add(fact)
                    self.document_sources.setdefault(fact, set()).add(documents[document_index][1])

            edit = Edit("add_fact", relation, 0, 1)
            program_id = f"P{self.next_program}"
            self.next_program += 1
            self.programs[program_id] = Program(program_id, self._signature((edit,)), (edit,), canonical_patterns)
            self.fact_program_ids.add(program_id)
            self.document_patterns[relation] = canonical_patterns
            all_new_facts.update(facts)

        self.document_facts.update(all_new_facts)
        self.independent_documents += len(documents)
        self.document_relation_clusters += len(accepted_components)
        self.training_episodes += len(accepted_components)
        return DocumentStreamResult(
            documents=len(documents),
            candidate_templates=len(candidate_patterns),
            retained_templates=len(patterns),
            relation_clusters=len(accepted_components),
            facts=len(all_new_facts),
            rejected_isolated_templates=sum(len(component) for component in components.values() if len(component) < 2),
        )

    def learned_document_world(self) -> World:
        return World.from_parts(self.document_facts)

    def report(self):
        result = super().report()
        result.update({
            "independent_documents": self.independent_documents,
            "document_candidate_templates": self.document_candidate_templates,
            "document_retained_templates": self.document_retained_templates,
            "document_relation_clusters": self.document_relation_clusters,
            "document_rejected_isolated_templates": self.document_rejected_isolated_templates,
            "document_facts": len(self.document_facts),
            "document_sources": sum(len(sources) for sources in self.document_sources.values()),
            "paraphrase_group_labels_supplied": False,
            "entity_spans_supplied": False,
            "document_relation_labels_supplied": False,
        })
        return result
