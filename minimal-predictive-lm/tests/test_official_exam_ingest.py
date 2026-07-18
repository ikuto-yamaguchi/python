from __future__ import annotations

import json

import minimal_predictive_lm.official_exam_ingest as ingest


def test_freeze_requires_official_hashed_assets(monkeypatch, tmp_path) -> None:
    pages = {
        url: (
            "<html><body>"
            + "".join(
                f'<a href="/asset/{source_id}/{index}.pdf">PDF {index}</a>'
                for index in range(40)
            )
            + '<a href="/asset/audio.mp3">audio</a>'
            + "</body></html>"
        ).encode()
        for source_id, url in ingest.DEFAULT_SOURCES.items()
    }

    def fake_download(url: str) -> tuple[bytes, str]:
        if url in pages:
            return pages[url], "text/html"
        if url.endswith(".mp3"):
            return b"audio-bytes", "audio/mpeg"
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
