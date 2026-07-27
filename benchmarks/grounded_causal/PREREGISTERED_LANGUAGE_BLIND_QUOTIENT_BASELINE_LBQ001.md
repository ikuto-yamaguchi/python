# Preregistered Language-Blind Quotient Baseline LBQ001

## Status

- Canonical branch: `research/intelligence-swarm-reconstruction-001`.
- Purpose: preregister the first admissible baseline after C070.
- This document does not introduce a new architecture.
- This document does not extend legacy A–E toy mechanisms.
- Numerical execution has not started.
- Novelty, intelligence-principle, and capability-progress claims are prohibited.

## Decision question

Before raw language is allowed to claim discovery of an intervention-target ontology, how much of the target partition is recoverable from the complete declared non-language controlled process alone?

LBQ001 defines a language-blind baseline for the controlled predictive/bisimulation quotient and fixes direct partition metrics, leakage exclusions, controls, resource reporting, and rejection criteria before implementation.

## Primary theoretical basis

1. Zhang et al., *Learning Causal State Representations of Partially Observable Environments*, arXiv:1906.10437 / RLDM 2019.
   - Causal states are the coarsest partition of action-observation histories inducing the same future controlled observation law.
2. Ferns, Panangaden, and Precup, *Metrics for Finite Markov Decision Processes*, UAI 2004 / arXiv:1207.4114.
   - Bisimulation metrics quantify behavioral similarity and support state aggregation with value bounds.
3. Gelada et al., *DeepMDP: Learning Continuous Latent Space Models for Representation Learning*, ICML 2019.
   - Reward and latent transition prediction losses provide a practical continuous-state approximation connected to bisimulation theory.

These references define prior-art baselines; they are not treated as new mechanisms.

## Formal target object

Let a history be

`h_t = (o_1, a_1, ..., a_{t-1}, o_t)`.

Let `A*` be the preregistered admissible clarification/intervention action family and let `Y*` be the preregistered consequence vector. `Y*` may contain only non-semantic measurements such as sensor values, action availability, costs, terminal physical outcomes, and state transitions.

Define

`h ~_LBQ h'`

iff for every admissible future action policy or finite action sequence,

`P(Y_future | h, do(A_future)) = P(Y_future | h', do(A_future))`.

The corresponding quotient is `P_LBQ`.

No partition finer than `P_LBQ` may be called identified unless a preregistered held-out consequence separates the proposed blocks.

## Dataset contract

Each episode record must contain only:

- raw non-language observation;
- action or intervention actually issued;
- physical/sensor consequence vector;
- action cost and availability where physically defined;
- episode boundary;
- environment split identifier that does not encode target identity.

The language-blind training view must exclude:

- raw utterance text;
- token IDs or language embeddings;
- parser output;
- entity, object, role, or target names;
- target masks or intervention-target labels;
- simulator variable names;
- success labels derived from semantic targets;
- reference structures or evaluators generated from the target codebook;
- completed-trajectory annotations that reveal the target;
- pretrained representations trained on the same target names.

A machine-readable feature inventory and SHA-256 digest of the final training/evaluation tables are required before the first run.

## Baseline hierarchy

The first execution must compare the following without adding a new architecture.

### B0: observation-identity baseline

- Treat each observed discrete state/history key as its own block.
- Purpose: upper-bound over-fragmentation and verify partition metrics.

### B1: one-step consequence partition

- Merge histories only when empirical immediate consequence distributions match under every observed admissible action.
- Purpose: determine how much apparent structure is recoverable without long-horizon prediction.

### B2: finite-horizon controlled predictive partition

- Use the same estimator family already available in the repository or a faithful public baseline implementation.
- Predict preregistered consequence vectors for horizons `H in {1, 2, 4, 8}` under actions.
- Cluster only through a preregistered distance threshold selected on the development split.

### B3: reward/task-relative bisimulation control

- Use only the training task reward and transition law.
- Purpose: demonstrate expected under-partitioning relative to the full consequence family.
- This control may not be reported as environment-level semantic recovery.

### B4: full-consequence language-blind quotient baseline

- Use all preregistered non-semantic consequence channels.
- This is the principal comparator for any later language-conditioned model.

No additional encoder, attention mechanism, memory module, causal mechanism family, or language module may be introduced in LBQ001.

## Evaluation objects

