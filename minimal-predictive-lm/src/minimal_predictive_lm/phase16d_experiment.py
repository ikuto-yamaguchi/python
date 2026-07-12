from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import random

from .corrected_proposition_machine import CorrectedPropositionMachine
from .generic_proposition_machine import MonadicSentence, MonadicTheory, atom, implies
from .queue_signed_claim_runtime import QueueSignedClaimRuntime
from .signed_claim_graph import SignedClaimRuntime


def _alpha(index: int) -> str:
    value = index
    output = ""
    while True:
        value, remainder = divmod(value, 26)
        output = chr(ord("A") + remainder) + output
        if value == 0:
            return output
        value -= 1


def _entity(index: int) -> str:
    return f"Node{_alpha(index)}"


_TRUE_PHRASES = (
    "is reliable",
    "is accurate",
    "is correct",
    "is valid",
    "tells the truth",
)
_FALSE_PHRASES = (
    "is unreliable",
    "is inaccurate",
    "is wrong",
    "is invalid",
    "lies",
)
_ATTRIBUTIONS = ("says", "reports", "claims")


def _phrase(value: bool, index: int) -> str:
    pool = _TRUE_PHRASES if value else _FALSE_PHRASES
    return pool[index % len(pool)]


def build_chain_prompt(
    claim_count: int,
    *,
    seed: int = 0,
    order: str = "forward",
) -> tuple[str, str]:
    if claim_count < 1:
        raise ValueError("claim_count must be positive")
    truth = [((seed + index * 17) % 7) not in (0, 3, 6) for index in range(claim_count + 1)]
    statements = [f"{_entity(0)} {_phrase(truth[0], seed)}."]
    claims: list[str] = []
    for index in range(1, claim_count + 1):
        asserted = truth[index] == truth[index - 1]
        claims.append(
            f"{_entity(index)} {_ATTRIBUTIONS[(seed + index) % len(_ATTRIBUTIONS)]} "
            f"{_entity(index - 1)} {_phrase(asserted, seed + index)}."
        )
    if order == "forward":
        statements.extend(claims)
    elif order == "reverse":
        statements.extend(reversed(claims))
    elif order == "shuffled":
        rows = claims[:]
        random.Random(seed).shuffle(rows)
        statements.extend(rows)
    else:
        raise ValueError(f"unknown order: {order}")
    prompt = "Question: " + " ".join(statements) + f" Does {_entity(claim_count)} tell the truth?"
    return prompt, "Yes" if truth[-1] else "No"


def _run_chain(
    machine: CorrectedPropositionMachine,
    claim_count: int,
    *,
    seed: int,
    order: str,
) -> dict[str, object]:
    prompt, expected = build_chain_prompt(claim_count, seed=seed, order=order)
    program = machine.claim_machine.compile(prompt)
    if program is None:
        raise AssertionError("generated chain did not compile")
    legacy = SignedClaimRuntime().execute(program)
    queue = QueueSignedClaimRuntime().execute(program)
    return {
        "claims": claim_count,
        "order": order,
        "expected": expected,
        "legacy": asdict(legacy),
        "queue": asdict(queue),
        "equivalent": legacy.output == queue.output == expected,
        "operation_speedup": legacy.operations / max(queue.operations, 1),
    }


def _random_shift_audit(machine: CorrectedPropositionMachine) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for seed in range(100):
        claim_count = 1 + (seed * 29) % 96
        order = ("forward", "reverse", "shuffled")[seed % 3]
        prompt, expected = build_chain_prompt(claim_count, seed=seed + 101, order=order)
        prediction = machine.predict(prompt)
        rows.append(
            {
                "seed": seed,
                "claims": claim_count,
                "order": order,
                "expected": expected,
                "actual": prediction.output,
                "correct": prediction.output == expected,
                "operations": prediction.operations,
            }
        )
    return {
        "examples": len(rows),
        "correct": sum(int(row["correct"]) for row in rows),
        "maximum_claims": max(int(row["claims"]) for row in rows),
        "maximum_operations": max(int(row["operations"]) for row in rows),
        "failures": [row for row in rows if not row["correct"]],
    }


def _abstention_audit(machine: CorrectedPropositionMachine) -> dict[str, object]:
    cases = {
        "contradiction": (
            "Question: BaseA is reliable. JudgeB says BaseA is reliable. "
            "JudgeB reports BaseA is unreliable. Does JudgeB tell the truth?"
        ),
        "unanchored_cycle": (
            "Question: AnchorA is reliable. NodeB says NodeC is reliable. "
            "NodeC claims NodeB is reliable. Does NodeB tell the truth?"
        ),
        "unknown_grounding": (
            "Question: BaseA is trustworthy. JudgeB says BaseA is reliable. "
            "Does JudgeB tell the truth?"
        ),
    }
    predictions = {name: machine.predict(prompt).output for name, prompt in cases.items()}
    return {
        "predictions": predictions,
        "all_abstained": all(output is None for output in predictions.values()),
    }


