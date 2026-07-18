from __future__ import annotations

import json

import minimal_predictive_lm.official_exam_ingest as ingest


def test_freeze_requires_official_hashed_assets(monkeypatch, tmp_path) -> None:
    pages = {
        url: (
            "<html><body>"
            + "".join(
                (
                    '<a href="/albums/abm.php?d=2144'
                    f'&f=asset_{source_id}_{index}.pdf'
                    f'&n=exam_{index}.pdf">PDF {index}</a>'
                )
                for index in range(40)
            )
            + (
                '<a href="/albums/abm.php?d=2144'
                f'&f=audio_{source_id}.mp3&n=listening.mp3">audio</a>'
            )
            + "</body></html>"
        ).encode()
        for source_id, url in ingest.DEFAULT_SOURCES.items()
    }

    def fake_download(url: str) -> tuple[bytes, str]:
        if url in pages:
            return pages[url], "text/html"
        if ingest._asset_extension(url) == ".mp3":
            return b"audio-bytes", "application/octet-stream"
        return ("pdf:" + url).encode(), "application/pdf"

    monkeypatch.setattr(ingest, "_download", fake_download)
    output = tmp_path / "manifest.json"
    report = ingest.freeze_sources(output, polite_delay_seconds=0.0)
    assert report["source_freeze_passed"] is True
    assert report["protocol"]["targets_used_for_training"] == 0
    assert report["protocol"]["frozen_before_curriculum_training"] is True
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["asset_total"] >= 160
    assert all(len(row["sha256"]) == 64 for row in saved["assets"])
    assert sum(ingest._asset_extension(row["url"]) == ".mp3" for row in saved["assets"]) == 4


def test_abm_query_filename_is_recognized() -> None:
    pdf = "https://www.dnc.ac.jp/albums/abm.php?d=2144&f=x.pdf&n=exam.pdf"
    audio = "https://www.dnc.ac.jp/albums/abm.php?d=2144&f=x.mp3&n=audio.mp3"
    assert ingest._asset_extension(pdf) == ".pdf"
    assert ingest._asset_extension(audio) == ".mp3"
    assert ingest._asset_link(pdf) is True
    assert ingest._asset_link(audio) is True


def test_non_official_seed_is_rejected(tmp_path) -> None:
    try:
        ingest.freeze_sources(
            tmp_path / "bad.json",
            {"bad": "https://example.com/exam.html"},
            polite_delay_seconds=0.0,
        )
    except ValueError as exc:
        assert "non-official" in str(exc)
    else:
        raise AssertionError("non-official seed should be rejected")
