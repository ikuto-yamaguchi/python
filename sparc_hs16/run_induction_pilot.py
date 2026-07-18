from __future__ import annotations

import json
import random
import time

from sparc_hs16.induction import NumericDemonstration, NumericMechanismBank
from sparc_hs16.model import SparseMemory


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * 0.95)]


def main() -> None:
    memory = SparseMemory()
    bank = NumericMechanismBank(memory)
    distance = bank.learn(
        "distance",
        [
            NumericDemonstration("時速30kmで2時間進む距離は？", "60"),
            NumericDemonstration("時速45kmで3時間進む距離は？", "135"),
            NumericDemonstration("時速12kmで5時間進む距離は？", "60"),
            NumericDemonstration("時速80kmで4時間進む距離は？", "320"),
        ],
    )
    inventory = bank.learn(
        "inventory",
        [
            NumericDemonstration("在庫10個に3箱、各4個を追加すると？", "22"),
            NumericDemonstration("在庫7個に5箱、各2個を追加すると？", "17"),
            NumericDemonstration("在庫20個に2箱、各8個を追加すると？", "36"),
            NumericDemonstration("在庫1個に9箱、各3個を追加すると？", "28"),
        ],
    )

    rng = random.Random(1919)
    correct = 0
    total = 0
    latencies: list[float] = []
    for _ in range(100):
        speed, hours = rng.randint(1, 120), rng.randint(1, 12)
        prompt = f"時速{speed}kmで{hours}時間進む距離は？"
        started = time.perf_counter()
        solved = bank.solve(prompt)
        latencies.append((time.perf_counter() - started) * 1000)
        correct += int(solved is not None and solved[0] == str(speed * hours))
        total += 1
    for _ in range(100):
        base, boxes, each = rng.randint(0, 100), rng.randint(1, 20), rng.randint(1, 30)
        prompt = f"在庫{base}個に{boxes}箱、各{each}個を追加すると？"
        started = time.perf_counter()
        solved = bank.solve(prompt)
        latencies.append((time.perf_counter() - started) * 1000)
        correct += int(solved is not None and solved[0] == str(base + boxes * each))
        total += 1

    report = {
        "capability_id": "SPARC-HS16-AUTONOMOUS-NUMERIC-PROGRAM-INDUCTION",
        "demonstrations": 8,
        "unseen_cases": total,
        "correct": correct,
        "accuracy": correct / total,
        "learned_programs": {
            "distance": distance.expression,
            "inventory": inventory.expression,
        },
        "candidates_checked": {
            "distance": distance.candidates_checked,
            "inventory": inventory.candidates_checked,
        },
        "serialized_program_bank_bytes": bank.serialized_bytes(),
        "p95_latency_ms": percentile95(latencies),
        "transformer_used": False,
        "gradient_training_used": False,
        "task_specific_formulas_supplied": False,
        "university_exam_mastery_passed": False,
        "claim_boundary": "Two compact numeric mechanisms were induced from examples and transferred to unseen values. This is not broad Japanese language understanding or full university-entrance-exam ability.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
