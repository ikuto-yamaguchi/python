from __future__ import annotations

import base64
import json
import math
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .sparc_cross_domain_plans import _template_regex
from .sparc_episodic import SparseEpisodicRevisionMemory
from .sparc_goal_rules import GoalRule, SPARCHS13Model, SparseGoalRuleBank, _answer_value
from .sparc_language import ReplyResult
from .sparc_relational_plans import SparseRelationalPlanBank


@dataclass(frozen=True)
class GuardCondition:
    relation: str
    value: str
    refutation_support: int


@dataclass(frozen=True)
class RuleValidationState:
    rule_id: int
    supports: int
    refutations: int
    exclusion_guards: tuple[GuardCondition, ...]


class SparseCounterexampleValidator:
    """Learns a few local exclusion conditions from source-grounded refutations."""

    def __init__(self, *, max_guards_per_rule: int = 4) -> None:
        self.max_guards_per_rule = max_guards_per_rule
        self.states: dict[int, RuleValidationState] = {}
        self.last_validation_examples = 0
        self.last_validation_edge_reads = 0
        self.last_guard_reads = 0
        self.last_rule_candidates = 0
        self.last_blocked_rules = 0
        self.last_matched_guards = 0

    @staticmethod
    def _matching_schema(
        question: str,
        rules: SparseGoalRuleBank,
    ) -> tuple[str, str] | None:
        for schema_id in rules._candidate_schemas(question):
            schema = rules.schemas[schema_id]
            match = _template_regex(schema.template).match(question)
            if match is not None:
                return match.group(1), schema.head_relation
        return None

    @staticmethod
    def _execute_body(
        subject: str,
        rule: GoalRule,
        *,
        rules: SparseGoalRuleBank,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> set[str]:
        frontier: set[str] = {subject}
        for relation in rule.body_relations:
            next_frontier: set[str] = set()
            for node in tuple(frontier)[: rules.max_frontier]:
                values = rules._resolve(
                    node,
                    relation,
                    graph=graph,
                    episodic=episodic,
                    depth=1,
                    visited=frozenset(),
                )
                if rules.last_conflict:
                    return set()
                next_frontier.update(item.value for item in values[: rules.max_frontier])
            if not next_frontier:
                return set()
            frontier = next_frontier
        return frontier

    @staticmethod
    def _context_features(
        subject: str,
        rule: GoalRule,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
        edge_counter: list[int],
    ) -> set[tuple[str, str]]:
        excluded_relations = {rule.head_relation, *rule.body_relations}
        features: set[tuple[str, str]] = set()
        for relation in sorted(graph.outgoing.get(subject, {})):
            if relation in excluded_relations:
                continue
            evidence = graph._relation_values(subject, relation, episodic)
            edge_counter[0] += len(graph.outgoing.get(subject, {}).get(relation, ()))
            values = {item.value for item in evidence}
            if len(values) == 1:
                features.add((relation, next(iter(values))))
        return features

    def validate(
        self,
        examples: Iterable[tuple[str, str]],
        *,
        rules: SparseGoalRuleBank,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
        min_refutations: int = 2,
    ) -> dict[int, RuleValidationState]:
        support_features: dict[int, Counter[tuple[str, str]]] = defaultdict(Counter)
        refute_features: dict[int, Counter[tuple[str, str]]] = defaultdict(Counter)
        supports: Counter[int] = Counter()
        refutations: Counter[int] = Counter()
        self.last_validation_examples = 0
        self.last_validation_edge_reads = 0

        for question, observed_answer in examples:
            matched = self._matching_schema(question, rules)
            if matched is None:
                raise ValueError("validation question matches no learned goal schema")
            subject, head_relation = matched
            expected = _answer_value(observed_answer)
            rule_ids = tuple(rules.rules_by_head.get(head_relation, ()))
            if not rule_ids:
                raise ValueError("validation target has no learned rule")

            direct_counter = [0]
            observed = rules._direct_values(
                subject,
                head_relation,
                graph=graph,
                episodic=episodic,
                counter=direct_counter,
            )
            self.last_validation_edge_reads += direct_counter[0]
            if expected not in {item.value for item in observed}:
                raise ValueError(
                    "validation answer must be backed by an active direct head fact"
                )

            for rule_id in rule_ids[:8]:
                rule = rules.rules[rule_id]
                rules.last_conflict = False
                predicted = self._execute_body(
                    subject,
                    rule,
                    rules=rules,
                    graph=graph,
                    episodic=episodic,
                )
                edge_counter = [0]
                features = self._context_features(
                    subject,
                    rule,
                    graph=graph,
                    episodic=episodic,
                    edge_counter=edge_counter,
                )
                self.last_validation_edge_reads += edge_counter[0]
                if expected in predicted and len(predicted) == 1:
                    supports[rule_id] += 1
                    support_features[rule_id].update(features)
                else:
                    refutations[rule_id] += 1
                    refute_features[rule_id].update(features)
            self.last_validation_examples += 1

        for rule_id in set(supports) | set(refutations):
            refute_total = refutations[rule_id]
            candidates: list[GuardCondition] = []
            if refute_total >= min_refutations:
                for (relation, value), count in refute_features[rule_id].items():
                    if count == refute_total and support_features[rule_id][(relation, value)] == 0:
                        candidates.append(GuardCondition(relation, value, count))
            candidates.sort(
                key=lambda guard: (
                    -guard.refutation_support,
                    guard.relation,
                    guard.value,
                )
            )
            self.states[rule_id] = RuleValidationState(
                rule_id,
                supports[rule_id],
                refutations[rule_id],
                tuple(candidates[: self.max_guards_per_rule]),
            )
        return dict(self.states)

    def matching_guards(
        self,
        subject: str,
        rule_id: int,
        *,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> tuple[GuardCondition, ...]:
        state = self.states.get(rule_id)
        if state is None or not state.exclusion_guards:
            return ()
        matched: list[GuardCondition] = []
        for guard in state.exclusion_guards:
            evidence = graph._relation_values(subject, guard.relation, episodic)
            self.last_guard_reads += len(
                graph.outgoing.get(subject, {}).get(guard.relation, ())
            )
            if guard.value in {item.value for item in evidence}:
                matched.append(guard)
        return tuple(matched)

    def blocked_rules(
        self,
        subject: str,
        head_relation: str,
        *,
        rules: SparseGoalRuleBank,
        graph: SparseRelationalPlanBank,
        episodic: SparseEpisodicRevisionMemory,
    ) -> dict[int, tuple[GuardCondition, ...]]:
        self.last_guard_reads = 0
        self.last_blocked_rules = 0
        self.last_matched_guards = 0
        output: dict[int, tuple[GuardCondition, ...]] = {}
        rule_ids = tuple(rules.rules_by_head.get(head_relation, ()))[:8]
        self.last_rule_candidates = len(rule_ids)
        for rule_id in rule_ids:
            guards = self.matching_guards(
                subject,
                rule_id,
                graph=graph,
                episodic=episodic,
            )
            if guards:
                output[rule_id] = guards
                self.last_blocked_rules += 1
                self.last_matched_guards += len(guards)
        return output

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-counterexample-validator-hs14",
            "max_guards_per_rule": self.max_guards_per_rule,
            "states": [asdict(state) for state in self.states.values()],
        }
        return zlib.compress(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SparseCounterexampleValidator":
        payload = json.loads(zlib.decompress(data))
        validator = cls(max_guards_per_rule=int(payload["max_guards_per_rule"]))
        for row in payload["states"]:
            state = RuleValidationState(
                int(row["rule_id"]),
                int(row["supports"]),
                int(row["refutations"]),
                tuple(
                    GuardCondition(
                        str(guard["relation"]),
                        str(guard["value"]),
                        int(guard["refutation_support"]),
                    )
                    for guard in row["exclusion_guards"]
                ),
            )
            validator.states[state.rule_id] = state
        return validator

    def report(self) -> dict[str, int | bool | float]:
        supports = sum(state.supports for state in self.states.values())
        refutations = sum(state.refutations for state in self.states.values())
        return {
            "validated_rules": len(self.states),
            "supports": supports,
            "refutations": refutations,
            "exclusion_guards": sum(
                len(state.exclusion_guards) for state in self.states.values()
            ),
            "posterior_support_fraction": (
                (supports + 1) / (supports + refutations + 2)
                if self.states
                else 0.5
            ),
            "serialized_bytes": len(self.to_bytes()),
            "last_validation_examples": self.last_validation_examples,
            "last_validation_edge_reads": self.last_validation_edge_reads,
            "last_rule_candidates": self.last_rule_candidates,
            "last_guard_reads": self.last_guard_reads,
            "last_blocked_rules": self.last_blocked_rules,
            "last_matched_guards": self.last_matched_guards,
            "validation_scan_used_at_inference": False,
            "global_exception_scan_used": False,
        }


class SPARCHS14Model:
    def __init__(self, base: SPARCHS13Model | None = None) -> None:
        self.base = base or SPARCHS13Model()
        self.validator = SparseCounterexampleValidator()

    @property
    def episodic(self) -> SparseEpisodicRevisionMemory:
        return self.base.episodic

    @property
    def graph(self) -> SparseRelationalPlanBank:
        return self.base.graph

    @property
    def rules(self) -> SparseGoalRuleBank:
        return self.base.goal_rules

    def ingest_fact(
        self, text: str, *, source_id: str, revision: bool = False
    ) -> tuple[int, ...]:
        return self.base.ingest_fact(text, source_id=source_id, revision=revision)

    def validate_rules(
        self, examples: Iterable[tuple[str, str]], *, min_refutations: int = 2
    ) -> dict[int, RuleValidationState]:
        return self.validator.validate(
            examples,
            rules=self.rules,
            graph=self.graph,
            episodic=self.episodic,
            min_refutations=min_refutations,
        )

    def reply(self, text: str) -> ReplyResult:
        matched = self.validator._matching_schema(text, self.rules)
        if matched is not None:
            subject, head_relation = matched
            direct_counter = [0]
            direct = self.rules._direct_values(
                subject,
                head_relation,
                graph=self.graph,
                episodic=self.episodic,
                counter=direct_counter,
            )
            if not direct:
                blocked = self.validator.blocked_rules(
                    subject,
                    head_relation,
                    rules=self.rules,
                    graph=self.graph,
                    episodic=self.episodic,
                )
                all_rule_ids = tuple(self.rules.rules_by_head.get(head_relation, ()))[:8]
                if all_rule_ids and all(rule_id in blocked for rule_id in all_rule_ids):
                    conditions = sorted(
                        {
                            f"{guard.relation}={guard.value}"
                            for guards in blocked.values()
                            for guard in guards
                        }
                    )
                    operations = (
                        self.validator.last_guard_reads
                        + self.validator.last_rule_candidates
                        + len(conditions)
                    )
                    return ReplyResult(
                        text=(
                            f"{subject}は反例から学んだ条件"
                            f"{'、'.join(conditions)}に一致するため、"
                            f"規則だけでは{head_relation}を確定できません。"
                        ),
                        confidence=0.30,
                        mechanism="counterexample-guarded-rule",
                        candidates_inspected=self.validator.last_rule_candidates,
                        active_bits=len(conditions),
                        estimated_sparse_operations=operations,
                    )
        return self.base.reply(text)

    def to_bytes(self) -> bytes:
        payload = {
            "format": "sparc-hs14",
            "base": base64.b85encode(self.base.to_bytes()).decode("ascii"),
            "validator": base64.b85encode(self.validator.to_bytes()).decode("ascii"),
        }
        return zlib.compress(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            9,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS14Model":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS13Model.from_bytes(base64.b85decode(payload["base"])))
        model.validator = SparseCounterexampleValidator.from_bytes(
            base64.b85decode(payload["validator"])
        )
        return model

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.to_bytes())

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS14Model":
        return cls.from_bytes(Path(path).read_bytes())

    def report(self) -> dict[str, object]:
        return {
            "stage": "SPARC-HS14",
            "base": self.base.report(),
            "counterexample_validator": self.validator.report(),
            "serialized_bytes": len(self.to_bytes()),
            "transformer_used": False,
            "growing_kv_cache_used": False,
        }
