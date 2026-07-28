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
4. Dean and Givan, *Model Minimization in Markov Decision Processes*, AAAI 1997.
   - The coarsest exact homogeneous refinement supplies the unique exact quotient relative to the declared observable labels and named actions.

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

## C087 estimand lock

The canonical B4 estimand is now fixed to the **exact full-consequence controlled predictive quotient** `P_LBQ` defined above.

This choice is made because it has all of the following properties relative to the declared action and consequence interface:

- a unique coarsest quotient up to block-label permutation;
- monotonic refinement when new admissible non-semantic consequence channels are added;
- direct compatibility with exact known-model bisimulation/homogeneous-partition oracles;
- no arbitrary distance threshold, linkage rule, perturbation budget, or split-order tie break;
- a clear observation-level meaning: equality of the entire allowed controlled future law.

The following objects are retained only as diagnostics or explicitly different estimands and may not be reported as recovery of canonical `P_LBQ`:

- bisimulation-metric threshold clusters;
- epsilon-homogeneous partitions;
- robust-exact relations under a perturbation family;
- perturbation-repair quotients;
- task-relative reward/value abstractions;
- plug-in empirical partitions without confidence and coverage certification.

### Exact empirical decision contract

For an unconstrained finite sample, equality of two real-valued transition/consequence laws cannot generally be certified. Therefore the empirical exact-mode pair decision is asymmetric:

- `separate`: admitted only when a simultaneous confidence argument excludes equality for at least one covered action/consequence condition;
- `merge`: admitted only when equality follows from preregistered symbolic parameter tying, a known deterministic identity, or an exact complete-model oracle—not merely failure to reject a difference;
- `unidentified`: mandatory whenever both equal and unequal point models remain compatible with the observations or an admissible action lacks coverage.

A finite-sample system that converts `fail to reject` into `merge` is invalid for canonical B4.

### Approximate-mode firewall

An approximate analysis may be run only as a separately named diagnostic after fixing:

- its exact estimand;
- discrepancy metric;
- tolerance source;
- global partition-selection rule;
- action/channel error allocation;
- coverage and abstention rule.

Approximate output cannot establish the exact latent intervention partition `P`, raw-language equivalence `Q`, or denotation `d`.

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

### B1: one-step consequence diagnostic

- Compare empirical immediate consequence distributions under every covered admissible action.
- May certify separations, but may not certify exact merges from finite samples without structural equality.
- Purpose: determine how much apparent structure is recoverable without long-horizon prediction.

### B2: finite-horizon controlled predictive diagnostic

- Use the same estimator family already available in the repository or a faithful public baseline implementation.
- Predict preregistered consequence vectors for horizons `H in {1, 2, 4, 8}` under actions.
- Any threshold clustering is approximate-mode output and must not be labelled canonical `P_LBQ` recovery.

### B3: reward/task-relative bisimulation control

- Use only the training task reward and transition law.
- Purpose: demonstrate expected under-partitioning relative to the full consequence family.
- This control may not be reported as environment-level semantic recovery.

### B4: exact full-consequence language-blind quotient

- Use all preregistered non-semantic consequence channels and all admissible named actions.
- Exact known-model reference: compute the coarsest exact quotient of the supplied complete model.
- Empirical output: a partially resolved relation consisting of certified `separate`, structurally/oracularly certified `merge`, and `unidentified` pairs.
- This is the principal comparator for any later language-conditioned model.

No additional encoder, attention mechanism, memory module, causal mechanism family, or language module may be introduced in LBQ001.

## Evaluation objects

Ground-truth labels, when available, are used only after training for evaluation and never as features, losses, sampling strata, early-stopping signals, or hyperparameter selectors.

The evaluation must separately report:

1. `P_LBQ` recovery:
   - adjusted Rand index, adjusted mutual information, pairwise precision/recall/F1, variation of information, and block-count error for the exact oracle or any fully resolved structurally tied case;
   - coverage-adjusted pairwise precision/recall for certified empirical decisions;
   - abstention/unidentified rate overall and by action coverage stratum;
   - false-merge count, which is a critical failure metric.
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
   - task success, next-state accuracy, representation similarity, large p-values, or overlapping confidence intervals alone cannot substitute for direct exact partition evidence.

## Required controls

### C1: action shuffle

Shuffle actions within the allowed matching strata. Partition evidence must degrade if controlled consequences are genuinely used.

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

### C8: fail-to-reject firewall

Construct a positive-distance alternative small enough to evade a low-power finite-sample test. The empirical pipeline must return `unidentified`, never `merge`.

### C9: missing-action coverage

Remove all samples for at least one admissible state-action condition. Every affected equality claim must remain `unidentified`.

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
3. exact known-model B4 reproduces the preregistered oracle quotient;
4. every empirical `merge` is backed by symbolic equality or an exact complete-model oracle;
5. empirical `separate` decisions have simultaneous error control and no false separation beyond the preregistered level;
6. uncovered actions and statistically unresolved pairs are explicitly abstained;
7. held-out controlled-law discrepancy is lower within valid oracle/structural blocks than between separated blocks;
8. action and consequence shuffles materially degrade usable evidence;
9. resource and checksum bundles are complete;
10. conclusions are limited to controlled behavioral quotient recovery.

No universal numeric threshold is preregistered before inspecting the dataset cardinality and oracle separability. Before execution, a dataset-specific separation target and simultaneous confidence rule must be appended without using test labels.

## Rejection criteria

The following reject the baseline qualification or the stronger interpretation:

- finite-sample failure to reject is converted into exact merge;
- B4 fails to detect oracle-separated pairs with adequate covered separation;
- apparent success exists only in reward/task metrics;
- B3 and B4 are indistinguishable despite a known held-out physical distinction;
- recovered blocks contain a preregistered held-out consequence difference;
- target identity, parser output, semantic reward, or target-derived evaluator enters training;
- unresolved or uncovered pairs are silently forced into a partition;
- results depend on one seed;
- model size, RSS, runtime, commands, or checksums are missing after execution begins.

## Consequence for RQ-001

A later language-conditioned experiment is decision-relevant only if it compares against qualified B4 and shows one of the following:

- language improves sample efficiency for certified separations without changing the exact ontology claim; or
- language proposes a coupling or finer distinction that is independently validated by a preregistered non-semantic consequence unavailable to the language model.

Language cannot convert an empirically `unidentified` target pair into an identified denotation merely through internal confidence or distributional similarity. If language proposes a finer partition without independent consequence evidence, the result is extra-behavioral convention or unsupported ontology, not joint identification.

## Current status

- Preregistration: updated by C087; canonical exact estimand fixed.
- Exact known-model B4 oracle: selected in prior audits; execution not started.
- Empirical exact-mode contract: `separate / structurally-oracularly merge / unidentified` fixed.
- Approximate estimands: diagnostics only unless separately preregistered.
- Baseline implementation: not started in this document.
- Numerical reproduction: not started.
- New architecture: none.
- Legacy toy mechanism: none added.
- Model size, RSS, runtime, and three-seed results: required only when execution starts.
- RQ-001: not adopted.