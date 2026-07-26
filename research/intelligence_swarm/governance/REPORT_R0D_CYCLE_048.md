# R0-D Cycle 048 — statistics recomputation evidence binding

## Scope

This cycle changes no model, memory mechanism, replay, fast weights, sleep,
forgetting, architecture, or research hypothesis. It strengthens only the R0
benchmark evidence and acceptance contract on the canonical reconstruction branch.

## Defect found

The existing evidence audit required SHA-256 checksums for prediction JSONL and the
saved statistics JSON. A checksum fixes the submitted bytes, but it does not prove
that the statistics were derived from the submitted dataset and predictions. A
fabricated or post-edited report could be checksummed again and still pass the
checksum/shape/`valid=true` checks.

Consequently, reported domain×seed×condition cells, means, minimum-cell gaps,
confidence intervals, paired randomization tests, cluster bootstrap intervals, and
McNemar tests were not cryptographically or computationally bound to the prediction
rows from which they were claimed to originate.

## Fail-closed change

Added `audit_statistics_recomputation_binding.py` and made it mandatory in
`audit_r0_acceptance_bundle.py`.

The new contract:

1. loads the saved `statistics_path` from the manifest;
2. freshly runs `evaluation_contract.score(dataset, predictions)`;
3. canonicalizes both complete score objects with sorted JSON keys and
   `allow_nan=false`;
4. requires exact equality of the saved and recomputed score objects;
5. records stable hashes of both objects;
6. classifies every mismatch, invalid fresh score, malformed report, or non-finite
   value as `initial_reproduction_failure`.

A valid checksum is therefore necessary but no longer sufficient. The saved report
must be exactly reproducible from the submitted dataset and prediction rows.

## Regression coverage

Added tests for:

- exact saved/fresh score equality;
- a well-formed but fabricated summary value;
- non-finite saved statistics;
- unified-gate rejection when checksum and paired-statistics contracts pass but
  recomputation binding fails;
- preservation of recomputation failure alongside other contract failures.

The short unified acceptance workflow now compiles the new auditor and runs both its
focused tests and the unified-gate regression suite. The long SILG workflow is not
triggered by this governance-only change.

## Current classification

- accepted real R0 bundles: **0**
- accepted public-baseline reproductions: **0**
- accepted model/RSS/runtime/CPU-latency evidence bundles: **0**
- new intelligence principle: **not established**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- current status: **initial_reproduction_failure**
