# R0-D Cycle 081 — Raw-log/resource canonical cell identity

## Scope

R0 benchmark reproducibility, statistics, leakage, and artifact auditing only. No memory, replay, fast weights, sleep, forgetting, or new mechanism work.

## Defect

The scoring contract already canonicalized `domain` and `condition` for dataset and statistical cells, but `_raw_log_cell()` and `audit_artifacts()` still used raw labels. Width, case, whitespace, invisible-character, separator, or condition-token-order variants could therefore create inconsistent resource topology and raw-log measurement binding relative to the scored cell identity.

Examples include `RTFM` versus `ＲＴＦＭ`, and `entity_holdout+dynamics_holdout` versus `DYNAMICS_HOLDOUT | ENTITY_HOLDOUT`.

## Fail-closed change

Cycle 081 makes raw-log and resource cells use the same canonical identity as scoring:

- domain: Unicode NFKC, case folding, removal of whitespace/control/format characters;
- condition: canonicalized tokens, deduplicated and sorted;
- manifest/raw-log field comparison uses the same canonicalization;
- different raw artifact labels collapsing to one canonical domain or condition are rejected;
- audit output records the normalization requirement and collision findings.

Any violation is classified as `initial_reproduction_failure`.

## Evidence status

- core patch script: added to the canonical branch;
- focused regression: added;
- same-branch workflow: added;
- core integration commit and CI success: not recognized until GitHub Actions completes;
- accepted real R0 bundle: 0;
- accepted public baseline reproduction: 0.