def _formal_scaling_audit() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for length in (2, 4, 8, 12):
        predicates = [atom(f"trait-{_alpha(index).lower()}") for index in range(length + 1)]
        premises = tuple(
            MonadicSentence("all", implies(predicates[index], predicates[index + 1]))
            for index in range(length)
        )
        theory = MonadicTheory(premises)
        forward = theory.entails(MonadicSentence("all", implies(predicates[0], predicates[-1])))
        converse = theory.entails(MonadicSentence("all", implies(predicates[-1], predicates[0])))
        rows.append(
            {
                "links": length,
                "forward_valid": forward,
                "converse_invalid": not converse,
            }
        )
    return {
        "cases": rows,
        "all_correct": all(row["forward_valid"] and row["converse_invalid"] for row in rows),
    }


def run() -> dict[str, object]:
    machine = CorrectedPropositionMachine()
    scaling = [
        _run_chain(machine, length, seed=41, order=order)
        for length in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        for order in ("forward", "reverse")
    ]
    random_shift = _random_shift_audit(machine)
    abstention = _abstention_audit(machine)
    formal = _formal_scaling_audit()
    worst_reverse = next(
        row for row in scaling if row["claims"] == 1024 and row["order"] == "reverse"
    )
    queue_linear = all(
        int(row["queue"]["operations"]) <= 4 * int(row["claims"]) + 4
        for row in scaling
    )
    return {
        "phase": "16d",
        "protocol": {
            "public_benchmark_examples_used": 0,
            "public_benchmark_targets_used": 0,
            "generated_chain_examples": len(scaling) + random_shift["examples"],
            "fixed_random_seed": True,
            "tested_shifts": [
                "truth phrase substitution",
                "attribution phrase substitution",
                "forward order",
                "reverse order",
                "shuffled order",
                "long chains",
                "contradiction",
                "unanchored cycle",
                "unknown grounding",
            ],
        },
        "runtime": {
            "algorithm": "queue work-list signed propagation",
            "description_bits": machine.description_bits,
            "description_bytes": (machine.description_bits + 7) // 8,
            "model_size_independent_of_chain_length": True,
        },
        "scaling": scaling,
        "random_distribution_shift": random_shift,
        "abstention": abstention,
        "formal_logic": formal,
        "headline": {
            "reverse_1024_legacy_operations": worst_reverse["legacy"]["operations"],
            "reverse_1024_queue_operations": worst_reverse["queue"]["operations"],
            "reverse_1024_operation_speedup": worst_reverse["operation_speedup"],
        },
        "gates": {
            "legacy_queue_semantic_equivalence": all(row["equivalent"] for row in scaling),
            "queue_operations_linear": queue_linear,
            "reverse_1024_speedup_over_100x": worst_reverse["operation_speedup"] > 100,
            "random_shift_100_of_100": random_shift["correct"] == random_shift["examples"],
            "safe_abstention_retained": abstention["all_abstained"],
            "formal_chain_and_converse_checks_passed": formal["all_correct"],
            "general_llm_parity_allowed": False,
        },
        "limitations": [
            "generated chains exercise unary signed reliability claims, not arbitrary nested propositions",
            "operation counts are abstract interpreter steps rather than hardware energy measurements",
            "phrase meanings remain independently supervised groundings",
            "formal finite-model search remains bounded to the controlled monadic fragment",
            "this phase measures robustness and scaling, not a new public capability",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    headline = payload["headline"]
    shifted = payload["random_distribution_shift"]
    gates = payload["gates"]
    lines = [
        "# Phase 16d results: signed-claim scaling and shift audit",
        "",
        "No public benchmark examples or targets are used. The Phase 16c semantics",
        "are held fixed while a queue work-list replaces repeated whole-graph scans.",
        "",
        "## Headline",
        "",
        f"- random shifted chains: **{shifted['correct']}/{shifted['examples']}**",
        f"- reverse 1,024-link legacy operations: **{headline['reverse_1024_legacy_operations']:,}**",
        f"- reverse 1,024-link queue operations: **{headline['reverse_1024_queue_operations']:,}**",
        f"- abstract operation speedup: **{headline['reverse_1024_operation_speedup']:.1f}x**",
        f"- safe abstention retained: **{gates['safe_abstention_retained']}**",
        f"- formal chain/converse checks: **{gates['formal_chain_and_converse_checks_passed']}**",
        "",
        "## Scaling",
        "",
        "| claims | order | legacy operations | queue operations | speedup | correct |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in payload["scaling"]:
        lines.append(
            f"| {row['claims']} | {row['order']} | {row['legacy']['operations']} | "
            f"{row['queue']['operations']} | {row['operation_speedup']:.1f}x | {row['equivalent']} |"
        )
    lines.extend(["", "## Claim boundary", ""])
    lines.append(
        "This phase supports only semantic equivalence, distribution-shift robustness, "
        "and abstract operation-scaling claims for the measured signed-claim fragment."
    )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase16d.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "phase16d.md").write_text(render_markdown(payload), encoding="utf-8")
    print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
