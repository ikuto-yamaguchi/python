from __future__ import annotations

import random

from . import close_communication_experiment as experiment


JAQUAD_TRAIN_PARQUET = (
    "https://huggingface.co/datasets/SkelterLabsInc/JaQuAD/resolve/"
    "refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)


def load_jaquad_parquet(count: int, seed: int) -> list[dict]:
    from datasets import load_dataset

    dataset = load_dataset(
        "parquet",
        data_files={"train": JAQUAD_TRAIN_PARQUET},
        split="train",
    )
    rows = []
    for row in dataset:
        context = str(row.get("context", "")).strip()
        question = str(row.get("question", "")).strip()
        answers = row.get("answers", {})
        texts = answers.get("text", []) if isinstance(answers, dict) else []
        answer = str(texts[0]).strip() if texts else ""
        if context and question and answer and len(context) <= 1800:
            rows.append(
                {"context": context, "question": question, "answer": answer}
            )
    random.Random(seed).shuffle(rows)
    return rows[:count]


def main() -> None:
    experiment.load_jaquad = load_jaquad_parquet
    experiment.main()


if __name__ == "__main__":
    main()
