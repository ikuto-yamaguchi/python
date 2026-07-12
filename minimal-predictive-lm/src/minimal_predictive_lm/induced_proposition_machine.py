from __future__ import annotations

from .corrected_proposition_machine import (
    CorrectedPropositionMachine,
    build_default_signed_claim_machine,
)
from .generic_proposition_machine import PropositionPrediction
from .induced_clause_compiler import (
    ClauseEvent,
    ClauseObservation,
    InducedClauseCompiler,
    induce_clause_compiler,
)


def independent_clause_observations() -> tuple[ClauseObservation, ...]:
    """Canonical event supervision from non-benchmark testimony-like domains."""

    return (
        ClauseObservation(
            "Mira is reliable.",
            ClauseEvent("base", entity="Mira", polarity=True),
        ),
        ClauseObservation(
            "SensorA is inaccurate.",
            ClauseEvent("base", entity="SensorA", polarity=False),
        ),
        ClauseObservation(
            "Sol reports Mira is reliable.",
            ClauseEvent(
                "claim",
                speaker="Sol",
                target="Mira",
                polarity=True,
            ),
        ),
        ClauseObservation(
            "SensorB claims SensorA is inaccurate.",
            ClauseEvent(
                "claim",
                speaker="SensorB",
                target="SensorA",
                polarity=False,
            ),
        ),
        ClauseObservation(
            "ReviewerB says PatchA is invalid.",
            ClauseEvent(
                "claim",
                speaker="ReviewerB",
                target="PatchA",
                polarity=False,
            ),
        ),
        ClauseObservation(
            "Does Taro tell the truth?",
            ClauseEvent("query", entity="Taro", polarity=True),
        ),
        ClauseObservation(
            "Does SensorC lie?",
            ClauseEvent("query", entity="SensorC", polarity=False),
        ),
    )


def build_induced_clause_compiler() -> InducedClauseCompiler:
    grounded = build_default_signed_claim_machine()
    return induce_clause_compiler(
        independent_clause_observations(),
        truth_phrases=grounded.truth_map(),
        attribution_phrases=grounded.attribution_phrases,
    )


class InducedPropositionMachine(CorrectedPropositionMachine):
    """Use observed clause templates for claims and retain shared formal logic."""

    def __init__(self) -> None:
        super().__init__()
        self.induced_clause_compiler = build_induced_clause_compiler()
        self.description_bits += self.induced_clause_compiler.description_bits
        self.human_designed_surface_compilers = 1
        self.induced_surface_compilers = 1

    def _predict_belief(self, prompt: str) -> PropositionPrediction | None:
        program = self.induced_clause_compiler.compile_prompt(prompt)
        if program is None:
            return None
        prediction = self.claim_machine.runtime.execute(program)
        return PropositionPrediction(
            prediction.output,
            prediction.operations,
            prediction.reads,
            prediction.writes,
            "proposition-induced-signed-claim",
        )
