from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Iterable, Sequence
import zlib


TOKEN_RE = re.compile(r"[一-龯々〆ヵヶぁ-んァ-ヶーA-Za-z0-9]+")


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    text: str
    source: str = ""


@dataclass(frozen=True)
class MemoryPrediction:
    index: int
    scores: tuple[float, ...]
    retrieved_documents: tuple[str, ...]
    active_postings: int
    confidence: float


def _stable_hash(namespace: str, text: str, buckets: int) -> int:
    digest = hashlib.blake2b((namespace + text).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % buckets


def _normalize(text: str) -> str:
    return "".join(TOKEN_RE.findall(text.lower()))


def _features(text: str, *, buckets: int) -> Counter[int]:
    normalized = _normalize(text)
    values: Counter[int] = Counter()
    words = TOKEN_RE.findall(text.lower())
    for word in words:
        if len(word) >= 2:
            values[_stable_hash("W:", word, buckets)] += 3
    for width, weight in ((2, 1), (3, 2), (4, 2)):
        for index in range(max(0, len(normalized) - width + 1)):
            token = normalized[index : index + width]
            values[_stable_hash(f"C{width}:", token, buckets)] += weight
    return values


def _unit(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    scale = math.sqrt(variance) or 1.0
    return [(value - mean) / scale for value in values]


def _occurrences(text: str, needle: str) -> tuple[int, ...]:
    if not needle:
        return ()
    return tuple(
        index
        for index in range(max(0, len(text) - len(needle) + 1))
        if text.startswith(needle, index)
    )


def _relation_proximity(stem: str, option: str, document: str) -> float:
    """Score option proximity to longest relation spans shared by question and evidence."""

    normalized_stem = _normalize(stem)
    normalized_option = _normalize(option)
    normalized_document = _normalize(document)
    option_positions = _occurrences(normalized_document, normalized_option)
    if not option_positions:
        return 0.0

    candidates: set[str] = set()
    for width in range(6, 1, -1):
        for index in range(max(0, len(normalized_stem) - width + 1)):
            cue = normalized_stem[index : index + width]
            if cue in normalized_option or cue not in normalized_document:
                continue
            candidates.add(cue)
    selected: list[str] = []
    for cue in sorted(candidates, key=lambda value: (-len(value), value)):
        if any(cue in stronger for stronger in selected):
            continue
        selected.append(cue)
        if len(selected) >= 12:
            break

    score = 0.0
    for cue in selected:
        cue_positions = _occurrences(normalized_document, cue)
        if not cue_positions:
            continue
        distance = min(
            abs(
                (option_position + len(normalized_option) / 2.0)
                - (cue_position + len(cue) / 2.0)
            )
            for option_position in option_positions
            for cue_position in cue_positions
        )
        score += len(cue) ** 2 / (1.0 + distance)
    return score


class QuantizedCurriculumMemory:
    """Paged, quantized, task-name-free curriculum retrieval for weak phones."""

    FORMAT = "quantized-curriculum-memory-002"

    def __init__(
        self,
        *,
        buckets: int,
        titles: tuple[str, ...],
        snippets: tuple[str, ...],
        doc_features: tuple[tuple[int, ...], ...],
        postings: dict[int, tuple[tuple[int, int], ...]],
        doc_norms: tuple[float, ...],
        idf: dict[int, int],
        max_active_postings: int = 8192,
    ) -> None:
        if not (len(titles) == len(snippets) == len(doc_features) == len(doc_norms)):
            raise ValueError("curriculum-memory document arrays disagree")
        self.buckets = buckets
        self.titles = titles
        self.snippets = snippets
        self.doc_features = doc_features
        self._doc_feature_sets = tuple(frozenset(row) for row in doc_features)
        self.postings = postings
        self.doc_norms = doc_norms
        self.idf = idf
        self.max_active_postings = max_active_postings

    @classmethod
    def build(
        cls,
        documents: Iterable[KnowledgeDocument],
        *,
        buckets: int = 262_144,
        max_features_per_document: int = 384,
        max_postings_per_feature: int = 96,
        max_snippet_chars: int = 420,
    ) -> "QuantizedCurriculumMemory":
        rows = [row for row in documents if row.text.strip()]
        if not rows:
            raise ValueError("curriculum memory needs documents")
        encoded: list[Counter[int]] = []
        document_frequency: Counter[int] = Counter()
        for row in rows:
            raw = _features(row.title + "\n" + row.text, buckets=buckets)
            selected = Counter(dict(raw.most_common(max_features_per_document)))
            encoded.append(selected)
            document_frequency.update(selected.keys())

        count = len(rows)
        idf_float = {
            feature: math.log((1.0 + count) / (1.0 + frequency)) + 1.0
            for feature, frequency in document_frequency.items()
        }
        maximum_idf = max(idf_float.values(), default=1.0)
        idf = {
            feature: max(1, min(31, int(round(31.0 * value / maximum_idf))))
            for feature, value in idf_float.items()
        }
        temporary: dict[int, list[tuple[int, float]]] = defaultdict(list)
        norms: list[float] = []
        for doc_id, features in enumerate(encoded):
            weighted = {
                feature: (1.0 + math.log(value)) * idf_float[feature]
                for feature, value in features.items()
            }
            norm = math.sqrt(sum(value * value for value in weighted.values())) or 1.0
            norms.append(norm)
            for feature, value in weighted.items():
                temporary[feature].append((doc_id, value / norm))

        postings: dict[int, tuple[tuple[int, int], ...]] = {}
        for feature, rows_for_feature in temporary.items():
            strongest = sorted(rows_for_feature, key=lambda item: item[1], reverse=True)[
                :max_postings_per_feature
            ]
            maximum = max((value for _doc, value in strongest), default=1.0)
            postings[feature] = tuple(
                (doc_id, max(1, min(127, int(round(127.0 * value / maximum)))))
                for doc_id, value in strongest
            )
        return cls(
            buckets=buckets,
            titles=tuple(row.title for row in rows),
            snippets=tuple(_normalize(row.text)[:max_snippet_chars] for row in rows),
            doc_features=tuple(tuple(sorted(features)) for features in encoded),
            postings=postings,
            doc_norms=tuple(norms),
            idf=idf,
        )

    def _retrieve(self, text: str, *, top_k: int = 6) -> tuple[list[tuple[int, float]], int]:
        query = _features(text, buckets=self.buckets)
        scores: defaultdict[int, float] = defaultdict(float)
        active = 0
        for feature, frequency in query.items():
            rows = self.postings.get(feature, ())
            weight = (1.0 + math.log(frequency)) * self.idf.get(feature, 1)
            for doc_id, quantized in rows:
                scores[doc_id] += weight * quantized
                active += 1
                if active >= self.max_active_postings:
                    break
            if active >= self.max_active_postings:
                break
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k], active

    def score_options(self, stem: str, options: Sequence[str]) -> MemoryPrediction:
        base_docs, base_active = self._retrieve(stem, top_k=8)
        base_ids = {doc_id for doc_id, _score in base_docs}
        raw_scores: list[float] = []
        active = base_active
        evidence_titles = [self.titles[doc_id] for doc_id, _ in base_docs[:4]]
        for option in options:
            combined, used = self._retrieve(stem + "\n" + option, top_k=8)
            active += used
            option_features = _features(option, buckets=self.buckets)
            option_feature_count = max(1, len(option_features))
            score = 0.0
            normalized_option = _normalize(option)
            for rank, (doc_id, retrieval_score) in enumerate(combined):
                rank_weight = 1.0 / (1.0 + rank)
                document_features = self._doc_feature_sets[doc_id]
                support = sum(
                    self.idf.get(feature, 1) * min(3, frequency)
                    for feature, frequency in option_features.items()
                    if feature in document_features
                )
                coverage = (
                    sum(1 for feature in option_features if feature in document_features)
                    / option_feature_count
                )
                novelty = 1.15 if doc_id not in base_ids else 1.0
                score += novelty * rank_weight * (
                    math.log1p(retrieval_score)
                    + 0.05 * support / option_feature_count
                    + 5.0 * coverage
                )
                if normalized_option and normalized_option in self.snippets[doc_id]:
                    score += 10.0 * rank_weight
                score += 30.0 * rank_weight * _relation_proximity(
                    stem, option, self.snippets[doc_id]
                )
            raw_scores.append(score)
        normalized = _unit(raw_scores)
        index = max(range(len(options)), key=lambda item: normalized[item]) if options else 0
        ordered = sorted(normalized, reverse=True)
        confidence = ordered[0] - ordered[1] if len(ordered) > 1 else 0.0
        return MemoryPrediction(
            index=index,
            scores=tuple(normalized),
            retrieved_documents=tuple(evidence_titles),
            active_postings=active,
            confidence=confidence,
        )

    def resource_report(self) -> dict[str, object]:
        serialized = len(self.to_bytes())
        posting_count = sum(len(rows) for rows in self.postings.values())
        document_feature_count = sum(len(row) for row in self.doc_features)
        return {
            "documents": len(self.titles),
            "features": len(self.postings),
            "postings": posting_count,
            "document_features": document_feature_count,
            "serialized_bytes": serialized,
            "max_active_postings": self.max_active_postings,
            "estimated_active_bytes": self.max_active_postings * 8,
            "paged_sparse": True,
            "document_local_support": True,
            "local_relation_scoring": True,
            "retrieval_magnitude_normalized": True,
        }

    def to_bytes(self) -> bytes:
        payload = {
            "format": self.FORMAT,
            "buckets": self.buckets,
            "titles": self.titles,
            "snippets": self.snippets,
            "doc_features": self.doc_features,
            "postings": {str(feature): rows for feature, rows in self.postings.items()},
            "doc_norms": self.doc_norms,
            "idf": {str(feature): value for feature, value in self.idf.items()},
            "max_active_postings": self.max_active_postings,
        }
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "QuantizedCurriculumMemory":
        payload = json.loads(zlib.decompress(data))
        if payload.get("format") != cls.FORMAT:
            raise ValueError("unsupported curriculum memory format")
        return cls(
            buckets=int(payload["buckets"]),
            titles=tuple(payload["titles"]),
            snippets=tuple(payload["snippets"]),
            doc_features=tuple(
                tuple(int(feature) for feature in row)
                for row in payload["doc_features"]
            ),
            postings={
                int(feature): tuple((int(doc_id), int(weight)) for doc_id, weight in rows)
                for feature, rows in payload["postings"].items()
            },
            doc_norms=tuple(float(value) for value in payload["doc_norms"]),
            idf={int(feature): int(value) for feature, value in payload["idf"].items()},
            max_active_postings=int(payload["max_active_postings"]),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "QuantizedCurriculumMemory":
        return cls.from_bytes(Path(path).read_bytes())
