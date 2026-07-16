from __future__ import annotations

import base64
import json
import re
import zlib
from pathlib import Path

from .sparc_episodic import (
    SPARCHS8Model as _BaseHS8Model,
    SparseEpisodicRevisionMemory as _BaseEpisodicMemory,
)
from .sparc_language import ReplyResult
from .sparc_units import SPARCHS7Model

_FOLLOWUP_RE = re.compile(
    r"(?:それ|そのこと|このこと|先ほど|さっき|今の話|その話|今の内容)"
)


class SparseEpisodicRevisionMemory(_BaseEpisodicMemory):
    """HS8 episodic memory with an explicit bounded discourse-focus circuit.

    The base HS8 implementation expanded an anaphoric query with text from the
    last evidence item and then reran ordinary retrieval. With a crowded memory,
    another recent claim could still win. This class treats the most recently
    *used* evidence episode as a temporary focus node and locally reactivates
    only episodes sharing its subject, value, source, or rare anchors.
    """

    def _focused_followup(self, query: str) -> ReplyResult | None:
        if not _FOLLOWUP_RE.search(query) or not self.workspace:
            return None

        recent_ids: list[int] = []
        seen: set[int] = set()
        for episode_id in reversed(self.workspace):
            if episode_id in seen or episode_id >= len(self.episodes):
                continue
            seen.add(episode_id)
            if self.episodes[episode_id].active:
                recent_ids.append(episode_id)
            if len(recent_ids) >= min(4, self.workspace_size):
                break
        if not recent_ids:
            return None

        focus_id = recent_ids[0]
        focus = self.episodes[focus_id]
        focus_terms = tuple(
            term
            for term in (focus.claim_subject, focus.claim_value)
            if term and len(term) >= 2
        )
        focus_query = "".join(focus_terms) or focus.sentence
        routed = self._candidate_ids(focus_query)

        selected: list[int] = [focus_id]
        for episode_id in routed:
            if episode_id == focus_id or episode_id in selected:
                continue
            episode = self.episodes[episode_id]
            if not episode.active:
                continue
            related = (
                episode.source_id == focus.source_id
                or any(term in episode.sentence for term in focus_terms)
                or (
                    focus.claim_subject is not None
                    and episode.claim_subject == focus.claim_subject
                )
            )
            if not related:
                continue
            selected.append(episode_id)
            if len(selected) >= 3:
                break

        evidence = " ".join(self.episodes[item].sentence for item in selected)
        sources = "、".join(
            f"［{self.episodes[item].source_id}］" for item in selected
        )
        subject = focus.claim_subject or focus.claim_value or "先ほどの内容"
        text = f"{subject}については、{evidence} 出典: {sources}"

        self.workspace.extend(selected)
        for episode_id in selected:
            episode = self.episodes[episode_id]
            if episode.claim_subject:
                self.focus_terms.append(episode.claim_subject)
            if episode.claim_value:
                self.focus_terms.append(episode.claim_value)

        return ReplyResult(
            text=text,
            confidence=0.82,
            mechanism="bounded-discourse-focus",
            candidates_inspected=self.last_candidates,
            active_bits=len(selected),
            estimated_sparse_operations=self.last_estimated_operations
            + len(recent_ids)
            + len(selected),
        )

    def answer(self, query: str) -> ReplyResult | None:
        focused = self._focused_followup(query)
        if focused is not None:
            return focused
        return super().answer(query)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseEpisodicRevisionMemory":
        base = _BaseEpisodicMemory.from_bytes(data)
        memory = cls(
            max_episodes=base.max_episodes,
            max_candidates=base.max_candidates,
            read_budget=base.read_budget,
            workspace_size=base.workspace_size,
        )
        memory.__dict__.update(base.__dict__)
        return memory


class SPARCHS8Model(_BaseHS8Model):
    def __init__(self, base: SPARCHS7Model | None = None) -> None:
        self.base = base or SPARCHS7Model()
        self.episodic = SparseEpisodicRevisionMemory()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS8Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(
            SPARCHS7Model.from_bytes(base64.b85decode(payload["base"]))
        )
        model.episodic = SparseEpisodicRevisionMemory.from_bytes(
            base64.b85decode(payload["episodic"])
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS8Model":
        return cls.from_bytes(Path(path).read_bytes())
