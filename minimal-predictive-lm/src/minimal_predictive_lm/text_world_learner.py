from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
import re
import zlib
from typing import Iterable, Mapping, Sequence

_SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_NUMBER_RE = re.compile(r"-?\d+")
_ENTITY_ASSERT_RE = re.compile(r"(?:^|[、,])(?P<entity>[一-龠々ぁ-んァ-ヶーA-Za-z0-9]{1,24}?)(?:には|は)(?P<value>-?\d+)個")


def _cosine(left: Mapping[int, float], right: Mapping[int, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _normalise(vector: Mapping[int, float]) -> dict[int, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm <= 0:
        return {}
    return {key: value / norm for key, value in vector.items()}


def _stable_hash(text: str, dimensions: int) -> tuple[int, float]:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    raw = int.from_bytes(digest, "little")
    return raw % dimensions, -1.0 if (raw >> 63) else 1.0


def _char_ngrams(text: str, minimum: int = 2, maximum: int = 4) -> tuple[str, ...]:
    compact = re.sub(r"\s+", "", text)
    rows: list[str] = []
    for size in range(minimum, maximum + 1):
        for index in range(max(0, len(compact) - size + 1)):
            rows.append(compact[index : index + size])
    return tuple(rows)


@dataclass(frozen=True)
class Assignment:
    destination_role: int
    expression: str
    source_roles: tuple[int, ...] = ()


@dataclass(frozen=True)
class LatentProgram:
    assignments: tuple[Assignment, ...]

    @property
    def role_count(self) -> int:
        roles = [row.destination_role for row in self.assignments]
        for row in self.assignments:
            roles.extend(row.source_roles)
        return max(roles, default=-1) + 1

    @property
    def signature(self) -> str:
        parts = []
        for row in self.assignments:
            src = ",".join(str(value) for value in row.source_roles)
            parts.append(f"r{row.destination_role}={row.expression}({src})")
        return ";".join(parts)


@dataclass(frozen=True)
class InferenceResult:
    program: LatentProgram | None
    role_entities: tuple[str, ...]
    confidence: float
    candidates: int
    feature_reads: int
    mechanism: str


class DistributionalCharEncoder:
    """Learns sparse character n-gram meaning from unlabelled sentence context."""

    def __init__(self, *, dimensions: int = 512, maximum_df_ratio: float = 0.55) -> None:
        self.dimensions = dimensions
        self.maximum_df_ratio = maximum_df_ratio
        self.vectors: dict[str, dict[int, float]] = {}
        self.weights: dict[str, float] = {}
        self.documents = 0
        self.active_ngrams = 0

    def fit(self, sentences: Iterable[str]) -> "DistributionalCharEncoder":
        docs = [tuple(dict.fromkeys(_char_ngrams(sentence))) for sentence in sentences]
        docs = [row for row in docs if row]
        self.documents = len(docs)
        document_frequency: Counter[str] = Counter()
        for row in docs:
            document_frequency.update(row)
        maximum_df = max(2, int(max(1, len(docs)) * self.maximum_df_ratio))
        active = {gram for gram, count in document_frequency.items() if count <= maximum_df}
        accum: dict[str, Counter[int]] = defaultdict(Counter)
        for row in docs:
            filtered = [gram for gram in row if gram in active]
            for target in filtered:
                for context in filtered:
                    if context == target:
                        continue
                    bucket, sign = _stable_hash(context, self.dimensions)
                    accum[target][bucket] += sign / math.sqrt(max(1, document_frequency[context]))
        self.vectors = {gram: _normalise(vector) for gram, vector in accum.items() if vector}
        self.weights = {
            gram: (math.log((len(docs) + 1.0) / (document_frequency[gram] + 1.0)) + 1.0)
            * (1.0 + 0.20 * max(0, len(gram) - 2))
            for gram in self.vectors
        }
        self.active_ngrams = len(self.vectors)
        return self

    def encode(self, text: str) -> dict[int, float]:
        merged: Counter[int] = Counter()
        used = 0
        for gram in _char_ngrams(text):
            vector = self.vectors.get(gram)
            if not vector:
                continue
            used += 1
            weight = self.weights.get(gram, 1.0)
            for key, value in vector.items():
                merged[key] += value * weight
        return _normalise(merged) if used else {}


class TextWorldLearner:
    """Learns state-edit programs from Japanese narratives and converses over state.

    Training receives only sentences: initial facts, an event sentence, and later
    observed facts. At inference, result facts are omitted. The learner must map
    the event to a latent edit program, update its own sparse world state, retain
    provenance, and answer questions from that state.
    """

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.25,
        margin_threshold: float = 0.015,
        max_entities: int = 128,
        max_events: int = 256,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        self.max_entities = max_entities
        self.max_events = max_events
        self.encoder = DistributionalCharEncoder()
        self.program_texts: dict[str, list[str]] = defaultdict(list)
        self.programs: dict[str, LatentProgram] = {}
        self.prototypes: dict[str, dict[int, float]] = {}
        self.unlabelled_sentences: list[str] = []
        self.training_documents = 0
        self.world: dict[str, int] = {}
        self.event_log: deque[dict[str, object]] = deque(maxlen=max_events)
        self.last_candidates = 0
        self.last_feature_reads = 0

    @staticmethod
    def split_sentences(document: str) -> tuple[str, ...]:
        return tuple(
            match.group(0).strip()
            for match in _SENTENCE_RE.finditer(document)
            if match.group(0).strip()
        )

    @staticmethod
    def assertions(sentence: str) -> dict[str, int]:
        clean = sentence.strip().rstrip("。！？!?")
        for prefix in (
            "はじめに、",
            "最初に、",
            "観測すると、",
            "その結果、",
            "記録では、",
            "現在、",
        ):
            if clean.startswith(prefix):
                clean = clean[len(prefix) :]
        return {
            match.group("entity"): int(match.group("value"))
            for match in _ENTITY_ASSERT_RE.finditer(clean)
        }

    @staticmethod
    def _entities_in_text(text: str, entities: Iterable[str]) -> tuple[str, ...]:
        positions = []
        for entity in entities:
            start = text.find(entity)
            if start >= 0:
                positions.append((start, -len(entity), entity))
        positions.sort()
        return tuple(row[2] for row in positions)

    @staticmethod
    def _numbers(text: str) -> tuple[int, ...]:
        return tuple(int(value) for value in _NUMBER_RE.findall(text))

    @staticmethod
    def _program_from_transition(
        event: str,
        before: Mapping[str, int],
        after: Mapping[str, int],
    ) -> tuple[LatentProgram, dict[str, int]]:
        mentions = TextWorldLearner._entities_in_text(event, before)
        if not mentions:
            raise ValueError(f"event contains no known entity: {event}")
        changed = [
            key
            for key in sorted(set(before) | set(after))
            if before.get(key, 0) != after.get(key, 0)
        ]
        if not changed:
            raise ValueError("event produced no state change")
        numbers = TextWorldLearner._numbers(event)
        numeric = numbers[-1] if numbers else None
        role_map: dict[str, int] = {}

        def role(entity: str) -> int:
            if entity not in role_map:
                role_map[entity] = len(role_map)
            return role_map[entity]

        if len(changed) == 2:
            left, right = changed
            if after[left] == before[right] and after[right] == before[left]:
                left_role, right_role = role(left), role(right)
                return (
                    LatentProgram(
                        (
                            Assignment(left_role, "copy", (right_role,)),
                            Assignment(right_role, "copy", (left_role,)),
                        )
                    ),
                    role_map,
                )

        if len(changed) == 2 and numeric is not None:
            losses = [key for key in changed if before[key] - after[key] == numeric]
            gains = [key for key in changed if after[key] - before[key] == numeric]
            if len(losses) == 1 and len(gains) == 1:
                source, destination = losses[0], gains[0]
                source_role, destination_role = role(source), role(destination)
                return (
                    LatentProgram(
                        (
                            Assignment(source_role, "sub_number"),
                            Assignment(destination_role, "add_number"),
                        )
                    ),
                    role_map,
                )

        if len(changed) != 1:
            raise ValueError(f"no compact latent program for changes: {changed}")
        target = changed[0]
        target_role = role(target)
        old, new = before[target], after[target]

        if numeric is not None and new == numeric:
            return LatentProgram((Assignment(target_role, "assign_number"),)), role_map
        if numeric is not None and new == old + numeric:
            return LatentProgram((Assignment(target_role, "add_number"),)), role_map
        if numeric is not None and new == old - numeric:
            return LatentProgram((Assignment(target_role, "sub_number"),)), role_map
        if numeric is not None and new == old * numeric:
            return LatentProgram((Assignment(target_role, "mul_number"),)), role_map
        if "倍" in event and old != 0 and new % old == 0 and new // old >= 2:
            return LatentProgram((Assignment(target_role, "mul_number"),)), role_map

        for source in before:
            if source == target:
                continue
            if new == before[source]:
                source_role = role(source)
                return (
                    LatentProgram((Assignment(target_role, "copy", (source_role,)),)),
                    role_map,
                )
            if new == old + before[source]:
                source_role = role(source)
                return (
                    LatentProgram(
                        (Assignment(target_role, "add_source", (source_role,)),)
                    ),
                    role_map,
                )
        raise ValueError(f"no exact expression explains {target}: {old} -> {new}")

    @staticmethod
    def _mask(
        text: str,
        entities: Iterable[str],
        role_map: Mapping[str, int] | None = None,
    ) -> str:
        output = text
        for entity in sorted(set(entities), key=len, reverse=True):
            replacement = (
                "＜対象＞"
                if role_map is None or entity not in role_map
                else f"＜役{chr(0x7532 + role_map[entity])}＞"
            )
            output = output.replace(entity, replacement)
        output = _NUMBER_RE.sub("＜数＞", output)
        return output.strip().rstrip("。！？!?")

    def _rebuild(self) -> None:
        all_program_sentences = [
            text for rows in self.program_texts.values() for text in rows
        ]
        self.encoder.fit((*self.unlabelled_sentences, *all_program_sentences))
        self.prototypes = {}
        for signature, rows in self.program_texts.items():
            merged: Counter[int] = Counter()
            used = 0
            for text in rows:
                vector = self.encoder.encode(text)
                if not vector:
                    continue
                used += 1
                for key, value in vector.items():
                    merged[key] += value
            self.prototypes[signature] = _normalise(merged) if used else {}
        empty = [name for name, vector in self.prototypes.items() if not vector]
        if empty:
            raise ValueError(f"empty program prototypes: {empty}")

    def learn_documents(
        self,
        documents: Iterable[str],
        *,
        unlabelled_sentences: Iterable[str] = (),
        reset: bool = False,
    ) -> int:
        if reset:
            self.program_texts.clear()
            self.programs.clear()
            self.unlabelled_sentences.clear()
            self.training_documents = 0
        self.unlabelled_sentences.extend(
            sentence for sentence in unlabelled_sentences if sentence.strip()
        )
        for document in documents:
            state: dict[str, int] = {}
            pending_event: str | None = None
            for sentence in self.split_sentences(document):
                facts = self.assertions(sentence)
                if facts:
                    if pending_event is None:
                        state.update(facts)
                    else:
                        after = dict(state)
                        after.update(facts)
                        program, role_map = self._program_from_transition(
                            pending_event, state, after
                        )
                        signature = program.signature
                        self.programs[signature] = program
                        self.program_texts[signature].append(
                            self._mask(pending_event, state, role_map)
                        )
                        state = after
                        pending_event = None
                    continue
                pending_event = sentence.strip().rstrip("。！？!?")
            if pending_event is not None:
                raise ValueError(
                    "training document ended with an event lacking an observed result"
                )
            self.training_documents += 1
        self._rebuild()
        return len(self.programs)

    def reset_world(self) -> None:
        self.world.clear()
        self.event_log.clear()

    def _candidate_role_maps(
        self, program: LatentProgram, text: str
    ) -> tuple[dict[str, int], ...]:
        mentions = self._entities_in_text(text, self.world)
        if len(mentions) < program.role_count:
            return ()
        rows = []
        for chosen in itertools.permutations(mentions, program.role_count):
            rows.append({entity: index for index, entity in enumerate(chosen)})
        return tuple(rows[:24])

    def infer_event(self, text: str) -> InferenceResult:
        if not self.world or not self.programs:
            return InferenceResult(
                None,
                (),
                0.0,
                0,
                0,
                "abstain-empty-world-or-programs",
            )
        best_by_signature: dict[str, tuple[float, dict[str, int]]] = {}
        reads = 0
        role_candidates = 0
        for signature, program in self.programs.items():
            for role_map in self._candidate_role_maps(program, text):
                role_candidates += 1
                masked = self._mask(text, self.world, role_map)
                vector = self.encoder.encode(masked)
                score = (
                    _cosine(vector, self.prototypes[signature]) if vector else 0.0
                )
                reads += len(vector) + len(self.prototypes[signature])
                current = best_by_signature.get(signature)
                if current is None or score > current[0]:
                    best_by_signature[signature] = (score, role_map)
        scored = sorted(
            (
                (score, signature, role_map)
                for signature, (score, role_map) in best_by_signature.items()
            ),
            key=lambda row: (-row[0], row[1], tuple(sorted(row[2].items()))),
        )
        self.last_candidates = role_candidates
        self.last_feature_reads = reads
        if not scored:
            return InferenceResult(
                None, (), 0.0, 0, reads, "abstain-no-role-mapping"
            )
        best_score, best_signature, best_map = scored[0]
        runner = scored[1][0] if len(scored) > 1 else 0.0
        margin = best_score - runner
        confidence = max(
            0.0, min(1.0, 0.70 * best_score + 0.30 * max(0.0, margin))
        )
        if (
            best_score < self.confidence_threshold
            or margin < self.margin_threshold
        ):
            return InferenceResult(
                None,
                (),
                confidence,
                role_candidates,
                reads,
                "abstain-ambiguous-event",
            )
        inverse = [""] * self.programs[best_signature].role_count
        for entity, role_index in best_map.items():
            inverse[role_index] = entity
        return InferenceResult(
            self.programs[best_signature],
            tuple(inverse),
            confidence,
            role_candidates,
            reads,
            "distributional-text-world-program",
        )

    @staticmethod
    def _apply(
        program: LatentProgram,
        roles: Sequence[str],
        text: str,
        world: Mapping[str, int],
    ) -> dict[str, int]:
        numbers = TextWorldLearner._numbers(text)
        number = numbers[-1] if numbers else None
        before = dict(world)
        after = dict(world)
        for row in program.assignments:
            destination = roles[row.destination_role]
            if row.expression == "assign_number":
                if number is None:
                    raise ValueError("program requires a number")
                value = number
            elif row.expression == "add_number":
                if number is None:
                    raise ValueError("program requires a number")
                value = before[destination] + number
            elif row.expression == "sub_number":
                if number is None:
                    raise ValueError("program requires a number")
                value = before[destination] - number
            elif row.expression == "mul_number":
                if number is None:
                    number = 2 if "倍" in text else None
                if number is None:
                    raise ValueError("program requires a number")
                value = before[destination] * number
            elif row.expression == "copy":
                value = before[roles[row.source_roles[0]]]
            elif row.expression == "add_source":
                value = before[destination] + before[roles[row.source_roles[0]]]
            else:
                raise ValueError(f"unsupported expression: {row.expression}")
            after[destination] = value
        return after

    def observe(self, sentence: str) -> str:
        clean = sentence.strip()
        facts = self.assertions(clean)
        if facts:
            for entity, value in facts.items():
                if entity not in self.world and len(self.world) >= self.max_entities:
                    raise ValueError("world entity budget exceeded")
                self.world[entity] = value
            return "状態を記憶しました。"
        result = self.infer_event(clean)
        if result.program is None:
            return "その出来事の意味をまだ確定できません。"
        before = dict(self.world)
        try:
            self.world = self._apply(
                result.program, result.role_entities, clean, self.world
            )
        except (KeyError, ValueError):
            return "必要な対象や数量が不足しています。"
        changed = tuple(
            key for key in self.world if self.world[key] != before.get(key)
        )
        self.event_log.append(
            {
                "text": clean.rstrip("。！？!?"),
                "changed": changed,
                "program": result.program.signature,
            }
        )
        return "出来事を反映しました。"

    def answer(self, question: str) -> str | None:
        text = question.strip().rstrip("。！？!?")
        mentions = self._entities_in_text(text, self.world)
        if ("一番多" in text or "最も多" in text) and self.world:
            entity = sorted(
                self.world, key=lambda key: (-self.world[key], key)
            )[0]
            return f"{entity}で、{self.world[entity]}個です。"
        if len(mentions) >= 2 and "どちらが多" in text:
            left, right = mentions[:2]
            if self.world[left] == self.world[right]:
                return "同じです。"
            return f"{left if self.world[left] > self.world[right] else right}です。"
        if len(mentions) >= 2 and "差" in text:
            return f"{abs(self.world[mentions[0]] - self.world[mentions[1]])}個です。"
        if len(mentions) >= 2 and "合計" in text:
            return f"{self.world[mentions[0]] + self.world[mentions[1]]}個です。"
        if mentions and ("理由" in text or "なぜ" in text):
            entity = mentions[0]
            for row in reversed(self.event_log):
                if entity in row["changed"]:
                    return f"「{row['text']}」という出来事を反映したためです。"
            return "現在の記録内には、その変化の原因がありません。"
        if mentions and (
            "いくつ" in text or "何個" in text or "現在" in text
        ):
            return f"{self.world[mentions[0]]}個です。"
        return None

    def chat(self, turn: str) -> str:
        if "?" in turn or "？" in turn or any(
            key in turn
            for key in (
                "いくつ",
                "何個",
                "どちら",
                "差",
                "合計",
                "一番多",
                "最も多",
                "理由",
                "なぜ",
            )
        ):
            answer = self.answer(turn)
            return (
                answer
                if answer is not None
                else "その質問には、今の内部状態だけでは答えられません。"
            )
        return self.observe(turn)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-text-world-v1",
            "confidence_threshold": self.confidence_threshold,
            "margin_threshold": self.margin_threshold,
            "max_entities": self.max_entities,
            "max_events": self.max_events,
            "training_documents": self.training_documents,
            "programs": {
                signature: [asdict(row) for row in program.assignments]
                for signature, program in self.programs.items()
            },
            "program_texts": self.program_texts,
            "unlabelled_sentences": self.unlabelled_sentences,
            "encoder": {
                "dimensions": self.encoder.dimensions,
                "maximum_df_ratio": self.encoder.maximum_df_ratio,
                "documents": self.encoder.documents,
                "active_ngrams": self.encoder.active_ngrams,
                "vectors": {
                    gram: {str(key): value for key, value in vector.items()}
                    for gram, vector in self.encoder.vectors.items()
                },
                "weights": self.encoder.weights,
            },
            "prototypes": {
                signature: {
                    str(key): value for key, value in vector.items()
                }
                for signature, vector in self.prototypes.items()
            },
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
    def from_bytes(cls, data: bytes) -> "TextWorldLearner":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            confidence_threshold=float(payload["confidence_threshold"]),
            margin_threshold=float(payload["margin_threshold"]),
            max_entities=int(payload["max_entities"]),
            max_events=int(payload["max_events"]),
        )
        model.training_documents = int(payload["training_documents"])
        model.programs = {
            signature: LatentProgram(
                tuple(
                    Assignment(
                        int(row["destination_role"]),
                        str(row["expression"]),
                        tuple(int(value) for value in row["source_roles"]),
                    )
                    for row in rows
                )
            )
            for signature, rows in payload["programs"].items()
        }
        model.program_texts = defaultdict(
            list,
            {
                str(key): list(value)
                for key, value in payload["program_texts"].items()
            },
        )
        model.unlabelled_sentences = list(payload["unlabelled_sentences"])
        encoder = payload["encoder"]
        model.encoder = DistributionalCharEncoder(
            dimensions=int(encoder["dimensions"]),
            maximum_df_ratio=float(encoder["maximum_df_ratio"]),
        )
        model.encoder.documents = int(encoder["documents"])
        model.encoder.active_ngrams = int(encoder["active_ngrams"])
        model.encoder.vectors = {
            gram: {int(key): float(value) for key, value in vector.items()}
            for gram, vector in encoder["vectors"].items()
        }
        model.encoder.weights = {
            str(gram): float(value)
            for gram, value in encoder.get("weights", {}).items()
        }
        model.prototypes = {
            signature: {
                int(key): float(value) for key, value in vector.items()
            }
            for signature, vector in payload["prototypes"].items()
        }
        return model
