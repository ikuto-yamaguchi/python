from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .mobile_curriculum_memory import KnowledgeDocument


WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
USER_AGENT = (
    "minimal-predictive-lm-research/1.0 "
    "(https://github.com/ikuto-yamaguchi/python; curriculum-memory research)"
)

CURRICULUM_QUERIES = (
    "代数 方程式 不等式 因数分解", "二次関数 指数関数 対数関数 三角関数",
    "微分 積分 極限 数列", "平面幾何 空間幾何 ベクトル",
    "確率 統計 確率分布 推定", "整数論 素数 合同式 組合せ数学",
    "力学 運動方程式 運動量 エネルギー", "円運動 万有引力 単振動",
    "熱力学 気体 状態方程式 エントロピー", "波動 音波 光波 干渉 回折",
    "電場 電位 コンデンサ 直流回路", "磁場 電磁誘導 交流回路",
    "原子物理 量子力学 放射線", "原子構造 周期表 化学結合",
    "物質量 化学反応式 酸化還元", "酸 塩基 中和 平衡 電離",
    "熱化学 反応速度 化学平衡", "無機化学 金属 非金属 錯体",
    "有機化学 炭化水素 官能基 高分子", "細胞 生体膜 酵素 代謝",
    "遺伝 DNA RNA タンパク質", "進化 系統分類 生物多様性",
    "生態系 個体群 物質循環", "人体 恒常性 神経 内分泌 免疫",
    "地質 岩石 鉱物 プレートテクトニクス", "地震 火山 地層 地球史",
    "気象 大気 海洋 気候", "天文学 太陽系 恒星 銀河 宇宙論",
    "現代文 論説文 小説 読解 要約", "日本語 文法 品詞 敬語 修辞",
    "古文 文法 助動詞 敬語 和歌", "漢文 句法 漢詩 中国古典",
    "日本文学 古典文学 近代文学 現代文学", "英語 文法 時制 仮定法 関係詞",
    "英語 語彙 熟語 語源", "英語 読解 英作文 翻訳",
    "言語学 音韻論 統語論 意味論 語用論", "日本史 縄文 弥生 古墳 飛鳥 奈良",
    "日本史 平安 鎌倉 室町 戦国", "日本史 江戸 幕藩体制 産業 文化",
    "日本史 明治 大正 昭和 戦後", "世界史 古代文明 ギリシャ ローマ",
    "世界史 中世ヨーロッパ イスラム 世界", "世界史 近世 大航海時代 宗教改革",
    "世界史 市民革命 産業革命 帝国主義", "世界史 世界大戦 冷戦 現代史",
    "地理 地形 気候 土壌 植生", "地理 人口 都市 農業 工業 貿易",
    "地理 地図 GIS 統計 資料読解", "政治 日本国憲法 国会 内閣 裁判所",
    "政治 国際関係 国際連合 安全保障", "経済 市場 価格 金融 財政",
    "経済 国民所得 景気 国際経済", "法律 民法 刑法 行政法 国際法",
    "倫理 哲学 思想 宗教", "論理学 命題 推論 誤謬 科学的方法",
    "情報科学 アルゴリズム データ構造", "プログラミング Python C言語 計算量",
    "データベース 情報検索 機械学習", "コンピュータネットワーク インターネット セキュリティ",
    "情報理論 符号化 暗号", "コミュニケーション 対話 説明 議論 面接",
    "文章作法 小論文 論証 批判的思考", "医学 解剖学 生理学 病理学",
    "栄養 健康 公衆衛生 疫学", "心理学 認知 発達 社会心理学",
    "社会学 文化 家族 労働 教育",
)


def _retry_delay(error: HTTPError | URLError, attempt: int) -> float:
    if isinstance(error, HTTPError):
        raw = error.headers.get("Retry-After") if error.headers else None
        if raw:
            try:
                return min(90.0, max(1.0, float(raw)))
            except ValueError:
                pass
    return min(90.0, 2.0 ** attempt)


def _get_json(parameters: dict[str, str | int], *, retries: int = 8) -> tuple[dict[str, object], int]:
    enriched = dict(parameters)
    enriched.setdefault("maxlag", 5)
    url = WIKIPEDIA_API + "?" + urlencode(enriched)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Api-User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=90) as response:
                payload = json.loads(response.read())
            if isinstance(payload, dict) and "error" in payload:
                error = payload["error"]
                code = str(error.get("code", "")) if isinstance(error, dict) else ""
                if code == "maxlag" and attempt < retries:
                    time.sleep(min(90.0, 2.0 ** attempt))
                    continue
                raise RuntimeError(f"Wikimedia API error: {error}")
            return payload, attempt
        except HTTPError as error:
            last_error = error
            if error.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                raise
            time.sleep(_retry_delay(error, attempt))
        except URLError as error:
            last_error = error
            if attempt >= retries:
                raise
            time.sleep(_retry_delay(error, attempt))
    raise RuntimeError(f"Wikimedia API retries exhausted: {last_error}")


def acquire_curriculum(output_path: str | Path, *, results_per_query: int = 20, delay_seconds: float = 0.75) -> dict[str, object]:
    documents: dict[int, KnowledgeDocument] = {}
    query_records: list[dict[str, object]] = []
    total_retries = 0
    for query in CURRICULUM_QUERIES:
        payload, retries_used = _get_json({
            "action": "query", "format": "json", "formatversion": 2,
            "generator": "search", "gsrsearch": query, "gsrnamespace": 0,
            "gsrlimit": results_per_query, "prop": "extracts|info",
            "explaintext": 1, "exintro": 1, "exlimit": "max",
            "inprop": "url", "redirects": 1,
        })
        total_retries += retries_used
        query_payload = payload.get("query")
        pages = query_payload.get("pages", []) if isinstance(query_payload, dict) else []
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
        query_records.append({"query": query, "accepted": accepted, "page_ids": sorted(page_ids), "retries_used": retries_used})
        if delay_seconds:
            time.sleep(delay_seconds)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ordered = [documents[key] for key in sorted(documents)]
    with output.open("w", encoding="utf-8") as handle:
        for row in ordered:
            handle.write(json.dumps({"title": row.title, "text": row.text, "source": row.source}, ensure_ascii=False) + "\n")
    report = {
        "capability_id": "JAPANESE-CURRICULUM-CORPUS-004",
        "queries": query_records,
        "query_count": len(CURRICULUM_QUERIES),
        "documents": len(ordered),
        "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "source": WIKIPEDIA_API,
        "rate_limit_retries": total_retries,
        "request_delay_seconds": delay_seconds,
        "extract_mode": "multi-page introductory extracts",
        "target_exam_questions_used": 0,
        "target_exam_answers_used": 0,
        "development_corpus_passed": len(ordered) >= 250,
    }
    report_path = output.with_suffix(output.suffix + ".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["development_corpus_passed"]:
        raise SystemExit("curriculum corpus coverage too small")
    return report


def load_curriculum(path: str | Path) -> list[KnowledgeDocument]:
    result: list[KnowledgeDocument] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result.append(KnowledgeDocument(str(row["title"]), str(row["text"]), str(row.get("source", ""))))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/japanese_curriculum.jsonl")
    parser.add_argument("--results-per-query", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(acquire_curriculum(args.output, results_per_query=args.results_per_query), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
