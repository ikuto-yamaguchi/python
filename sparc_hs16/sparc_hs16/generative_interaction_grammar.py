from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence


BOS = "\u0002"
EOS = "\u0003"


def _stable_hash(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


@dataclass(frozen=True, slots=True)
class DialogueExample:
    context: tuple[str, ...]
    response: str


class GenerativeInteractionGrammar:
    """Bounded, non-neural variable-order dialogue generator.

    The model receives raw dialogue only. It has no task names, labels, answer
    candidates, topic dictionaries, external retrieval, or problem-specific
    branches. Reusable continuations are compressed into a variable-order
    character grammar and conditioned by a bounded dialogue-state signature.
    """

    def __init__(self, *, max_order: int = 8, state_buckets: int = 4096, max_edges: int = 250_000) -> None:
        if max_order < 1:
            raise ValueError("max_order must be positive")
        self.max_order = max_order
        self.state_buckets = state_buckets
        self.max_edges = max_edges
        self.edges: dict[tuple[int, str], Counter[str]] = defaultdict(Counter)
        self.global_edges: dict[str, Counter[str]] = defaultdict(Counter)
        self.response_starts: Counter[str] = Counter()
        self.training_examples = 0
        self.reads = 0

    def _state(self, context: Sequence[str]) -> int:
        joined = "\n".join(_normalize(turn) for turn in context[-6:])
        grams = []
        for size in (2, 3, 4):
            grams.extend(joined[i : i + size] for i in range(max(0, len(joined) - size + 1)))
        signature = "|".join(sorted(set(grams))[:96])
        return _stable_hash(signature) % self.state_buckets

    def observe(self, example: DialogueExample) -> None:
        state = self._state(example.context)
        response = _normalize(example.response)
        stream = BOS * self.max_order + response + EOS
        self.response_starts[response[:1] or EOS] += 1
        for position in range(self.max_order, len(stream)):
            token = stream[position]
            for order in range(1, self.max_order + 1):
                history = stream[position - order : position]
                self.edges[(state, history)][token] += 1
                self.global_edges[history][token] += 1
        self.training_examples += 1
        self._prune_if_needed()

    def fit(self, examples: Sequence[DialogueExample], *, seed: int = 0) -> None:
        order = list(range(len(examples)))
        random.Random(seed).shuffle(order)
        for index in order:
            self.observe(examples[index])

    def _edge_count(self) -> int:
        return sum(len(row) for row in self.edges.values()) + sum(len(row) for row in self.global_edges.values())

    def _prune_if_needed(self) -> None:
        if self._edge_count() <= self.max_edges:
            return
        scored: list[tuple[int, str, tuple[int, str] | str, str]] = []
        for key, row in self.edges.items():
            for token, count in row.items():
                scored.append((count, "local", key, token))
        for key, row in self.global_edges.items():
            for token, count in row.items():
                scored.append((count, "global", key, token))
        scored.sort(key=lambda row: (row[0], str(row[2]), row[3]))
        remove = max(1, len(scored) - self.max_edges)
        for _, scope, key, token in scored[:remove]:
            table = self.edges if scope == "local" else self.global_edges
            row = table[key]  # type: ignore[index]
            row.pop(token, None)
            if not row:
                table.pop(key, None)  # type: ignore[arg-type]

    def _distribution(self, state: int, output: str) -> Counter[str]:
        combined: Counter[str] = Counter()
        for order in range(self.max_order, 0, -1):
            history = (BOS * self.max_order + output)[-order:]
            local = self.edges.get((state, history))
            global_row = self.global_edges.get(history)
            if local:
                self.reads += len(local)
                weight = order * order * 2
                for token, count in local.items():
                    combined[token] += weight * count
            if global_row:
                self.reads += len(global_row)
                weight = order * order
                for token, count in global_row.items():
                    combined[token] += weight * count
            if combined and order <= 3:
                break
        return combined

    def generate(self, context: Sequence[str], *, seed: int = 0, max_chars: int = 160) -> str:
        state = self._state(context)
        output = ""
        rng = random.Random(seed ^ state)
        for _ in range(max_chars):
            row = self._distribution(state, output)
            if not row:
                break
            best = max(row.values())
            choices = sorted(token for token, score in row.items() if score == best)
            token = choices[rng.randrange(len(choices))]
            if token == EOS:
                break
            if token != BOS:
                output += token
        return output.strip()

    def continuation_nll(self, example: DialogueExample) -> float:
        state = self._state(example.context)
        output = ""
        total = 0.0
        count = 0
        for token in _normalize(example.response) + EOS:
            row = self._distribution(state, output)
            denom = sum(row.values()) + max(1, len(row))
            total -= math.log((row.get(token, 0) + 1) / denom)
            count += 1
            if token != EOS:
                output += token
        return total / max(1, count)

    def to_dict(self) -> dict:
        return {
            "format": "generative-interaction-grammar-v1",
            "max_order": self.max_order,
            "state_buckets": self.state_buckets,
            "max_edges": self.max_edges,
            "training_examples": self.training_examples,
            "edges": [
                [state, history, dict(row)] for (state, history), row in sorted(self.edges.items())
            ],
            "global_edges": [[history, dict(row)] for history, row in sorted(self.global_edges.items())],
        }

    def serialized_bytes(self) -> int:
        return len(json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    @classmethod
    def from_dict(cls, data: dict) -> "GenerativeInteractionGrammar":
        if data.get("format") != "generative-interaction-grammar-v1":
            raise ValueError("unsupported format")
        model = cls(
            max_order=int(data["max_order"]),
            state_buckets=int(data["state_buckets"]),
            max_edges=int(data["max_edges"]),
        )
        model.training_examples = int(data.get("training_examples", 0))
        for state, history, row in data.get("edges", []):
            model.edges[(int(state), str(history))] = Counter({str(k): int(v) for k, v in row.items()})
        for history, row in data.get("global_edges", []):
            model.global_edges[str(history)] = Counter({str(k): int(v) for k, v in row.items()})
        return model


def exact_or_semantic_anchor(output: str, required: Iterable[str]) -> bool:
    return all(fragment in output for fragment in required)
