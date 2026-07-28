# Causal Identifiability Audit C018

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Causal Representation Learning Made Identifiable by Grouping of Observational Variables

Hiroshi Morioka and Aapo Hyvärinen, ICML 2024, PMLR 235:36249–36293.

Primary sources:

- paper record: https://proceedings.mlr.press/v235/morioka24a.html
- paper PDF: https://raw.githubusercontent.com/mlresearch/v235/main/assets/morioka24a/morioka24a.pdf
- official implementation: https://github.com/hmorioka/GCaRL
- official implementation commit audited: `0020bfce34736d61d70ab8175f061d02951a7ed4`

The official repository identifies itself as the implementation of the ICML 2024 paper and provides training and evaluation entry points. Its README specifies only `Python3` and `Pytorch`, without a dependency lockfile or exact framework versions. Therefore it is public code, but not a fully dependency-pinned reproduction package.

## Result established by the prior work

The paper studies observations divided in advance into non-overlapping groups

`x = (x^1, ..., x^M)`,

where each group is generated from its own latent group through a group-wise invertible mixing map,

`x^m = f^m(s^m)`.

Causal relations may exist within and across latent groups. Under the paper's nondegeneracy and causal-function conditions, the latent variables in qualifying groups are identifiable from the observational distribution up to permutation and variable-wise invertible transformations. No temporal ordering, intervention labels, weak supervision, or language channel is required.

The central assumptions relevant to RQ-001 are:

1. **The observational grouping is given in advance.** The learner knows which observed coordinates belong to each group.
2. **Group-wise invertible mixing.** Each `f^m` is an invertible `C^2` diffeomorphism.
3. **Graph nondegeneracy (A1).** Variables in a group have sufficiently distinctive cross-group neighbour patterns; the relevant inter-group adjacency collection has full row rank after zero rows are removed.
4. **Causal-function variation and asymmetry (A2).** Cross-derivatives of the pairwise potential obey non-factorisation and asymmetry conditions that exclude unresolved degenerate alternatives.
5. **Population and optimisation conditions for the estimator.** The self-supervised G-CaRL consistency result assumes universal approximation, group-wise `C^2` diffeomorphic encoders and the infinite-sample optimum.

The official estimator forms negative examples by independently shuffling samples across the pre-specified observational groups, and trains a structured nonlinear logistic-regression discriminator. The theorem connects the learned group-wise feature extractors to the latent variables up to the stated indeterminacies.

## Precise overlap with RQ-001

This result eliminates another broad novelty route.

The following are not novel contributions by themselves:

- using known sensor, modality, object-slot, time-slice, or field groups to make a causal representation identifiable;
- using language merely to assign observed coordinates to already-valid groups;
- learning group-specific latent variables from grouped observations without interventions;
- interpreting a language-induced grouping as discovery of the latent intervention-target partition;
- showing that group shuffling produces a useful self-supervised signal.

If a raw instruction or description only tells the learner that observation fields belong to groups which could have been supplied directly as metadata, then the causal-identification contribution is the known grouping assumption, not a new raw-language principle.

## Theorem/assumption comparison

| Dimension | G-CaRL observational grouping | Remaining RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Data | Grouped observational samples | Environment trajectories plus raw utterances | State exactly which observable grouping is not already available from schema, sensor, object, time or modality metadata |
| Group information | Group membership is given a priori | Language equivalence and target partition are both unknown | Jointly identify the grouping instead of silently supplying it through preprocessing |
| Mixing | Group-wise invertible `C^2` maps | Discrete, stochastic, non-injective language channel plus environment mixing | Replace group-wise invertibility with a justified language-specific condition |
| Identification signal | Cross-group causal dependence and structured group shuffle | Language must refine a residual causal abstraction | Prove strict refinement beyond the strongest valid non-language grouping |
| Identified object | Latents within qualifying known groups, up to permutation and component-wise transforms | Unknown raw-language equivalence and unknown intervention-target partition | Prove that the partition itself, not only latents conditional on a partition, is identified |
| Generalisation | Population result under a fixed known grouping | Unseen utterance form, composition and system | Use a population grammar and anti-lookup split |

