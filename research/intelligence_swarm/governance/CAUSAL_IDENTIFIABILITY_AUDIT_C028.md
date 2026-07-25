# Causal Identifiability Audit C028

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + public-code availability audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Nonparametric Identification of Latent Concepts

Yujia Zheng, Shaoan Xie, and Kun Zhang. ICML 2025, PMLR 267:78374–78404.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/zheng25p.html
- OpenReview: https://openreview.net/forum?id=cW9Ttnm1aC
- arXiv: https://arxiv.org/abs/2510.00136

The work studies observations `x = f(z)` generated from class-dependent concepts `z_A` and class-independent concepts `z_B`, with observed class variables `c`. The unknown observation map is a diffeomorphism onto its image, densities are smooth and positive, and class-dependent and class-independent concepts are conditionally independent given class variables.

Its identification signal is **diversity across observed classes**, not target-labelled intervention data or natural-language denotation. The main guarantees are:

1. pairwise/local comparison can disentangle concepts unique to one class from concepts associated with another class;
2. sufficient structural diversity across classes identifies all class-dependent concepts up to element-wise transformations and permutation;
3. additional sparsity can identify class-independent concepts;
4. the hidden class–concept connective structure can also be recovered nonparametrically.

The paper therefore covers a substantial part of the apparent RQ-001 intuition: hidden semantic/concept factors and their grouping can be recovered by comparing multiple observation classes, without specifying concept types, linear relations, or a parametric generator.

No author-maintained implementation repository with immutable source and dependency pins was located from the PMLR record, OpenReview record, arXiv record, author/lab publication pages, or targeted repository search. The paper reports synthetic and five real-data validations, but this cycle does not classify them as an independently reproducible public baseline.

## What this prior art establishes

The following are no longer admissible novelty claims for RQ-001:

- discovering latent concepts merely by comparing multiple utterance or observation classes;
- identifying class-specific latent factors without specifying their semantic type;
- identifying a hidden class–concept incidence structure;
- claiming novelty because the observation decoder is nonlinear and nonparametric;
- claiming novelty because only a locally diverse subset of concepts is identifiable;
- treating an observed language class, paraphrase group, speaker group, or instruction family as a new source of identifiability by itself;
- describing learned concepts with words after class-comparison identification and calling that joint grounding;
- using class-conditioned reconstruction, concept probes, or compositional extrapolation as proof that raw-utterance equivalence itself was discovered.

If raw utterances are first assigned to observed classes or groups, and those groups drive concept comparison, the latent-concept part is substantially within this existing framework. The unresolved burden is the identification of the grouping itself and its externally fixed denotation to an intervention-target partition.

## What this prior art does not establish

The work does not identify:

- an unknown equivalence relation over raw utterance strings when no class variable is supplied;
- an unknown intervention-target partition;
- the joint identification of both unknown partitions;
- an externally anchored denotation map between utterance classes and causal targets;
- a causal intervention interpretation for the recovered class-dependent concepts;
- an interactive grounding guarantee under action/outcome/trajectory leakage exclusions;
- finite-sample recovery of the requested joint partitions;
- elimination of a simultaneous recoding of utterance classes, concepts, and target blocks.

Its class variable is observed. Therefore it solves concept identification **conditional on class membership**, not discovery of raw-language equivalence from unlabelled utterances.

## Assumption and guarantee comparison

| Dimension | Zheng–Xie–Zhang 2025 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Group signal | Observed class variable `c` | Raw utterance equivalence is unknown | Identify grouping rather than assume it |
| Latent variables | Class-dependent and class-independent concepts | Residual causal/intervention-target blocks | Prove recovered blocks have causal target semantics |
| Observation map | Unknown nonparametric diffeomorphism | Symbolic/rendered state, language, actions, outcomes | State exact admissible decoder and support conditions |
| Diversity | Class–concept Jacobian/support diversity | Population language and intervention diversity | Show language supplies nonredundant diversity |
| Guarantee | Local disentanglement; global concepts up to permutation and element-wise transforms; class–concept structure | Joint identification of two unknown partitions | Eliminate joint class/concept/target automorphisms |
| Supervision | Class membership is observed | No hand-authored utterance class or target ontology | Avoid smuggling the answer through metadata |
| Causality | Concepts need not be intervention targets | Latent intervention-target partition | Add a valid causal bridge, not a naming convention |
| Evidence | Synthetic and real-data concept experiments | Direct partition recovery and causal transfer | Task success and probes remain insufficient |

## Prior-art matrix refinement

The novelty matrix must now separate four different problems:

1. **supplied-class concept identification** — class labels/groups are given and latent concepts are recovered;
2. **predicted-class concept identification** — a separate predictor produces groups and a concept method conditions on them;
3. **unsupervised utterance-equivalence discovery** — the equivalence relation over raw forms is itself estimated;
4. **joint causal denotation identification** — utterance equivalence and a residual intervention-target partition are jointly recovered with an externally fixed denotation law.