Ground-truth labels, when available, are used only after training for evaluation and never as features, losses, sampling strata, early-stopping signals, or hyperparameter selectors.

The evaluation must separately report:

1. `P_LBQ` recovery:
   - adjusted Rand index;
   - adjusted mutual information;
   - pairwise precision, recall, and F1 for same-block decisions;
   - variation of information;
   - block-count error.
2. Controlled-law adequacy:
   - held-out one-step consequence error;
   - held-out multi-step consequence error;
   - action-conditioned calibration;
   - maximum within-block held-out consequence discrepancy;
   - minimum between-block held-out consequence discrepancy.
3. Task-relative behavior:
   - return or success only as a secondary metric;
   - value difference where defined.
4. Forbidden substitutions:
   - task success, next-state accuracy, or representation similarity alone cannot substitute for direct partition recovery.

## Required controls

### C1: action shuffle

Shuffle actions within the allowed matching strata. Partition recovery must degrade if controlled consequences are genuinely used.

### C2: consequence-channel shuffle

Independently shuffle each consequence channel. Recovery of the full quotient must degrade.

### C3: semantic leakage positive control

Expose the gold target ID intentionally in a separate marked run. This checks metric/pipeline ceilings but is never admissible evidence.

### C4: language leakage audit

Scan feature names, serialized values, manifests, and embeddings for target names, parser slots, utterance tokens, and semantic IDs. Any detection invalidates the run.

### C5: reward-only control

Compare B3 against B4 to quantify task-relative under-partitioning.

### C6: held-out consequence test

Train without at least one preregistered physical consequence channel and evaluate whether proposed within-block equality survives that held-out channel.

### C7: environment-label shuffle

Shuffle non-semantic environment split IDs. Results should remain stable unless those IDs leaked target structure.

## Split and seed contract

- Three fixed seeds are mandatory at experiment start: `17`, `29`, `43`.
- The environment/episode split must be fixed before training and shared across baselines.
- Hyperparameters may be selected on development data only.
- Test partition labels and held-out consequence channels are inaccessible until the final evaluation.
- All seed-specific outputs and the aggregate must be retained.

## Resource contract

Once execution starts, every baseline and seed must report:

- serialized model size in bytes;
- parameter count where applicable;
- peak resident set size;
- wall-clock training time;
- wall-clock evaluation time;
- hardware and software environment;
- dataset size and digest;
- command line and exact commit;
- raw result digest.

Missing any mandatory resource field makes the run incomplete, not negative.

## Acceptance criteria for the baseline

LBQ001 is qualified only if all of the following hold:

1. all three seeds complete under the identical split and manifest;
2. no language or target-codebook leakage is detected;
3. B4 directly recovers the preregistered quotient above the random/shuffle controls;
4. held-out controlled-law discrepancy is lower within recovered blocks than between blocks;
5. action and consequence shuffles materially degrade partition recovery;
6. resource and checksum bundles are complete;
7. conclusions are limited to controlled behavioral quotient recovery.

No universal numeric threshold is preregistered before inspecting the dataset cardinality and oracle separability. Before execution, a dataset-specific minimum effect size and confidence rule must be appended without using test labels.

## Rejection criteria

The following reject the baseline qualification or the stronger interpretation:

- B4 fails to outperform shuffled controls on direct partition metrics;
- apparent success exists only in reward/task metrics;
- B3 and B4 are indistinguishable despite a known held-out physical distinction;
- recovered blocks contain a preregistered held-out consequence difference;
- target identity, parser output, semantic reward, or target-derived evaluator enters training;
- results depend on one seed;
- model size, RSS, runtime, commands, or checksums are missing after execution begins.

## Consequence for RQ-001

A later language-conditioned experiment is decision-relevant only if it compares against qualified B4 and shows one of the following:

- language estimates the same quotient more sample-efficiently without changing the ontology claim; or
- language separates blocks that B4 merges, and an independent preregistered held-out consequence validates that separation.

If language proposes a finer partition without such an independent consequence, the result is extra-behavioral convention or unsupported ontology, not joint identification.

## Current status

- Preregistration: written.
- Baseline implementation: not started in this document.
- Numerical reproduction: not started.
- New architecture: none.
- Legacy toy mechanism: none added.
- Model size, RSS, runtime, and three-seed results: required only when execution starts.
- RQ-001: not adopted.
