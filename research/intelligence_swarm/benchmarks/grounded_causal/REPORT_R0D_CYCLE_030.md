# R0-D Cycle 030 — Prediction payload leakage and schema integrity

## Scope

This cycle continues R0 benchmark reproducibility, statistics, and leakage auditing only. It adds no memory, replay, fast weights, sleep, forgetting, architecture, or toy mechanism.

## Defect found

The canonical dataset contract rejects gold action/state, rewards, terminal outputs, and completed trajectories when they appear in model inputs. However, a prediction exporter could still write those same fields into the prediction JSONL. The existing scorer ignored unknown payload fields, so a bundle containing leaked gold/outcome material could still enter coverage and paired-statistics aggregation.

The scorer also compared `pred_action` with the gold action without independently checking whether the predicted action was valid under the instance action schema, and accepted non-finite values nested in predicted states.

## Added fail-closed audit

`audit_prediction_payload_leakage.py` now requires:

- exactly the preregistered six methods;
- complete prediction coverage for every non-training instance;
- one prediction per `instance_id × method`;
- a strict registered top-level prediction schema;
- rejection of gold action/state/inverse, answers, labels, rewards, terminal outputs, episode success/return, future state, rollout, and completed trajectory fields;
- finite JSON-compatible prediction values;
- predicted actions valid under `valid_action_mask` or `valid` when supplied;
- no predictions for training instances.

Any violation is classified as `initial_reproduction_failure`.

## Regression coverage

The focused test suite fixes the following cases:

1. clean six-method complete payload passes;
2. leaked `gold_state_after` fails;
3. leaked `completed_trajectory` fails;
4. unregistered debug/hidden payload fails;
5. action outside the instance valid-action schema fails;
6. non-finite predicted state fails;
7. one missing outcome-shuffle prediction fails coverage.

A dedicated short GitHub Actions workflow compiles and executes the auditor and tests without starting the long SILG reproduction workflow.

## Evidence status

This cycle changes qualification logic only. It does not produce or accept a public benchmark result.

- real R0 bundle passing all contracts: 0
- accepted public baseline reproduction: 0
- accepted model/RSS/runtime/latency bundle: 0
- capability progress: not recognized
- classification: `initial_reproduction_failure`
