# R0-D Cycle 023 — Enforce semantic leakage regression in canonical CI

## Scope

This cycle adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, branch, or PR chain. It advances only R0 benchmark reproducibility and leakage enforcement on the canonical reconstruction branch.

## Concrete gap closed

Cycle D022 added `audit_model_input_semantic_leakage.py`, but the canonical `r0_evaluation_contract_tests.yml` workflow neither watched that file nor compiled or executed its regression tests. A semantic leakage regression could therefore be introduced while the evaluation-contract workflow remained green or did not run.

The canonical workflow now:

- triggers when the semantic leakage auditor or its test changes;
- compiles `audit_model_input_semantic_leakage.py` together with the other R0 audit modules;
- executes `test_audit_model_input_semantic_leakage.py` in the mandatory evaluation-contract test job.

The enforced cases are:

1. clean prospective input passes;
2. `future_state` carrying the gold after-state fails;
3. completed `rollout_context` / post-treatment information fails;
4. `target_action` carrying the current gold action fails.

## Remaining limitation

The semantic checks remain implemented as a fail-closed companion auditor rather than duplicated inside the 764-line `evaluation_contract.py`. The canonical CI now makes the companion mandatory, but a consumer invoking only `evaluation_contract.py` outside the canonical workflow would not receive the alias/value checks. Direct composition into one public CLI remains an explicit integration item; no claim is made that this limitation is closed.

## Current evidence status

No real R0 dataset/prediction/resource bundle has passed the complete canonical contract. No new public-baseline result, model bytes, RSS, wall time, CPU latency, raw log, or checksum was produced in this cycle.

Formal classification remains:

`initial_reproduction_failure`

No capability progress, novelty, intelligence principle, or high-school-level intelligence is recognized.
