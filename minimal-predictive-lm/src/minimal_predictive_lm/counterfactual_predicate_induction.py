from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence


def _grams(text: str, n: int = 2) -> set[str]:
    value = "".join(text.split())
    return {value[i:i+n] for i in range(max(0, len(value)-n+1))}


@dataclass(frozen=True, slots=True)
class Episode:
    context: tuple[str, ...]
    latent: str
    clarification: str
    future: tuple[str, ...]


class CounterfactualPredicateInducer:
    """Non-neural future-equivalence predicate inducer.

    Episodes are grouped only when their later interaction traces match.  A
    clarification act is anti-unified inside each future-equivalence class.
    There are no topic dictionaries, neural weights, answer candidates, RAG,
    or task-specific solvers.
    """

    def __init__(self, max_predicates: int = 128, read_limit: int = 32) -> None:
        self.max_predicates = max_predicates
        self.read_limit = read_limit
        self.rows: dict[str, list[Episode]] = defaultdict(list)
        self.schemas: dict[str, str] = {}
        self.latent_to_signature: dict[str, str] = {}
        self.reads = 0

    @staticmethod
    def _signature(episode: Episode) -> str:
        payload = "|".join(episode.future)
        return hashlib.blake2b(payload.encode("utf-8"), digest_size=8).hexdigest()

    @staticmethod
    def _anti_unify(texts: Sequence[str]) -> str:
        if not texts:
            return ""
        prefix = texts[0]
        for text in texts[1:]:
            i = 0
            while i < min(len(prefix), len(text)) and prefix[i] == text[i]:
                i += 1
            prefix = prefix[:i]
        suffix = texts[0]
        for text in texts[1:]:
            i = 0
            while i < min(len(suffix), len(text)) and suffix[-1-i] == text[-1-i]:
                i += 1
            suffix = suffix[len(suffix)-i:] if i else ""
        if len(prefix) + len(suffix) >= min(map(len, texts)):
            return texts[0]
        middles = []
        for text in texts:
            end = len(text)-len(suffix) if suffix else len(text)
            middles.append(text[len(prefix):end])
        return prefix + min(middles, key=len) + suffix

    def fit(self, episodes: Sequence[Episode]) -> None:
        grouped: dict[str, list[Episode]] = defaultdict(list)
        for episode in episodes:
            grouped[self._signature(episode)].append(episode)
        for signature, rows in list(grouped.items())[:self.max_predicates]:
            self.rows[signature] = rows
            self.schemas[signature] = self._anti_unify([row.clarification for row in rows])
        self.latent_to_signature = {
            episode.latent: self._signature(episode) for episode in episodes
        }

    def infer_candidates(self, context: Sequence[str]) -> tuple[str, ...]:
        observed = _grams("|".join(context[-4:]))
        scores: list[tuple[float, str]] = []
        for signature, rows in self.rows.items():
            self.reads += 1
            best = 0.0
            for episode in rows[:8]:
                remembered = _grams("|".join(episode.context))
                union = len(observed | remembered)
                best = max(best, len(observed & remembered) / union if union else 0.0)
            scores.append((best, signature))
        scores.sort(reverse=True)
        return tuple(signature for _, signature in scores[:self.read_limit])

    def clarify(self, candidates: Sequence[str]) -> str:
        if not candidates:
            return "確認できません。"
        if len(candidates) == 1:
            return self.schemas.get(candidates[0], "確認できません。")
        left = self.schemas.get(candidates[0], "")
        right = self.schemas.get(candidates[1], "")
        if not left or not right:
            return "確認できません。"
        return left.rstrip("？?。") + "、" + right

    def serialized_bytes(self) -> int:
        payload = {
            "schemas": self.schemas,
            "rows": {
                signature: [
                    {"context": row.context, "clarification": row.clarification, "future": row.future}
                    for row in rows
                ]
                for signature, rows in self.rows.items()
            },
        }
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
