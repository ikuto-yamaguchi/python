# R0-D Cycle 038 — alias-normalized leakage in the core contract

## Scope

This cycle changes only R0 benchmark reproducibility and leakage auditing. It does not add a memory mechanism, replay, fast weights, sleep, forgetting, a toy task, an architecture, or a capability claim.

## Defect found

`audit_schema_alias_leakage.py` and the integrated acceptance gate rejected schema variants such as `goldAction`, `completed-Trajectory`, and `episodeReturn`. However, callers could still invoke `evaluation_contract.py validate` or `evaluation_contract.py score` directly. The core contract compared nested model-input keys and prediction keys primarily by exact spelling, so camelCase, kebab-case, spacing, or Unicode-width variants could bypass the direct entry point.

A second ambiguity existed for aliases of otherwise allowed prediction fields. Silently accepting `predAction` as `pred_action` would make evidence schemas exporter-dependent and could create key collisions when both spellings were present.

## Change

`evaluation_contract.py` now performs fail-closed key normalization itself:

1. Unicode NFKC normalization;
2. case folding;
3. removal of non-ASCII-alphanumeric separators;
4. comparison against canonical forbidden-key maps.

The direct `validate` path now rejects alias-normalized forbidden names in both `model_input_fields` and recursively nested `model_input` payloads. The direct `score` path rejects alias-normalized gold/outcome/trajectory fields and records their canonical forbidden names.

Allowed prediction keys are not silently rewritten. A noncanonical alias such as `predAction` is rejected as an unregistered field, and two keys that normalize to the same schema key are rejected as an alias collision.

## Regression coverage

`test_evaluation_contract_alias_core.py` covers:

- a clean canonical dataset and six-method prediction bundle;
- camelCase `goldAction` in `model_input_fields`;
- nested kebab-case `completed-Trajectory`;
- prediction-side `episodeReturn`;
- noncanonical aliasing of an allowed field;
- simultaneous alias-colliding keys.

The expected failure classification remains `initial_reproduction_failure`.

## Evidence status

This cycle strengthens evidence admission only. It does not produce or accept a new SILG/RTFM reproduction bundle. No public-baseline value, model-size bundle, peak RSS, training wall time, CPU inference latency, raw log, or checksum bundle is newly accepted here.

- accepted R0 bundles: 0
- public baseline reproduction: not established
- capability progress: not recognized
- new intelligence principle: not recognized
- classification until a complete bundle passes: `initial_reproduction_failure`
