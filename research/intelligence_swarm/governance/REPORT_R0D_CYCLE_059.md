# R0-D Cycle 059 — Core artifact evaluation split scope

`evaluation_contract.audit_artifacts()` now rejects resource runs outside the registered evaluation split vocabulary.

Accepted splits: `test`, `eval`, `validation`, `valid` after Unicode NFKC and case-fold normalization.

Rejected examples include `train`, `debug`, `calibration`, `analysis`, and `posthoc`. A self-consistent resource topology on an unregistered split is classified as `initial_reproduction_failure` and cannot contribute model bytes, peak RSS, training wall time, CPU inference latency, raw-log, or checksum evidence.

No memory, replay, fast weights, sleep, or forgetting mechanism was introduced.
