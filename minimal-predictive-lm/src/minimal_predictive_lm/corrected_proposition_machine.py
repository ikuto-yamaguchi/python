from __future__ import annotations

import json
import re

from .generic_proposition_machine import (
    BoolExpr,
    GenericPropositionMachine,
    PropositionPrediction,
    any_of,
    neg,
)
from .queue_signed_claim_runtime import QueueSignedClaimRuntime
from .signed_claim_graph import (
    AttributionObservation,
    SignedClaimMachine,
    TruthPhraseObservation,
    induce_signed_claim_machine,
)


def _bits(payload: object) -> int:
    return len(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) * 8


def build_default_signed_claim_machine() -> SignedClaimMachine:
    """Ground shared truth-report language from independent phrase observations."""

    induced = induce_signed_claim_machine(
        (
            TruthPhraseObservation("tells the truth", True),
            TruthPhraseObservation("tell the truth", True),
            TruthPhraseObservation("is reliable", True),
            TruthPhraseObservation("is accurate", True),
            TruthPhraseObservation("is correct", True),
            TruthPhraseObservation("is valid", True),
            TruthPhraseObservation("lies", False),
            TruthPhraseObservation("lie", False),
            TruthPhraseObservation("is unreliable", False),
            TruthPhraseObservation("is inaccurate", False),
            TruthPhraseObservation("is wrong", False),
            TruthPhraseObservation("is invalid", False),
        ),
        (
            AttributionObservation("says"),
            AttributionObservation("reports"),
            AttributionObservation("claims"),
        ),
    )
    return SignedClaimMachine(
        truth_phrases=induced.truth_phrases,
        attribution_phrases=induced.attribution_phrases,
        runtime=QueueSignedClaimRuntime(),
    )


class CorrectedPropositionMachine(GenericPropositionMachine):
    """Shared signed-claim and monadic finite-model proposition machine.

    The belief component is no longer tied to one benchmark surface. Phrase
    meanings are grounded by independent observations and compile testimony,
    sensor reports, incident logs, and code-review claims into one signed graph.
    A queue work-list propagates each discovered signed value once. The
    controlled monadic formal-language compiler and finite-model entailment
    runtime remain shared with the previous machine.
    """

    def __init__(self) -> None:
        super().__init__()
        self.claim_machine = build_default_signed_claim_machine()
        formal_spec = {
            "runtime": "finite-model-entailment-for-equality-free-monadic-logic",
            "surface": "controlled-quantified-proposition-compiler",
            "maximum_predicate_atoms": 14,
            "none_of_scope": "negate-full-disjunction",
            "outside_fragment": "abstain",
            "signed_claim_schedule": "linear-queue-worklist",
        }
        self.description_bits = self.claim_machine.description_bits + _bits(formal_spec)
        self.human_designed_surface_compilers = 2
        self.benchmark_task_name_branches = 0

    def _predict_belief(self, prompt: str) -> PropositionPrediction | None:
        program = self.claim_machine.compile(prompt)
        if program is None:
            return None
        prediction = self.claim_machine.runtime.execute(program)
        return PropositionPrediction(
            prediction.output,
            prediction.operations,
            prediction.reads,
            prediction.writes,
            "proposition-signed-claim",
        )

    def _expr(self, text: str) -> BoolExpr:
        cleaned = self._clean(text)
        match = re.fullmatch(
            r"none of (?:this|these):\s*(.+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if match:
            members = self._split_top(match.group(1), "or")
            if len(members) > 1:
                return neg(any_of(*(self._expr(member) for member in members)))
        return super()._expr(text)
