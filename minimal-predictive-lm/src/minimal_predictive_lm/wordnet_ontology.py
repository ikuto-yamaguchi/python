from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen
import zipfile
from io import BytesIO
from typing import Iterable

from .generic_quantifier import GenericQuantifierProgram, IdentifiabilityInterval


OEWN_2025_URL = "https://en-word.net/static/english-wordnet-2025.zip"
OEWN_2025_SHA256 = "38b16326159f51853626b7d24a44c453fa88ab33f06fce5ec8fc5996d1c2be93"


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = value.replace("-", "_")
    value = re.sub(r"[^a-z0-9_ ]+", " ", value)
    value = re.sub(r"\s+", "_", value).strip("_")
    return value


def _bits(payload: object) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ) * 8


@dataclass(frozen=True)
class NounSynset:
    offset: int
    lemmas: tuple[str, ...]
    hypernyms: tuple[int, ...]


@dataclass(frozen=True)
class OntologyDecision:
    item: str
    concept: str
    value: bool | None
    item_candidates: tuple[str, ...]
    concept_candidates: tuple[str, ...]
    proof_offsets: tuple[int, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class OntologyMetrics:
    source_bytes: int
    source_sha256: str
    synsets: int
    lemmas: int
    hypernym_edges: int
    queries: int
    cache_hits: int
    synset_reads: int
    edge_reads: int
    cache_entries: int
    cache_bits: int


class WordNetNounOntology:
    def __init__(
        self,
        *,
        synsets: dict[int, NounSynset],
        lemma_to_synsets: dict[str, tuple[int, ...]],
        exceptions: dict[str, tuple[str, ...]],
        source_bytes: int,
        source_sha256: str,
    ) -> None:
        self.synsets = synsets
        self.lemma_to_synsets = lemma_to_synsets
        self.exceptions = exceptions
        self.source_bytes = source_bytes
        self.source_sha256 = source_sha256
        self.queries = 0
        self.cache_hits = 0
        self.synset_reads = 0
        self.edge_reads = 0
        self._cache: dict[tuple[str, str], OntologyDecision] = {}

    @classmethod
    def from_zip_bytes(
        cls,
        payload: bytes,
        *,
        expected_sha256: str | None = OEWN_2025_SHA256,
    ) -> "WordNetNounOntology":
        observed = hashlib.sha256(payload).hexdigest()
        if expected_sha256 is not None and observed != expected_sha256:
            raise ValueError(
                f"Open English WordNet checksum mismatch: expected {expected_sha256}, got {observed}"
            )
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            data_name = _find_archive_member(archive.namelist(), "data.noun")
            exception_name = _find_archive_member(archive.namelist(), "noun.exc")
            data_payload = archive.read(data_name)
            exception_payload = archive.read(exception_name)
        synsets, lemma_to_synsets = parse_data_noun(data_payload)
        exceptions = parse_noun_exceptions(exception_payload)
        return cls(
            synsets=synsets,
            lemma_to_synsets=lemma_to_synsets,
            exceptions=exceptions,
            source_bytes=len(payload),
            source_sha256=observed,
        )

    @classmethod
    def from_zip_path(
        cls,
        path: str | Path,
        *,
        expected_sha256: str | None = OEWN_2025_SHA256,
    ) -> "WordNetNounOntology":
        return cls.from_zip_bytes(Path(path).read_bytes(), expected_sha256=expected_sha256)

    def lemma_candidates(self, surface: str) -> tuple[str, ...]:
        normalized = _normalize_text(surface)
        if not normalized:
            return ()
        candidates: list[str] = [normalized]
        tokens = normalized.split("_")

        # Generic measure-noun compositions: "heads of broccoli", "stalk of celery".
        if "of" in tokens:
            index = tokens.index("of")
            if index + 1 < len(tokens):
                candidates.append("_".join(tokens[index + 1 :]))
        if tokens and tokens[-1] in {"head", "heads", "stalk", "stalks", "piece", "pieces"}:
            if len(tokens) > 1:
                candidates.append("_".join(tokens[:-1]))

        # Morphology is applied both to the whole lemma and to the final head token.
        expanded: list[str] = []
        for candidate in candidates:
            expanded.append(candidate)
            expanded.extend(self.exceptions.get(candidate, ()))
            parts = candidate.split("_")
            for final in _singular_forms(parts[-1], self.exceptions):
                expanded.append("_".join(parts[:-1] + [final]))

        # For modified concepts, retain both the full compound and its semantic head.
        for candidate in tuple(expanded):
            parts = candidate.split("_")
            if len(parts) > 1:
                expanded.append(parts[-1])

        return tuple(dict.fromkeys(value for value in expanded if value))

    def lookup(self, surface: str) -> tuple[int, ...]:
        offsets: list[int] = []
        for candidate in self.lemma_candidates(surface):
            offsets.extend(self.lemma_to_synsets.get(candidate, ()))
        return tuple(dict.fromkeys(offsets))

    def is_a(self, item: str, concept: str) -> OntologyDecision:
        key = (_normalize_text(item), _normalize_text(concept))
        self.queries += 1
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached

        item_candidates = self.lemma_candidates(item)
        concept_candidates = self.lemma_candidates(concept)
        item_synsets = self.lookup(item)
        concept_synsets = set(self.lookup(concept))
        if not item_synsets:
            decision = OntologyDecision(
                item,
                concept,
                None,
                item_candidates,
                concept_candidates,
                reason="item-unresolved",
            )
        elif not concept_synsets:
            decision = OntologyDecision(
                item,
                concept,
                None,
                item_candidates,
                concept_candidates,
                reason="concept-unresolved",
            )
        else:
            path = self._shortest_hypernym_path(item_synsets, concept_synsets)
            if path is None:
                decision = OntologyDecision(
                    item,
                    concept,
                    False,
                    item_candidates,
                    concept_candidates,
                    reason="no-hypernym-path",
                )
            else:
                decision = OntologyDecision(
                    item,
                    concept,
                    True,
                    item_candidates,
                    concept_candidates,
                    proof_offsets=path,
                    reason="hypernym-path",
                )
        self._cache[key] = decision
        return decision

    def _shortest_hypernym_path(
        self,
        starts: Iterable[int],
        targets: set[int],
    ) -> tuple[int, ...] | None:
        queue: deque[int] = deque()
        parent: dict[int, int | None] = {}
        for offset in starts:
            if offset not in self.synsets:
                continue
            parent[offset] = None
            queue.append(offset)
        while queue:
            offset = queue.popleft()
            self.synset_reads += 1
            if offset in targets:
                path: list[int] = []
                current: int | None = offset
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return tuple(reversed(path))
            synset = self.synsets.get(offset)
            if synset is None:
                continue
            for hypernym in synset.hypernyms:
                self.edge_reads += 1
                if hypernym not in parent and hypernym in self.synsets:
                    parent[hypernym] = offset
                    queue.append(hypernym)
        return None

    def proof_lemmas(self, decision: OntologyDecision) -> tuple[tuple[str, ...], ...]:
        return tuple(self.synsets[offset].lemmas for offset in decision.proof_offsets)

    def cache_payload(self) -> object:
        return [
            {
                "item": decision.item,
                "concept": decision.concept,
                "value": decision.value,
                "proof": [list(self.synsets[offset].lemmas) for offset in decision.proof_offsets],
                "reason": decision.reason,
            }
            for _, decision in sorted(self._cache.items())
        ]

    @property
    def cache_bits(self) -> int:
        return _bits(self.cache_payload())

    def metrics(self) -> OntologyMetrics:
        return OntologyMetrics(
            source_bytes=self.source_bytes,
            source_sha256=self.source_sha256,
            synsets=len(self.synsets),
            lemmas=len(self.lemma_to_synsets),
            hypernym_edges=sum(len(row.hypernyms) for row in self.synsets.values()),
            queries=self.queries,
            cache_hits=self.cache_hits,
            synset_reads=self.synset_reads,
            edge_reads=self.edge_reads,
            cache_entries=len(self._cache),
            cache_bits=self.cache_bits,
        )


class OntologyBackedQuantifier:
    def __init__(
        self,
        base: GenericQuantifierProgram,
        ontology: WordNetNounOntology,
    ) -> None:
        self.base = base
        self.ontology = ontology
        self.last_decisions: tuple[OntologyDecision, ...] = ()

    def identifiability_interval(self, prompt: str) -> IdentifiabilityInterval | None:
        parsed = self.base.parse(prompt)
        if parsed is None:
            self.last_decisions = ()
            return None
        if parsed.query_concept in self.base.universal_concepts:
            self.last_decisions = ()
            total = sum(item.quantity for item in parsed.items)
            return IdentifiabilityInterval(total, total)
        minimum = 0
        maximum = 0
        decisions: list[OntologyDecision] = []
        for item in parsed.items:
            decision = self.ontology.is_a(item.surface, parsed.query_concept)
            decisions.append(decision)
            if decision.value is True:
                minimum += item.quantity
                maximum += item.quantity
            elif decision.value is None:
                maximum += item.quantity
        self.last_decisions = tuple(decisions)
        return IdentifiabilityInterval(minimum, maximum)

    def answer(self, prompt: str) -> int | None:
        interval = self.identifiability_interval(prompt)
        if interval is None or not interval.identifiable:
            return None
        return interval.minimum


def _find_archive_member(names: Iterable[str], basename: str) -> str:
    matches = [name for name in names if name.rsplit("/", 1)[-1] == basename]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {basename!r} in WordNet archive, got {matches}")
    return matches[0]


def parse_data_noun(
    payload: bytes,
) -> tuple[dict[int, NounSynset], dict[str, tuple[int, ...]]]:
    synsets: dict[int, NounSynset] = {}
    lemma_map: dict[str, list[int]] = {}
    for raw_line in payload.decode("utf-8", errors="replace").splitlines():
        if not raw_line or raw_line[0].isspace():
            continue
        data = raw_line.split("|", 1)[0].strip()
        fields = data.split()
        if len(fields) < 5 or not fields[0].isdigit() or fields[2] != "n":
            continue
        offset = int(fields[0])
        word_count = int(fields[3], 16)
        cursor = 4
        lemmas: list[str] = []
        for _ in range(word_count):
            if cursor + 1 >= len(fields):
                raise ValueError(f"truncated WordNet lemma row at offset {offset}")
            lemma = _normalize_text(fields[cursor])
            lemmas.append(lemma)
            cursor += 2  # lemma + lex_id
        if cursor >= len(fields):
            raise ValueError(f"missing pointer count at offset {offset}")
        pointer_count = int(fields[cursor])
        cursor += 1
        hypernyms: list[int] = []
        for _ in range(pointer_count):
            if cursor + 3 >= len(fields):
                raise ValueError(f"truncated WordNet pointer row at offset {offset}")
            symbol, target, pos, _source_target = fields[cursor : cursor + 4]
            cursor += 4
            if symbol in {"@", "@i"} and pos == "n":
                hypernyms.append(int(target))
        synsets[offset] = NounSynset(offset, tuple(lemmas), tuple(hypernyms))
        for lemma in lemmas:
            lemma_map.setdefault(lemma, []).append(offset)
    if not synsets:
        raise ValueError("WordNet archive contained no noun synsets")
    return synsets, {lemma: tuple(offsets) for lemma, offsets in lemma_map.items()}


def parse_noun_exceptions(payload: bytes) -> dict[str, tuple[str, ...]]:
    output: dict[str, tuple[str, ...]] = {}
    for raw_line in payload.decode("utf-8", errors="replace").splitlines():
        fields = raw_line.strip().split()
        if len(fields) >= 2:
            output[_normalize_text(fields[0])] = tuple(
                _normalize_text(value) for value in fields[1:]
            )
    return output


def _singular_forms(
    word: str,
    exceptions: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    output: list[str] = list(exceptions.get(word, ()))
    if word.endswith("ies") and len(word) > 3:
        output.append(word[:-3] + "y")
    if word.endswith("ves") and len(word) > 3:
        output.extend((word[:-3] + "f", word[:-3] + "fe"))
    if word.endswith(("ches", "shes", "sses", "xes", "zes")) and len(word) > 2:
        output.append(word[:-2])
    if word.endswith("s") and not word.endswith("ss") and len(word) > 1:
        output.append(word[:-1])
    return tuple(dict.fromkeys(value for value in output if value))


def download_pinned_wordnet(
    path: str | Path,
    *,
    url: str = OEWN_2025_URL,
    expected_sha256: str | None = OEWN_2025_SHA256,
    timeout_seconds: float = 180.0,
) -> tuple[Path, str, int]:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        request = Request(url, headers={"User-Agent": "minimal-predictive-lm/0.1"})
        with urlopen(request, timeout=timeout_seconds) as response:
            destination.write_bytes(response.read())
    payload = destination.read_bytes()
    observed = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise ValueError(
            f"Open English WordNet checksum mismatch: expected {expected_sha256}, got {observed}"
        )
    return destination, observed, len(payload)
