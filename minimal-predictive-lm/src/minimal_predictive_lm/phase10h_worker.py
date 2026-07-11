from __future__ import annotations

from fractions import Fraction
import json
import resource
import sys

from .minimal_math_program import MathTrace, induce_math_grounder


ENGLISH_CALIBRATION = (
    MathTrace.from_value("What is 12 plus 34?", 46),
    MathTrace.from_value("What is 21 plus 45?", 66),
    MathTrace.from_value("What is 34 minus 12?", 22),
    MathTrace.from_value("What is 50 minus 17?", 33),
    MathTrace.from_value("What is 6 times 7?", 42),
    MathTrace.from_value("What is 9 times 8?", 72),
    MathTrace.from_value("What is 42 divided by 6?", 7),
    MathTrace.from_value("What is 72 divided by 8?", 9),
    MathTrace.from_value("What is 20 percent of 50?", 10),
    MathTrace.from_value("What is 25 percent of 80?", 20),
)


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
    maximum = int(request["policy"]["max_output_chars"])
    grounder = induce_math_grounder(ENGLISH_CALIBRATION)
    predictions: list[dict[str, object]] = []
    for example in request["examples"]:
        prediction = grounder.predict(str(example["prompt"]))
        predictions.append(
            {
                "id": str(example["id"]),
                "text": _format_fraction(prediction.answer)[:maximum],
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
