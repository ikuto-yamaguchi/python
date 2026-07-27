# R0-D Cycle 071 — Normalized cell identity audit

## Scope

This cycle continues R0 benchmark reproducibility, leakage, and statistics auditing only. It does not add memory, replay, fast weights, sleep, or forgetting mechanisms.

## Finding

`evaluation_contract.py` currently uses raw `domain` and `condition` strings in the domain×seed×split×condition cell key. Unicode-width, case, whitespace, control/format-character, separator, or condition-token-order differences can therefore split a semantic cell into multiple apparent cells.

That can hide missing prediction coverage, create misleading domain-local topology, alter per-cell means and minimum-cell gaps, and permit shuffle assignments to exploit a representation-only boundary.

## Added fail-closed audit

`audit_normalized_cell_identity.py` canonicalizes:

- domain: Unicode NFKC, case folding, removal of whitespace and control/format characters;
- condition: the same normalization, then tokenization on `+`, comma, pipe, or whitespace, followed by sorting and deduplication.

Multiple raw labels resolving to one canonical label are rejected as `initial_reproduction_failure`. Empty canonical labels are also rejected.

## Regression coverage

The focused test fixes the following cases:

- genuinely distinct domain and condition cells pass;
- `RTFM` versus full-width `ＲＴＦＭ` fails;
- invisible-character and whitespace aliases fail;
- reordered and differently separated compound holdout conditions fail;
- labels empty after normalization fail.

## Status

The focused auditor and short CI workflow are present on the canonical reconstruction branch. Direct integration into `evaluation_contract.py` and the unified acceptance gate remains required before this audit becomes non-optional.

No public baseline reproduction, accepted resource/statistics bundle, or R0 success is claimed. Current classification remains `initial_reproduction_failure`.
