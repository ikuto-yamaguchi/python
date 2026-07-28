# R0-D Cycle 084 — strict seed identity core integration

## Scope

This cycle changes only the R0 reproducibility/evaluation contract. It adds no memory, replay, fast weights, sleep or forgetting mechanism.

## Fail-closed rule

Every dataset, score, resource-manifest and raw-log cell accepts a seed only when `type(seed) is int`. Python booleans, floats, numeric strings and Unicode-width numeric strings are rejected rather than coerced.

Examples rejected: `true`, `1.0`, `1.9`, `"1"`, `"１"`.

Any violation is classified as `initial_reproduction_failure`, and invalid score statistics remain suppressed.
