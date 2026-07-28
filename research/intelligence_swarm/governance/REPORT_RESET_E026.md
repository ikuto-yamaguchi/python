# RESET-E026 — R0 Research Reconstruction integration

Date: 2026-07-25

## Scope

This integration updates the single canonical reconstruction branch only. It adds no toy mechanism, memory/replay/fast-weights/sleep/forgetting mechanism, architecture family, intervention ontology, branch, or stacked PR chain. Existing stacked drafts remain negative-results archives and are not used as bases for new work.

## Integrated evidence

### 1. Primary literature and official-code overlap audit

C019 adds Schneider et al., ICML 2025, *Generative Intervention Models for Causal Perturbation Modeling* to the novelty boundary. The work already learns a map from observed perturbation features to distributions over unknown atomic interventions in a jointly estimated causal model and evaluates unseen perturbation effects.

Consequences:

- feature-to-unknown-target prediction is not a new raw-language causal-identification contribution;
- replacing perturbation features with utterance embeddings is not sufficient novelty;
- unseen perturbation prediction and interpretable target probabilities do not establish target-partition identifiability;
- a joint-recoding counterexample remains unless language denotation is externally fixed.

A corresponding official implementation repository was not located from the primary records and targeted GitHub search, so no reproduction is claimed.

### 2. SILG / J-CRe3 reproduction progress

No new public capability result is accepted in this integration.

Accepted SILG/RTFM evidence remains:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent, no pretrained LM
- seeds `1 / 7 / 19`
- 32,768 requested frames, 32,800-frame checkpoints
- Correct `1/60`, Random `4/60`

The learned policy remains below Random. There is no verified clean 131,072-frame artifact at the integrated canonical head. J-CRe3 remains unreproduced.

### 3. Matched controls

The accepted fixed-instance controls remain Correct, Random, Language-blind, State-only, and Language-shuffle. Transition/outcome shuffle and target-label shuffle remain subject to the immutable evaluation contract; target-label shuffle requires a non-oracle target label or a formal inapplicability record.

No new control result is accepted because no competent canonical public baseline bundle exists.

### 4. Model and resource accounting

Accepted 32,768-frame values remain:

- parameters: `4,916,915`
- state-dict audit: `19,694,385 bytes`
- maximum RSS: `505,600 KiB`
- total three-seed training wall time: `1,033.885 s`
- CPU forward audit: `6.911 ms/step`

No resource or performance values from incomplete, cancelled, duplicated, or unverified runs are accepted.

### 5. Leakage and statistical qualification

D022 adds fail-closed semantic alias detection over concrete model inputs. It rejects future/post-treatment/action-label/outcome information hidden under names such as `future_state`, `rollout_context`, `target_action`, `chosen_action`, or `oracle_*`. The prospective allowlist is limited to utterance, state-before, history, and valid-action mask.

The four D022 regression tests passed locally. GitHub Actions completion is not claimed. The real R0 bundle has not passed D016–D022 and remains classified as `initial_reproduction_failure`.

### 6. R0.2 transfer qualification

Cycle 015 adds a preregistered generator-metadata manifest builder. It cannot use action, reward, done, return, task success, prediction, action accuracy, or next-state loss to assign holdouts.

The remaining blocker is a real sidecar from the pinned RTFM generator containing:

- `entity_signature`
- `dynamics_signature`
- `language_form_signature`

Until that sidecar and competent three-seed source trajectories exist, Environment-first / End-to-end / State-only online comparison remains blocked.

### 7. RQ-001 decision

Broad RQ-001 remains rejected. The only admissible candidate is now narrower than known grouping and feature-conditioned intervention modelling:

> Can an externally fixed denotational population-language channel jointly identify raw-utterance equivalence classes and a residual latent intervention-target partition after all known non-language identifiability routes and feature-conditioned intervention models are accounted for?

This candidate remains not adopted. Before adoption it requires a formal residual equivalence class, anti-recoding anchor, uniqueness theorem, matched impossibility result, GIM-type baseline comparison, unseen-form/composition/target-combination/system splits, public baseline reproduction, and exactly one preregistered claim and stopping rule.

## Integrated decision

- R0.1 public capability baseline: **not reproduced**
- R0.2 formal reproduction: **not completed**
- R0.3 hidden intervention-target track: **rejected**
- novelty matrix: **expanded, not closed**
- successor central claim: **not preregistered**
- evaluation classification: **`initial_reproduction_failure`**
- next-stage proposal: **forbidden**
- new architecture: **none**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**

## Single active bottleneck

Finish and qualify exactly one clean 131,072-frame official recurrent SILG run with all three seeds, immutable matched controls, raw logs, checksums, model bytes, RSS, training time, CPU latency, policy competence, and action-collapse checks. New mechanism or RQ implementation remains blocked until this succeeds or reaches a preregistered reproduction-failure stopping condition.
