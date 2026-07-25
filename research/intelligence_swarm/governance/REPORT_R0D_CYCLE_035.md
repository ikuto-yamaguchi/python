# R0-D Cycle 035 — Alias-normalized leakage is mandatory at acceptance

## Scope

This cycle changes only the R0 benchmark reproducibility and leakage acceptance path. It introduces no memory, replay, fast-weight, sleep, forgetting, architecture, operation, or goal mechanism.

## Defect found

`audit_schema_alias_leakage.py` already rejected schema variants such as `goldStateAfter`, `gold-action`, `completedTrajectory`, `terminalObservation`, and `episodeReturn`. However, `audit_r0_acceptance_bundle.py` did not invoke that auditor.

A caller could therefore run the official single-bundle acceptance gate while omitting the alias-normalized audit. Exact snake_case checks and paired statistics could pass even though a camelCase or kebab-case alias remained in `model_input_fields` or nested `model_input`.

## Change

The fail-closed acceptance gate now requires all of the following in one invocation:

1. dataset/evaluation contract;
2. alias-normalized schema leakage audit;
3. prediction payload leakage audit;
4. paired statistics and same-instance coverage;
5. model/data/raw-log/resource artifact audit;
6. prediction/statistics evidence checksum audit.

Any failure, including alias-only leakage, classifies the whole bundle as `initial_reproduction_failure`.

## Regression coverage

`test_audit_r0_acceptance_bundle.py` now fixes these cases:

- every contract passes;
- alias-normalized leakage fails while paired statistics pass;
- prediction payload leakage fails while paired statistics pass;
- prediction/statistics checksum failure rejects the bundle;
- alias, payload, and checksum failures are all preserved rather than masked.

## Evidence status

This closes an acceptance-path bypass; it does not create a successful public benchmark reproduction.

- accepted R0 evidence bundles: 0
- accepted public baseline reproductions: 0
- accepted model/RSS/runtime/latency bundles: 0
- capability progress: not established
- intelligence principle: not established
- current failure classification: `initial_reproduction_failure`
