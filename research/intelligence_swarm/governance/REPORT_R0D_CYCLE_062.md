# R0-D Cycle 062 — core raw-log measurement binding

`evaluation_contract.audit_artifacts()` now requires every resource-manifest run to be backed by exactly one machine-readable raw-log measurement record for the same method, seed, domain, split, and condition.

The raw record must exactly match the manifest's immutable code commit, model/data SHA-256 values, model bytes, peak RSS, training wall time, and CPU inference latency. Missing, duplicate, wrong-cell, non-finite, or altered records fail closed as `initial_reproduction_failure`.

This closes the direct-core bypass that remained after the focused auditor and unified acceptance gate had already required raw-log binding. No memory, replay, fast weights, sleep, or forgetting mechanism was added.
