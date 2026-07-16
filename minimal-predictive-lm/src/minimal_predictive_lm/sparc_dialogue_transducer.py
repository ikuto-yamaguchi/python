from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
import json
import math
import re
import zlib
from typing import Iterable, Mapping


_COPY_RE = re.compile(r"\{copy_(\d+)\}")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _contains_content(text: str) -> bool:
    return any(character.isalnum() or "\u3040" <= character <= "\u9fff" for character in text)


def _anchors(text: str) -> tuple[str, ...]:
    cleaned = _COPY_RE.sub("", _normalise(text))
    output: set[str] = set()
    for size in (2, 3, 4):
        for index in range(max(0, len(cleaned) - size + 1)):
            piece = cleaned[index : index + size]
            if piece.strip() and not piece.isdigit():
                output.add(f"N{size}:{piece}")
    if cleaned:
        output.add(f"H:{cleaned[: min(6, len(cleaned))]}")
        output.add(f"T:{cleaned[-min(6, len(cleaned)): ]}")
    return tuple(sorted(output))


@dataclass(frozen=True)
class DialoguePair:
    user: str
    assistant: str


@dataclass(frozen=True)
class SharedBlock:
    user_start: int
    assistant_start: int
    length: int
    text: str


@dataclass(frozen=True)
class TransductionSchema:
    schema_id: int
    input_surface: str
    output_surface: str
    copies: int
    examples: int
    anchors: tuple[str, ...]


@dataclass(frozen=True)
class TransductionResult:
    text: str | None
    mechanism: str
    confidence: float
    candidates: int
    feature_reads: int
    schema_id: int | None


def _shared_blocks(user: str, assistant: str) -> tuple[SharedBlock, ...]:
    matcher = SequenceMatcher(None, user, assistant, autojunk=False)
    output: list[SharedBlock] = []
    for block in matcher.get_matching_blocks():
        if block.size < 2:
            continue
        text = user[block.a : block.a + block.size]
        if not _contains_content(text):
            continue
        output.append(SharedBlock(block.a, block.b, block.size, text))
    return tuple(output)


def _abstract(text: str, blocks: tuple[SharedBlock, ...], *, user_side: bool) -> str:
    position = 0
    output: list[str] = []
    for index, block in enumerate(blocks):
        start = block.user_start if user_side else block.assistant_start
        output.append(text[position:start])
        output.append(f"{{copy_{index}}}")
        position = start + block.length
    output.append(text[position:])
    return "".join(output)


def _compile_input(surface: str) -> re.Pattern[str]:
    position = 0
    output: list[str] = ["^"]
    seen: set[str] = set()
    for match in _COPY_RE.finditer(surface):
        static = re.escape(surface[position : match.start()]).replace(r"\ ", r"\s*")
        output.append(static)
        name = f"copy_{match.group(1)}"
        if name in seen:
            output.append(f"(?P={name})")
        else:
            output.append(f"(?P<{name}>.+?)")
            seen.add(name)
        position = match.end()
    output.append(re.escape(surface[position:]).replace(r"\ ", r"\s*"))
    output.append("$")
    return re.compile("".join(output))


def _render(surface: str, values: Mapping[str, str]) -> str | None:
    output = surface
    for name in set(_COPY_RE.findall(surface)):
        key = f"copy_{name}"
        value = values.get(key)
        if value is None:
            return None
        output = output.replace("{" + key + "}", value)
    return _normalise(output)


