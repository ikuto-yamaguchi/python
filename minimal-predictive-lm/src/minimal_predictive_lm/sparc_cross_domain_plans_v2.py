from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

from .sparc_cross_domain_plans import (
    SPARCHS11Model,
    SparseCrossDomainPlanBank,
)
from .sparc_role_induction_v3 import SPARCHS10ModelV3


class SparseCrossDomainPlanBankV2(SparseCrossDomainPlanBank):
    """Question-local exact subject routing independent of stored subject count."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.max_subject_chars = 0
        self.last_subject_substring_checks = 0

    def register_episode(self, episode_id, episode) -> None:
        before = len(self.subject_relations)
        super().register_episode(episode_id, episode)
        if episode.claim_subject in self.subject_relations:
            self.max_subject_chars = max(
                self.max_subject_chars, len(episode.claim_subject or "")
            )

    def rebuild_fact_index(self, episodic) -> None:
        super().rebuild_fact_index(episodic)
        self.max_subject_chars = max(
            (len(subject) for subject in self.subject_relations), default=0
        )

    def _candidate_subjects(self, question: str) -> list[str]:
        self.last_subject_substring_checks = 0
        maximum = min(self.max_subject_chars, len(question))
        for size in range(maximum, 1, -1):
            matches: list[str] = []
            for start in range(0, len(question) - size + 1):
                self.last_subject_substring_checks += 1
                piece = question[start : start + size]
                if piece in self.subject_relations:
                    matches.append(piece)
            if matches:
                self.last_anchor_reads = 0
                return sorted(set(matches), key=lambda value: (-len(value), value))[:8]
        self.last_anchor_reads = 0
        return []

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseCrossDomainPlanBankV2":
        base = SparseCrossDomainPlanBank.from_bytes(data)
        bank = cls(
            max_plans=base.max_plans,
            max_schemas=base.max_schemas,
            max_candidates=base.max_candidates,
        )
        bank.__dict__.update(base.__dict__)
        bank.max_subject_chars = max(
            (len(subject) for subject in bank.subject_relations), default=0
        )
        bank.last_subject_substring_checks = 0
        return bank

    def report(self) -> dict[str, int | bool]:
        report = super().report()
        report["max_subject_chars"] = self.max_subject_chars
        report["last_subject_substring_checks"] = self.last_subject_substring_checks
        report["global_subject_scan_used"] = False
        return report


class SPARCHS11ModelV2(SPARCHS11Model):
    def __init__(self, base: SPARCHS10ModelV3 | None = None) -> None:
        self.base = base or SPARCHS10ModelV3()
        self.plans = SparseCrossDomainPlanBankV2()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS11ModelV2":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS10ModelV3.from_bytes(base64.b85decode(payload["base"])))
        model.plans = SparseCrossDomainPlanBankV2.from_bytes(
            base64.b85decode(payload["plans"])
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS11ModelV2":
        return cls.from_bytes(Path(path).read_bytes())
