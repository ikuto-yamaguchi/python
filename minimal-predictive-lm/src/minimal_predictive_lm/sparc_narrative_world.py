from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import pickle
import re
import zlib
from typing import Iterable, Mapping, Sequence

_SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_NUMBER_RE = re.compile(r"-?\d+")
_PROPERTY = r"(?:在庫|得点|温度|残高|数量|値|個数)"
_OBS_PATTERNS = (
    re.compile(rf"^(?P<entity>.+?)の{_PROPERTY}は(?P<value>-?\d+)(?:だった|である|になった|になりました|です|となった|を記録した)?$"),
)
_QUESTION_PATTERNS = (
    re.compile(rf"(?P<entity>.+?)の{_PROPERTY}は(?:いくつ|何(?:点|度|個)?)(?:ですか|だ|でしょうか)?"),
    re.compile(r"(?P<entity>.+?)は(?:いくつ|何(?:点|度|個)?)(?:ですか|だ|でしょうか)?"),
)
_PUNCT_RE = re.compile(r"[、。！？!?；：:\s]+")


def split_sentences(text: str) -> tuple[str, ...]:
    return tuple(
        cleaned
        for match in _SENTENCE_RE.findall(text)
        if (cleaned := match.strip().rstrip("。！？!?"))
    )


def char_ngrams(text: str, lo: int = 2, hi: int = 6) -> set[str]:
    text = _PUNCT_RE.sub("", text)
    text = _NUMBER_RE.sub("数", text)
    return {
        text[i : i + width]
        for width in range(lo, hi + 1)
        for i in range(max(0, len(text) - width + 1))
    }


def cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def normalise(values: Mapping[str, float], limit: int = 512) -> dict[str, float]:
    rows = sorted(values.items(), key=lambda row: (-abs(row[1]), row[0]))[:limit]
    norm = math.sqrt(sum(value * value for _, value in rows))
    return {} if norm <= 0.0 else {key: value / norm for key, value in rows}


@dataclass(frozen=True)
class Atom:
    target: int
    expression: str


@dataclass(frozen=True)
class Program:
    atoms: tuple[Atom, ...]


@dataclass(frozen=True)
class NarrativeAnswer:
    answer: int | None
    entity: str | None
    state: Mapping[str, int]
    confidence: float
    mechanism: str
    applied_events: int
    trace: tuple[str, ...]


@dataclass(frozen=True)
class TrainingTransition:
    event: str
    before: Mapping[str, int]
    after: Mapping[str, int]


def parse_observation(sentence: str) -> tuple[str, int] | None:
    sentence = sentence.strip()
    for pattern in _OBS_PATTERNS:
        match = pattern.fullmatch(sentence)
        if match:
            entity = match.group("entity").strip("、。 ")
            return entity, int(match.group("value"))
    return None


def parse_question(sentence: str) -> str | None:
    for pattern in _QUESTION_PATTERNS:
        match = pattern.search(sentence)
        if match:
            return match.group("entity").strip("、。 ")
    return None


def roles(text: str, state: Mapping[str, int], focus: str | None = None) -> tuple[str, ...]:
    found = [(text.find(key), key) for key in state if text.find(key) >= 0]
    found.sort()
    ordered = [key for _, key in found]
    if not ordered and focus in state:
        ordered.append(focus)
    return tuple(ordered)


def numbers(text: str, entities: Iterable[str] = ()) -> tuple[int, ...]:
    masked = text
    for entity in sorted(set(entities), key=len, reverse=True):
        masked = masked.replace(entity, "対象")
    return tuple(int(item) for item in _NUMBER_RE.findall(masked))


def eval_expr(expr: str, old: Sequence[int], nums: Sequence[int]) -> int | None:
    parts = expr.split(":")
    op = parts[0]
    try:
        if op == "old":
            return old[int(parts[1])]
        if op == "const":
            return nums[int(parts[1])]
        if op in {"addc", "subc", "mulc", "divc"}:
            left = old[int(parts[1])]
            right = nums[int(parts[2])]
            if op == "addc":
                return left + right
            if op == "subc":
                return left - right
            if op == "mulc":
                return left * right
            return left // right if right else None
        left = old[int(parts[1])]
        right = old[int(parts[2])]
        if op == "addr":
            return left + right
        if op == "subr":
            return left - right
        if op == "maxr":
            return max(left, right)
        if op == "minr":
            return min(left, right)
    except (IndexError, ValueError):
        return None
    return None