Only item 4 remains a candidate contribution. Items 1 and much of item 2 are prior art. Item 3 alone is not enough unless the learned equivalence is proven to have causal target semantics and not merely distributional or class-predictive utility.

Any future experiment must compare at least:

- true observed grouping supplied;
- grouping predicted from allowed pre-outcome inputs;
- grouping removed;
- grouping shuffled within the same seed/domain/split/condition cell;
- target labels shuffled independently;
- outcomes shuffled independently;
- full language, language-blind, and state-only models on identical instances.

## Counterexample: observed classes identify concepts while raw-language equivalence remains non-identifiable

Let raw utterances be `U`, an unknown equivalence relation be `Q`, observed comparison classes be `C`, latent concepts be `Z`, and residual intervention-target blocks be `P`.

Assume the data available to the concept learner are `(X, C)`, where `X = f(Z)`, and the structural-diversity conditions are sufficient to identify `Z` and the class–concept incidence matrix up to the theorem's allowed permutation and element-wise transformations.

Now construct two models:

- Model A uses utterance partition `Q`, target partition `P`, and maps utterances to observed classes through `r(U)`;
- Model B uses a different utterance partition `Q'` and a different target partition `P'`, but preserves the same observed class map `r'(U) = r(U)` and the same conditional distribution `p(X | C)`.

Within every observed class, Model B may split or merge raw utterance equivalence classes and simultaneously recode target blocks, provided those changes do not alter `C` or `p(X | C)`.

Both models therefore have identical:

- observed class membership;
- concept-identification objective;
- class-conditioned observation distribution;
- identified latent concepts up to allowed indeterminacy;
- class–concept incidence structure;
- reconstruction and likelihood;
- concept probes and compositional extrapolation;
- downstream action accuracy and task success if policy depends only on `C` and identified concepts.

Yet `Q != Q'` and `P != P'`.

Therefore:

> Nonparametric identification of latent concepts conditional on observed classes does not identify the equivalence relation over raw utterances that produced those classes, nor an unknown causal target partition denoted by them.

A second failure occurs when class labels are natural-language strings. Renaming, paraphrasing, or jointly permuting class strings and target blocks leaves all class-conditioned distributions invariant. Human-readable labels are not an anti-recoding anchor.

## Necessary anti-shortcut condition added by C028

Let `S` denote the strongest sufficient statistic available from observed class membership, states, actions, transitions, outcomes, environment IDs, and completed trajectories. A language channel can contribute to the residual target partition only if it contains target-distinguishing information not already determined by `S`:

`I(P_residual ; L | S) > 0`.

This remains only a necessary condition. Adoption additionally requires an externally fixed law that prevents simultaneous recoding of:

- raw-utterance classes;
- latent concepts;
- intervention-target blocks;
- the denotation map connecting them.

The residual joint automorphism group must be proven trivial. A class-comparison theorem conditional on supplied labels cannot provide this proof.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After applying the strongest non-language CRL methods and nonparametric class-comparison concept-identification results, can a preregistered, externally fixed language law identify the raw-utterance equivalence relation itself and strictly refine a residual intervention-target partition, without using supplied or retrospectively inferred class membership, outcome-derived grouping, or a jointly recodable denotation map?

This formulation is **not adopted**.

## Adoption requirements added by C028

Before adoption, the candidate must provide:

1. a formal distinction between observed class membership and unknown raw-utterance equivalence;
2. the maximal concept/target partition identifiable when true class membership is supplied;
3. a countermodel pair with identical `p(X,C,A,Y)` and class–concept structure but different raw-language and target partitions;
4. a population language law that distinguishes that pair without outcome, reward, action-target, environment-ID, or completed-trajectory leakage;
5. an externally fixed denotation anchor defined before observing predictions or outcomes;
6. a proof that the residual joint automorphism group is trivial;
7. a complementary impossibility theorem when language only restates supplied classes or identified concepts;
8. supplied-group, predicted-group, no-group, group-shuffle, target-label-shuffle, outcome-shuffle, language-blind, and state-only controls on identical instances;
9. direct utterance-partition and target-partition recovery metrics rather than task success alone;
10. immutable public-baseline reproduction before any new architecture;
11. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND SUPPLIED-CLASS NONPARAMETRIC CONCEPT IDENTIFICATION — NOT ADOPTED

The candidate remains potentially distinct only if it identifies the raw-utterance grouping rather than taking a class/group variable as observed, and if it jointly assigns externally fixed causal target semantics beyond the concept structure already identifiable from class diversity.

No experiment or architecture is authorised by this result.

## Resource accounting

No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable in this cycle and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art matrix refinement, theorem/assumption comparison, public-code availability audit, counterexample
- supplied-class nonparametric concept identification: established by prior work
- official immutable implementation: not located
- raw-language equivalence identification: not established
- residual target-partition identification: not established
- RQ-001: further narrowed, not adopted
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
