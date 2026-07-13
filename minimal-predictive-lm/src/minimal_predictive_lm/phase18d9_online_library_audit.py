from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping

from .phase18d9_online_library_growth import (
    grow_program_library,
    markdown as engine_markdown,
    run as engine_run,
)


def run() -> dict[str, Any]:
    payload = engine_run()
    learner_source = inspect.getsource(grow_program_library)
    no_external_support_episode_api = all(
        token not in learner_source
        for token in ("support_episode", "support_hex", "support_records")
    )
    payload["theorem_checks"][
        "learner_has_no_support_episode_api"
    ] = no_external_support_episode_api
    payload["all_theorem_checks_pass"] = all(payload["theorem_checks"].values())
    payload["claim_boundary"][
        "program_library_grows_from_stream_observations"
    ] = payload["all_theorem_checks_pass"]
    payload["campaign"]["audit_fix"] = (
        "minimum_support is an internal sample threshold, not a supplied support episode"
    )
    return payload


def markdown(payload: Mapping[str, Any]) -> str:
    return engine_markdown(payload)


def main() -> None:
    payload = run()
    Path("results").mkdir(exist_ok=True)
    Path("results/phase18d9.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("results/phase18d9.md").write_text(markdown(payload), encoding="utf-8")
    print(markdown(payload), end="")


if __name__ == "__main__":
    main()
