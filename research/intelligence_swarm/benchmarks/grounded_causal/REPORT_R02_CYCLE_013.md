# R0.2 Cycle 013 — Holdout Assignment Integrity

## Scope

This cycle changes no model family and introduces no operation/goal toy hypothesis.
It audits whether the existing typed SILG trajectory path can support the required
held-out entity, dynamics and language-form transfer measurements.

## Finding

The current exporter does not create real held-out entity or dynamics cells:

- `entity_holdout` is written as `false` for every row;
- `dynamics_holdout` is written as `false` for every row;
- every row from the public test environment is labeled `language_holdout=true`.

Consequently, the current comparison harness can print keys named
`entity_holdout`, `dynamics_holdout` and `language_holdout`, but it cannot measure
the three requested transfer questions. Treating the public test split wholesale
as a language-form holdout also conflates environment split with linguistic-form
novelty.

## Added fail-closed audit

`audit_r02_holdout_assignments.py` now requires, for each holdout condition:

- non-empty held-out test rows;
- exact seed coverage `1, 7, 19`;
- an explicit condition-specific signature;
- zero signature overlap with training rows;
- no placeholder all-false entity/dynamics assignment;
- no wholesale relabeling of the test split as language-form holdout.

Required signatures are:

- `entity_signature`;
- `dynamics_signature`;
- `language_form_signature`.

The audit records the immutable dataset SHA-256, row count, per-condition seed
coverage, unique-signature count and overlap examples. Any violation is classified
as `initial_reproduction_failure`.

## Regression cases

`test_audit_r02_holdout_assignments.py` fixes three cases:

1. genuine three-seed, disjoint holdout cells pass;
2. the current placeholder annotation pattern fails;
3. a train/test signature overlap fails.

The tests are committed but no successful CI result is claimed in this cycle.

## Minimal next correction

Do not tune the Environment-first model. First produce an externally specified,
immutable holdout manifest from the pinned RTFM generator/configuration that
assigns episodes to disjoint entity, dynamics and language-form cells and records
the three signatures above. The manifest must be created without inspecting
model predictions or test outcomes. Then re-export all three seeds and run this
audit before the matched comparison harness.

## Decision

- R0.2 public-data execution: blocked;
- cause: required transfer cells do not exist in the exported dataset;
- classification: `initial_reproduction_failure`;
- novelty, intelligence principle and capability progress: not established.