def expression_candidates(target: int, old: Sequence[int], nums: Sequence[int], wanted: int) -> list[tuple[float, str]]:
    candidates: list[tuple[float, str]] = []
    for role, value in enumerate(old):
        if role != target and value == wanted:
            candidates.append((1.0, f"old:{role}"))
    for index, number in enumerate(nums):
        if number == wanted:
            candidates.append((1.05, f"const:{index}"))
    for role, value in enumerate(old):
        for index, number in enumerate(nums):
            formulas = (
                (1.15 if role == target else 2.1, f"addc:{role}:{index}", value + number),
                (1.15 if role == target else 2.1, f"subc:{role}:{index}", value - number),
                (1.25 if role == target else 2.2, f"mulc:{role}:{index}", value * number),
                (1.35 if role == target else 2.3, f"divc:{role}:{index}", value // number if number else None),
            )
            for cost, expression, result in formulas:
                if result == wanted:
                    candidates.append((cost, expression))
        for other, other_value in enumerate(old):
            if role == other:
                continue
            for cost, expression, result in (
                (1.6, f"addr:{role}:{other}", value + other_value),
                (1.7, f"subr:{role}:{other}", value - other_value),
                (1.8, f"maxr:{role}:{other}", max(value, other_value)),
                (1.8, f"minr:{role}:{other}", min(value, other_value)),
            ):
                if result == wanted:
                    candidates.append((cost, expression))
    return sorted(candidates, key=lambda row: (row[0], row[1]))


def derive_program(row: TrainingTransition, focus: str | None = None) -> Program:
    ordered = roles(row.event, row.before, focus)
    if not ordered:
        raise ValueError(f"event has no resolvable entity: {row.event}")
    old = tuple(int(row.before[key]) for key in ordered)
    nums = numbers(row.event, row.before)
    atoms: list[Atom] = []
    for target, key in enumerate(ordered):
        wanted = int(row.after[key])
        if wanted == old[target]:
            continue
        choices = expression_candidates(target, old, nums, wanted)
        if not choices:
            raise ValueError(f"cannot derive event program: {row}")
        atoms.append(Atom(target, choices[0][1]))
    if not atoms:
        raise ValueError(f"event did not change state: {row.event}")
    return Program(tuple(atoms))


def apply_program(program: Program, event: str, state: Mapping[str, int], focus: str | None) -> dict[str, int] | None:
    ordered = roles(event, state, focus)
    if not ordered:
        return None
    old = tuple(int(state[key]) for key in ordered)
    nums = numbers(event, state)
    updated = dict(state)
    for atom in program.atoms:
        if atom.target >= len(ordered):
            return None
        value = eval_expr(atom.expression, old, nums)
        if value is None:
            return None
        updated[ordered[atom.target]] = value
    return updated


class NarrativeWorldLearner:
    """Learns executable world updates from raw Japanese narrative strings."""

    def __init__(self, *, threshold: float = 0.15, margin: float = 0.01, max_candidates: int = 12) -> None:
        self.threshold = threshold
        self.margin = margin
        self.max_candidates = max_candidates
        self.feature_sums: dict[Program, Counter[str]] = defaultdict(Counter)
        self.program_counts: Counter[Program] = Counter()
        self.prototypes: dict[Program, dict[str, float]] = {}
        self.postings: dict[str, set[Program]] = defaultdict(set)
        self.training_documents = 0
        self.training_events = 0
        self.last_candidates = 0
        self.last_reads = 0
        self.state: dict[str, int] = {}
        self.focus: str | None = None
        self.trace: list[str] = []

    @staticmethod
    def mask_event(text: str, entities: Iterable[str]) -> str:
        masked = text
        for entity in sorted(set(entities), key=len, reverse=True):
            masked = masked.replace(entity, "対象")
        return _NUMBER_RE.sub("数", masked)

    @staticmethod
    def _extract_transitions(document: str) -> tuple[TrainingTransition, ...]:
        state: dict[str, int] = {}
        pending_event: str | None = None
        before_event: dict[str, int] | None = None
        focus: str | None = None
        transitions: list[TrainingTransition] = []

        def flush() -> None:
            nonlocal pending_event, before_event
            if pending_event is None or before_event is None:
                return
            if state != before_event:
                transitions.append(TrainingTransition(pending_event, dict(before_event), dict(state)))
            pending_event = None
            before_event = None

        for sentence in split_sentences(document):
            if parse_question(sentence) is not None:
                flush()
                continue
            observation = parse_observation(sentence)
            if observation is not None:
                entity, value = observation
                state[entity] = value
                focus = entity
                continue
            flush()
            pending_event = sentence
            before_event = dict(state)
            event_roles = roles(sentence, state, focus)
            if event_roles:
                focus = event_roles[-1]
        flush()
        return tuple(transitions)

    def learn_documents(self, documents: Iterable[str], *, reset: bool = False) -> int:
        if reset:
            self.feature_sums.clear()
            self.program_counts.clear()
            self.prototypes.clear()
            self.postings.clear()
            self.training_documents = 0
            self.training_events = 0
        rows = tuple(documents)
        for document in rows:
            for transition in self._extract_transitions(document):
                event_roles = roles(transition.event, transition.before)
                focus = event_roles[-1] if event_roles else next(iter(transition.before), None)
                program = derive_program(transition, focus)
                features = char_ngrams(self.mask_event(transition.event, transition.before))
                self.feature_sums[program].update(features)
                self.program_counts[program] += 1
                self.training_events += 1
            self.training_documents += 1
        self._rebuild_index()
        return len(self.prototypes)

    def _rebuild_index(self) -> None:
        self.prototypes.clear()
        self.postings.clear()
        total_documents = max(1, self.training_events)
        feature_df: Counter[str] = Counter()
        for counts in self.feature_sums.values():
            feature_df.update(counts.keys())
        for program, counts in self.feature_sums.items():
            weighted = {
                feature: math.log1p(count) * (math.log((total_documents + 1) / (feature_df[feature] + 1)) + 1.0)
                for feature, count in counts.items()
            }
            prototype = normalise(weighted, 384)
            self.prototypes[program] = prototype
            for feature, _ in sorted(prototype.items(), key=lambda row: (-abs(row[1]), row[0]))[:96]:
                self.postings[feature].add(program)

    def _infer_event(self, event: str) -> tuple[Program | None, float, str]:
        features = char_ngrams(self.mask_event(event, self.state))
        votes: Counter[Program] = Counter()
        reads = 0
        for feature in features:
            posting = self.postings.get(feature, ())
            for program in posting:
                votes[program] += 1.0 / max(1, len(posting))
                reads += 1
        candidates = sorted(
            votes or Counter(self.prototypes),
            key=lambda program: (-votes[program], -self.program_counts[program], str(program)),
        )[: self.max_candidates]
        query = normalise({feature: 1.0 for feature in features}, 384)
        scores: list[tuple[float, Program]] = []
        for program in candidates:
            reads += min(len(query), len(self.prototypes[program]))
            scores.append((cosine(query, self.prototypes[program]), program))
        scores.sort(key=lambda row: (-row[0], str(row[1])))
        self.last_candidates = len(scores)
        self.last_reads = reads
        if not scores:
            return None, 0.0, "abstain-no-program"
        best_score, best = scores[0]
        second = scores[1][0] if len(scores) > 1 else 0.0
        gap = best_score - second
        confidence = max(0.0, min(1.0, 0.65 * best_score + 0.35 * gap))
        if best_score < self.threshold or gap < self.margin:
            return None, confidence, "abstain-ambiguous-event"
        return best, confidence, "learned-narrative-program"

    def reset_session(self) -> None:
        self.state = {}
        self.focus = None
        self.trace = []

    def observe(self, text: str) -> NarrativeAnswer:
        answer_entity: str | None = None
        confidence = 1.0
        applied = 0
        mechanism = "state-observation"
        for sentence in split_sentences(text):
            question_entity = parse_question(sentence)
            if question_entity is not None:
                answer_entity = question_entity
                continue
            observation = parse_observation(sentence)
            if observation is not None:
                entity, value = observation
                self.state[entity] = value
                self.focus = entity
                self.trace.append(f"観測:{entity}={value}")
                continue
            program, event_confidence, event_mechanism = self._infer_event(sentence)
            confidence = min(confidence, event_confidence)
            if program is None:
                mechanism = event_mechanism
                self.trace.append(f"棄権:{sentence}")
                continue
            updated = apply_program(program, sentence, self.state, self.focus)
            if updated is None:
                mechanism = "abstain-unresolved-arguments"
                self.trace.append(f"棄権:{sentence}")
                continue
            mentioned = roles(sentence, self.state, self.focus)
            if mentioned:
                self.focus = mentioned[-1]
            self.state = updated
            applied += 1
            mechanism = event_mechanism
            self.trace.append(f"適用:{sentence}:{program}")
        if answer_entity is None:
            return NarrativeAnswer(None, None, dict(self.state), confidence, mechanism, applied, tuple(self.trace))
        value = self.state.get(answer_entity)
        return NarrativeAnswer(
            value,
            answer_entity,
            dict(self.state),
            confidence if value is not None else 0.0,
            mechanism if value is not None else "abstain-unknown-entity",
            applied,
            tuple(self.trace),
        )

    def respond(self, text: str) -> str:
        result = self.observe(text)
        if result.entity is None:
            return "内容を内部状態に反映しました。"
        if result.answer is None:
            return "その情報だけでは答えを確定できません。"
        return f"{result.entity}は{result.answer}です。"

    def to_bytes(self) -> bytes:
        return zlib.compress(pickle.dumps(self, protocol=5), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "NarrativeWorldLearner":
        model = pickle.loads(zlib.decompress(data))
        if not isinstance(model, cls):
            raise TypeError("invalid narrative world model")
        return model

    def report(self) -> dict[str, object]:
        return {
            "programs": len(self.prototypes),
            "training_documents": self.training_documents,
            "training_events": self.training_events,
            "serialized_bytes": len(self.to_bytes()),
            "operation_names_supplied": False,
            "explicit_state_maps_supplied_to_training_api": False,
            "whitespace_tokenizer_used": False,
            "morphological_dictionary_used": False,
        }
