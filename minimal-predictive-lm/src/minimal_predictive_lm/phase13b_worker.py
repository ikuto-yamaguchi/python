from __future__ import annotations

from fractions import Fraction
import json
import resource
import sys

from .benchmark_harness import ABSTAIN_TOKEN
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions
from .phase13b_experiment import build_algebra_model


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def _format(value: object | None) -> str:
    if value is None:
        return ABSTAIN_TOKEN
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def main() -> None:
    request = json.load(sys.stdin)
    maximum = int(request["policy"]["max_output_chars"])
    phase12 = induce_mixed_task_model(calibration_interactions())
    algebra = build_algebra_model()
    predictions: list[dict[str, object]] = []
    for example in request["examples"]:
        prompt = str(example["prompt"])
        prior = phase12.predict(prompt)
        if prior.output is not None:
            output = prior.output
            operations = prior.operations
            reads = prior.feature_reads
            family = "phase12"
        else:
            added = algebra.predict(prompt)
            output = added.output
            operations = prior.operations + added.operations
            reads = prior.feature_reads + 1
            family = added.family
        predictions.append(
            {
                "id": str(example["id"]),
                "text": _format(output)[:maximum],
                "operations": operations,
                "reads": reads,
                "writes": 1 if output is not None else 0,
                "family": family,
            }
        )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    combined_bits = phase12.description_bits + algebra.description_bits
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (combined_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "phase12_rules": len(phase12.rules),
                "algebra_operator_programs": len(algebra.expression.operators),
                "precedence_candidates_evaluated": algebra.expression.precedence_candidates_evaluated,
                "domain_specific_handlers": 0,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