class SparseDialogueTransducer:
    """Induces bounded copy-and-reorder programs directly from dialogue pairs.

    No semantic slot labels are supplied. The learner finds low-frequency spans
    shared by a user turn and its response, abstracts them into copy variables,
    groups repeated input/output surfaces, and retrieves only schemas supported
    by sparse static anchors.
    """

    def __init__(
        self,
        *,
        max_schemas: int = 256,
        max_candidates: int = 16,
        max_copy_spans: int = 8,
        maximum_shared_df_ratio: float = 0.05,
    ) -> None:
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.max_copy_spans = max_copy_spans
        self.maximum_shared_df_ratio = maximum_shared_df_ratio
        self.schemas: list[TransductionSchema] = []
        self.postings: dict[str, set[int]] = defaultdict(set)
        self._regex_cache: dict[int, re.Pattern[str]] = {}
        self.training_pairs = 0
        self.last_candidates = 0
        self.last_feature_reads = 0

    def fit(self, pairs: Iterable[DialoguePair]) -> int:
        rows = tuple(
            DialoguePair(_normalise(row.user), _normalise(row.assistant))
            for row in pairs
        )
        if not rows:
            raise ValueError("dialogue transduction requires training pairs")
        self.training_pairs = len(rows)

        block_rows: list[tuple[DialoguePair, tuple[SharedBlock, ...]]] = []
        document_frequency: Counter[str] = Counter()
        for row in rows:
            blocks = _shared_blocks(row.user, row.assistant)
            block_rows.append((row, blocks))
            document_frequency.update({block.text for block in blocks})

        maximum_df = max(2, int(len(rows) * self.maximum_shared_df_ratio))
        grouped: Counter[tuple[str, str, int]] = Counter()
        for row, blocks in block_rows:
            selected = tuple(
                block
                for block in blocks
                if document_frequency[block.text] <= maximum_df
            )[: self.max_copy_spans]
            if not selected:
                continue
            input_surface = _abstract(row.user, selected, user_side=True)
            output_surface = _abstract(row.assistant, selected, user_side=False)
            grouped[(input_surface, output_surface, len(selected))] += 1

        ranked = sorted(
            grouped.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
        self.schemas.clear()
        self.postings.clear()
        self._regex_cache.clear()
        for schema_id, ((input_surface, output_surface, copies), examples) in enumerate(
            ranked[: self.max_schemas]
        ):
            anchors = _anchors(input_surface)
            schema = TransductionSchema(
                schema_id,
                input_surface,
                output_surface,
                copies,
                examples,
                anchors,
            )
            self.schemas.append(schema)
            for anchor in anchors:
                self.postings[anchor].add(schema_id)
        return len(self.schemas)

    def _candidate_schemas(self, text: str) -> tuple[tuple[float, int], ...]:
        query_anchors = _anchors(text)
        votes: Counter[int] = Counter()
        reads = 0
        for posting_size, anchor in sorted(
            (len(self.postings.get(anchor, ())), anchor)
            for anchor in query_anchors
            if self.postings.get(anchor)
        ):
            if posting_size > self.max_candidates * 4 and votes:
                continue
            for schema_id in self.postings[anchor]:
                votes[schema_id] += 1.0 / max(1, posting_size)
                reads += 1
                if reads >= self.max_candidates * 12:
                    break
            if reads >= self.max_candidates * 12:
                break
        scored = [
            (
                vote
                + 0.05 * self.schemas[schema_id].examples
                + 0.01 * len(self.schemas[schema_id].anchors),
                schema_id,
            )
            for schema_id, vote in votes.items()
        ]
        scored.sort(key=lambda row: (-row[0], row[1]))
        self.last_candidates = min(len(scored), self.max_candidates)
        self.last_feature_reads = reads + len(scored)
        return tuple(scored[: self.max_candidates])

    def transduce(self, user: str) -> TransductionResult:
        user = _normalise(user)
        candidates = self._candidate_schemas(user)
        for score, schema_id in candidates:
            schema = self.schemas[schema_id]
            pattern = self._regex_cache.get(schema_id)
            if pattern is None:
                pattern = _compile_input(schema.input_surface)
                self._regex_cache[schema_id] = pattern
            match = pattern.fullmatch(user)
            self.last_feature_reads += 1
            if match is None:
                continue
            text = _render(schema.output_surface, match.groupdict())
            if text is None:
                continue
            confidence = min(1.0, 0.60 + math.log1p(schema.examples) / 12 + score / 100)
            return TransductionResult(
                text,
                "induced-copy-schema",
                confidence,
                self.last_candidates,
                self.last_feature_reads,
                schema_id,
            )
        return TransductionResult(
            None,
            "abstain-unseen-surface",
            0.0,
            self.last_candidates,
            self.last_feature_reads,
            None,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs19-dialogue-transducer-v1",
            "max_schemas": self.max_schemas,
            "max_candidates": self.max_candidates,
            "max_copy_spans": self.max_copy_spans,
            "maximum_shared_df_ratio": self.maximum_shared_df_ratio,
            "training_pairs": self.training_pairs,
            "schemas": [asdict(row) for row in self.schemas],
        }
        return zlib.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseDialogueTransducer":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            max_schemas=int(payload["max_schemas"]),
            max_candidates=int(payload["max_candidates"]),
            max_copy_spans=int(payload["max_copy_spans"]),
            maximum_shared_df_ratio=float(payload["maximum_shared_df_ratio"]),
        )
        model.training_pairs = int(payload["training_pairs"])
        model.schemas = [
            TransductionSchema(
                int(row["schema_id"]),
                str(row["input_surface"]),
                str(row["output_surface"]),
                int(row["copies"]),
                int(row["examples"]),
                tuple(row["anchors"]),
            )
            for row in payload["schemas"]
        ]
        for schema in model.schemas:
            for anchor in schema.anchors:
                model.postings[anchor].add(schema.schema_id)
        return model

    def report(self) -> dict[str, object]:
        return {
            "schemas": len(self.schemas),
            "training_pairs": self.training_pairs,
            "posting_edges": sum(len(rows) for rows in self.postings.values()),
            "serialized_bytes": len(self.to_bytes()),
            "last_candidates": self.last_candidates,
            "last_feature_reads": self.last_feature_reads,
            "explicit_semantic_slots_used": False,
            "complete_response_selection_used": False,
            "full_history_scan_used": False,
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
