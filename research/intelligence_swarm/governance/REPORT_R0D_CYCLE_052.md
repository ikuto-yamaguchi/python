# R0-D Cycle 052 — explicit holdout conditions in the core contract

## Scope

R0 benchmark reproducibility, statistics, and leakage auditing only. No memory, replay, fast weights, sleep, forgetting, architecture, or toy mechanism was added.

## Defect closed

`evaluation_contract.validate_dataset()` previously rejected entity/dynamics overlap only when legacy boolean fields such as `entity_holdout=true` were present. A real-data row could instead declare `condition="entity_holdout"`, omit the boolean, and reuse a train entity signature. Missing signatures on explicitly held-out rows were also not fail-closed in the core path.

## Core contract

- `condition` is parsed into exact `+`, comma, pipe, or whitespace-delimited condition tokens after Unicode NFKC and case folding.
- `entity_holdout` and `dynamics_holdout` declarations are recognized from either the explicit condition token or the legacy boolean.
- Every declared holdout must be on a registered evaluation split.
- Every declared entity/dynamics holdout must provide the corresponding ID or signature.
- Each declared signature is checked per row against the train signature set.
- Compound conditions enforce every declared holdout dimension.
- Findings and overlap status are stored in validation evidence.

Any violation is an `initial_reproduction_failure`. No real R0 bundle, public baseline reproduction, capability progress, novelty, or intelligence principle is claimed.
