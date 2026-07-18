from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from .japanese_curriculum_corpus import _get_json


def enrich_curriculum(
    input_path: str | Path,
    output_path: str | Path,
    *,
    max_chars: int = 12_000,
    delay_seconds: float = 0.12,
) -> dict[str, object]:
    source_rows = [
        json.loads(line)
        for line in Path(input_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    enriched_rows: list[dict[str, str]] = []
    total_retries = 0
    expanded = 0
    failed_titles: list[str] = []
    for row in source_rows:
        title = str(row["title"])
        original = str(row["text"])
        try:
            payload, retries = _get_json(
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": 2,
                    "titles": title,
                    "prop": "extracts|info",
                    "explaintext": 1,
                    "exchars": max_chars,
                    "inprop": "url",
                    "redirects": 1,
                }
            )
            total_retries += retries
            query = payload.get("query")
            pages = query.get("pages", []) if isinstance(query, dict) else []
            page = pages[0] if isinstance(pages, list) and pages else {}
            extract = str(page.get("extract", "")).strip() if isinstance(page, dict) else ""
            text = extract if len(extract) > len(original) else original
            if len(text) > len(original):
                expanded += 1
            enriched_rows.append(
                {
                    "title": str(page.get("title", title)) if isinstance(page, dict) else title,
                    "text": text,
                    "source": (
                        str(page.get("fullurl", row.get("source", "")))
                        if isinstance(page, dict)
                        else str(row.get("source", ""))
                    ),
                }
            )
        except Exception:
            # Keep the already verified introductory extract rather than silently
            # dropping a curriculum topic. Failure counts remain explicit.
            failed_titles.append(title)
            enriched_rows.append(
                {
                    "title": title,
                    "text": original,
                    "source": str(row.get("source", "")),
                }
            )
        if delay_seconds:
            time.sleep(delay_seconds)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in enriched_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    lengths = [len(row["text"]) for row in enriched_rows]
    report = {
        "capability_id": "JAPANESE-CURRICULUM-FULL-EXTRACT-001",
        "documents": len(enriched_rows),
        "expanded_documents": expanded,
        "failed_documents": len(failed_titles),
        "failed_titles": failed_titles[:40],
        "characters": sum(lengths),
        "mean_characters": sum(lengths) / len(lengths) if lengths else 0.0,
        "maximum_characters": max(lengths, default=0),
        "minimum_characters": min(lengths, default=0),
        "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "max_extract_chars": max_chars,
        "rate_limit_retries": total_retries,
        "target_exam_questions_used": 0,
        "target_exam_answers_used": 0,
        "enrichment_passed": (
            len(enriched_rows) >= 250
            and expanded >= int(0.75 * len(enriched_rows))
            and len(failed_titles) <= int(0.10 * len(enriched_rows))
            and sum(lengths) >= 1_500_000
        ),
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not report["enrichment_passed"]:
        raise SystemExit("curriculum full-text enrichment failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--max-chars", type=int, default=12_000)
    args = parser.parse_args()
    print(
        json.dumps(
            enrich_curriculum(args.input, args.output, max_chars=args.max_chars),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
