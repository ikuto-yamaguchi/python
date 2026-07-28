# Causal Identifiability Audit C017

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Identifiable Multimodal Causal Representation Learning under Partial Latent Sharing

Benhamza, Clausel and Tami, arXiv:2605.19135, 2026 preprint.

Primary source:

- https://arxiv.org/abs/2605.19135

No official implementation repository was located from the paper record, author search, or repository search on 2026-07-25. Therefore this cycle is a theorem/assumption audit, not a public-code reproduction.

The paper studies multimodal observations in which modality `m` is generated from a subset `z_{A_m}` of causal latent variables through a modality-specific nonlinear mixing function. Modalities may share only part of the latent structure. Under its assumptions, the work establishes component-wise identifiability of both modality-specific and shared latent variables, including undercomplete observation settings, and proposes a Wasserstein-based module to align the recovered shared elements.

## Precise boundary with RQ-001

This work removes another broad novelty route for RQ-001.

If language is treated merely as one observed modality and environment trajectories, images, state variables or actions form other modalities, then the following claims are no longer admissible as novel by themselves:

- discovering which latent variables are shared between language and environment observations;
- separating shared latent factors from modality-specific factors;
- recovering a partially shared causal representation from multiple nonlinear modalities;
- using cross-modal agreement alone to infer a latent partition.

Those are already addressed, under explicit assumptions, by multimodal causal-representation identifiability.

The unresolved issue is narrower. Raw language generally does **not** satisfy the paper's observation model:

1. Surface language is discrete rather than a smooth Euclidean observation.
2. The map from latent semantics or mechanisms to utterances is generally stochastic.
3. It is non-injective: paraphrases map multiple strings to one meaning, while polysemy maps one string to multiple meanings in context.
4. Utterance length and syntax vary, so a fixed-dimensional smooth mixing model is not automatic.
5. Language may describe counterfactual, absent or future mechanisms rather than only variables generating the current observation.
6. The language channel may itself depend on speaker policy, pragmatics, history and environment selection.

Therefore the multimodal theorem cannot simply be cited as proving raw-language equivalence or language-target joint identification. But it does establish that **partial latent sharing itself is not the missing novelty**.

## Theorem/assumption comparison

| Dimension | Partial-sharing multimodal CRL | Raw-language / latent-target RQ-001 | Remaining burden |
|---|---|---|---|
| Observation channels | Multiple modalities generated from latent subsets | Environment observations plus raw utterances | Specify a population language channel, not a finite utterance lookup |
| Mixing | Modality-specific smooth injective nonlinear maps | Discrete, stochastic and often many-to-many language generation | Replace injectivity with a justified language-specific separation condition |
| Shared structure | Partially shared latent variables recovered | Unknown equivalence classes and unknown intervention-target partition | Show language relations refine a residual causal abstraction beyond multimodal sharing |
| Structural assumptions | Non-overlap, mixing-density and causal sparsity conditions | None yet accepted for raw language | State assumptions that forbid arbitrary merge/split and joint recoding |
| Identified object | Shared and modality-specific components up to component-wise transformations | Raw-language equivalence and target partition | Prove a bridge from observable utterance relations to target-block separation |
| Generalisation | Multimodal latent recovery under the stated distribution | Unseen utterance form, composition and system | Population-level grammar and anti-lookup split are mandatory |

## Counterexample: a non-injective language modality does not identify the partition

Let the non-language modality `X` be compatible with two latent binary variables `(Z1,Z2)`. Suppose the raw language observation is generated only through their parity:

`L = word(Z1 xor Z2, epsilon)`,

where `word` is a stochastic paraphrase generator and `epsilon` selects among surface forms.

Consider two candidate latent models.

Model M1:

- two separate target blocks `Z1` and `Z2`;
- language observes only the parity relation.

Model M2:

- one target block `W = Z1 xor Z2`;
- an unobserved nuisance variable absorbs the remaining degree of freedom;
- the same stochastic `word(W, epsilon)` generates language.

Choose the non-language mixing in M2 so that it reproduces the same distribution over `X`. Then M1 and M2 induce exactly the same joint distribution over `(X,L)` while disagreeing on:

- the number of latent target blocks;
- whether the language-relevant quantity is a primitive mechanism or a composition;
- the latent intervention partition.

Cross-modal alignment, mutual information, reconstruction, paraphrase consistency and a language-shuffle gap can all be identical in the two models. The ambiguity persists because the language channel is non-injective with respect to the candidate partition.

This counterexample is not excluded by calling language a modality. It is excluded only by a stronger condition ensuring that the family of language observations separates all candidate residual partitions.

## Consequence for the candidate RQ

A language channel can contribute to identifiability only if it supplies more than partial cross-modal sharing. It must break a stated residual symmetry left by the strongest non-language and multimodal criteria.

At minimum, the admissible problem now needs:

1. a formally specified population language generator;
2. a language-specific separation condition replacing smooth injectivity;
3. proof that distinct residual target partitions induce distinct distributions over unseen utterance families conditional on non-language observations;
4. restrictions forbidding arbitrary latent merge/split and joint recoding of the language generator;
5. explicit handling of stochastic paraphrase and contextual polysemy;
6. comparison against multimodal partial-sharing CRL, not only state-only or language-blind baselines;
7. unseen-form, unseen-composition and unseen-system evaluation;
8. an impossibility theorem when the language separation condition fails.

## Updated admissible RQ

The remaining admissible formulation is:

> After applying non-language causal-representation and multimodal partial-sharing identifiability criteria, can a discrete, stochastic and non-injective population language channel satisfy a verifiable separation condition that strictly refines the remaining causal abstraction and jointly identifies unseen raw-language equivalence classes with the latent intervention-target partition?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Decision on RQ-001

### Decision: NARROWED TO NON-INJECTIVE DISCRETE LANGUAGE SEPARATION BEYOND MULTIMODAL PARTIAL SHARING — NOT ADOPTED

Partial shared-latent recovery is not a novel contribution by itself. RQ-001 survives only around a language-specific identifiability theorem for a discrete, stochastic, many-to-many channel that provably breaks a residual symmetry which multimodal CRL cannot break.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is theory and primary-literature audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison and non-injective-language counterexample
- partial shared-latent discovery as novelty: rejected
- language-as-an-extra-modality as sufficient identification argument: rejected
- official code: not located; no reproduction claimed
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
