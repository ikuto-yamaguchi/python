# Causal Identifiability Audit C026

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, or branch was introduced.

## Primary work newly audited

### Unifying Causal Representation Learning with the Invariance Principle

Dingling Yao, Dario Rancati, Riccardo Cadei, Marco Fumero, and Francesco Locatello. ICLR 2025; arXiv:2409.02772.

Primary records:

- ICLR proceedings: https://proceedings.iclr.cc/paper_files/paper/2025/hash/85381f4549b5ddf1d48e2e287d7d3d15-Abstract-Conference.html
- OpenReview: https://openreview.net/forum?id=lk2Qk5xjeu
- arXiv: https://arxiv.org/abs/2409.02772

The paper reformulates a broad family of causal representation-learning results through known invariance relations across collections of observations. Its framework includes multiview, interventional, temporal, multitask, and domain-generalization settings. The identifiable latent subset is selected by an invariance property and a known assignment of observable “data pockets” to equivalence classes. The paper shows that many latent-variable identification results do not require the grouping signal itself to be causal; known non-causal symmetries can suffice. It reports that 30 prior identification results are special cases and derives, among other consequences, latent-variable identifiability from one imperfect intervention per node under its conditions.

A dedicated author-maintained repository for the complete ICLR 2025 framework was not identified from the ICLR/OpenReview/arXiv records or targeted repository search. Author publication records indicate a code link, but no uniquely attributable, dependency-pinned implementation was verified in this audit. No reproduction experiment was started.

## What this prior art establishes

The following cannot be treated as new contributions of RQ-001:

- identifying latent variables by aligning representations to known equivalence classes across data pockets;
- combining multiple invariance relations to identify different latent subsets;
- treating temporal transition invariance, interventional invariance, multiview overlap, task overlap, or risk invariance in a common identification framework;
- claiming that an identification signal is novel merely because it is linguistic rather than conventionally causal;
- using language-provided grouping metadata as an invariance relation when the utterance grouping is supplied or externally known;
- interpreting successful invariance-aligned representation learning as evidence that the invariance partition itself was discovered;
- claiming that intervention semantics are necessary for latent-variable identification when a non-causal symmetry provides the same equivalence relation.

## What this prior art does not establish

The work does not identify:

- an unknown equivalence relation over raw utterances;
- an unknown latent intervention-target partition jointly with that utterance relation;
- which observable utterances belong to the same semantic equivalence class when the grouping is not supplied;
- a denotation map that is externally fixed against joint recoding;
- a theorem where one unknown partition identifies another unknown partition without auxiliary anchors;
- finite-sample recovery of a jointly unknown language partition and target partition;
- interactive denotation from actions and feedback under the requested leakage exclusions.

## Theorem/assumption comparison

| Dimension | Invariance-principle CRL | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Grouping information | Observable subsets assigned to equivalence classes are known | Raw-utterance equivalence is unknown | The language partition cannot be treated as given metadata |
| Identification signal | Known invariance property over a known latent subset | Externally anchored language contrast beyond strongest non-language invariance | Prove the contrast is not derivable from existing data-pocket membership |
| Recoverable object | Latent variables/subsets up to stated ambiguities | Raw-language equivalence plus residual target partition | Jointly recover two unknown partitions rather than one under known grouping |
| Causality requirement | Invariance need not be causal | Language law may be causal, descriptive, or conventional | Causal wording alone adds no identification guarantee |
| Guarantee | Population identifiability under separation/invariance assumptions | Joint denotational and target identification | Supply anti-recoding and strict-refinement theorem |
| Evaluation | Representation alignment/recovery and downstream tasks | Partition recovery and prospective transfer | Do not infer partition discovery from task success or language-shuffle gaps |

## Prior-art matrix refinement

The novelty matrix must now distinguish at least:

1. latent identification from a **known** equivalence relation;
2. latent identification from several known invariance relations;
3. language used as supplied grouping metadata;
4. learning a predictor of supplied utterance groups;
5. discovering an unknown raw-utterance equivalence relation;
6. discovering an unknown residual intervention-target partition;
7. jointly identifying items 5 and 6 under an externally fixed denotation law.

The invariance-principle framework covers categories 1 and 2 and subsumes category 3 whenever language membership is supplied. RQ-001 can remain potentially distinct only in categories 5–7.

