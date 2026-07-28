# RESET-E034 — R0 Research Reconstruction Integration

## Scope

This integration keeps all work on `research/intelligence-swarm-reconstruction-001`. It adds no toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, branch, or stacked PR chain. Existing stacked drafts remain negative-results archives only.

## Verified repository state

- Canonical PR: #409, draft, mergeable.
- Current pre-integration head: `a44f384360b2be4c2466a1b437c054857caa3991`.
- Latest completed short CI: `R0 prediction method topology tests`, run `30165709843`, conclusion `success`.
- No new preserved real R0 benchmark bundle was established.
- No new accepted public capability value, checkpoint, model bytes, RSS, wall time, CPU latency, raw log, or checksum was established.

## R0.1

Run `30158106220` remains the latest long-run evidence. Installation, schema/random probe, official recurrent 131,072 requested frames for seeds `1,7,19`, and matched Correct/Random/Language-blind/State-only/Language-shuffle steps succeeded. The run failed during the downstream R0.2 step before dependency freeze and artifact upload; workflow artifacts remained empty.

Therefore:

- training/matched-control execution progress is recognized;
- reproducible R0.1 bundle is absent;
- public capability baseline reproduction remains unestablished;
- classification remains `initial_reproduction_failure_due_to_unpreserved_bundle_after_downstream_failure`.

The canonical workflow's split-job boundary remains mandatory: R0.1 must freeze and upload its immutable bundle before R0.2 downloads it.

## R0.2

No accepted three-seed task-success, next-state-prediction, action-accuracy, dynamics-transfer, or resource result exists. RTFM S1 supports a real dynamics holdout only; entity and language-form holdouts remain formally inapplicable.

## Evaluation contract — D028

D028 adds an exact prediction-method topology audit. Every evaluation instance and every observed `domain × seed × split × condition` cell must contain exactly:

- `correct`
- `random`
- `language_blind`
- `state_only`
- `target_label_shuffle`
- `outcome_shuffle`

The auditor rejects unregistered extra methods, globally missing methods, per-instance omissions, per-cell omissions, predictions outside the evaluation set, and all failures already detected by the dataset/scoring contracts. Its dedicated short CI passed at run `30165709843`.

This is an evaluation-integrity improvement only. It is not capability progress and does not substitute for applying the contract to a preserved real bundle.

## Prior-art and RQ-001

The C023–C025 boundary remains unchanged. State-dependent local dynamics, isolated language effects, and mechanistic-independence results remove additional broad novelty claims. The only remaining candidate asks whether an externally fixed, non-recodable language contrast can strictly separate an explicit residual countermodel pair after the strongest non-language, mechanistic, interaction-history, and language-effect criteria.

The candidate remains not adopted. Adoption still requires an explicit residual countermodel pair, anti-recoding anchor, strict joint-identification theorem, anchor-removal impossibility result, finite-sample or consistency guarantee, dependency-pinned public baseline reproduction, and exactly one preregistered claim with stopping rule.

## Stage decision

No stage transition is proposed. R0.1–R0.3, the novelty matrix, and one preregistered central claim are not all complete.

## Status

- accepted learned public capability baseline: 0
- formal R0.2 reproduction: 0
- real R0 bundle passing the unified contract: 0
- R0.3: rejected
- broad RQ-001: rejected
- narrowed RQ-001: not adopted
- evaluation classification: `initial_reproduction_failure`
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- completion: false
