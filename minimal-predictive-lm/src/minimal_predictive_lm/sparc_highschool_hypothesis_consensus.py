from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .sparc_highschool_evidence_revision import EvidenceRevisionWorkspaceLearner, StateRow


@dataclass(frozen=True)
class HypothesisConsensusResult:
    accepted: bool
    target: str
    selected_states: tuple[StateRow, ...]
    answer: str
    mechanism: str
    support: int
    competing_hypotheses: int
    focus_reused: bool


class HypothesisConsensusWorkspaceLearner(EvidenceRevisionWorkspaceLearner):
    """Retain competing verified worlds and answer only from unique support consensus.

    Every input is first solved and replay-verified by the same latent world model.
    Verified but incompatible state components coexist as hypotheses instead of one
    silently replacing another. Repeated independent evidence strengthens an equal
    state component, exact duplicate evidence is ignored, and a query is answered
    only when one hypothesis has strictly greater support. This is a shared bounded
    evidence mechanism; it receives no task/domain name, correction vocabulary, or
    problem-specific branch.
    """

    def __init__(self, max_hypotheses_per_target: int = 4, **kwargs):
        super().__init__(**kwargs)
        if max_hypotheses_per_target < 2:
            raise ValueError("max_hypotheses_per_target must be at least two")
        self.max_hypotheses_per_target = max_hypotheses_per_target
        self._hypotheses: dict[str, dict[str, dict[str, object]]] = {}
        self._hypothesis_order: list[str] = []
        self._hypothesis_focus: str | None = None
        self._hypothesis_sequence = 0
        self.hypothesis_reads = 0
        self.hypothesis_writes = 0
        self.hypothesis_support_updates = 0
        self.hypothesis_duplicate_evidence = 0
        self.hypothesis_conflict_abstentions = 0
        self.hypothesis_evictions = 0

    def reset_hypothesis_graph(self) -> None:
        self._hypotheses.clear()
        self._hypothesis_order.clear()
        self._hypothesis_focus = None
        self._hypothesis_sequence = 0

    @staticmethod
    def _state_key(states: tuple[StateRow, ...]) -> str:
        payload = json.dumps([list(row) for row in states], ensure_ascii=False, separators=(",", ":"))
        return hashlib.blake2s(payload.encode("utf-8"), digest_size=12).hexdigest()

    @staticmethod
    def _evidence_key(text: str) -> str:
        compact = "".join(text.split())
        return hashlib.blake2s(compact.encode("utf-8"), digest_size=12).hexdigest()

    def _store_verified_hypothesis(
        self, target: str, states: tuple[StateRow, ...], evidence_text: str
    ) -> tuple[int, int, bool]:
        if target not in self._hypotheses and len(self._hypothesis_order) >= self.max_evidence_components:
            evicted = self._hypothesis_order.pop(0)
            self._hypotheses.pop(evicted, None)
            if self._hypothesis_focus == evicted:
                self._hypothesis_focus = None
            self.hypothesis_evictions += 1
        if target not in self._hypotheses:
            self._hypotheses[target] = {}
            self._hypothesis_order.append(target)

        rows = self._hypotheses[target]
        state_key = self._state_key(states)
        evidence_key = self._evidence_key(evidence_text)
        self._hypothesis_sequence += 1
        duplicate = any(
            evidence_key in set(record["evidence_ids"]) for record in rows.values()
        )
        if duplicate:
            self.hypothesis_duplicate_evidence += 1
            record = rows.get(state_key)
            support = len(record["evidence_ids"]) if record is not None else 0
            return support, len(rows), False

        if state_key not in rows:
            if len(rows) >= self.max_hypotheses_per_target:
                victim_key, _victim = min(
                    rows.items(),
                    key=lambda item: (len(item[1]["evidence_ids"]), int(item[1]["last_seen"])),
                )
                rows.pop(victim_key)
                self.hypothesis_evictions += 1
            rows[state_key] = {
                "states": states,
                "evidence_ids": [],
                "first_seen": self._hypothesis_sequence,
                "last_seen": self._hypothesis_sequence,
            }
            self.hypothesis_writes += 1
        record = rows[state_key]
        evidence_ids = record["evidence_ids"]
        evidence_ids.append(evidence_key)
        record["last_seen"] = self._hypothesis_sequence
        self.hypothesis_support_updates += 1
        self._hypothesis_focus = target
        return len(evidence_ids), len(rows), True

    def ingest_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            return self._h_abstain("abstain-missing-hypothesis-evidence")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            return self._h_abstain("abstain-unverified-hypothesis-evidence")
        entities = tuple(sorted({row[0] for row in grounded.recovered_states}))
        targets = self._question_targets(question, entities)
        if len(targets) != 1:
            return self._h_abstain("abstain-ambiguous-hypothesis-evidence")
        target = targets[0]
        states = tuple(row for row in grounded.recovered_states if row[0] == target)
        if not states:
            return self._h_abstain("abstain-empty-hypothesis-evidence")
        support, alternatives, _changed = self._store_verified_hypothesis(target, states, text)
        return self._h_answer(target, states, support, alternatives, False)

    def answer_from_hypothesis_graph(self, question: str) -> HypothesisConsensusResult:
        entities = tuple(self._hypothesis_order)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unsupported-hypothesis-target")
        if len(targets) == 1:
            target = targets[0]
        elif len(targets) == 0 and self._hypothesis_focus in self._hypotheses:
            target = self._hypothesis_focus  # type: ignore[assignment]
            reused = True
        else:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-ambiguous-hypothesis-query")

        rows = self._hypotheses[target]
        self.hypothesis_reads += len(rows)
        ranked = sorted(
            rows.values(),
            key=lambda record: (-len(record["evidence_ids"]), -int(record["last_seen"])),
        )
        if not ranked:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-empty-hypothesis-graph")
        best_support = len(ranked[0]["evidence_ids"])
        tied = [record for record in ranked if len(record["evidence_ids"]) == best_support]
        if len(tied) != 1:
            self.hypothesis_conflict_abstentions += 1
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unresolved-verified-hypothesis-conflict")

        self._hypothesis_focus = target
        states = tuple(ranked[0]["states"])
        return self._h_answer(target, states, best_support, len(ranked), reused)

    @staticmethod
    def _h_answer(
        target: str,
        states: tuple[StateRow, ...],
        support: int,
        alternatives: int,
        reused: bool,
    ) -> HypothesisConsensusResult:
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        answer = (
            f"{target}は{details}です。独立した検算済み証拠{support}件が支持し、"
            f"競合仮説{alternatives}件の中で支持が一意に最大です。"
        )
        return HypothesisConsensusResult(
            True,
            target,
            states,
            answer,
            "shared-bounded-verified-hypothesis-consensus-graph",
            support,
            alternatives,
            reused,
        )

    @staticmethod
    def _h_abstain(mechanism: str) -> HypothesisConsensusResult:
        return HypothesisConsensusResult(False, "", (), "", mechanism, 0, 0, False)

    def hypothesis_graph_bytes(self) -> bytes:
        payload = {
            "order": self._hypothesis_order,
            "focus": self._hypothesis_focus,
            "sequence": self._hypothesis_sequence,
            "targets": {
                target: {
                    key: {
                        "states": [list(row) for row in record["states"]],
                        "evidence_ids": list(record["evidence_ids"]),
                        "first_seen": record["first_seen"],
                        "last_seen": record["last_seen"],
                    }
                    for key, record in rows.items()
                }
                for target, rows in self._hypotheses.items()
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def load_hypothesis_graph_bytes(self, payload: bytes) -> None:
        data = json.loads(payload.decode("utf-8"))
        order = [str(value) for value in data["order"]]
        if len(order) > self.max_evidence_components:
            raise ValueError("invalid bounded hypothesis target count")
        targets: dict[str, dict[str, dict[str, object]]] = {}
        for target, rows in data["targets"].items():
            if len(rows) > self.max_hypotheses_per_target:
                raise ValueError("invalid bounded hypothesis count")
            targets[str(target)] = {}
            for key, record in rows.items():
                states = tuple(
                    (str(row[0]), str(row[1]), int(row[2]), int(row[3]))
                    for row in record["states"]
                )
                targets[str(target)][str(key)] = {
                    "states": states,
                    "evidence_ids": [str(value) for value in record["evidence_ids"]],
                    "first_seen": int(record["first_seen"]),
                    "last_seen": int(record["last_seen"]),
                }
        if set(order) != set(targets):
            raise ValueError("hypothesis target order mismatch")
        self._hypothesis_order = order
        self._hypotheses = targets
        self._hypothesis_sequence = int(data.get("sequence", 0))
        focus = data.get("focus")
        self._hypothesis_focus = str(focus) if focus in targets else None

    def report(self):
        result = super().report()
        result.update({
            "shared_bounded_verified_hypothesis_consensus_graph": True,
            "hypothesis_targets": len(self._hypotheses),
            "hypothesis_count": sum(len(rows) for rows in self._hypotheses.values()),
            "hypothesis_reads": self.hypothesis_reads,
            "hypothesis_writes": self.hypothesis_writes,
            "hypothesis_support_updates": self.hypothesis_support_updates,
            "hypothesis_duplicate_evidence": self.hypothesis_duplicate_evidence,
            "hypothesis_conflict_abstentions": self.hypothesis_conflict_abstentions,
            "hypothesis_evictions": self.hypothesis_evictions,
            "hypothesis_graph_bytes": len(self.hypothesis_graph_bytes()),
            "task_name_supplied": False,
            "domain_name_supplied": False,
        })
        return result
