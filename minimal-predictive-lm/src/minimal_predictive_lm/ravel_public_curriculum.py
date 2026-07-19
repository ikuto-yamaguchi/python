from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

QUERIES = (
    "数学", "代数学", "幾何学", "微分積分学", "確率論", "統計学", "数列", "ベクトル",
    "物理学", "力学", "電磁気学", "熱力学", "波動", "量子力学",
    "化学", "無機化学", "有機化学", "化学反応", "酸と塩基",
    "生物学", "遺伝学", "生態学", "細胞生物学", "進化",
    "地球科学", "地質学", "気象学", "天文学",
    "日本史", "世界史", "地理学", "政治学", "経済学", "倫理学", "哲学", "論理学",
    "日本語文法", "古典文学", "漢文", "言語学", "英語学",
    "情報科学", "計算機科学", "アルゴリズム", "データ構造", "ネットワーク",
)


def _request_json(params: dict[str, str | int], *, retries: int = 3) -> dict:
    url = "https://ja.wikipedia.org/w/api.php?" + urlencode(params)
    for attempt in range(retries):
        try:
            request = Request(
                url,
                headers={"User-Agent": "RAVEL-1G research/0.1 (public curriculum experiment)"},
            )
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(1.0 + attempt)
    raise RuntimeError("unreachable")


def acquire(*, results_per_query: int = 8, max_documents: int = 320) -> list[dict[str, str]]:
    documents: dict[int, dict[str, str]] = {}
    for query in QUERIES:
        payload = _request_json(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 0,
                "gsrlimit": results_per_query,
                "prop": "extracts|info",
                "explaintext": 1,
                "exsectionformat": "plain",
                "inprop": "url",
                "format": "json",
                "formatversion": 2,
                "utf8": 1,
            }
        )
        for page in payload.get("query", {}).get("pages", []):
            page_id = int(page.get("pageid", 0))
            title = str(page.get("title", "")).strip()
            text = str(page.get("extract", "")).strip()
            if page_id <= 0 or not title or len(text) < 300:
                continue
            documents[page_id] = {
                "title": title,
                "text": text[:20_000],
                "source": str(page.get("fullurl", "https://ja.wikipedia.org/")),
            }
            if len(documents) >= max_documents:
                return list(documents.values())
    return list(documents.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--results-per-query", type=int, default=8)
    parser.add_argument("--max-documents", type=int, default=320)
    args = parser.parse_args()
    rows = acquire(
        results_per_query=args.results_per_query,
        max_documents=args.max_documents,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "documents": len(rows),
        "characters": sum(len(row["text"]) for row in rows),
        "queries": len(QUERIES),
        "target_exam_questions_used": 0,
        "source": "Japanese Wikipedia API",
    }
    output.with_suffix(output.suffix + ".report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
