from __future__ import annotations

from fractions import Fraction
import json
import resource
import sys

from .benchmark_harness import ABSTAIN_TOKEN
from .mixed_task_learner import induce_mixed_task_model
from .phase12a_experiment import calibration_interactions


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
    model = induce_mixed_task_model(calibration_interactions())
    predictions: list[dict[str, object]] = []
    for example in request["examples"]:
        prediction = model.predict(str(example["prompt"]))
        predictions.append(
            {
                "id": str(example["id"]),
                "text": _format(prediction.output)[:maximum],
                "operations": prediction.operations,
                "reads": prediction.feature_reads,
                "writes": 1 if prediction.output is not None else 0,
            }
        )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (model.description_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
            "metadata": {
                "rules": len(model.rules),
                "candidate_evaluations": model.candidate_evaluations,
                "domain_specific_handlers": model.domain_specific_handlers,
                "calibration_examples": model.calibration_examples,
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
