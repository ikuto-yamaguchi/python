from __future__ import annotations

import json
import os
import resource
import sys

from .aggregate_routing import phase12_prompt_eligibility, routing_guard_description_bits
from .benchmark_harness import ABSTAIN_TOKEN
from .english_role_compiler_v2 import EnglishRoleReferenceResolverV2
from .generic_state_machine import GenericStateMachine
from .generic_temporal_state import GenericTemporalMachine
from .induced_proposition_machine import InducedPropositionMachine
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13d_experiment import build_public_quantifier
from .phase14b_experiment import build_phase14b_graph
from .phase15b_experiment import build_guarded_algebra_model
from .provenance_concept_graph import ProvenanceOverlayOntology
from .wordnet_ontology import OntologyBackedQuantifier, WordNetNounOntology


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def main() -> None:
    request = json.load(sys.stdin)
    maximum = int(request["policy"]["max_output_chars"])
    source_path = os.environ.get("MPM_WORDNET_ZIP")
    if not source_path:
        raise RuntimeError("MPM_WORDNET_ZIP is required for HS17")

    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_guarded_algebra_model()
    state_machine = GenericStateMachine()
    temporal_machine = GenericTemporalMachine()
    proposition_machine = InducedPropositionMachine()
    reference_resolver = EnglishRoleReferenceResolverV2()
    quantifier = build_public_quantifier()
    wordnet = WordNetNounOntology.from_zip_path(source_path)
    document_graph = build_phase14b_graph()
    overlay = ProvenanceOverlayOntology(wordnet, document_graph)
    grounded = OntologyBackedQuantifier(quantifier, overlay)  # type: ignore[arg-type]

    predictions: list[dict[str, object]] = []
    decision_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for example in request["examples"]:
        prompt = str(example["prompt"])
        decision = phase12_prompt_eligibility(prompt)
        decision_counts[decision.reason] = decision_counts.get(decision.reason, 0) + 1
        output: object | None = None
        operations = 1
        reads = 0
        writes = 0
        family: str | None = None

        if decision.eligible:
            prior = phase12.predict(prompt)
            output = prior.output
            operations += prior.operations
            reads += prior.feature_reads
            if output is not None:
                writes += 1
                family = "phase12"
        if output is None:
            expression = algebra.predict(prompt)
            output = expression.output
            operations += expression.operations
            reads += 1
            if output is not None:
                writes += 1
                family = expression.family
        if output is None:
            state = state_machine.predict(prompt)
            output = state.output
            operations += state.operations
            reads += state.reads
            writes += state.writes
            if output is not None:
                family = state.family
        if output is None:
            temporal = temporal_machine.predict(prompt)
            output = temporal.output
            operations += temporal.operations
            reads += temporal.reads
            writes += temporal.writes
            if output is not None:
                family = "temporal"
        if output is None:
            proposition = proposition_machine.predict(prompt)
            output = proposition.output
            operations += proposition.operations
            reads += proposition.reads
            writes += proposition.writes
            if output is not None:
                family = proposition.family
        if output is None:
            reference = reference_resolver.answer(prompt)
            output = reference.output
            operations += reference.operations
            reads += reference.candidates
            if output is not None:
                writes += 1
                family = "shared-role-reference"
        if output is None:
            before = wordnet.metrics()
            output = grounded.answer(prompt)
            after = wordnet.metrics()
            operations += len(prompt) + (after.synset_reads - before.synset_reads)
            reads += 1 + (after.edge_reads - before.edge_reads)
            if output is not None:
                writes += 1
                family = "quantifier"

        text = ABSTAIN_TOKEN if output is None else str(output)
        if isinstance(output, bool):
            text = "true" if output else "false"
        if family is not None:
            family_counts[family] = family_counts.get(family, 0) + 1
        predictions.append(
            {
                "id": str(example["id"]),
                "text": text[:maximum],
                "operations": operations,
                "reads": reads,
                "writes": writes,
                "family": family,
                "routing_reason": decision.reason,
            }
        )

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    program_bits = (
        phase12.description_bits
        + algebra.description_bits
        + state_machine.description_bits
        + temporal_machine.description_bits
        + proposition_machine.description_bits
        + reference_resolver.machine.description_bits
        + quantifier.description_bits
        + routing_guard_description_bits()
    )
    persistent_bits = (
        program_bits
        + document_graph.description_bits
        + wordnet.cache_bits
        + overlay.cache_bits
        + wordnet.source_bytes * 8
    )
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (persistent_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "routing_guard_bits": routing_guard_description_bits(),
                "routing_decision_counts": decision_counts,
                "family_counts": family_counts,
                "proposition_runtime_bits": proposition_machine.description_bits,
                "reference_runtime_bits": reference_resolver.machine.description_bits,
                "reference_compiler_version": 2,
                "benchmark_task_name_branches": 0,
                "domain_specific_handlers": 0,
                "public_targets_used_for_role_weights": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
