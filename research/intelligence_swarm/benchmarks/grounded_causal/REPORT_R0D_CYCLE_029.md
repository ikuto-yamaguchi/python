# R0-D Cycle 029 — Exact method topology and artifact identity in the core contract

Date: 2026-07-26
Branch: `research/intelligence-swarm-reconstruction-001`
Classification: `initial_reproduction_failure`

## Scope

This cycle changes only the R0 reproducibility/statistics/leakage contract. It does not add memory, replay, fast weights, sleep, forgetting, a toy mechanism, an architecture family, a branch, or a PR chain.

## Defect closed

The repository already had companion auditors for prediction-method topology and artifact-cell identity, but `evaluation_contract.py` itself remained permissive in two ways:

1. `score()` accepted unregistered prediction methods and included them in summaries and paired gaps.
2. `audit_artifacts()` did not itself reject unregistered methods, mixed code commits, or different dataset path/hash pairs within one `seed × domain × split × condition` cell.

A caller running only the core contract could therefore bypass the stricter companion audits.

## Core-contract changes

`evaluation_contract.py` now requires the exact six-method set:

- `correct`
- `random`
- `language_blind`
- `state_only`
- `target_label_shuffle`
- `outcome_shuffle`

Prediction scoring rejects every additional method before it can enter cell summaries, confidence intervals, or paired comparisons.

Artifact auditing now additionally requires:

- no unregistered method;
- exactly one full `code_commit` across the bundle;
- one identical `data_path + data_sha256` pair across all methods in each `seed × domain × split × condition` cell;
- the existing exact seeds `1 / 7 / 19`, complete observed-topology coverage, model bytes, peak RSS, training wall time, CPU inference latency, raw logs, artifact paths, and independently verified SHA-256 values.

Any violation remains classified as `initial_reproduction_failure`.

## Regression coverage

Added `test_evaluation_contract_method_identity.py` with fail-closed cases for:

- an extra prediction method;
- an extra artifact method;
- mixed code commits;
- a different dataset artifact for one method in an otherwise matched cell.

The canonical short evaluation-contract workflow compiles and runs the new tests. Local focused regression execution passed before commit.

## Evidence status

This cycle does not create or accept a new real R0 result.

- real R0 bundle passing the unified contract: 0
- accepted public baseline reproduction: 0
- accepted model/RSS/runtime/latency/checksum bundle: 0
- capability progress: not recognized
- new intelligence principle: not claimed

The standing classification remains `initial_reproduction_failure` until one immutable real bundle passes the complete contract.
