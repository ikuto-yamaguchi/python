from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
import re
import zlib
from typing import Iterable, Mapping, Sequence

_TOKEN_RE = re.compile(r"[一-龠々ぁ-んァ-ヶーA-Za-z0-9_.]+")
_DEFAULT_STOPWORDS = frozenset(
    {
        "を",
        "に",
        "へ",
        "から",
        "の",
        "で",
        "と",
        "して",
        "する",
        "値",
        "数量",
        "在庫",
        "残高",
        "得点",
        "温度",
        "レベル",
        "資源",
        "ポイント",
        "個",
        "だけ",
    }
)


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text))


def _normalise(vector: Mapping[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm <= 0.0:
        return {}
    return {key: value / norm for key, value in vector.items()}


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


@dataclass(frozen=True)
class GroundedTransition:
    text: str
    before: Mapping[str, int]
    after: Mapping[str, int]


@dataclass(frozen=True)
class LatentPlan:
    operation: str
    target: str
    value: int
    destination: str = ""


@dataclass(frozen=True)
class PlanResult:
    plan: LatentPlan | None
    confidence: float
    mechanism: str
    candidates: int
    feature_reads: int


class SparseDistributionalLexicon:
    """Small PPMI lexicon learned from ordinary token co-occurrence."""

    def __init__(self, *, window: int = 4) -> None:
        self.window = window
        self.vectors: dict[str, dict[str, float]] = {}
        self.sentences = 0
        self.pair_events = 0

    def fit(self, sentences: Iterable[str]) -> "SparseDistributionalLexicon":
        pair_counts: Counter[tuple[str, str]] = Counter()
        target_counts: Counter[str] = Counter()
        context_counts: Counter[str] = Counter()
        total = 0.0
        self.sentences = 0
        for sentence in sentences:
            tokens = tokenize(sentence)
            if not tokens:
                continue
            self.sentences += 1
            for index, token in enumerate(tokens):
                lower = max(0, index - self.window)
                upper = min(len(tokens), index + self.window + 1)
                for other in range(lower, upper):
                    if other == index:
                        continue
                    context = tokens[other]
                    weight = 1.0 / abs(index - other)
                    pair_counts[(token, context)] += weight
                    target_counts[token] += weight
                    context_counts[context] += weight
                    total += weight
        self.pair_events = len(pair_counts)
        vectors: dict[str, dict[str, float]] = defaultdict(dict)
        for (token, context), count in pair_counts.items():
            denominator = target_counts[token] * context_counts[context]
            if denominator <= 0.0:
                continue
            ppmi = math.log(max(1e-12, count * total / denominator))
            if ppmi > 0.0:
                vectors[token][context] = ppmi
        self.vectors = {
            token: _normalise(vector) for token, vector in vectors.items()
        }
        return self

    def mean_vector(self, tokens: Iterable[str]) -> dict[str, float]:
        merged: dict[str, float] = defaultdict(float)
        used = 0
        for token in tokens:
            vector = self.vectors.get(token)
            if not vector:
                continue
            used += 1
            for key, value in vector.items():
                merged[key] += value
        if used == 0:
            return {}
        return _normalise(merged)

    def report(self) -> dict[str, int]:
        return {
            "sentences": self.sentences,
            "tokens": len(self.vectors),
            "pair_events": self.pair_events,
        }


class GroundedLatentProgramLearner:
    """Induces edit programs from before/after experience, then grounds raw text.

    Operation names are never supplied in demonstrations. They are derived from
    state edits, while language prototypes are learned from non-argument tokens.
    A separately learned distributional lexicon lets a withheld expression map
    to an existing latent operation through shared descriptive contexts.
    """

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.45,
        margin_threshold: float = 0.08,
        stopwords: Sequence[str] = tuple(_DEFAULT_STOPWORDS),
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        self.stopwords = frozenset(stopwords)
        self.lexicon = SparseDistributionalLexicon()
        self.prototypes: dict[str, dict[str, float]] = {}
        self.training_examples = 0
        self.last_feature_reads = 0

    @staticmethod
    def derive_plan(transition: GroundedTransition) -> LatentPlan:
        before = transition.before
        after = transition.after
        changed: list[tuple[str, int, int]] = []
        for key in sorted(set(before) | set(after)):
            old = int(before.get(key, 0))
            new = int(after.get(key, 0))
            if old != new:
                changed.append((key, new - old, new))
        numbers = [
            int(token) for token in tokenize(transition.text) if token.isdigit()
        ]
        if len(changed) == 2:
            negative = [row for row in changed if row[1] < 0]
            positive = [row for row in changed if row[1] > 0]
            if (
                len(negative) == 1
                and len(positive) == 1
                and abs(negative[0][1]) == positive[0][1]
            ):
                return LatentPlan(
                    "transfer",
                    negative[0][0],
                    positive[0][1],
                    destination=positive[0][0],
                )
        if len(changed) != 1:
            raise ValueError(
                f"transition is not representable by one latent edit: {changed}"
            )
        key, delta, new_value = changed[0]
        mentioned = numbers[-1] if numbers else None
        if mentioned is not None and new_value == mentioned and abs(delta) != mentioned:
            return LatentPlan("assign", key, new_value)
        if delta > 0:
            return LatentPlan("increase", key, delta)
        return LatentPlan("decrease", key, -delta)

    def _language_tokens(
        self,
        text: str,
        state_keys: Iterable[str],
    ) -> tuple[str, ...]:
        excluded = set(state_keys) | self.stopwords
        return tuple(
            token
            for token in tokenize(text)
            if token not in excluded and not token.isdigit()
        )

    def fit(
        self,
        transitions: Iterable[GroundedTransition],
        *,
        unlabelled_sentences: Iterable[str],
    ) -> int:
        rows = tuple(transitions)
        if not rows:
            raise ValueError("at least one grounded transition is required")
        self.lexicon.fit(unlabelled_sentences)
        operation_tokens: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            plan = self.derive_plan(row)
            operation_tokens[plan.operation].extend(
                self._language_tokens(row.text, row.before.keys())
            )
        self.prototypes = {
            operation: self.lexicon.mean_vector(tokens)
            for operation, tokens in operation_tokens.items()
        }
        if any(not vector for vector in self.prototypes.values()):
            missing = [
                name for name, vector in self.prototypes.items() if not vector
            ]
            raise ValueError(f"empty language prototypes: {missing}")
        self.training_examples = len(rows)
        return len(self.prototypes)

    def infer(self, text: str, before: Mapping[str, int]) -> PlanResult:
        language_tokens = self._language_tokens(text, before.keys())
        query = self.lexicon.mean_vector(language_tokens)
        if not query:
            return PlanResult(None, 0.0, "abstain-no-semantic-vector", 0, 0)
        scores = sorted(
            (
                (_cosine(query, prototype), operation)
                for operation, prototype in self.prototypes.items()
            ),
            reverse=True,
        )
        self.last_feature_reads = sum(
            len(self.prototypes[name]) for _, name in scores
        )
        best_score, best_operation = scores[0]
        runner_up = scores[1][0] if len(scores) > 1 else 0.0
        margin = best_score - runner_up
        confidence = max(0.0, min(1.0, 0.55 * best_score + 0.45 * margin))
        if best_score < self.confidence_threshold or margin < self.margin_threshold:
            return PlanResult(
                None,
                confidence,
                "abstain-ambiguous-latent-program",
                len(scores),
                self.last_feature_reads,
            )
        tokens = tokenize(text)
        keys = [key for key in before if key in tokens]
        numbers = [int(token) for token in tokens if token.isdigit()]
        value = numbers[-1] if numbers else 0
        if best_operation == "transfer":
            if len(keys) < 2 or value <= 0:
                return PlanResult(
                    None,
                    confidence,
                    "abstain-missing-arguments",
                    len(scores),
                    self.last_feature_reads,
                )
            plan = LatentPlan(
                best_operation,
                keys[0],
                value,
                destination=keys[1],
            )
        else:
            if not keys or value < 0:
                return PlanResult(
                    None,
                    confidence,
                    "abstain-missing-arguments",
                    len(scores),
                    self.last_feature_reads,
                )
            plan = LatentPlan(best_operation, keys[0], value)
        return PlanResult(
            plan,
            confidence,
            "distributional-grounded-latent-program",
            len(scores),
            self.last_feature_reads,
        )

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-latent-program-v1",
            "confidence_threshold": self.confidence_threshold,
            "margin_threshold": self.margin_threshold,
            "stopwords": sorted(self.stopwords),
            "training_examples": self.training_examples,
            "lexicon": self.lexicon.vectors,
            "lexicon_sentences": self.lexicon.sentences,
            "lexicon_pair_events": self.lexicon.pair_events,
            "prototypes": self.prototypes,
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
    def from_bytes(cls, data: bytes) -> "GroundedLatentProgramLearner":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            confidence_threshold=float(payload["confidence_threshold"]),
            margin_threshold=float(payload["margin_threshold"]),
            stopwords=tuple(payload["stopwords"]),
        )
        model.training_examples = int(payload["training_examples"])
        model.lexicon.vectors = {
            str(token): {
                str(key): float(value) for key, value in vector.items()
            }
            for token, vector in payload["lexicon"].items()
        }
        model.lexicon.sentences = int(payload["lexicon_sentences"])
        model.lexicon.pair_events = int(payload["lexicon_pair_events"])
        model.prototypes = {
            str(name): {
                str(key): float(value) for key, value in vector.items()
            }
            for name, vector in payload["prototypes"].items()
        }
        return model


@dataclass(frozen=True)
class StateProposalResult:
    cue_pair: tuple[str, str] | None
    baseline_bits: float
    latent_bits: float
    description_length_gain: float
    candidates: int
    canonical_signature: tuple[int, int] | None


class PredictiveStateInducer:
    """Proposes an unlabelled last-seen state variable using MDL.

    It searches token pairs without knowing cue names. For every pair it asks
    whether "which token occurred most recently" compresses outcomes following a
    query token. The winning pair becomes a reusable two-state latent program.
    """

    def __init__(self, *, max_candidates: int = 256) -> None:
        self.max_candidates = max_candidates

    @staticmethod
    def _entropy_bits(counts: Mapping[str, int]) -> float:
        total = sum(counts.values())
        if total <= 0:
            return 0.0
        return -sum(
            count / total * math.log2(count / total)
            for count in counts.values()
            if count
        )

    def fit(
        self,
        sequence: Sequence[str],
        *,
        query_token: str,
    ) -> StateProposalResult:
        outcomes: list[tuple[int, str]] = []
        for index in range(len(sequence) - 1):
            if sequence[index] == query_token:
                outcomes.append((index, sequence[index + 1]))
        if not outcomes:
            raise ValueError("sequence contains no query outcomes")
        baseline_counts = Counter(outcome for _, outcome in outcomes)
        baseline_bits = len(outcomes) * self._entropy_bits(baseline_counts)
        vocabulary = sorted(set(sequence) - {query_token} - set(baseline_counts))
        pairs: list[tuple[str, str]] = []
        for left_index, left in enumerate(vocabulary):
            for right in vocabulary[left_index + 1 :]:
                pairs.append((left, right))
                if len(pairs) >= self.max_candidates:
                    break
            if len(pairs) >= self.max_candidates:
                break
        best_pair: tuple[str, str] | None = None
        best_bits = baseline_bits
        best_signature: tuple[int, int] | None = None
        for pair in pairs:
            state_counts = {0: Counter(), 1: Counter(), -1: Counter()}
            last = {pair[0]: -1, pair[1]: -1}
            for index, token in enumerate(sequence):
                if token in last:
                    last[token] = index
                if token != query_token or index + 1 >= len(sequence):
                    continue
                if last[pair[0]] < 0 and last[pair[1]] < 0:
                    state = -1
                else:
                    state = 0 if last[pair[0]] > last[pair[1]] else 1
                state_counts[state][sequence[index + 1]] += 1
            data_bits = sum(
                sum(counts.values()) * self._entropy_bits(counts)
                for counts in state_counts.values()
            )
            model_bits = math.log2(max(2, len(vocabulary))) * 2 + 2.0
            total_bits = data_bits + model_bits
            if total_bits < best_bits:
                best_bits = total_bits
                best_pair = pair
                dominant: list[int] = []
                for state in (0, 1):
                    counts = state_counts[state]
                    if not counts:
                        dominant.append(-1)
                        continue
                    outcome = sorted(
                        counts.items(), key=lambda item: (-item[1], item[0])
                    )[0][0]
                    dominant.append(sorted(baseline_counts).index(outcome))
                best_signature = tuple(sorted(dominant))
        return StateProposalResult(
            best_pair,
            baseline_bits,
            best_bits,
            baseline_bits - best_bits,
            len(pairs),
            best_signature,
        )
