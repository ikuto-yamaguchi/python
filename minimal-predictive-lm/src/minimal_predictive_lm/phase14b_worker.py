from __future__ import annotations

import json
import os
import resource
import sys

from .benchmark_harness import ABSTAIN_TOKEN
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13c_experiment import build_scope_corrected_algebra_model
from .phase13d_experiment import build_public_quantifier
from .phase14b_experiment import build_phase14b_graph
from .provenance_concept_graph import ProvenanceOverlayOntology
from .wordnet_ontology import OntologyBackedQuantifier, WordNetNounOntology


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def main() -> None:
    request = json.load(sys.stdin)
    maximum = int(request["policy"]["max_output_chars"])
    source_path = os.environ.get("MPM_WORDNET_ZIP")
    if not source_path:
        raise RuntimeError("MPM_WORDNET_ZIP is required for Phase 14b")

    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_scope_corrected_algebra_model()
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
            before_overlay_queries = overlay.queries
            output = grounded.answer(prompt)
            after = wordnet.metrics()
            operations += len(prompt) + (after.synset_reads - before.synset_reads)
            reads += (
                1
                + (after.edge_reads - before.edge_reads)
                + (overlay.queries - before_overlay_queries)
                + sum(len(decision.graph_proof) for decision in grounded.last_decisions)
            )
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
    metrics = wordnet.metrics()
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (persistent_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "wordnet_source_sha256": metrics.source_sha256,
                "wordnet_source_bytes": metrics.source_bytes,
                "wordnet_cache_bits": metrics.cache_bits,
                "document_sources": len(graph.source_ids),
                "document_edges": len(graph.edges),
                "document_graph_bits": graph.description_bits,
                "overlay_cache_bits": overlay.cache_bits,
                "overlay_queries": overlay.queries,
                "overlay_cache_hits": overlay.cache_hits,
                "domain_specific_handlers": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
