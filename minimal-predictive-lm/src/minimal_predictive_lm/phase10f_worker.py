from __future__ import annotations

from fractions import Fraction
import json
import resource
import sys

from .minimal_math_program import induce_math_grounder
from .phase10b_experiment import CALIBRATION, TRAINING


def _format_fraction(value: Fraction | None) -> str:
    if value is None:
        return "__ABSTAIN__"
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _rss_bytes(value: int) -> int:
    return value if sys.platform == "darwin" else value * 1024


def main() -> None:
    request = json.load(sys.stdin)
    policy = request["policy"]
    maximum = int(policy["max_output_chars"])
    grounder = induce_math_grounder(TRAINING + CALIBRATION)
    predictions: list[dict[str, object]] = []
    for example in request["examples"]:
        prediction = grounder.predict(str(example["prompt"]))
        text = _format_fraction(prediction.answer)[:maximum]
        predictions.append(
            {
                "id": str(example["id"]),
                "text": text,
                "operations": prediction.feature_reads + prediction.matched_rules + 1,
                "reads": prediction.feature_reads,
                "writes": 1,
            }
        )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    json.dump(
        {
            "predictions": predictions,
            "model_bytes": (grounder.description_bits + 7) // 8,
            "peak_rss_bytes": _rss_bytes(int(peak)),
            "energy_joules": None,
        },
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
