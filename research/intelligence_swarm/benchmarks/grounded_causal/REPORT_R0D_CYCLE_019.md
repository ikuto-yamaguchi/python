# R0-D Cycle 019 — Condition-scoped holdout leakage audit

## Scope

This cycle changes only benchmark reproducibility/leakage auditing on the single
canonical reconstruction branch. It adds no memory, replay, fast weights,
sleep, forgetting, architecture family, capability claim, or PR chain.

## Problem found

The main evaluation contract aggregates entity and dynamics signatures by split.
If one `test` split contains both in-distribution rows and true holdout rows, an
in-distribution entity that legitimately also appeared in training can be mixed
with the holdout cell. This can create a false holdout failure and, more
importantly, does not identify the exact leaking `domain × split × condition`
cell.

A benchmark qualification decision must be made per declared transfer cell, not
from a split-wide union.

## Implemented audit

`audit_holdout_condition_integrity.py` now:

- compares each entity/dynamics holdout cell against training signatures from
  the same domain;
- indexes results by `domain × split × condition × kind`;
- permits expected train overlap in explicitly in-distribution cells;
- requires every declared holdout row to contain the corresponding signature;
- requires canonical seeds `1, 7, 19` in every holdout cell;
- records overlap counts and hashed signature examples without exposing raw
  entity/dynamics labels;
- classifies any missing signature, overlap, missing seed, extra seed, or absent
  training reference as `initial_reproduction_failure`.

## Regression coverage

`test_audit_holdout_condition_integrity.py` fixes four cases:

1. mixed in-distribution and holdout rows in one test split remain valid when the
   actual holdout cells are disjoint;
2. entity overlap in the entity-holdout cell fails;
3. a missing dynamics signature in a declared dynamics-holdout row fails;
4. one missing canonical seed in only one condition fails.

The lightweight evaluation-contract workflow compiles and runs the new audit and
tests without restarting the long SILG training workflow.

## Status

The real R0 prediction/data/artifact bundle has not yet passed this condition-
scoped audit. Public baseline competence, complete prediction joins, semantic
shuffle payloads, resource artifacts, and immutable checksums remain required.

Formal classification remains:

`initial_reproduction_failure`

No novelty, intelligence principle, capability progress, or high-school-level
intelligence is claimed.
