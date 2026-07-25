# R0-D Cycle 031 — Prediction/statistics evidence-chain audit

## Scope

This cycle adds no memory, replay, fast weights, sleep, forgetting, architecture, or toy mechanism. It only strengthens fail-closed reproducibility evidence for the canonical R0 benchmark branch.

## Gap found

The existing artifact contract independently verifies model, dataset, and raw-log files. Prediction JSONL files and the derived statistics report were not themselves mandatory independently checksummed evidence. Therefore, a bundle could preserve the trained model and raw logs while replacing predictions or summary statistics after evaluation.

That is not an acceptable public-baseline reproduction bundle.

## Change

Added `audit_prediction_statistics_artifacts.py` with these requirements:

- every method/seed run declares `predictions_path` and `predictions_sha256`;
- prediction artifacts exist, are non-empty JSONL, match their declared method, contain only finite JSON values, and match SHA-256;
- the method set is exactly Correct, Random, Language-blind, State-only, Target-label shuffle, and Outcome shuffle;
- seeds are exactly 1, 7, and 19;
- the manifest declares `statistics_path` and `statistics_sha256`;
- the statistics artifact matches SHA-256 and contains coverage, cell statistics, summaries, and paired gaps versus Correct;
- neither the outer report nor score object may be invalid or classified as `initial_reproduction_failure`.

Any failure is classified as `initial_reproduction_failure`.

## Regression coverage

The focused regression fixes the following cases:

1. a complete checksummed prediction/statistics evidence bundle passes;
2. a prediction file modified after hashing fails;
3. missing statistics checksum provenance fails;
4. prediction rows whose method disagrees with the manifest fail;
5. a checksummed statistics report that declares failure still fails.

A dedicated short CI workflow compiles and executes the auditor and regression test without triggering the long SILG training workflow.

## Status

This is an evaluation-evidence improvement only. No public baseline value, model bytes, RSS, wall time, CPU latency, capability gain, novelty, or intelligence principle is accepted by this cycle.

Formal status remains:

- accepted real R0 bundle: 0;
- accepted public-baseline reproduction: 0;
- capability progress: not recognized;
- failure classification until a complete bundle passes: `initial_reproduction_failure`.
