# R0-D Cycle 056 — public-baseline values bound to saved statistics

## Scope

R0 benchmark reproducibility, statistics, and leakage auditing only. No memory, replay, fast weights, sleep, forgetting, or new mechanism was added.

## Defect

The existing public-baseline contract required immutable source metadata, expected and observed values, tolerances, and a statistics checksum. A checksum fixed the statistics artifact bytes, but `public_baseline.observed_values` still did not identify the exact fields from which those values were taken. A submitter could therefore keep a valid checksummed statistics file while entering unrelated favorable observed values in the manifest.

## Fail-closed change

`audit_public_baseline_statistics_binding.py` now requires `public_baseline.metric_paths` with the same keys as `observed_values`. Each path is an RFC 6901 JSON pointer into the bundle-contained, non-empty `statistics_path` artifact. The auditor independently verifies the artifact SHA-256 and requires every claimed observed value to equal the finite numeric value resolved from the saved statistics JSON.

The unified acceptance gate now requires this contract together with public-baseline provenance, fresh statistics recomputation, prediction coverage, leakage, resource, path-containment, and checksum contracts. Checksum agreement alone is explicitly insufficient.

## Regression coverage

- exact value-to-field binding passes;
- claimed observed value mismatch fails;
- missing JSON pointer fails;
- metric-key mismatch fails;
- statistics checksum mismatch fails;
- parent-directory escape fails;
- the unified gate rejects baseline value-binding failure even when provenance and recomputation contracts pass.

Any failure is classified as `initial_reproduction_failure`. This change does not establish a successful public baseline reproduction or accept any real R0 evidence bundle.
