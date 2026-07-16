from __future__ import annotations

import hashlib
import json
import math
import re
import zlib
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class BrainScaleProfile:
    name: str
    code_space: int
    active_bits: int
    max_chunks: int
    max_response_assemblies: int
    max_sparse_edges: int
    workspace_turns: int
    max_candidates: int
    routing_bits: int


SCALE_PROFILES: dict[str, BrainScaleProfile] = {
    "ci": BrainScaleProfile(
        name="ci",
        code_space=1 << 16,
        active_bits=128,
        max_chunks=4096,
        max_response_assemblies=16384,
        max_sparse_edges=1 << 18,
        workspace_turns=8,
        max_candidates=96,
        routing_bits=24,
    ),
    "desktop-large": BrainScaleProfile(
        name="desktop-large",
        code_space=1 << 20,
        active_bits=192,
        max_chunks=65536,
        max_response_assemblies=262144,
        max_sparse_edges=1 << 23,
        workspace_turns=32,
        max_candidates=192,
        routing_bits=32,
    ),
    "desktop-xl": BrainScaleProfile(
        name="desktop-xl",
        code_space=1 << 22,
        active_bits=256,
        max_chunks=262144,
        max_response_assemblies=1048576,
        max_sparse_edges=1 << 25,
        workspace_turns=64,
        max_candidates=256,
        routing_bits=48,
    ),
}


def _normalise(text: str) -> str:
    text = text.strip().replace("?", "？").replace("!", "！")
    text = re.sub(r"\s+", " ", text)
    return text


def _stable_u64(value: str, seed: int = 0) -> int:
    digest = hashlib.blake2b(
        value.encode("utf-8"),
        digest_size=8,
        person=seed.to_bytes(8, "little", signed=False),
    ).digest()
    return int.from_bytes(digest, "little")


@dataclass
class SurpriseChunker:
    max_chunks: int = 4096
    max_chunk_length: int = 8
    min_count: int = 2
    chunks: tuple[str, ...] = ()
    _chunk_set: set[str] = field(default_factory=set, repr=False)

    def fit(self, texts: Iterable[str]) -> "SurpriseChunker":
        counts: Counter[str] = Counter()
        for raw in texts:
            text = _normalise(raw)
            n = len(text)
            for start in range(n):
                upper = min(self.max_chunk_length, n - start)
                for length in range(2, upper + 1):
                    piece = text[start : start + length]
                    if " " in piece and piece.strip() != piece:
                        continue
                    counts[piece] += 1
        ranked = [
            (-(len(piece) - 1) * (count - 1), -len(piece), piece)
            for piece, count in counts.items()
            if count >= self.min_count
        ]
        ranked.sort()
        selected = [piece for _gain, _length, piece in ranked[: self.max_chunks]]
        self.chunks = tuple(selected)
        self._chunk_set = set(selected)
        return self

    def segment(self, text: str) -> tuple[str, ...]:
        text = _normalise(text)
        if not self._chunk_set and self.chunks:
            self._chunk_set = set(self.chunks)
        output: list[str] = []
        index = 0
        while index < len(text):
            chosen: str | None = None
            for length in range(min(self.max_chunk_length, len(text) - index), 1, -1):
                piece = text[index : index + length]
                if piece in self._chunk_set:
                    chosen = piece
                    break
            if chosen is None:
                chosen = text[index]
            output.append(chosen)
            index += len(chosen)
        return tuple(output)


