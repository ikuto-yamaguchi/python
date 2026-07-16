from __future__ import annotations

import base64
import json
import re
import zlib
from collections import defaultdict, deque
from pathlib import Path

from .sparc_counterexamples_v2 import SPARCHS14ModelV2
from .sparc_language import ReplyResult
from .sparc_perspective_event import PerspectiveEventMixin
from .sparc_perspective_query import PerspectiveQueryMixin
from .sparc_perspective_runtime import PerspectiveRuntimeMixin
from .sparc_perspective_types import (
    CauseProgram, CauseSchema, EventProgram, EventRecord, EventSchema,
    FocusedQueryExample, QueryProgram, QuerySchema, StateFact, TransitionExample,
)


class SparsePerspectiveWorkspace(
    PerspectiveEventMixin, PerspectiveQueryMixin, PerspectiveRuntimeMixin
):
    def __init__(
        self,
        *,
        max_event_programs: int = 1024,
        max_query_programs: int = 1024,
        max_schemas: int = 100_000,
        max_candidates: int = 24,
        focus_size: int = 16,
    ) -> None:
        self.max_event_programs = max_event_programs
        self.max_query_programs = max_query_programs
        self.max_schemas = max_schemas
        self.max_candidates = max_candidates
        self.world: dict[tuple[str, str], StateFact] = {}
        self.beliefs: dict[tuple[str, str, str], StateFact] = {}
        self.entity_kinds: dict[str, str] = {}
        self.events: list[EventRecord] = []
        self.last_writer: dict[tuple[str, str], int] = {}
        self.focus: deque[tuple[str, str]] = deque(maxlen=focus_size)
        self.max_entity_chars = 0

        self.event_programs: list[EventProgram] = []
        self.event_schemas: list[EventSchema] = []
        self.event_program_ids: dict[tuple[object, ...], int] = {}
        self.event_schema_ids: dict[str, int] = {}
        self.event_postings: dict[str, set[int]] = defaultdict(set)

        self.query_programs: list[QueryProgram] = []
        self.query_schemas: list[QuerySchema] = []
        self.query_program_ids: dict[tuple[object, ...], int] = {}
        self.query_schema_ids: dict[str, int] = {}
        self.query_postings: dict[str, set[int]] = defaultdict(set)

        self.cause_programs: list[CauseProgram] = []
        self.cause_schemas: list[CauseSchema] = []
        self.cause_program_ids: dict[tuple[object, ...], int] = {}
        self.cause_schema_ids: dict[str, int] = {}
        self.cause_postings: dict[str, set[int]] = defaultdict(set)

        self.last_event_candidates = 0
        self.last_query_candidates = 0
        self.last_schema_reads = 0
        self.last_state_reads = 0
        self.last_focus_reads = 0
        self.last_entity_substring_checks = 0
        self.last_estimated_operations = 0
        self._event_regex_cache: dict[int, re.Pattern[str]] = {}
        self._query_regex_cache: dict[int, re.Pattern[str]] = {}
        self._cause_regex_cache: dict[int, re.Pattern[str]] = {}


class SPARCHS15Model:
    def __init__(self, base: SPARCHS14ModelV2 | None = None) -> None:
        self.base = base or SPARCHS14ModelV2()
        self.perspective = SparsePerspectiveWorkspace()

    def reply(self, text: str) -> ReplyResult:
        answer = self.perspective.answer(text)
        if answer is not None:
            return answer
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs15",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "perspective": base64.b85encode(self.perspective.to_bytes()).decode("ascii"),
        }
        return zlib.compress(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"), 9)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS15Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS14ModelV2.from_bytes(base64.b85decode(payload["base"])))
        model.perspective = SparsePerspectiveWorkspace.from_bytes(base64.b85decode(payload["perspective"]))
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS15Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS15",
            "base": self.base.report(),
            "perspective": self.perspective.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
