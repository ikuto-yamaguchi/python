from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .mobile_curriculum_memory import KnowledgeDocument


WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
CURRICULUM_QUERIES = (
    "高校 数学 代数 幾何 確率 統計",
    "高校 物理 力学 電磁気 波動 熱力学",
    "高校 化学 無機化学 有機化学 化学反応",
    "高校 生物 遺伝 生態 細胞 進化",
    "地学 天文学 地質 気象",
    "日本史 古代 中世 近世 近代 現代",
    "世界史 古代 中世 近代 現代",
    "地理 地形 気候 人口 産業",
    "公共 政治 経済 倫理 法律",
    "情報科学 アルゴリズム データ構造 ネットワーク",
    "国語 現代文 古文 漢文 文法",
    "英語 文法 語彙 読解",
    "論理学 命題 推論 誤謬",
    "心理学 社会学 哲学",
    "医学 解剖 生理 遺伝 栄養",
)


def _get_json(parameters: dict[str, str | int]) -> dict[str, object]:
    url = WIKIPEDIA_API + "?" + urlencode(parameters)
    request = Request(
        url,
        headers={"User-Agent": "minimal-predictive-lm-research/1.0 (+curriculum-memory)"},
    )
    with urlopen(request, timeout=90) as response:
        data = response.read()
    return json.loads(data)


def acquire_curriculum(
    output_path: str | Path,
    *,
    results_per_query: int = 30,
    delay_seconds: float = 0.1,
) -> dict[str, object]:
    documents: dict[int, KnowledgeDocument] = {}
    query_records: list[dict[str, object]] = []
    for query in CURRICULUM_QUERIES:
        payload = _get_json(
            {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 0,
                "gsrlimit": results_per_query,
                "prop": "extracts|info",
                "explaintext": 1,
                "exintro": 1,
                "inprop": "url",
                "redirects": 1,
            }
        )
        pages = payload.get("query", {}).get("pages", []) if isinstance(payload.get("query"), dict) else []
        accepted = 0
        page_ids: list[int] = []
        if isinstance(pages, list):
            for raw in pages:
                if not isinstance(raw, dict):
                    continue
                page_id = int(raw.get("pageid", 0))
                title = str(raw.get("title", "")).strip()
                extract = str(raw.get("extract", "")).strip()
                source = str(raw.get("fullurl", ""))
                if page_id <= 0 or len(extract) < 120:
                    continue
                documents[page_id] = KnowledgeDocument(title, extract, source)
                accepted += 1
                page_ids.append(page_id)
        query_records.append(
            {
                "query": query,
                "accepted": accepted,
                "page_ids": sorted(page_ids),
            }
        )
        if delay_seconds:
            time.sleep(delay_seconds)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ordered = [documents[key] for key in sorted(documents)]
    with output.open("w", encoding="utf-8") as handle:
        for row in ordered:
            handle.write(
                json.dumps(
                    {"title": row.title, "text": row.text, "source": row.source},
                    ensure_ascii=False,
                )
                + "\n"
            )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    report = {
        "capability_id": "JAPANESE-CURRICULUM-CORPUS-001",
        "queries": query_records,
        "documents": len(ordered),
        "bytes": output.stat().st_size,
        "sha256": digest,
        "source": WIKIPEDIA_API,
        "target_exam_questions_used": 0,
        "target_exam_answers_used": 0,
        "development_corpus_passed": len(ordered) >= 250,
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not report["development_corpus_passed"]:
        raise SystemExit("curriculum corpus coverage too small")
    return report


def load_curriculum(path: str | Path) -> list[KnowledgeDocument]:
    result: list[KnowledgeDocument] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result.append(
            KnowledgeDocument(
                title=str(row["title"]),
                text=str(row["text"]),
                source=str(row.get("source", "")),
            )
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/japanese_curriculum.jsonl")
    parser.add_argument("--results-per-query", type=int, default=30)
    args = parser.parse_args()
    print(
        json.dumps(
            acquire_curriculum(
                args.output,
                results_per_query=args.results_per_query,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
