# Causal Identifiability Audit C086

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, and (d) identifiability/applicability counterexamples.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C085 established that action-conditioned recursive MDP bisimulation metrics and exact known-model computation are existing prior art. It left open whether a *global approximate partition*—rather than a pairwise metric—was itself still missing from the baseline stack.

This run audits the older MDP state-aggregation literature on homogeneous and epsilon-homogeneous partitions. The central question is whether the remaining novelty candidate can still be described as “define a globally coherent action-conditioned approximate quotient,” or whether that object already exists and the actual unresolved part is statistical recovery, estimand selection, and language coupling.

## Primary prior art

### Dean, Givan, and Leach: epsilon-homogeneous MDP partitions

The line of work beginning with Dean and Givan's exact model minimization and extended by Dean, Givan, and Leach introduces state-space partitions for finite MDPs that preserve action-conditioned reward and transition behavior.

For exact homogeneity, states in one block must have the same reward and, for every named action, the same probability of reaching every block of the partition. Partition refinement computes the coarsest homogeneous refinement of an initial partition, yielding a reduced MDP that is equivalent for planning.

The approximate extension replaces exact equality by an `epsilon` tolerance. Informally, a partition is epsilon-homogeneous when, within every block and for every action:

- rewards differ by at most the chosen tolerance;
- transition probability into every aggregate block differs by at most the chosen tolerance.

The resulting approximate partition induces a bounded-parameter MDP (BMDP): aggregate rewards and transition probabilities are represented by intervals spanning the values of concrete states in each block. Planning in the BMDP then yields approximate policies and value bounds for the original factored MDP.

Primary records:

- Dean and Givan, *Model Minimization in Markov Decision Processes*, AAAI 1997.
- Dean, Givan, and Leach, *Model Reduction Techniques for Computing Approximately Optimal Solutions for Markov Decision Processes* (technical report / arXiv `1302.1533`, work originating in the late 1990s).
- Kim and Dean, *Solving Factored MDPs Using Non-Homogeneous Partitions*, Artificial Intelligence 147, 2003.

## What is existing prior art

The following are not available as novelty claims for RQ-001 or LBQ001:

- constructing a global state partition rather than independent pairwise similarity decisions;
- preserving named actions while aggregating MDP states;
- defining approximate block consistency through reward and block-transition tolerances;
- refining a partition until action-conditioned aggregate behavior is sufficiently homogeneous;
- converting an approximate partition into interval-valued aggregate dynamics;
- trading quotient size against planning error by varying a tolerance parameter;
- using approximate MDP aggregation to derive value or policy-loss guarantees.

Therefore the remaining B4 problem must not be stated as “invent a transitive global approximate MDP partition.” A classical action-conditioned global partition formalism already exists.

## Assumption and guarantee comparison

### Exact homogeneous partition

The exact construction assumes:

- a fully specified finite MDP or an exact factored representation;
- a fixed action alphabet;
- rewards and transition probabilities available without statistical uncertainty;
- an initial partition whose observable labels must be preserved.

It guarantees a stable homogeneous refinement and an exact reduced model relative to the supplied reward/transition observables.

For LBQ001, this is another known-model oracle family, comparable in role to the pinned Storm quotient but historically earlier and naturally expressed for factored MDPs.

### Epsilon-homogeneous partition

The approximate construction assumes:

- a fully specified MDP, not merely a finite trajectory sample;
- a user-selected tolerance;
- a particular coordinate-wise comparison to the current aggregate blocks;
- an explicit choice of which rewards and consequences are part of the model.

It supplies:

- a globally represented partition;
- action-conditioned approximate block stability;
- an interval aggregate model;
- planning-oriented approximation guarantees under the paper's assumptions.

It does **not** by itself supply:

- confidence-valid estimation from finite trajectories;
- abstention for uncovered state-action pairs;
- a unique semantic ontology;
- a tolerance calibrated from physical measurement error or sampling uncertainty;
- preservation of independent sensor, cost, action-availability, or held-out consequence channels unless encoded;
- leakage checks preventing target IDs or semantic rewards from defining the initial partition;
- raw-language quotient `Q`;
- denotation `d: Q -> P`.

## Counterexample 1: global approximate partition prior art does not imply a unique quotient

Consider three states with identical transition laws and one action, but rewards

