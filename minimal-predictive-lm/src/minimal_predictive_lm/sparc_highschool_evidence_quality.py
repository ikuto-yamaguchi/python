from __future__ import annotations

from dataclasses import dataclass
import json

from .sparc_highschool_evidence_lineage import EvidenceLineageConsensusLearner
from .sparc_highschool_evidence_revision import StateRow
from .sparc_highschool_hypothesis_consensus import HypothesisConsensusResult


@dataclass(frozen=True)
class EvidenceQualityStats:
    lineage_id: str
    observed_anchors: int
    verified_transitions: int
    quality_weight: int


class EvidenceQualityConsensusLearner(EvidenceLineageConsensusLearner):
    """Rank competing verified worlds by bounded structural evidence coverage.

    Independent provenance is necessary but not sufficient: one weakly anchored
    reconstruction must not equal a world constrained at several observed nodes.
    Quality is derived only from constraints accepted by the same latent-world
    learner and replay verifier. No source-name list, trust label, task/domain name,
    phrase exception, or problem-specific routing is supplied.
    """

    def __init__(self, max_quality_weight: int = 3, **kwargs):
        super().__init__(**kwargs)
        if max_quality_weight < 1:
            raise ValueError("max_quality_weight must be positive")
        self.max_quality_weight = max_quality_weight
        self._quality: dict[tuple[str, str, str], int] = {}
        self.quality_observation_reads = 0
        self.quality_transition_reads = 0
        self.quality_writes = 0
        self.quality_reads = 0
        self.quality_canonical_replays = 0
        self.last_quality = EvidenceQualityStats("", 0, 0, 0)

    def reset_quality_graph(self) -> None:
        self.reset_lineage_graph()
        self._quality.clear()
        self.last_quality = EvidenceQualityStats("", 0, 0, 0)

    def _verified_coverage(self, body: str) -> tuple[int, int, int]:
        observations = 0
        transitions = 0
        for sentence in self._sentences(body):
            observed = self.observe_world([sentence])
            if observed.accepted == 1 and not observed.abstained:
                observations += 1
            if self._affine_transition(sentence) is not None:
                transitions += 1
        self.quality_observation_reads += observations
        self.quality_transition_reads += transitions
        weight = min(self.max_quality_weight, max(1, observations)) if transitions else 0
        return observations, transitions, weight

    def _canonical_states(self, grounded, target: str) -> tuple[StateRow, ...]:
        """Replay the verified world into one observation-layout-invariant trajectory."""
        keys = sorted(key for key in grounded.initial_world.number_map() if key[0] == target)
        if len(keys) != 1:
            return ()
        key = keys[0]
        relation = key[1]
        world = grounded.initial_world
        current = world.number_map().get(key)
        if current is None:
            return ()
        states: list[StateRow] = [(target, relation, 0, current)]
        node = 0
        for action in grounded.actions:
            applied = self.apply(action, world)
            self.quality_canonical_replays += 1
            if not applied.accepted:
                return ()
            world = applied.world
            value = world.number_map().get(key)
            if value is not None and value != current:
                node += 1
                current = value
                states.append((target, relation, node, value))
        expected = grounded.final_world.number_map().get(key)
        if current != expected:
            return ()
        return tuple(states)

    def ingest_quality_verified_hypothesis(self, text: str) -> HypothesisConsensusResult:
        sentences = tuple(self._sentences(text))
        if len(sentences) < 2:
            return self._h_abstain("abstain-missing-quality-evidence")
        question = sentences[-1]
        body = "。".join(sentences[:-1]) + "。"
        grounded = self.infer_latent_state_graph(body)
        if not grounded.accepted or not grounded.verified:
            return self._h_abstain("abstain-unverified-quality-evidence")
        entities = tuple(sorted({key[0] for key in grounded.initial_world.number_map()}))
        targets = self._question_targets(question, entities)
        if len(targets) != 1:
            return self._h_abstain("abstain-ambiguous-quality-evidence")
        target = targets[0]
        states = self._canonical_states(grounded, target)
        if not states:
            return self._h_abstain("abstain-noncanonical-quality-evidence")
        _support, alternatives, stored = self._store_lineage_hypothesis(target, states, text)
        lineage_id = self.last_lineage.lineage_id
        observations, transitions, weight = self._verified_coverage(body)
        state_key = self._state_key(states)
        if stored and lineage_id and not self.last_lineage.conflicted and weight:
            self._quality[(lineage_id, target, state_key)] = weight
            self.quality_writes += 1
        self.last_quality = EvidenceQualityStats(lineage_id, observations, transitions, weight)
        return self._quality_answer(target, states, self._weighted_support(target, state_key), alternatives, False)

    def _weighted_support(self, target: str, state_key: str) -> int:
        record = self._hypotheses.get(target, {}).get(state_key)
        if record is None:
            return 0
        total = 0
        for lineage_id in record["lineage_ids"]:
            self.quality_reads += 1
            if (lineage_id, target) in self._lineage_conflicts:
                continue
            total += self._quality.get((lineage_id, target, state_key), 0)
        return total

    def answer_from_quality_graph(self, question: str) -> HypothesisConsensusResult:
        entities = tuple(self._hypothesis_order)
        targets = self._question_targets(question, entities)
        unsupported = self._unsupported_entity_mentions(question, entities)
        reused = False
        if unsupported:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unsupported-quality-target")
        if len(targets) == 1:
            target = targets[0]
        elif len(targets) == 0 and self._hypothesis_focus in self._hypotheses:
            target = self._hypothesis_focus  # type: ignore[assignment]
            reused = True
        else:
            self._hypothesis_focus = None
            return self._h_abstain("abstain-ambiguous-quality-query")
        rows = self._hypotheses[target]
        self.hypothesis_reads += len(rows)
        ranked = []
        for state_key, record in rows.items():
            ranked.append((self._weighted_support(target, state_key), int(record["last_seen"]), record))
        ranked.sort(key=lambda row: (-row[0], -row[1]))
        if not ranked or ranked[0][0] <= 0:
            return self._h_abstain("abstain-no-verified-quality-support")
        best = ranked[0][0]
        tied = [row for row in ranked if row[0] == best]
        if len(tied) != 1:
            self.hypothesis_conflict_abstentions += 1
            self._hypothesis_focus = None
            return self._h_abstain("abstain-unresolved-verified-quality-conflict")
        self._hypothesis_focus = target
        return self._quality_answer(target, tuple(tied[0][2]["states"]), best, len(ranked), reused)

    @staticmethod
    def _quality_answer(target: str, states, support: int, alternatives: int, reused: bool) -> HypothesisConsensusResult:
        details = "、".join(f"時点{node}は{value}" for _subject, _relation, node, value in states)
        answer = f"{target}は{details}です。独立由来だけでなく検算済み観測被覆を合計した支持重みは{support}で、競合仮説{alternatives}件の中で一意に最大です。"
        return HypothesisConsensusResult(True, target, tuple(states), answer, "shared-bounded-verified-evidence-quality-consensus-graph", support, alternatives, reused)

    def quality_graph_bytes(self) -> bytes:
        payload = {
            "lineage": json.loads(self.lineage_graph_bytes().decode("utf-8")),
            "quality": [(*key, value) for key, value in sorted(self._quality.items())],
            "max_quality_weight": self.max_quality_weight,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