@dataclass
class SparseCorticalEncoder:
    code_space: int
    active_bits: int
    document_frequency: Counter[str] = field(default_factory=Counter)
    documents: int = 0

    def _raw_features(self, text: str, chunker: SurpriseChunker) -> tuple[str, ...]:
        chunks = chunker.segment(text)
        features: list[str] = [f"c:{chunk}" for chunk in chunks]
        features.extend(f"p:{left}|{right}" for left, right in zip(chunks, chunks[1:]))
        features.extend(f"t:{a}|{b}|{c}" for a, b, c in zip(chunks, chunks[1:], chunks[2:]))
        compact = _normalise(text).replace(" ", "")
        for size in (2, 3, 4):
            features.extend(f"g{size}:{compact[i:i+size]}" for i in range(max(0, len(compact) - size + 1)))
        features.append(f"len:{min(15, len(compact) // 4)}")
        if compact:
            features.append(f"head:{compact[: min(4, len(compact))]}")
            features.append(f"tail:{compact[-min(4, len(compact)): ]}")
        return tuple(dict.fromkeys(features))

    def fit(self, texts: Iterable[str], chunker: SurpriseChunker) -> "SparseCorticalEncoder":
        self.document_frequency.clear()
        self.documents = 0
        for text in texts:
            self.documents += 1
            self.document_frequency.update(set(self._raw_features(text, chunker)))
        return self

    def encode(self, text: str, chunker: SurpriseChunker) -> tuple[int, ...]:
        features = self._raw_features(text, chunker)
        ranked: list[tuple[float, int]] = []
        seen_bits: set[int] = set()
        total_docs = max(1, self.documents)
        for feature in features:
            df = self.document_frequency.get(feature, 0)
            idf = math.log2((total_docs + 1) / (df + 1)) + 1.0
            for replica in range(2):
                code = _stable_u64(feature, replica + 1)
                bit = code % self.code_space
                if bit in seen_bits:
                    continue
                seen_bits.add(bit)
                rank = idf + ((code >> 32) / (1 << 32)) * 0.01
                ranked.append((-rank, bit))
        ranked.sort()
        chosen = [bit for _rank, bit in ranked[: self.active_bits]]
        salt = 0
        normal = _normalise(text)
        while len(chosen) < self.active_bits:
            bit = _stable_u64(f"fill:{normal}:{salt}", 17) % self.code_space
            salt += 1
            if bit not in seen_bits:
                seen_bits.add(bit)
                chosen.append(bit)
        return tuple(sorted(chosen))


@dataclass
class ResponseAssembly:
    response_counts: Counter[str] = field(default_factory=Counter)
    bit_counts: Counter[int] = field(default_factory=Counter)
    examples: int = 0

    @property
    def response(self) -> str:
        return self.response_counts.most_common(1)[0][0]

    def prototype(self, active_bits: int) -> tuple[int, ...]:
        return tuple(bit for bit, _count in self.bit_counts.most_common(active_bits))


@dataclass(frozen=True)
class ReplyResult:
    text: str
    confidence: float
    mechanism: str
    candidates_inspected: int
    active_bits: int
    estimated_sparse_operations: int


