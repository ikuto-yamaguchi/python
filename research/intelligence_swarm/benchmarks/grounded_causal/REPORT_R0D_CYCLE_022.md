# R0-D Cycle 022 — Semantic model-input leakage audit

## Scope

This cycle adds no memory, replay, fast weights, sleep, forgetting, toy mechanism, architecture family, branch, or PR chain. It tightens the existing grounded-causal evaluation contract on the canonical reconstruction branch.

## Gap closed

`evaluation_contract.py` already rejects explicit forbidden fields such as `gold_action`, `gold_state_after`, `completed_trajectory`, `reward`, and `done` when they appear under their canonical names. A producer could still hide the same post-treatment information under aliases such as `future_state`, `rollout_context`, `target_action`, or `oracle_*`.

`audit_model_input_semantic_leakage.py` now performs a fail-closed companion audit over the concrete JSONL rows. It:

- adapts SILG-style `action` and `state_after` to gold fields;
- recursively scans `model_input` keys for future, outcome, terminal, trajectory, rollout, reward, success, oracle, answer, and gold aliases;
- rejects current-action labels hidden under aliases such as `target_action` or `chosen_action` when the value equals the gold action;
- rejects exact gold-after-state values placed outside the prospective input allowlist when the after-state differs from the before-state;
- classifies every failure as `initial_reproduction_failure`.

The allowlist is limited to `utterance`, `state_before`, `history`, and `valid_action_mask`. Historical actions are not rejected merely because a past action happens to equal the current gold action; a current-action alias and matching value are both required.

## Regression coverage

`test_audit_model_input_semantic_leakage.py` fixes four cases:

1. clean prospective input passes;
2. `future_state` containing the gold after-state fails;
3. `rollout_context` containing completed/post-treatment information fails;
4. `target_action` equal to the gold action fails.

The four tests passed in a local standard-library-only execution before commit. GitHub Actions status is not claimed until a run is independently observed.

## Current classification

No real R0 prediction/data/artifact bundle has yet passed the complete evaluation contract plus this semantic leakage audit. The formal status therefore remains:

`initial_reproduction_failure`

No public baseline reproduction, capability progress, novelty, or intelligence principle is recognized by this cycle.
