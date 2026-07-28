#!/usr/bin/env python3
"""Static regression checks for the SILG official-evaluation parity audit."""
from __future__ import annotations

import ast
from pathlib import Path


HERE = Path(__file__).resolve().parent
TARGET = HERE / "audit_silg_official_eval_parity.py"


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        'SILG_SHA = "2af07578e1264029a240fcfb78d4ac0aea16f5de"',
        'RTFM_SHA = "58f17955595b5a127c96d045d896fcbcc7d4b570"',
        'OFFICIAL_TEST_SOURCE = "run_exp.py:test"',
        'CANONICAL_SEEDS = [1, 7, 19]',
        '"official_continuous_stream"',
        '"fresh_seeded_instances"',
        'agent_state = model.initial_state(batch_size=1)',
        'if bool(observation["done"].item()):',
        'episode_seed = seed * 1_000_003 + episode',
        '"new_architecture": False',
        '"capability_progress_claimed": False',
    )
    missing = [needle for needle in required if needle not in source]
    if missing:
        raise AssertionError(f"missing parity-contract clauses: {missing}")

    if "model.train()" in source or "optimizer" in source:
        raise AssertionError("parity audit must not train or optimize a model")
    if "R0.2" in source and "not" not in source:
        raise AssertionError("parity audit must not claim R0.2 completion")

    print("official evaluation parity audit contract: PASS")


if __name__ == "__main__":
    main()
