from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

from .sparc_abstraction import (
    SPARCHS9Model as _BaseHS9Model,
    SparseAbstractionMemory as _BaseAbstractionMemory,
)
from .sparc_episodic import SPARCHS8Model
from .sparc_language import ReplyResult


class SparseAbstractionMemory(_BaseAbstractionMemory):
    """Topic-centred abstraction that keeps the queried subject in the summary."""

    def summarize(self, topic: str, *, base: SPARCHS8Model) -> ReplyResult | None:
        local_ids = [
            episode_id
            for episode_id in self.subject_claims.get(topic, ())
            if episode_id < len(base.episodic.episodes)
            and base.episodic.episodes[episode_id].active
        ]
        if not local_ids:
            return super().summarize(topic, base=base)

        statements: list[str] = []
        source_ids: list[str] = []
        inspected = 0
        for episode_id in local_ids[:8]:
            episode = base.episodic.episodes[episode_id]
            if episode.source_id not in source_ids:
                source_ids.append(episode.source_id)
            if not episode.claim_relation or not episode.claim_value:
                statements.append(episode.sentence)
                continue
            key = f"{episode.claim_relation}\u241f{episode.claim_value}"
            peers = [topic]
            for peer_id in self.abstraction_episodes.get(key, ())[:32]:
                inspected += 1
                peer = base.episodic.episodes[peer_id]
                if not peer.active or not peer.claim_subject:
                    continue
                if peer.claim_subject not in peers:
                    peers.append(peer.claim_subject)
                if peer.source_id not in source_ids:
                    source_ids.append(peer.source_id)
                if len(peers) >= 4:
                    break
            if len(peers) >= 2:
                if episode.claim_relation == "属性":
                    statements.append(
                        f"{'・'.join(peers)}は共通して{episode.claim_value}。"
                    )
                else:
                    statements.append(
                        f"{topic}の{episode.claim_relation}は{episode.claim_value}。"
                        f"同じ関係は{'・'.join(peers[1:])}にも見られます。"
                    )
            else:
                statements.append(episode.sentence)
            if len(statements) >= 3:
                break

        focused_ids = local_ids[: min(3, len(local_ids))]
        base.episodic.workspace.extend(focused_ids)
        for episode_id in focused_ids:
            episode = base.episodic.episodes[episode_id]
            if episode.claim_subject:
                base.episodic.focus_terms.append(episode.claim_subject)
            if episode.claim_value:
                base.episodic.focus_terms.append(episode.claim_value)

        self.last_candidates = 1
        self.last_anchor_reads = 0
        self.last_estimated_operations = len(local_ids[:8]) + inspected + len(statements)
        text = (
            f"{topic}の要約: "
            + " ".join(statements)
            + " 根拠: "
            + "、".join(f"［{source}］" for source in source_ids[:8])
        )
        return ReplyResult(
            text=text,
            confidence=min(0.95, 0.74 + 0.05 * len(statements)),
            mechanism="topic-centred-sparse-abstraction",
            candidates_inspected=1,
            active_bits=min(len(local_ids), 8),
            estimated_sparse_operations=self.last_estimated_operations,
        )

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        base: SPARCHS8Model,
    ) -> "SparseAbstractionMemory":
        original = _BaseAbstractionMemory.from_bytes(data, base=base)
        memory = cls(
            max_paragraphs=original.max_paragraphs,
            max_candidates=original.max_candidates,
            read_budget=original.read_budget,
        )
        memory.__dict__.update(original.__dict__)
        return memory


class SPARCHS9Model(_BaseHS9Model):
    def __init__(self, base: SPARCHS8Model | None = None) -> None:
        self.base = base or SPARCHS8Model()
        self.abstraction = SparseAbstractionMemory()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS9Model":
        payload = json.loads(zlib.decompress(data))
        base = SPARCHS8Model.from_bytes(base64.b85decode(payload["base"]))
        model = cls(base)
        model.abstraction = SparseAbstractionMemory.from_bytes(
            base64.b85decode(payload["abstraction"]),
            base=base,
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS9Model":
        return cls.from_bytes(Path(path).read_bytes())
