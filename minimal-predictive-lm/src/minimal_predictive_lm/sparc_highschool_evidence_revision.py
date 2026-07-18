from __future__ import annotations

from dataclasses import dataclass
import json

from .sparc_highschool_discourse_workspace import DiscourseEvidenceWorkspaceLearner


StateRow = tuple[str, str, int, int]


@dataclass(frozen=True)
class EvidenceRevisionResult:
    accepted: bool
    target: str
    selected_states: tuple[StateRow, ...]
    answer: str
    mechanism: str
    revised: bool
    version: int
    focus_reused: bool


class EvidenceRevisionWorkspaceLearner(DiscourseEvidenceWorkspaceLearner):
    """Keep several verified issues and revise them only with newly verified worlds.

    The ledger contains bounded evidence components rather than raw dialogue text. A
    new component for the same induced entity replaces the old component only after
    the shared latent-world solver and forward verifier accept it. Queries read one
    component by grounding against the currently stored entity set. This is a shared
    evidence-update mechanism, not a correction-word list or problem-specific route.
    """

    def __init__(self, max_evidence_components: int = 8, **kwargs):
        super().__init__(**kwargs)
        if max_evidence_components < 1:
            raise ValueError("max_evidence_components must be positive")
        self.max_evidence_components = max_evidence_components
        self._evidence_ledger: dict[str, tuple[StateRow, ...]] = {}
        self._evidence_versions: dict[str, int] = {}
        self._evidence_order: list[str] = []
        self._ledger_focus: str | None = None
        self.evidence_component_reads = 0
        self.evidence_component_writes = 0
        self.evidence_revisions = 0
        self.evidence_rejected_updates = 0
        self.evidence_evictions = 0

    def reset_evidence_ledger(self) -> None:
        self._evidence_ledger.clear()
        self._evidence_versions.clear()
        self._evidence_order.clear()
        self._ledger_focus = None

    def _store_verified_component(self, target: str, states: tuple[StateRow, ...]) -> tuple[bool, int]:
        previous = self._evidence_ledger.get(target)
        revised = previous is not None and previous != states
        if previous == states:
            self._ledger_focus = target
            return False, self._evidence_versions[target]
        if target not in self._evidence_ledger and len(self._evidence_order) >= self.max_evidence_components:
            evicted = self._evidence_order.pop(0)
            self._evidence_ledger.pop(evicted, None)
            self._evidence_versions.pop(evicted, None)
            if self._ledger_focus == evicted:
                self._ledger_focus = None
            self.evidence_evictions += 1
        if target in self._evidence_order:
            self._evidence_order.remove(target)
        self._evidence_order.append(target)
        self._evidence_ledger[target] = states
        self._evidence_versions[target] = self._evidence_versions.get(target, 0) + 1
        self._ledger_focus = target
        self.evidence_component_writes += 1
        if revised:
            self.evidence_revisions += 1
        return revised, self._evidence_versions[target]

    def ingest_verified_evidence(self, text: str) -> EvidenceRevisionResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            self.evidence_rejected_updates += 1
            return self._e_abstain("abstain-missing-evidence-update")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            self.evidence_rejected_updates += 1
            return self._e_abstain("abstain-unverified-evidence-update")
        entities = tuple(sorted({row[0] for row in grounded.recovered_states}))
        targets = self._question_targets(question, entities)
        if len(targets) != 1:
            self.evidence_rejected_updates += 1
            return self._e_abstain("abstain-ambiguous-evidence-update")
        target = targets[0]
        states = tuple(row for row in grounded.recovered_states if row[0] == target)
        if not states:
            self.evidence_rejected_updates += 1
            return self._e_abstain("abstain-empty-evidence-update")
        revised, version = self._store_verified_component(target, states)
        return self._e_answer(target, states, revised, version, False)

    def answer_from_evidence_ledger(self, question: str) -> EvidenceRevisionResult:
        entities = tuple(self._evidence_order)
        self.evidence_component_reads += len(entities)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            return self._e_abstain("abstain-unsupported-ledger-target")
        if len(targets) == 1:
            target = targets[0]
            self._ledger_focus = target
        elif len(targets) == 0 and self._ledger_focus in self._evidence_ledger:
            target = self._ledger_focus  # type: ignore[assignment]
            reused = True
        else:
            return self._e_abstain("abstain-ambiguous-ledger-query")
        states = self._evidence_ledger[target]
        return self._e_answer(target, states, False, self._evidence_versions[target], reused)

    def _e_answer(
        self,
        target: str,
        states: tuple[StateRow, ...],
        revised: bool,
        version: int,
        reused: bool,
    ) -> EvidenceRevisionResult:
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        revision = "新しい検算済み証拠で更新しました。" if revised else "検算済み証拠を保持しています。"
        answer = f"{target}は{details}です。{revision}"
        return EvidenceRevisionResult(
            True,
            target,
            states,
            answer,
            "shared-bounded-verified-evidence-revision-ledger",
            revised,
            version,
            reused,
        )

    @staticmethod
    def _e_abstain(mechanism: str) -> EvidenceRevisionResult:
        return EvidenceRevisionResult(False, "", (), "", mechanism, False, 0, False)

    def evidence_ledger_bytes(self) -> bytes:
        payload = {
            "order": self._evidence_order,
            "versions": self._evidence_versions,
            "components": {key: [list(row) for row in value] for key, value in self._evidence_ledger.items()},
            "focus": self._ledger_focus,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def load_evidence_ledger_bytes(self, payload: bytes) -> None:
        data = json.loads(payload.decode("utf-8"))
        order = [str(value) for value in data["order"]]
        components = {
            str(key): tuple((str(row[0]), str(row[1]), int(row[2]), int(row[3])) for row in rows)
            for key, rows in data["components"].items()
        }
        if len(order) > self.max_evidence_components or set(order) != set(components):
            raise ValueError("invalid bounded evidence ledger")
        self._evidence_order = order
        self._evidence_ledger = components
        self._evidence_versions = {str(key): int(value) for key, value in data["versions"].items()}
        focus = data.get("focus")
        self._ledger_focus = str(focus) if focus in components else None

    def report(self):
        result = super().report()
        result.update({
            "shared_bounded_verified_evidence_revision_ledger": True,
            "evidence_components": len(self._evidence_ledger),
            "evidence_component_reads": self.evidence_component_reads,
            "evidence_component_writes": self.evidence_component_writes,
            "evidence_revisions": self.evidence_revisions,
            "evidence_rejected_updates": self.evidence_rejected_updates,
            "evidence_evictions": self.evidence_evictions,
            "evidence_ledger_bytes": len(self.evidence_ledger_bytes()),
            "task_name_supplied": False,
            "domain_name_supplied": False,
        })
        return result