- `R(s1)=0`,
- `R(s2)=0.6 epsilon`,
- `R(s3)=1.2 epsilon`.

Under a within-block reward-diameter tolerance of `epsilon`:

- partition `{{s1,s2},{s3}}` is admissible;
- partition `{{s1},{s2,s3}}` is also admissible;
- partition `{{s1,s2,s3}}` is not admissible.

The two admissible partitions are incomparable: neither refines the other. Thus an approximate homogeneity criterion can define a family of valid partitions without selecting one unique greatest semantic quotient.

A refinement algorithm may return a valid partition according to its initialization and splitting rule, but algorithmic output is not automatically an identifiable ontology.

Therefore:

> global transitivity and approximate block consistency are not sufficient for uniqueness of `P`; the estimand and tie-breaking or optimality criterion must be preregistered.

## Counterexample 2: coordinate-wise block tolerance depends on the current partition

Suppose two states differ slightly in transition probability to many successor blocks. If the per-block discrepancy is bounded by `epsilon`, an epsilon-homogeneity test can accept them even when the total-variation discrepancy across all blocks is as large as roughly the number of blocks times `epsilon` (subject to normalization).

Conversely, merging successor blocks can reduce apparent coordinate differences and make a source-state pair admissible, while splitting successors can expose differences and force separation.

Thus the approximate relation is recursively partition-dependent. It is not equivalent to a fixed, partition-independent pairwise metric threshold.

For LBQ001 this means the tolerance contract must specify at least:

- coordinate-wise, total-variation, Wasserstein/Kantorovich, or consequence-vector discrepancy;
- whether tolerance is per action, per channel, or jointly allocated;
- how error scales with the number of current blocks;
- how refinement and stopping select one result among multiple admissible partitions.

## Counterexample 3: a known-model epsilon partition is not a finite-sample identifier

Let `M0` and `Meta` be two point MDPs consistent with the same finite dataset.

- In `M0`, two states have exactly equal action-conditioned transition laws.
- In `Meta`, one transition probability differs by a small positive `eta`.

For a fixed epsilon:

- both may fall inside one epsilon-homogeneous block when `eta <= epsilon`;
- only `M0` is exactly bisimilar;
- for a smaller preregistered tolerance, their admissible partitions may differ.

The classical algorithm gives the correct partition family for whichever complete point model is supplied. It does not determine which model generated the data, nor whether the selected epsilon reflects statistical uncertainty, physical tolerance, or task preference.

Therefore:

> exact computation of an epsilon-homogeneous partition for an empirical plug-in model does not establish finite-sample identification of the true target partition.

Coverage, simultaneous uncertainty, and abstention remain separate requirements.

## Counterexample 4: planning approximation is not semantic identification

Two concrete states can be merged with negligible loss for one reward function while differing on an independent physical sensor, intervention cost, action availability, or a held-out task.

An epsilon-homogeneous partition built only from task reward and aggregate transitions may be entirely valid for approximate planning yet too coarse for the preregistered full-consequence B4 ontology.

If those extra channels are appended using gold target identity, parser output, simulator object names, or semantic evaluator labels, the resulting finer partition merely preserves supplied semantics.

Therefore planning-loss guarantees cannot substitute for direct recovery of leakage-free `P`.

## Public-code availability audit

The primary papers and algorithm descriptions are publicly accessible. This run did not confirm a paper-specific author-maintained repository with:

- an immutable commit implementing the original epsilon-homogeneous factored-MDP refinement;
- a canonical command and dependency lock;
- a machine-readable benchmark mapping to the published experiments;
- partition outputs compatible with LBQ001 metrics;
- seeds `17 / 29 / 43`;
- model-size, peak-RSS, wall-time, and digest instrumentation.

No unofficial reimplementation is promoted to canonical-baseline status.

Classification:

> theorem-level and algorithm-level prior art for exact and epsilon-homogeneous MDP partitions; no pinned paper-specific executable baseline confirmed in this run.

## Prior-art matrix update

