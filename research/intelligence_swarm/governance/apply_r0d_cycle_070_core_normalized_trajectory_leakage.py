#!/usr/bin/env python3
"""Idempotently harden completed-trajectory split identities in the R0 core."""
from pathlib import Path

TARGET = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"expected core fragment not found: {old[:120]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "def _split_sig(row: dict[str, Any], *keys: str) -> str | None:\n",
        "def _trajectory_split_identity(value: Any) -> str:\n"
        "    \"\"\"Normalize episode/observation identities before split-leakage comparison.\"\"\"\n"
        "    return stable_hash(canonical_holdout_identity(value))\n\n\n"
        "def _split_sig(row: dict[str, Any], *keys: str) -> str | None:\n",
    )
    text = replace_once(
        text,
        '        if row.get("episode_id") is not None: episode_splits[str(row["episode_id"])].add(split)\n'
        '        if row.get("episode_seed") is not None: episode_seed_splits[str(row["episode_seed"])].add(split)\n'
        '        if row.get("observation_fingerprint") is not None: observation_splits[str(row["observation_fingerprint"])].add(split)\n',
        '        if row.get("episode_id") is not None: episode_splits[_trajectory_split_identity(row["episode_id"])].add(split)\n'
        '        if row.get("episode_seed") is not None: episode_seed_splits[_trajectory_split_identity(row["episode_seed"])].add(split)\n'
        '        if row.get("observation_fingerprint") is not None: observation_splits[_trajectory_split_identity(row["observation_fingerprint"])].add(split)\n',
    )
    text = replace_once(
        text,
        '"episode_split_isolation_required": True, "unicode_utterance_overlap_required": True,',
        '"episode_split_isolation_required": True, "normalized_trajectory_identity_required": True, "trajectory_identity_normalization": "recursive NFKC + casefold + remove whitespace/control-format + numeric scalar alias collapse", "unicode_utterance_overlap_required": True,',
    )
    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
