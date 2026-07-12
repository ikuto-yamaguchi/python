from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from .benchmark_harness import ABSTAIN_TOKEN, RunPolicy, run_command_adapter
from .phase16a_public_benchmarks import load_phase16a_public_transfer_suite
from .wordnet_ontology import download_pinned_wordnet


def run() -> dict[str, object]:
    output_dir = Path("results")
    source_path, source_sha256, _source_bytes = download_pinned_wordnet(
        output_dir / "cache" / "english-wordnet-2025.zip"
    )
    os.environ["MPM_WORDNET_ZIP"] = str(source_path.resolve())
    manifest = load_phase16a_public_transfer_suite(examples_per_task=40)
    report = run_command_adapter(
        manifest,
        RunPolicy(
            max_output_chars=256,
            stop_sequences=("\n\n",),
            tools_allowed=(
                "pinned-open-english-wordnet-2025",
                "fixed-phase14b-provenance-documents",
            ),
            temperature=0.0,
            seed=0,
        ),
        model_id="mpm-phase15d-frozen-third-slice-diagnostic",
        command=(sys.executable, "-m", "minimal_predictive_lm.phase15d_worker"),
        timeout_seconds=300.0,
    )
    by_id = {row.example_id: row for row in manifest.examples}
    non_abstentions = []
    for prediction in report.predictions:
        text = prediction.text.strip()
        if not text or text == ABSTAIN_TOKEN:
            continue
        example = by_id[prediction.example_id]
        non_abstentions.append(
            {
                "id": prediction.example_id,
                "axis": example.axis,
                "prompt": example.prompt,
                "target": example.target,
                "prediction": text,
                "operations": prediction.operations,
                "reads": prediction.reads,
                "writes": prediction.writes,
            }
        )
    return {
        "manifest_sha256": manifest.sha256,
        "wordnet_sha256": source_sha256,
        "non_abstentions": non_abstentions,
    }


def main() -> None:
    payload = run()
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "phase16a_diagnostic.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
