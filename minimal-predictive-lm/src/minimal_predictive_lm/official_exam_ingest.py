from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen


OFFICIAL_HOST = "www.dnc.ac.jp"
DEFAULT_SOURCES = {
    "common_test_2026_main_questions": "https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_honshiken_mondai.html",
    "common_test_2026_main_answers": "https://www.dnc.ac.jp/kyotsu/kako_shiken_jouhou/r8/r8_honsiken_seikai.html",
    "common_test_2026_makeup_questions": "https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_tuisaishiken_mondai.html",
    "common_test_2026_makeup_answers": "https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_tuisaisiken_seikai.html",
}


@dataclass(frozen=True)
class Asset:
    source_id: str
    label: str
    url: str
    media_type: str
    size_bytes: int
    sha256: str


class _LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self._href: str | None = None
        self._parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = dict(attrs)
        href = values.get("href")
        if href:
            self._href = urljoin(self.base_url, href)
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            label = " ".join("".join(self._parts).split())
            self.links.append((self._href, label))
            self._href = None
            self._parts = []


def _download(url: str) -> tuple[bytes, str]:
    request = Request(
        url,
        headers={"User-Agent": "minimal-predictive-lm-research/1.0 (+exam-source-freeze)"},
    )
    with urlopen(request, timeout=90) as response:
        data = response.read()
        media_type = response.headers.get_content_type()
    return data, media_type


def _asset_extension(url: str) -> str | None:
    parsed = urlparse(url)
    candidates = [parsed.path]
    for values in parse_qs(parsed.query).values():
        candidates.extend(values)
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered.endswith(".pdf"):
            return ".pdf"
        if lowered.endswith(".mp3"):
            return ".mp3"
    return None


def _asset_link(url: str) -> bool:
    return _asset_extension(url) in {".pdf", ".mp3"}


def freeze_sources(
    output_path: str | Path,
    sources: dict[str, str] | None = None,
    *,
    polite_delay_seconds: float = 0.05,
) -> dict[str, object]:
    sources = dict(sources or DEFAULT_SOURCES)
    assets: list[Asset] = []
    page_records: dict[str, object] = {}
    seen: set[tuple[str, str]] = set()
    for source_id, page_url in sources.items():
        if urlparse(page_url).hostname != OFFICIAL_HOST:
            raise ValueError(f"non-official source host: {page_url}")
        page_data, page_type = _download(page_url)
        parser = _LinkParser(page_url)
        parser.feed(page_data.decode("utf-8", errors="replace"))
        page_records[source_id] = {
            "url": page_url,
            "media_type": page_type,
            "size_bytes": len(page_data),
            "sha256": hashlib.sha256(page_data).hexdigest(),
        }
        for asset_url, label in parser.links:
            if not _asset_link(asset_url):
                continue
            if urlparse(asset_url).hostname != OFFICIAL_HOST:
                continue
            key = (source_id, asset_url)
            if key in seen:
                continue
            seen.add(key)
            data, media_type = _download(asset_url)
            assets.append(
                Asset(
                    source_id=source_id,
                    label=label,
                    url=asset_url,
                    media_type=media_type,
                    size_bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                )
            )
            if polite_delay_seconds:
                time.sleep(polite_delay_seconds)

    counts = {
        source_id: sum(asset.source_id == source_id for asset in assets)
        for source_id in sources
    }
    checks = {
        "four_official_source_pages": len(page_records) == 4,
        "main_question_assets_at_least_35": counts.get("common_test_2026_main_questions", 0) >= 35,
        "main_answer_assets_at_least_20": counts.get("common_test_2026_main_answers", 0) >= 20,
        "makeup_question_assets_at_least_35": counts.get("common_test_2026_makeup_questions", 0) >= 35,
        "makeup_answer_assets_at_least_20": counts.get("common_test_2026_makeup_answers", 0) >= 20,
        "audio_assets_present": sum(
            asset.media_type.startswith("audio/") or _asset_extension(asset.url) == ".mp3"
            for asset in assets
        ) >= 4,
        "all_assets_official": all(urlparse(asset.url).hostname == OFFICIAL_HOST for asset in assets),
        "all_assets_nonempty": all(asset.size_bytes > 0 for asset in assets),
        "all_assets_hashed": all(len(asset.sha256) == 64 for asset in assets),
    }
    report = {
        "capability_id": "OFFICIAL-UNIVERSITY-EXAM-SOURCE-FREEZE-001",
        "purpose": "Freeze official Common Test problem, answer, and listening assets before model training.",
        "source_pages": page_records,
        "asset_counts": counts,
        "asset_total": len(assets),
        "asset_bytes": sum(asset.size_bytes for asset in assets),
        "assets": [asdict(asset) for asset in assets],
        "protocol": {
            "official_host": OFFICIAL_HOST,
            "targets_used_for_training": 0,
            "targets_inspected_by_model_builder": 0,
            "frozen_before_curriculum_training": True,
        },
        "checks": checks,
        "source_freeze_passed": all(checks.values()),
        "university_exam_mastery_passed": False,
        "highschool_level_passed": False,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["source_freeze_passed"]:
        raise SystemExit("official exam source freeze failed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/official_exam_source_manifest.json")
    args = parser.parse_args()
    print(json.dumps(freeze_sources(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
