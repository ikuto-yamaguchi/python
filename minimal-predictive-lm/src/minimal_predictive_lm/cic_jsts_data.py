from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .cic_choice_data import ChoiceExample

JSTS_OPTIONS = tuple(f"{index / 2:.1f}" for index in range(11))


@dataclass(frozen=True)
class JSTSRecord:
    choice: ChoiceExample
    target: float


def load_jsts_dataset(path: str | Path) -> list[JSTSRecord]:
    records: list[JSTSRecord] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        left = str(row["sentence1"]).strip()
        right = str(row["sentence2"]).strip()
        target = float(row["label"])
        answer_index = max(0, min(10, int(round(target * 2.0))))
        stem = f"文1：{left}\n文2：{right}"
        raw_question = stem + "\n" + "\n".join(
            f"({index}){option}" for index, option in enumerate(JSTS_OPTIONS)
        )
        records.append(
            JSTSRecord(
                ChoiceExample(
                    raw_question,
                    stem,
                    JSTS_OPTIONS,
                    answer_index,
                ),
                target,
            )
        )
    return records


def stable_jsts_split(
    rows: Sequence[JSTSRecord],
    *,
    test_threshold: int = 1500,
    namespace: str = "jsts-inner:",
) -> tuple[list[JSTSRecord], list[JSTSRecord]]:
    train: list[JSTSRecord] = []
    test: list[JSTSRecord] = []
    for row in rows:
        digest = hashlib.sha256(
            (namespace + row.choice.raw_question).encode("utf-8")
        ).digest()
        code = int.from_bytes(digest[:8], "little") % 10000
        (test if code < test_threshold else train).append(row)
    return train, test