class SPARCLanguageModel:
    """Learned Japanese event compiler plus sparse cortical response assemblies.

    Capacity and active compute are deliberately separated. The profile can
    permit hundreds of thousands of assemblies, while one turn touches only
    postings associated with a fixed-size sparse code and a bounded workspace.
    No dense vocabulary projection, full-history attention, or growing KV cache
    is used.
    """

    def __init__(self, profile: str | BrainScaleProfile = "ci") -> None:
        self.profile = SCALE_PROFILES[profile] if isinstance(profile, str) else profile
        self.chunker = SurpriseChunker(max_chunks=self.profile.max_chunks)
        self.encoder = SparseCorticalEncoder(
            code_space=self.profile.code_space,
            active_bits=self.profile.active_bits,
        )
        self.assemblies: list[ResponseAssembly] = []
        self.response_to_assembly: dict[str, int] = {}
        self.postings: dict[int, set[int]] = defaultdict(set)
        self.transitions: dict[int, Counter[int]] = defaultdict(Counter)
        self.workspace: deque[int] = deque(maxlen=self.profile.workspace_turns)
        self.training_turns = 0
        self.last_candidate_count = 0
        self.last_sparse_operations = 0
        self.last_posting_reads = 0

    def reset(self) -> None:
        self.workspace.clear()

    def fit(self, records: Iterable[tuple[str, str]]) -> "SPARCLanguageModel":
        rows = [(_normalise(user), _normalise(assistant)) for user, assistant in records]
        if not rows:
            raise ValueError("records must not be empty")
        corpus = [text for row in rows for text in row]
        self.chunker.fit(corpus)
        self.encoder.fit((user for user, _assistant in rows), self.chunker)
        self.assemblies.clear()
        self.response_to_assembly.clear()
        self.postings.clear()
        self.transitions.clear()
        self.training_turns = 0
        self.reset()
        for user, assistant in rows:
            self.reset()
            self.learn(user, assistant)
        self.reset()
        return self

    def fit_sessions(
        self, sessions: Iterable[Iterable[tuple[str, str]]]
    ) -> "SPARCLanguageModel":
        prepared = [
            [(_normalise(user), _normalise(assistant)) for user, assistant in session]
            for session in sessions
        ]
        prepared = [session for session in prepared if session]
        if not prepared:
            raise ValueError("sessions must not be empty")
        corpus = [text for session in prepared for row in session for text in row]
        users = [user for session in prepared for user, _assistant in session]
        self.chunker.fit(corpus)
        self.encoder.fit(users, self.chunker)
        self.assemblies.clear()
        self.response_to_assembly.clear()
        self.postings.clear()
        self.transitions.clear()
        self.training_turns = 0
        for session in prepared:
            self.reset()
            for user, assistant in session:
                self.learn(user, assistant)
        self.reset()
        return self

    def _assembly_for_response(self, response: str) -> int:
        assembly_id = self.response_to_assembly.get(response)
        if assembly_id is not None:
            return assembly_id
        if len(self.assemblies) >= self.profile.max_response_assemblies:
            raise MemoryError("response assembly capacity reached")
        assembly_id = len(self.assemblies)
        self.assemblies.append(ResponseAssembly())
        self.response_to_assembly[response] = assembly_id
        return assembly_id

    def learn(self, user: str, assistant: str) -> int:
        user = _normalise(user)
        assistant = _normalise(assistant)
        code = self.encoder.encode(user, self.chunker)
        assembly_id = self._assembly_for_response(assistant)
        assembly = self.assemblies[assembly_id]
        assembly.response_counts[assistant] += 1
        assembly.bit_counts.update(code)
        assembly.examples += 1
        for bit in code:
            self.postings[bit].add(assembly_id)
        if self.workspace:
            previous = self.workspace[-1]
            counter = self.transitions[previous]
            counter[assembly_id] += 1
            if sum(len(value) for value in self.transitions.values()) > self.profile.max_sparse_edges:
                victim = min(counter, key=lambda target: (counter[target], target))
                del counter[victim]
        self.workspace.append(assembly_id)
        self.training_turns += 1
        return assembly_id

    def _bit_weight(self, bit: int) -> float:
        assembly_df = len(self.postings.get(int(bit), ()))
        return math.log2((len(self.assemblies) + 1) / (assembly_df + 1)) + 1.0

    def _candidate_ids(self, code: Sequence[int]) -> list[tuple[int, float]]:
        votes: Counter[int] = Counter()
        routes = sorted(
            (len(self.postings[int(bit)]), int(bit))
            for bit in code
            if self.postings.get(int(bit))
        )
        reads = 0
        used_routes = 0
        read_budget = self.profile.max_candidates * 8
        for posting_size, bit in routes:
            if used_routes >= self.profile.routing_bits:
                break
            if posting_size > read_budget and votes:
                continue
            weight = self._bit_weight(bit)
            for assembly_id in self.postings[bit]:
                votes[assembly_id] += weight
                reads += 1
                if reads >= read_budget:
                    break
            used_routes += 1
            if reads >= read_budget:
                break
        self.last_posting_reads = reads
        if not votes:
            return []
        return votes.most_common(self.profile.max_candidates)

    def reply(self, text: str, *, unknown: str = "まだ十分に学習できていません。教えてください。") -> ReplyResult:
        code = self.encoder.encode(text, self.chunker)
        candidates = self._candidate_ids(code)
        self.last_candidate_count = len(candidates)
        self.last_sparse_operations = len(code) + self.last_posting_reads + len(candidates) * 3
        if not candidates:
            return ReplyResult(
                text=unknown,
                confidence=0.0,
                mechanism="calibrated-unknown",
                candidates_inspected=0,
                active_bits=len(code),
                estimated_sparse_operations=self.last_sparse_operations,
            )
        previous = self.workspace[-1] if self.workspace else None
        best_id = -1
        best_score = -1.0
        best_overlap = 0
        query_weight = sum(self._bit_weight(int(bit)) for bit in code)
        for assembly_id, _vote in candidates:
            assembly = self.assemblies[assembly_id]
            matched_bits = [bit for bit in code if bit in assembly.bit_counts]
            refined = len(matched_bits)
            lexical = (
                sum(self._bit_weight(int(bit)) for bit in matched_bits) / max(1e-9, query_weight)
            )
            support = min(1.0, math.log2(assembly.examples + 1) / 4.0)
            context = 0.0
            if previous is not None:
                outgoing = self.transitions.get(previous)
                if outgoing:
                    total = sum(outgoing.values())
                    context = outgoing.get(assembly_id, 0) / total
            score = 0.72 * lexical + 0.08 * support + 0.20 * context
            if score > best_score:
                best_score = score
                best_id = assembly_id
                best_overlap = refined
        confidence = min(1.0, best_score / 0.45)
        if best_id < 0 or best_overlap < max(3, self.profile.active_bits // 32) or confidence < 0.24:
            return ReplyResult(
                text=unknown,
                confidence=confidence,
                mechanism="calibrated-unknown",
                candidates_inspected=len(candidates),
                active_bits=len(code),
                estimated_sparse_operations=self.last_sparse_operations,
            )
        self.workspace.append(best_id)
        return ReplyResult(
            text=self.assemblies[best_id].response,
            confidence=confidence,
            mechanism="sparse-cortical-assembly",
            candidates_inspected=len(candidates),
            active_bits=len(code),
            estimated_sparse_operations=self.last_sparse_operations,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-language-hs1",
            "profile": asdict(self.profile),
            "chunker": {
                "max_chunks": self.chunker.max_chunks,
                "max_chunk_length": self.chunker.max_chunk_length,
                "min_count": self.chunker.min_count,
                "chunks": self.chunker.chunks,
            },
            "encoder": {
                "document_frequency": dict(self.encoder.document_frequency),
                "documents": self.encoder.documents,
            },
            "assemblies": [
                {
                    "response_counts": dict(assembly.response_counts),
                    "bit_counts": {str(bit): count for bit, count in assembly.bit_counts.items()},
                    "examples": assembly.examples,
                }
                for assembly in self.assemblies
            ],
            "transitions": {
                str(source): {str(target): count for target, count in targets.items()}
                for source, targets in self.transitions.items()
            },
            "training_turns": self.training_turns,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, level=9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCLanguageModel":
        payload = json.loads(zlib.decompress(data))
        profile = BrainScaleProfile(**payload["profile"])
        model = cls(profile)
        chunker_row = payload["chunker"]
        model.chunker = SurpriseChunker(
            max_chunks=int(chunker_row["max_chunks"]),
            max_chunk_length=int(chunker_row["max_chunk_length"]),
            min_count=int(chunker_row["min_count"]),
            chunks=tuple(chunker_row["chunks"]),
        )
        model.chunker._chunk_set = set(model.chunker.chunks)
        encoder_row = payload["encoder"]
        model.encoder.document_frequency.update(
            {str(key): int(value) for key, value in encoder_row["document_frequency"].items()}
        )
        model.encoder.documents = int(encoder_row["documents"])
        for row in payload["assemblies"]:
            assembly = ResponseAssembly()
            assembly.response_counts.update({str(k): int(v) for k, v in row["response_counts"].items()})
            assembly.bit_counts.update({int(k): int(v) for k, v in row["bit_counts"].items()})
            assembly.examples = int(row["examples"])
            assembly_id = len(model.assemblies)
            model.assemblies.append(assembly)
            model.response_to_assembly[assembly.response] = assembly_id
            for bit in assembly.bit_counts:
                model.postings[bit].add(assembly_id)
        for source, targets in payload["transitions"].items():
            model.transitions[int(source)].update({int(k): int(v) for k, v in targets.items()})
        model.training_turns = int(payload["training_turns"])
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCLanguageModel":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, int | float | str | bool]:
        edges = sum(len(targets) for targets in self.transitions.values())
        posting_edges = sum(len(ids) for ids in self.postings.values())
        return {
            "profile": self.profile.name,
            "configured_code_space": self.profile.code_space,
            "configured_response_capacity": self.profile.max_response_assemblies,
            "configured_sparse_edge_capacity": self.profile.max_sparse_edges,
            "learned_chunks": len(self.chunker.chunks),
            "response_assemblies": len(self.assemblies),
            "posting_edges": posting_edges,
            "transition_edges": edges,
            "training_turns": self.training_turns,
            "serialized_bytes": len(self.to_bytes()),
            "active_bits_per_turn": self.profile.active_bits,
            "last_candidates_inspected": self.last_candidate_count,
            "last_posting_reads": self.last_posting_reads,
            "last_estimated_sparse_operations": self.last_sparse_operations,
            "full_history_attention_used": False,
            "growing_kv_cache_used": False,
            "dense_vocabulary_projection_used": False,
            "capacity_preallocated": False,
        }
