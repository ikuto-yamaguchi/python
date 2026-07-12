from __future__ import annotations

import json
import os
import resource
import sys

from .benchmark_harness import ABSTAIN_TOKEN
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
        raise RuntimeError("MPM_WORDNET_ZIP is required for Phase 15b")

    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_guarded_algebra_model()
    quantifier = build_public_quantifier()
    wordnet = WordNetNounOntology.from_zip_path(source_path)
    graph = build_phase14b_graph()
    overlay = ProvenanceOverlayOntology(wordnet, graph)
    grounded = OntologyBackedQuantifier(quantifier, overlay)  # type: ignore[arg-type]

    predictions: list[dict[str, object]] = []
    for example in request["examples"]:
        prompt = str(example["prompt"])
        prior = phase12.predict(prompt)
        output: object | None = prior.output
        operations = prior.operations
        reads = prior.feature_reads
        if output is None:
            expression = algebra.predict(prompt)
            output = expression.output
            operations += expression.operations
            reads += 1
        if output is None:
            before = wordnet.metrics()
            output = grounded.answer(prompt)
            after = wordnet.metrics()
            operations += len(prompt) + (after.synset_reads - before.synset_reads)
            reads += 1 + (after.edge_reads - before.edge_reads)
        text = ABSTAIN_TOKEN if output is None else str(output)
        if isinstance(output, bool):
            text = "true" if output else "false"
        predictions.append(
            {
                "id": str(example["id"]),
                "text": text[:maximum],
                "operations": operations,
                "reads": reads,
                "writes": 1 if output is not None else 0,
            }
        )

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    program_bits = phase12.description_bits + algebra.description_bits + quantifier.description_bits
    persistent_bits = (
        program_bits
        + graph.description_bits
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
                "required_ordering_cues": list(algebra.ordering.required_cues),
                "ordering_candidate_cue_sets": algebra.ordering.candidate_cue_sets,
                "domain_specific_handlers": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