## Counterexample: circular joint identification from two unknown partitions

Let `U` be raw utterances, `X` the observable environment data, `Q` an unknown equivalence relation over utterances, and `P` an unknown partition of latent intervention targets. Suppose the learner only observes a compatibility relation saying that utterances in a class of `Q` co-occur with interventions in a block of `P`, together with trajectories and outcomes.

Assume a candidate model `(Q,P,d)` with denotation map `d : U/Q -> P`. For any bijection `pi` over target blocks, define

- `P' = pi(P)`;
- `d' = pi o d`;
- an utterance relabelling or within-class recoding `Q'` that preserves every observed compatibility and language distribution;
- a correspondingly recoded latent representation and decoder.

If the data-pocket grouping used by the invariance theorem is itself induced from `(Q,P,d)` rather than externally supplied, both candidates can induce the same:

- joint distribution of utterances, observations, actions, and outcomes;
- transition and intervention invariances;
- task success and action accuracy;
- next-state prediction;
- representation-alignment objective;
- language prediction, paraphrase accuracy, and shuffle gap;
- observable grouping of episodes after jointly relabelling both sides.

Yet `(Q,P,d)` and `(Q',P',d')` disagree about the semantic equivalence classes and target partition.

Therefore:

> A theorem that identifies latent variables from known invariance classes cannot be reused to claim discovery of the invariance classes themselves. When raw-language equivalence and target partition are both unknown and only constrain each other, joint relabelling creates a circular non-identifiability unless at least one side is externally anchored.

The necessary information condition from earlier cycles must be strengthened. It is not enough that language contains residual information about the target partition. There must exist an externally fixed variable or intervention law `A_ext` such that the denotation relation is identifiable conditional on the strongest non-language statistic `M`:

`I(P_residual ; L | M, A_ext) > 0`,

and the allowed automorphism group preserving `(M, A_ext, observed language law)` must be trivial on both the utterance quotient and the residual target partition. Positive conditional mutual information alone is insufficient.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After applying every known interventional, temporal, multiview, mechanistic, and general-environment invariance criterion, can an externally fixed and preregistered denotation law identify both (i) a previously unknown equivalence relation over raw utterances and (ii) a strict refinement of the residual intervention-target partition, while eliminating every joint automorphism that preserves the observable data-pocket structure?

This formulation is **not adopted**.

## Adoption requirements added by C026

Before adoption, the candidate must provide:

1. the complete observable sigma-field and the strongest applicable non-language invariance relations;
2. the maximal partition identifiable when all data-pocket memberships are known;
3. a formal distinction between supplied language grouping and discovered raw-language equivalence;
4. a concrete countermodel pair with identical observables and invariances but different utterance and target partitions;
5. an externally fixed anchor not generated from environment ID, intervention incidence, observations, trajectories, actions, outcomes, completed episodes, or researcher-authored target labels;
6. a proof that the residual joint automorphism group is trivial under that anchor;
7. a strict joint-identification theorem, not only representation identifiability conditional on known groups;
8. an impossibility theorem when the language equivalence classes or data-pocket assignments are not externally anchored;
9. direct comparison against an invariance-principle baseline with the true grouping supplied, predicted grouping, and no grouping;
10. preregistered unseen-form, composition, target-combination, dynamics, and system splits;
11. leakage controls and public baseline reproduction before architecture work;
12. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND KNOWN-INVARIANCE IDENTIFIABILITY — NOT ADOPTED

The central candidate remains potentially distinct only if it discovers the raw-language equivalence relation rather than receiving it as a known invariance grouping, and simultaneously uses an external anchor to remove the joint relabelling ambiguity with the latent target partition. Language used as known grouping metadata falls inside existing invariance-based CRL and is not a new joint-identification result.

No experiment or architecture is authorised by this result.

## Resource accounting

No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable in this cycle and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison, counterexample, public-code availability audit
- identification from known non-causal or causal invariance classes: established prior art under explicit assumptions
- language supplied as known grouping metadata: excluded from novelty
- circular identification of two unknown partitions without an external anchor: rejected
- RQ-001: further narrowed, not adopted
- public capability baseline: not accepted as reproduced by this audit track
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
