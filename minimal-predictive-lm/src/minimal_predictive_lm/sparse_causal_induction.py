from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Iterable, Mapping


_WORD = re.compile(r"[a-z0-9][a-z0-9'-]*")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _question(text: str) -> str:
    body = text.split("Options:", 1)[0]
    matches = re.findall(
        r"(?is)(?:^|[.!?][\"']?\s+)((?:did|does|was|were|is|do|could|would)\b[^?]*\?)",
        body,
    )
    return _normalise(matches[-1]) if matches else ""


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(_WORD.findall(_normalise(text)))


def _ngrams(tokens: tuple[str, ...], width: int) -> Iterable[str]:
    for index in range(0, len(tokens) - width + 1):
        yield "_".join(tokens[index : index + width])


def causal_features(prompt: str) -> Counter[str]:
    low = _normalise(prompt.split("Options:", 1)[0])
    query = _question(prompt)
    context = low[: max(0, len(low) - len(query))]
    q_tokens = _tokens(query)
    c_tokens = _tokens(context)
    output: Counter[str] = Counter()

    for prefix, rows in (("Q", q_tokens), ("C", c_tokens[-220:])):
        for width in (1, 2, 3):
            for gram in _ngrams(rows, width):
                output[f"{prefix}:W{width}:{gram}"] += 1
    for token in q_tokens:
        padded = f"^{token}$"
        for width in (3, 4, 5):
            for index in range(len(padded) - width + 1):
                output[f"Q:C{width}:{padded[index:index + width]}"] += 1

    cue_groups: Mapping[str, tuple[str, ...]] = {
        "MECH_AND": ("if both", "only if", "both together", "and the coin", "requires both"),
        "MECH_OR": ("if either", "if anyone", "at least one", "only one is needed", "or the spinner"),
        "ACCIDENT": ("accidentally", "by accident", "slips", "went wild", "loses balance", "no control"),
        "CONTROL": ("decided to", "pulled the trigger", "gave the order", "carried out", "implemented"),
        "FORESEEN": ("will also", "would definitely", "realizes that", "knowing that", "does not care", "as expected"),
        "DUTY": ("responsible for", "supposed to", "required to", "must ", "instructed"),
        "NO_DUTY": ("not responsible", "did not notice", "unaware", "unbeknownst"),
        "VIOLATION": ("not supposed", "violating", "disobey", "ignore the signal", "not permitted"),
        "NORMAL": ("as usual", "usually", "normally", "permitted", "allowed", "follows the signal"),
        "RARE": ("very unlikely", "amazingly", "surprisingly", "unexpectedly"),
        "OMISSION": ("did not", "does not", "not putting", "not changing", "left it"),
        "EARLY": ("first", "right at the beginning", "already", "before"),
        "LATE": ("later", "right at the end", "at the buzzer", "afterwards"),
        "INTERVENE": ("drunk driver", "wrong medication", "fatal burns", "cardiac arrest", "died minutes after"),
        "EQUIVALENT": ("both of these", "either choice", "regardless of which", "same outcome"),
    }
    active_cues: list[str] = []
    for name, cues in cue_groups.items():
        count = sum(low.count(cue) for cue in cues)
        if count:
            output[f"S:{name}"] = count
            active_cues.append(name)

    if query:
        if "intentional" in query:
            output["QTYPE:INTENT"] = 1
        elif any(row in query for row in ("not putting", "did not", "not changing", "did not change")):
            output["QTYPE:OMISSION"] = 1
        else:
            output["QTYPE:CAUSE"] = 1
        if any(row in query for row in ("later", "second", "at the end", "layup")):
            output["QROLE:LATE"] = 1
        if any(row in query for row in ("first", "beginning", "earlier")):
            output["QROLE:EARLY"] = 1
        if any(row in query for row in ("choice", "selection", "decided on")):
            output["QROLE:CHOICE"] = 1
        if any(row in query for row in ("job", "background", "generosity", "delay", "relocation")):
            output["QROLE:BACKGROUND"] = 1
        if any(row in query for row in ("wrong medication", "driver", "poison", "shot", "direct")):
            output["QROLE:DIRECT"] = 1

    for cue in active_cues:
        for qword in q_tokens:
            if len(qword) >= 4:
                output[f"X:{cue}:{qword}"] += 1
    return output


