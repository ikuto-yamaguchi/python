from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import random

from .minimal_math_program import (
    MathTrace,
    exact_surface_accuracy,
    induce_math_grounder,
    program_accuracy,
)
from .stage_c_readiness import CapabilityEvidence, build_scorecard


def _trace(raw: str, answer: int | Fraction) -> MathTrace:
    return MathTrace.from_value(raw, answer)


TRAINING = (
    _trace("3に8を足す", 11),
    _trace("5に12を足してください", 17),
    _trace("4と9を足す", 13),
    _trace("6と11を足してください", 17),
    _trace("17から5を引く", 12),
    _trace("23から8を引いてください", 15),
    _trace("31から12を引く", 19),
    _trace("44から19を引いてください", 25),
    _trace("4と7を掛ける", 28),
    _trace("6と9を掛けてください", 54),
    _trace("8を5倍する", 40),
    _trace("11を3倍してください", 33),
    _trace("20を5で割る", 4),
    _trace("36を6で割ってください", 6),
    _trace("49を7で割る", 7),
    _trace("72を8で割ってください", 9),
    _trace("200の15パーセント", 30),
    _trace("80の25パーセントを求める", 20),
    _trace("300の12%", 36),
    _trace("240の20%を求めてください", 48),
)

NEAR_HELDOUT = (
    _trace("14に27を足して", 41),
    _trace("19と33を足してください", 52),
    _trace("91から38を引いて", 53),
    _trace("64から17を引いてください", 47),
    _trace("13と7を掛けて", 91),
    _trace("16を4倍してください", 64),
    _trace("81を9で割って", 9),
    _trace("100を8で割ってください", Fraction(25, 2)),
    _trace("360の15パーセント", 54),
    _trace("125の24%を求めて", 30),
)

CALIBRATION = (
    _trace("2と9の合計", 11),
    _trace("7と15の合計を出す", 22),
    _trace("18と7の差を左から計算", 11),
    _trace("25と9の差を左から計算", 16),
    _trace("3と12の積", 36),
    _trace("5と14の積を求める", 70),
    _trace("42と6の商", 7),
    _trace("63と9の商を求める", 7),
    _trace("500に対する8パーセント分", 40),
    _trace("250に対する12パーセント分", 30),
)

SHIFTED = (
    _trace("21と34の合計", 55),
    _trace("70と26の差を左から計算", 44),
    _trace("9と13の積", 117),
    _trace("96と12の商", 8),
    _trace("640に対する5パーセント分", 32),
)


def _numeric_generalization(grounder: object, *, seed: int = 113) -> dict[str, object]:
    rng = random.Random(seed)
    templates = {
        "ADD": lambda a, b: (f"{a}に{b}を足して", Fraction(a + b)),
        "SUB": lambda a, b: (f"{a}から{b}を引いて", Fraction(a - b)),
        "MUL": lambda a, b: (f"{a}と{b}を掛けて", Fraction(a * b)),
        "DIV": lambda a, b: (f"{a}を{b}で割って", Fraction(a, b)),
        "PERCENT_OF": lambda a, b: (f"{a}の{b}%を求めて", Fraction(a * b, 100)),
    }
    traces: list[MathTrace] = []
    per_program = 200
    for program, template in templates.items():
        for _ in range(per_program):
            if program == "DIV":
                b = rng.randint(2, 20)
                quotient = rng.randint(2, 50)
                a = b * quotient
            elif program == "SUB":
                b = rng.randint(1, 50)
                a = rng.randint(b + 1, b + 100)
            else:
                a = rng.randint(2, 500)
                b = rng.randint(2, 50)
            raw, answer = template(a, b)
            traces.append(MathTrace(raw, answer))
    return {
        "examples": len(traces),
        "accuracy": program_accuracy(grounder, traces),
        "programs": len(templates),
    }


def run() -> dict[str, object]:
    base = induce_math_grounder(TRAINING)
    calibrated = induce_math_grounder(TRAINING + CALIBRATION)
    near_accuracy = program_accuracy(base, NEAR_HELDOUT)
    shifted_before = program_accuracy(base, SHIFTED)
    shifted_after = program_accuracy(calibrated, SHIFTED)
    numeric = _numeric_generalization(base)

    stage_c = build_scorecard(
        (
            CapabilityEvidence("conversation", 2, 0.0625, 7204, "interaction-shifted synthetic grounding"),
            CapabilityEvidence("knowledge", 1, 1.0, 36864, "closed-world indexed retrieval"),
            CapabilityEvidence("mathematics", 2, min(near_accuracy, shifted_after), base.description_bits, "held-out numbers and interaction-calibrated lexical shift"),
            CapabilityEvidence("code", 1, 1.0, 7204, "synthetic repair workflow"),
            CapabilityEvidence("long_context", 1, 1.0, 6, "synthetic persistent-state test"),
            CapabilityEvidence("creative_writing", 0, 0.0, 0, "unmeasured"),
        )
    )

    return {
        "training": {
            "examples": len(TRAINING),
            "programs": 5,
            "rules": len(base.rules),
            "description_bits": base.description_bits,
        },
        "heldout": {
            "examples": len(NEAR_HELDOUT),
            "exact_surface_accuracy": exact_surface_accuracy(TRAINING, NEAR_HELDOUT),
            "program_accuracy": near_accuracy,
        },
        "numeric_generalization": numeric,
        "lexical_shift": {
            "calibration_examples": len(CALIBRATION),
            "shifted_examples": len(SHIFTED),
            "accuracy_before": shifted_before,
            "accuracy_after": shifted_after,
            "added_description_bits": calibrated.description_bits - base.description_bits,
        },
        "stage_c_after_math": {
            "points": stage_c.level_points,
            "maximum_points": stage_c.maximum_points,
            "normalized_level": stage_c.normalized_level,
            "stage_c_ready": stage_c.stage_c_ready,
            "weakest_axes": list(stage_c.weakest_axes()),
        },
        "limitations": [
            "only five binary arithmetic programs are available",
            "word problems, equations, proofs, geometry, and multi-step reasoning are not solved",
            "the benchmark is generated rather than a public mathematics benchmark",
            "lexical grounding still uses sparse surface features",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    training = payload["training"]
    heldout = payload["heldout"]
    numeric = payload["numeric_generalization"]
    shifted = payload["lexical_shift"]
    stage = payload["stage_c_after_math"]
    lines = [
        "# Phase 10b results: induced exact natural-language arithmetic programs",
        "",
        f"- training examples / programs: **{training['examples']} / {training['programs']}**",
        f"- selected rules: **{training['rules']}**",
        f"- program description: **{training['description_bits']:,} bits**",
        f"- exact-surface held-out: **{heldout['exact_surface_accuracy']:.1%}**",
        f"- program held-out: **{heldout['program_accuracy']:.1%}**",
        f"- unseen-number examples: **{numeric['examples']:,}**",
        f"- unseen-number accuracy: **{numeric['accuracy']:.1%}**",
        "",
        "## Lexical interaction calibration",
        "",
        f"- before: **{shifted['accuracy_before']:.1%}**",
        f"- after: **{shifted['accuracy_after']:.1%}**",
        f"- added description: **{shifted['added_description_bits']:,} bits**",
        "",
        "## Stage-C evidence",
        "",
        f"- readiness points: **{stage['points']} / {stage['maximum_points']}**",
        f"- normalized level: **{stage['normalized_level']:.1%}**",
        f"- Stage C ready: **{stage['stage_c_ready']}**",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output = Path("results")
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase10b.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "phase10b.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
