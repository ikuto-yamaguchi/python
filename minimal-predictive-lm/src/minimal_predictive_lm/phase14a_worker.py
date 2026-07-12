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
from .wordnet_ontology import OntologyBackedQuantifier, WordNetNounOntology


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def main() -> None:
    request = json.load(sys.stdin)
    maximum = int(request["policy"]["max_output_chars"])
    source_path = os.environ.get("MPM_WORDNET_ZIP")
    if not source_path:
        raise RuntimeError("MPM_WORDNET_ZIP is required for Phase 14a")

    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_scope_corrected_algebra_model()
    quantifier = build_public_quantifier()
    ontology = WordNetNounOntology.from_zip_path(source_path)
    grounded = OntologyBackedQuantifier(quantifier, ontology)

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
            before = ontology.metrics()
            output = grounded.answer(prompt)
            after = ontology.metrics()
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
    metrics = ontology.metrics()
    program_bits = phase12.description_bits + algebra.description_bits + quantifier.description_bits
    persistent_bytes = (program_bits + ontology.cache_bits + 7) // 8 + ontology.source_bytes
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": persistent_bytes,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "ontology_source_sha256": metrics.source_sha256,
                "ontology_source_bytes": metrics.source_bytes,
                "ontology_cache_entries": metrics.cache_entries,
                "ontology_cache_bits": metrics.cache_bits,
                "ontology_queries": metrics.queries,
                "ontology_cache_hits": metrics.cache_hits,
                "ontology_synset_reads": metrics.synset_reads,
                "ontology_edge_reads": metrics.edge_reads,
                "domain_specific_handlers": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