@dataclass(frozen=True)
class CausalTrainingExample:
    prompt: str
    operator: str
    answer: str


@dataclass(frozen=True)
class Prototype:
    operator: str
    answer: str
    weights: tuple[tuple[str, float], ...]
    norm: float
    examples: int


@dataclass(frozen=True)
class SparseCausalPrediction:
    answer: str | None
    operator: str | None
    score: float
    margin: float
    candidates: int
    feature_reads: int


class SparseCausalPrototypeModel:
    def __init__(
        self,
        prototypes: tuple[Prototype, ...],
        postings: Mapping[str, tuple[int, ...]],
        *,
        minimum_score: float = 0.12,
        minimum_margin: float = 0.01,
    ) -> None:
        self.prototypes = prototypes
        self.postings = dict(postings)
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin
        self.description_bits = len(
            json.dumps(
                {
                    "prototypes": [
                        {
                            "operator": row.operator,
                            "answer": row.answer,
                            "weights": row.weights,
                            "norm": row.norm,
                        }
                        for row in prototypes
                    ],
                    "minimum_score": minimum_score,
                    "minimum_margin": minimum_margin,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ) * 8
        self.benchmark_task_name_branches = 0
        self.domain_specific_handlers = 0

    def predict(self, prompt: str) -> SparseCausalPrediction:
        features = causal_features(prompt)
        candidates: set[int] = set()
        reads = 0
        for feature in features:
            posting = self.postings.get(feature, ())
            candidates.update(posting)
            reads += 1 + len(posting)
        if not candidates:
            return SparseCausalPrediction(None, None, 0.0, 0.0, 0, reads)

        scores: list[tuple[float, int]] = []
        for index in candidates:
            proto = self.prototypes[index]
            dot = 0.0
            for feature, weight in proto.weights:
                value = features.get(feature)
                if value:
                    dot += weight * value
                reads += 1
            feature_norm = math.sqrt(sum(value * value for value in features.values())) or 1.0
            score = dot / (proto.norm * feature_norm) if proto.norm else 0.0
            scores.append((score, index))
        scores.sort(reverse=True)
        best_score, best_index = scores[0]
        best = self.prototypes[best_index]
        opposite = max(
            (score for score, index in scores if self.prototypes[index].answer != best.answer),
            default=0.0,
        )
        margin = best_score - opposite
        if best_score < self.minimum_score or margin < self.minimum_margin:
            return SparseCausalPrediction(None, None, best_score, margin, len(candidates), reads)
        return SparseCausalPrediction(
            best.answer,
            best.operator,
            best_score,
            margin,
            len(candidates),
            reads,
        )


def train_sparse_causal_prototypes(
    examples: Iterable[CausalTrainingExample],
    *,
    maximum_features_per_prototype: int = 384,
) -> SparseCausalPrototypeModel:
    rows = tuple(examples)
    if not rows:
        raise ValueError("causal prototype training requires examples")
    grouped: dict[tuple[str, str], list[Counter[str]]] = defaultdict(list)
    document_frequency: Counter[str] = Counter()
    for row in rows:
        features = causal_features(row.prompt)
        grouped[(row.operator, row.answer)].append(features)
        document_frequency.update(features.keys())

    prototypes: list[Prototype] = []
    total = len(rows)
    for (operator, answer), vectors in sorted(grouped.items()):
        counts: Counter[str] = Counter()
        for vector in vectors:
            counts.update(vector)
        weighted: list[tuple[str, float]] = []
        for feature, count in counts.items():
            idf = math.log((1 + total) / (1 + document_frequency[feature])) + 1.0
            weighted.append((feature, (count / len(vectors)) * idf))
        weighted.sort(key=lambda item: (-abs(item[1]), item[0]))
        selected = tuple(weighted[:maximum_features_per_prototype])
        norm = math.sqrt(sum(weight * weight for _feature, weight in selected)) or 1.0
        prototypes.append(Prototype(operator, answer, selected, norm, len(vectors)))

    postings: dict[str, list[int]] = defaultdict(list)
    for index, proto in enumerate(prototypes):
        for feature, _weight in proto.weights:
            postings[feature].append(index)
    return SparseCausalPrototypeModel(
        tuple(prototypes),
        {feature: tuple(indices) for feature, indices in postings.items()},
    )
