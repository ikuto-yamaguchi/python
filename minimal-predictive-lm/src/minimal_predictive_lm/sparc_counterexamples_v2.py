from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path

from .sparc_counterexamples import SPARCHS14Model, SparseCounterexampleValidator
from .sparc_goal_rules import SPARCHS13Model
from .sparc_language import ReplyResult


class SPARCHS14ModelV2(SPARCHS14Model):
    """HS14 model with guard reads included in successful-rule resource accounting."""

    def reply(self, text: str) -> ReplyResult:
        matched = self.validator._matching_schema(text, self.rules)
        direct_present = False
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
            direct_present = bool(direct)
            if not direct_present:
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
        result = self.base.reply(text)
        if (
            matched is not None
            and not direct_present
            and result.mechanism == "goal-directed-learned-rule"
        ):
            return ReplyResult(
                text=result.text,
                confidence=result.confidence,
                mechanism=result.mechanism,
                candidates_inspected=max(
                    result.candidates_inspected,
                    self.validator.last_rule_candidates,
                ),
                active_bits=result.active_bits + self.validator.last_matched_guards,
                estimated_sparse_operations=(
                    result.estimated_sparse_operations
                    + self.validator.last_guard_reads
                    + self.validator.last_rule_candidates
                ),
            )
        return result

    @classmethod
    def from_bytes(cls, data: bytes) -> "SPARCHS14ModelV2":
        payload = json.loads(zlib.decompress(data))
        model = cls(SPARCHS13Model.from_bytes(base64.b85decode(payload["base"])))
        model.validator = SparseCounterexampleValidator.from_bytes(
            base64.b85decode(payload["validator"])
        )
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SPARCHS14ModelV2":
        return cls.from_bytes(Path(path).read_bytes())
