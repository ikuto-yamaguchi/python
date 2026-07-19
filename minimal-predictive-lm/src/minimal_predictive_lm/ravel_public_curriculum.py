from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from pathlib import Path

import pyarrow.parquet as parquet

SOURCE_DATASET = "fujiki/llm-japanese-dataset_wikipedia"
SOURCE_FILE = "data/train-00000-of-00002-fe13897027598519.parquet"


def _rank(title: str, text: str) -> int:
    digest = hashlib.blake2b(
        (title + "\0" + text[:512]).encode("utf-8"),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, "little")


def acquire_from_parquet(
    parquet_path: str | Path,
    *,
    max_documents: int = 320,
    min_chars: int = 300,
    max_chars: int = 20_000,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Select a deterministic, corpus-wide sample without loading the shard at once."""

    source = Path(parquet_path)
    dataset = parquet.ParquetFile(source)
    available = set(dataset.schema.names)
    required = {"input", "output"}
    if not required.issubset(available):
        raise ValueError(
            f"Wikipedia parquet requires columns {sorted(required)}, got {sorted(available)}"
        )

    # Python's heap is a min-heap. Store negative ranks so the worst retained
    # sample is replaced whenever a globally smaller deterministic rank appears.
    selected: list[tuple[int, int, str, str]] = []
    scanned = 0
    eligible = 0
    serial = 0
    for batch in dataset.iter_batches(
        batch_size=4096,
        columns=["input", "output"],
    ):
        titles = batch.column(0).to_pylist()
        texts = batch.column(1).to_pylist()
        for raw_title, raw_text in zip(titles, texts, strict=True):
            scanned += 1
            title = str(raw_title or "").strip()
            text = str(raw_text or "").strip()
            if not title or len(text) < min_chars:
                continue
            eligible += 1
            serial += 1
            rank = _rank(title, text)
            candidate = (-rank, -serial, title, text[:max_chars])
            if len(selected) < max_documents:
                heapq.heappush(selected, candidate)
            elif rank < -selected[0][0]:
                heapq.heapreplace(selected, candidate)

    rows = [
        {
            "title": title,
            "text": text,
            "source": (
                "https://huggingface.co/datasets/"
                + SOURCE_DATASET
                + "/blob/main/"
                + SOURCE_FILE
            ),
        }
        for _negative_rank, _negative_serial, title, text in sorted(
            selected,
            key=lambda row: (-row[0], row[2]),
        )
    ]
    return rows, {
        "rows_scanned": scanned,
        "eligible_rows": eligible,
        "parquet_rows": dataset.metadata.num_rows,
        "row_groups": dataset.num_row_groups,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-documents", type=int, default=320)
    parser.add_argument("--min-chars", type=int, default=300)
    parser.add_argument("--max-chars", type=int, default=20_000)
    args = parser.parse_args()

    rows, scan = acquire_from_parquet(
        args.parquet,
        max_documents=args.max_documents,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )
    if len(rows) < args.max_documents:
        raise SystemExit(
            f"only {len(rows)} eligible documents were selected; expected {args.max_documents}"
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "documents": len(rows),
        "characters": sum(len(row["text"]) for row in rows),
        "target_exam_questions_used": 0,
        "selection": "global lowest blake2b ranks over one fixed parquet shard",
        "source_dataset": SOURCE_DATASET,
        "source_file": SOURCE_FILE,
        "license": "CC-BY-SA-3.0",
        **scan,
    }
    output.with_suffix(output.suffix + ".report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
