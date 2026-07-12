from __future__ import annotations

import json
import resource
import sys

from .benchmark_harness import ABSTAIN_TOKEN
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13c_experiment import build_scope_corrected_algebra_model
from .phase13d_experiment import build_public_quantifier


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def main() -> None:
    request = json.load(sys.stdin)
    maximum = int(request["policy"]["max_output_chars"])
    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_scope_corrected_algebra_model()
    quantifier = build_public_quantifier()
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
            output = quantifier.answer(prompt)
            operations += len(prompt)
            reads += 1
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
    combined_bits = phase12.description_bits + algebra.description_bits + quantifier.description_bits
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (combined_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "universal_concepts": quantifier.universal_concepts,
                "membership_entries": len(quantifier.memberships),
                "domain_specific_handlers": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
