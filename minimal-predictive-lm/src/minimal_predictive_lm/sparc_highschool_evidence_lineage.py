from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .sparc_highschool_evidence_revision import StateRow
from .sparc_highschool_hypothesis_consensus import (
    HypothesisConsensusResult,
    HypothesisConsensusWorkspaceLearner,
)


@dataclass(frozen=True)
class EvidenceLineageStats:
    lineage_id: str
    reused: bool
    similarity: float
    conflicted: bool


class EvidenceLineageConsensusLearner(HypothesisConsensusWorkspaceLearner):
    """Count verified support by bounded source lineage, not document count.

    The same latent-world solver verifies every claim first. Non-world context from
    the document is converted into sparse character features and clustered by
    overlap. Near-copies therefore share one lineage and cannot manufacture an
    independent majority. A lineage that supports incompatible worlds for the same
    target is invalidated for that target. No task/domain labels, source-name list,
    correction vocabulary, or problem-specific branch is supplied.
    """

    def __init__(self, max_lineages: int = 12, lineage_similarity_threshold: float = 0.52, **kwargs):
        super().__init__(**kwargs)
        if max_lineages < 2:
            raise ValueError("max_lineages must be at least two")
        if not 0.0 < lineage_similarity_threshold <= 1.0:
            raise ValueError("lineage similarity threshold must be in (0, 1]")
        self.max_lineages = max_lineages
        self.lineage_similarity_threshold = lineage_similarity_threshold
        self._lineages: dict[str, dict[str, object]] = {}
        self._lineage_order: list[str] = []
        self._lineage_sequence = 0
        self._lineage_claims: dict[str, dict[str, str]] = {}
        self._lineage_conflicts: set[tuple[str, str]] = set()
        self.lineage_feature_reads = 0
        self.lineage_comparisons = 0
        self.lineage_reuses = 0
        self.lineage_creations = 0
        self.lineage_dependent_duplicates = 0
        self.lineage_conflicts = 0
        self.lineage_evictions = 0
        self.last_lineage = EvidenceLineageStats("", False, 0.0, False)

    def reset_lineage_graph(self) -> None:
        self.reset_hypothesis_graph()
        self._lineages.clear()
        self._lineage_order.clear()
        self._lineage_claims.clear()
        self._lineage_conflicts.clear()
        self._lineage_sequence = 0
        self.last_lineage = EvidenceLineageStats("", False, 0.0, False)

    @staticmethod
    def _compact_source(text: str) -> str:
        value = re.sub(r"\s+", "", text)
        value = re.sub(r"[0-9０-９]+", "#", value)
        return re.sub(r"[A-Za-zＡ-Ｚａ-ｚ]+", "@", value)

    @staticmethod
    def _ngrams(text: str) -> frozenset[int]:
        padded = f"^{text}$"
        grams = {
            padded[index : index + size]
            for size in (2, 3)
            for index in range(max(0, len(padded) - size + 1))
        }
        return frozenset(
            int.from_bytes(hashlib.blake2s(gram.encode("utf-8"), digest_size=2).digest(), "big")
            for gram in grams
        )

    def _source_features(self, text: str) -> frozenset[int]:
        sentences = tuple(self._sentences(text))
        body = sentences[:-1] if len(sentences) >= 2 else sentences
        residual: list[str] = []
        for sentence in body:
            observed = self.observe_world([sentence])
            transition = self._affine_transition(sentence)
            if transition is None and not (observed.accepted == 1 and not observed.abstained):
                residual.append(sentence)
        source = "。".join(residual) if residual else "。".join(body)
        features = self._ngrams(self._compact_source(source))
        self.lineage_feature_reads += len(features)
        return features

    @staticmethod
    def _similarity(left: frozenset[int], right: frozenset[int]) -> float:
        union = len(left | right)
        return len(left & right) / union if union else 1.0

    def _evict_lineage(self) -> None:
        if len(self._lineage_order) < self.max_lineages:
            return
        victim = self._lineage_order.pop(0)
        self._lineages.pop(victim, None)
        claims = self._lineage_claims.pop(victim, {})
        self._lineage_conflicts = {pair for pair in self._lineage_conflicts if pair[0] != victim}
        for target, state_key in claims.items():
            record = self._hypotheses.get(target, {}).get(state_key)
            if record is not None and victim in record["lineage_ids"]:
                record["lineage_ids"].remove(victim)
        self.lineage_evictions += 1

    def _resolve_lineage(self, features: frozenset[int]) -> tuple[str, bool, float]:
        best_id = ""
        best_score = 0.0
        for lineage_id in self._lineage_order:
            stored = frozenset(self._lineages[lineage_id]["features"])
            score = self._similarity(features, stored)
            self.lineage_comparisons += 1
            if score > best_score:
                best_id, best_score = lineage_id, score
        if best_id and best_score >= self.lineage_similarity_threshold:
            self.lineage_reuses += 1
            self._lineages[best_id]["last_seen"] = self._lineage_sequence
            return best_id, True, best_score
        self._evict_lineage()
        digest = hashlib.blake2s(
            ",".join(str(value) for value in sorted(features)).encode("ascii"), digest_size=8
        ).hexdigest()
        lineage_id = f"L{self._lineage_sequence:x}-{digest}"
        self._lineages[lineage_id] = {
            "features": tuple(sorted(features)),
            "first_seen": self._lineage_sequence,
            "last_seen": self._lineage_sequence,
        }
        self._lineage_order.append(lineage_id)
        self._lineage_claims[lineage_id] = {}
        self.lineage_creations += 1
        return lineage_id, False, 0.0

    def _remove_lineage_support(self, target: str, state_key: str, lineage_id: str) -> None:
        record = self._hypotheses.get(target, {}).get(state_key)
        if record is not None and lineage_id in record["lineage_ids"]:
            record["lineage_ids"].remove(lineage_id)

    def _store_lineage_hypothesis(self, target: str, states: tuple[StateRow, ...], evidence_text: str) -> tuple[int, int, bool]:
        if target not in self._hypotheses and len(self._hypothesis_order) >= self.max_evidence_components:
            evicted = self._hypothesis_order.pop(0)
            self._hypotheses.pop(evicted, None)
            if self._hypothesis_focus == evicted:
                self._hypothesis_focus = None
            for claims in self._lineage_claims.values():
                claims.pop(evicted, None)
            self.hypothesis_evictions += 1
        if target not in self._hypotheses:
            self._hypotheses[target] = {}
            self._hypothesis_order.append(target)

        self._lineage_sequence += 1
        lineage_id, reused, similarity = self._resolve_lineage(self._source_features(evidence_text))
        state_key = self._state_key(states)
        rows = self._hypotheses[target]
        previous_state = self._lineage_claims[lineage_id].get(target)
        conflict_key = (lineage_id, target)
        if previous_state == state_key and conflict_key not in self._lineage_conflicts:
            self.lineage_dependent_duplicates += 1
            record = rows.get(state_key)
            support = len(record["lineage_ids"]) if record is not None else 0
            self.last_lineage = EvidenceLineageStats(lineage_id, reused, similarity, False)
            return support, len(rows), False
        if previous_state is not None and previous_state != state_key:
            self._remove_lineage_support(target, previous_state, lineage_id)
            self._lineage_claims[lineage_id].pop(target, None)
            self._lineage_conflicts.add(conflict_key)
            self.lineage_conflicts += 1
            self.last_lineage = EvidenceLineageStats(lineage_id, reused, similarity, True)
            return 0, len(rows), False
        if conflict_key in self._lineage_conflicts:
            self.last_lineage = EvidenceLineageStats(lineage_id, reused, similarity, True)
            return 0, len(rows), False

        self._hypothesis_sequence += 1
        if state_key not in rows:
            if len(rows) >= self.max_hypotheses_per_target:
                victim_key, _ = min(
                    rows.items(),
                    key=lambda item: (len(item[1]["lineage_ids"]), int(item[1]["last_seen"])),
                )
                victim = rows.pop(victim_key)
                for old_lineage in tuple(victim["lineage_ids"]):
                    self._lineage_claims.get(old_lineage, {}).pop(target, None)
                self.hypothesis_evictions += 1
            rows[state_key] = {
                "states": states,
                "lineage_ids": [],
                "first_seen": self._hypothesis_sequence,
                "last_seen": self._hypothesis_sequence,
            }
            self.hypothesis_writes += 1
        record = rows[state_key]
        record["lineage_ids"].append(lineage_id)
        record["last_seen"] = self._hypothesis_sequence
        self._lineage_claims[lineage_id][target] = state_key
        self.hypothesis_support_updates += 1
        self._hypothesis_focus = target
        self.last_lineage = EvidenceLineageStats(lineage_id, reused, similarity, False)
        return len(record["lineage_ids"]), len(rows), True

    def ingest_lineage_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            return self._h_abstain("abstain-missing-lineage-evidence")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            return self._h_abstain("abstain-unverified-lineage-evidence")
        entities = tuple(sorted({row[0] for row in grounded.recovered_states}))
        targets = self._question_targets(question, entities)
        if len(targets) != 1:
            return self._h_abstain("abstain-ambiguous-lineage-evidence")
        target = targets[0]
        states = tuple(row for row in grounded.recovered_states if row[0] == target)
        support, alternatives, _ = self._store_lineage_hypothesis(target, states, text)
        return self._lineage_answer(target, states, support, alternatives, False)

    def answer_from_lineage_graph(self, question: str) -> HypothesisConsensusResult:
        entities = tuple(self._hypothesis_order)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unsupported-lineage-target")
        if len(targets) == 1:
            target = targets[0]
        elif len(targets) == 0 and self._hypothesis_focus in self._hypotheses:
            target = self._hypothesis_focus  # type: ignore[assignment]
            reused = True
        else:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-ambiguous-lineage-query")
        rows = self._hypotheses[target]
        self.hypothesis_reads += len(rows)
        ranked = sorted(rows.values(), key=lambda record: (-len(record["lineage_ids"]), -int(record["last_seen"])))
        if not ranked or len(ranked[0]["lineage_ids"]) == 0:
            return self._h_abstain("abstain-no-independent-lineage-support")
        best_support = len(ranked[0]["lineage_ids"])
        tied = [record for record in ranked if len(record["lineage_ids"]) == best_support]
        if len(tied) != 1:
            self.hypothesis_conflict_abstentions += 1
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unresolved-independent-lineage-conflict")
        self._hypothesis_focus = target
        return self._lineage_answer(target, tuple(ranked[0]["states"]), best_support, len(ranked), reused)

    @staticmethod
    def _lineage_answer(target: str, states: tuple[StateRow, ...], support: int, alternatives: int, reused: bool) -> HypothesisConsensusResult:
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        answer = f"{target}は{details}です。依存する転載をまとめた独立由来{support}系統が支持し、競合仮説{alternatives}件の中で支持が一意に最大です。"
        return HypothesisConsensusResult(True, target, states, answer, "shared-bounded-verified-evidence-lineage-consensus-graph", support, alternatives, reused)

    def lineage_graph_bytes(self) -> bytes:
        payload = {
            "order": self._hypothesis_order,
            "focus": self._hypothesis_focus,
            "sequence": self._hypothesis_sequence,
            "lineage_sequence": self._lineage_sequence,
            "lineage_order": self._lineage_order,
            "lineages": self._lineages,
            "lineage_claims": self._lineage_claims,
            "lineage_conflicts": [list(pair) for pair in sorted(self._lineage_conflicts)],
            "targets": {target: {key: {"states": [list(row) for row in record["states"]], "lineage_ids": list(record["lineage_ids"]), "first_seen": record["first_seen"], "last_seen": record["last_seen"]} for key, record in rows.items()} for target, rows in self._hypotheses.items()},
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def load_lineage_graph_bytes(self, payload: bytes) -> None:
        data = json.loads(payload.decode("utf-8"))
        order = [str(value) for value in data["order"]]
        lineage_order = [str(value) for value in data["lineage_order"]]
        if len(order) > self.max_evidence_components or len(lineage_order) > self.max_lineages:
            raise ValueError("invalid bounded lineage graph")
        targets: dict[str, dict[str, dict[str, object]]] = {}
        for target, rows in data["targets"].items():
            if len(rows) > self.max_hypotheses_per_target:
                raise ValueError("invalid bounded hypothesis count")
            targets[str(target)] = {}
            for key, record in rows.items():
                targets[str(target)][str(key)] = {"states": tuple((str(row[0]), str(row[1]), int(row[2]), int(row[3])) for row in record["states"]), "lineage_ids": [str(value) for value in record["lineage_ids"]], "first_seen": int(record["first_seen"]), "last_seen": int(record["last_seen"])}
        lineages = {str(key): {"features": tuple(int(value) for value in record["features"]), "first_seen": int(record["first_seen"]), "last_seen": int(record["last_seen"])} for key, record in data["lineages"].items()}
        if set(order) != set(targets) or set(lineage_order) != set(lineages):
            raise ValueError("lineage graph order mismatch")
        self._hypothesis_order = order
        self._hypotheses = targets
        self._hypothesis_sequence = int(data.get("sequence", 0))
        self._lineage_sequence = int(data.get("lineage_sequence", 0))
        self._lineage_order = lineage_order
        self._lineages = lineages
        self._lineage_claims = {str(lineage): {str(target): str(state) for target, state in claims.items()} for lineage, claims in data["lineage_claims"].items()}
        self._lineage_conflicts = {(str(row[0]), str(row[1])) for row in data.get("lineage_conflicts", [])}
        focus = data.get("focus")
        self._hypothesis_focus = str(focus) if focus in targets else None

    def report(self):
        result = super().report()
        result.update({"shared_bounded_verified_evidence_lineage_consensus_graph": True, "lineages": len(self._lineages), "lineage_feature_reads": self.lineage_feature_reads, "lineage_comparisons": self.lineage_comparisons, "lineage_reuses": self.lineage_reuses, "lineage_creations": self.lineage_creations, "lineage_dependent_duplicates": self.lineage_dependent_duplicates, "lineage_conflicts": self.lineage_conflicts, "lineage_evictions": self.lineage_evictions, "lineage_graph_bytes": len(self.lineage_graph_bytes()), "task_name_supplied": False, "domain_name_supplied": False})
        return result