| Candidate | Global partition | Action-conditioned | Approximate | Known-model | Finite-sample identification | Unique estimand by default | Full-consequence by default | Public immutable code | C classification |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Dean–Givan exact homogeneity | yes | yes | no | yes | no | coarsest exact refinement relative to supplied labels | no | not confirmed | exact partition prior art |
| Dean–Givan–Leach epsilon homogeneity / BMDP | yes | yes | yes | yes | no | no; multiple admissible partitions/tolerance choices can remain | no | not confirmed | global approximate partition prior art |
| Suilen–Pérez metric baseline | metric, not partition selection | yes | metric-valued | yes | no | no threshold/partition contract | no | yes, pinned in C085 | exact known-model metric prior art |
| Storm B4 oracle | yes | yes | exact | yes | no | yes for supplied point model and labels | only supplied channels | yes, pinned in C073 | exact point-model oracle |
| Required empirical approximate B4 | yes | yes | yes | no | yes with coverage and abstention | must be preregistered | yes | not selected | remaining gate |

## Decision

> **NARROWED BEYOND GLOBAL ACTION-CONDITIONED EPSILON-HOMOGENEOUS MDP PARTITIONING — CLASSICAL PRIOR ART ALREADY DEFINES APPROXIMATE TRANSITIVE PARTITIONS AND BOUNDED-PARAMETER AGGREGATE MODELS, BUT IT ASSUMES A KNOWN MDP, DOES NOT UNIQUELY SELECT A SEMANTIC QUOTIENT UNDER APPROXIMATION, AND DOES NOT PROVIDE FINITE-SAMPLE FULL-CONSEQUENCE IDENTIFICATION OR LANGUAGE–TARGET COUPLING — NOT ADOPTED.**

The remaining target-side gate is no longer to invent either an action-preserving metric or a global approximate partition. Both exist in prior art.

The remaining work is to preregister one precise estimand and determine whether it is identifiable from the allowed observations:

1. an exact quotient with empirical output restricted to `separate / unidentified` unless equality is structurally tied;
2. a diameter-bounded approximate partition;
3. a robust-exact relation under a specified physical perturbation family;
4. a perturbation-repair quotient;
5. or an epsilon-homogeneous/BMDP partition with an explicit global selection rule.

Whichever estimand is selected must include all allowed non-semantic consequence channels, preserve action availability, abstain under missing coverage, and use simultaneous statistical guarantees.

## Consequence for RQ-001

This run further narrows only the target-side partition `P`.

Even a perfectly recovered homogeneous or epsilon-homogeneous partition does not identify:

- raw-language equivalence `Q`;
- whether language distinctions finer than the selected behavioral tolerance are externally justified;
- relative coupling between language classes and target blocks;
- external semantic orientation;
- denotation `d`.

The joint RQ remains unadopted until `Q`, `P`, and `d` are directly recoverable under one non-circular observation model and evaluated without target IDs, parser outputs, simulator names, semantic reward, or evaluator codebooks.

## Next gate

1. Update LBQ001 so “approximate B4” names one estimand rather than conflating metric threshold, epsilon homogeneity, robust exactness, and perturbation repair.
2. Audit whether any public implementation computes epsilon-homogeneous partitions for action-conditioned MDPs with a reproducible immutable commit; do not substitute an unverified reimplementation.
3. Compare candidate estimands by uniqueness, monotonicity under refinement, physical interpretability, finite-sample calibratability, and compatibility with Storm's exact oracle.
4. Keep exact empirical mode asymmetric: `separate / unidentified`, with `merge` only under symbolic equality.
5. Begin numerical execution only after estimator, global selection rule, tolerance, coverage, leakage, and partition metrics are fixed; then require seeds `17 / 29 / 43`, serialized model size, parameter count, peak RSS, training/evaluation wall time, hardware/software environment, exact command/commit, and dataset/result digests.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- identifiability/applicability counterexamples: complete;
- exact homogeneous MDP partition: existing prior art;
- action-conditioned epsilon-homogeneous global partition: existing prior art;
- bounded-parameter aggregate MDP planning: existing prior art;
- claim that a global approximate MDP partition is absent: rejected;
- unique finite-sample full-consequence estimand: not fixed;
- executable empirical B4 estimator: not selected;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://s.aaai.org/Library/AAAI/1997/aaai97-017.php
- https://arxiv.org/abs/1302.1533
- https://doi.org/10.1016/S0004-3702(02)00377-6
- https://ojs.aaai.org/index.php/AAAI/article/view/9701
