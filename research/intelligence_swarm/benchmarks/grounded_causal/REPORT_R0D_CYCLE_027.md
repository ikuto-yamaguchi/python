# R0-D Cycle 027 — Matched Artifact Cell Identity

## Scope

This cycle adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, branch, or PR chain.

It closes a provenance gap between the per-artifact checksum audit and the same-instance statistical comparison.

## Gap

The existing artifact contract verified each run's dataset path and SHA-256 independently, but did not require all methods in one `(seed, domain, split, condition)` cell to use the same dataset artifact. It also accepted a bundle assembled from multiple code commits.

That allowed a formally complete bundle in which, for example, `state_only` used a different data export from `correct`, or one control was produced after a code change. Prediction fingerprints may catch some row-level divergence, but the artifact manifest itself did not fail closed on this condition.

## Added audit

`audit_artifact_cell_identity.py` now requires:

- exactly the six registered methods: Correct, Random, Language-blind, State-only, Target-label shuffle, Outcome shuffle;
- exact canonical seeds `1, 7, 19`;
- complete method coverage in every observed `(seed, domain, split, condition)` cell;
- exactly one `data_path` and one `data_sha256` across all methods in each cell;
- exactly one immutable `code_commit` across the entire bundle;
- `initial_reproduction_failure` on any violation.

## Regression coverage

The accompanying tests reject:

- method-specific dataset hashes;
- method-specific dataset paths;
- mixed code commits;
- one missing method in one cell;
- unregistered extra methods.

A dedicated short CI workflow compiles and runs these tests without triggering the long SILG training workflow.

## Status

- real R0 bundle passing this audit: not yet demonstrated;
- public baseline reproduction: not yet accepted;
- capability progress: not recognized;
- classification until a real bundle passes: `initial_reproduction_failure`.