## Counterexample: language-derived grouping does not identify the partition when it is recoverable from observations

Let `X` denote the complete non-language observation and let `G` be a grouping label used by the learner. Suppose the raw utterance `L` is generated from the current observation and the grouping is computed as

`G = q(L) = r(X)`.

Thus language may express the grouping fluently, but the same grouping is already a deterministic function of the observed schema, sensor identity, object slot, time index, or state fields.

For any candidate latent partition `P`,

`p(X,L,G | P) = p(L | X) 1{G = r(X)} p(X | P)`.

Therefore two candidate causal models that induce the same distribution over `X` also induce the same joint distribution over `(X,L,G)`. Adding the language-derived group labels cannot distinguish them.

Equivalently,

`I(P ; G | X) = 0`.

A G-CaRL-style estimator may still recover latent variables after being supplied `G`, because identifiability is conditional on the grouping assumption. But this does not show that raw language jointly identified the grouping or the intervention-target partition. It only shows that a known grouping can support identification.

A stronger ambiguity remains when multiple groupings satisfy the same observational theorem. Let `G1` and `G2` be two admissible partitions of observed coordinates, each paired with a corresponding latent model and group-wise mixing functions that reproduce the same distribution over `X`. If the language generator can be redefined jointly with the chosen grouping, then

`p(X,L | G1, P1) = p(X,L | G2, P2)`

can hold while `P1 != P2`. Surface descriptions such as “these fields belong together” do not select one partition unless their denotation is externally anchored and cannot be recoded with the latent model.

## Consequence for interactive language grounding

Interactive language does not automatically solve the problem. A speaker response that is entirely determined by the already-observed state, environment ID, schema, action history or grouping metadata adds no population-level separation:

`L_t ⟂ P | X_{<=t}, A_{<t}, E, G`.

Such interaction may improve finite-sample estimation or optimisation, but it cannot shrink the causal equivalence class. To count as identifiability evidence, an interactive reply must provide an externally anchored distinction that is unavailable from the strongest valid non-language grouped-observation model and must separate candidate residual partitions.

## Updated admissible RQ

The remaining admissible formulation is narrowed to:

> After applying intervention-based, general-environment, trajectory-local, multimodal partial-sharing, and known-observational-grouping identifiability criteria, can an externally anchored population language channel jointly identify an otherwise unknown observational grouping and a residual latent intervention-target partition, rather than merely restating grouping metadata recoverable from non-language observations?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Additional adoption requirements

Before adoption, the candidate must provide:

1. an explicit residual equivalence class after applying G-CaRL-compatible known groupings;
2. a proof that the proposed language information is not measurable from observation schema, sensor identity, object slots, time indices, environment labels, or action history;
3. a language-grounding anchor that cannot be jointly recoded with the candidate grouping and latent partition;
4. a theorem identifying the grouping and partition jointly, not latents conditional on a supplied grouping;
5. an impossibility result when the external anchor or grouping-separation condition is removed;
6. evaluation against direct grouping metadata and G-CaRL, not only language-blind and state-only controls;
7. unseen-form, unseen-composition and unseen-system splits preventing utterance or group lookup;
8. a dependency-pinned public baseline reproduction before any architecture proposal.

## Decision on RQ-001

### Decision: NARROWED TO JOINT GROUPING-AND-PARTITION IDENTIFICATION BEYOND KNOWN OBSERVATIONAL GROUPING — NOT ADOPTED

Known grouping of observational variables already provides a non-language identifiability route. Language that merely predicts, restates or reconstructs such a grouping is not evidence for joint identification of raw-language equivalence and latent intervention targets.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is a theorem, official-code and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison and grouping counterexample
- known observational grouping as a novel language contribution: rejected
- language that restates recoverable grouping metadata as identifiability evidence: rejected
- official code: located and commit recorded; reproduction not started because this cycle is theory/audit only and the repository is not dependency-pinned
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
