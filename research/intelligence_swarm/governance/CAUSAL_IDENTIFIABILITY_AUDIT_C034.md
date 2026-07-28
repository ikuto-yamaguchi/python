# Causal Identifiability Audit C034

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Score-based Causal Representation Learning: Linear and General Transformations

Burak Varıcı, Emre Acartürk, Karthikeyan Shanmugam, Abhishek Kumar, and Ali Tajer. Journal of Machine Learning Research 26(112):1–90, May 2025.

Primary records:

- JMLR: https://jmlr.org/papers/v26/24-0194.html
- PDF: https://jmlr.org/papers/volume26/24-0194/24-0194.pdf
- Official code linked by JMLR: https://github.com/acarturk-e/score-based-crl

This work is directly relevant because it separates population identifiability from algorithmic achievability and gives constructive score-based procedures for latent causal-variable and graph recovery under unknown observation transformations. It therefore removes a large class of claims in which language is invoked merely because the latent variables, transformation, or correspondence between intervention environments and nodes is unknown.

## Theorem and assumption comparison

The audited paper studies a general nonparametric latent SCM with observed variables

\[
X=g(Z),
\]

where the latent causal mechanisms are unrestricted and the observation map is either linear or a diffeomorphism onto its image.

The principal guarantees relevant to RQ-001 are:

1. **Linear transformation, one stochastic hard intervention per node.** Perfect recovery of the latent variables and latent DAG is identifiable.
2. **Linear transformation, one stochastic soft intervention per node.** The transitive closure is recoverable and latent variables are identifiable up to linear mixing with ancestors; under sufficient nonlinearity of the latent mechanisms, the latent DAG can be recovered exactly and the learned representation preserves the relevant Markov structure.
3. **General nonlinear transformation, two distinct stochastic hard interventions per node.** Perfect identifiability is obtained even when the learner is not told which pair of intervention environments targets the same latent node.
4. **Achievability.** LSCALE-I and GSCALE-I are constructive algorithms driven by differences between observational and interventional score functions. The general-transformation result optimizes a differentiable objective whose global optima satisfy the identifiability guarantee.

Important assumptions and limits include:

- access to observational/interventional distributions or sufficiently accurate score estimates;
- stochastic interventions satisfying the paper's regularity and discrepancy conditions;
- for the general-transformation theorem, two distinct hard interventions per latent node;
- a smooth invertible observation map for the nonlinear setting;
- population/global-optimum guarantees do not by themselves establish finite-sample recovery in SILG;
- the single-node theorem family does not directly establish raw-language equivalence or semantic denotation;
- intervention environments need not be paired by target for the general theorem, but the intervention family must still provide the required per-node diversity.

## Official-code audit

The JMLR page links an author-controlled public repository, `acarturk-e/score-based-crl`. The repository explicitly maps folders to the JMLR 2025 and related papers:

- `LSCALE-I` for linear transformations and one intervention per node;
- `GSCALE-I-GLM`, `GSCALE-I-MLP`, and `GSCALE-I-images` for general transformations;
- `UMNI-CRL` for unknown multi-node interventions.

The repository provides a top-level Conda environment instruction and per-folder execution notes. It also states that older separate repositories are obsolete and that the consolidated repository should be used. This is stronger reproduction provenance than the papers audited in C030–C033.

However, no release is published, and the repository is an evolving multi-paper codebase. Therefore an R0-compliant reproduction must pin an exact commit, copy the relevant environment specification, record the selected subdirectory and command, and preserve raw outputs and checksums. A baseline experiment was not started in this cycle because the current task remains theorem/novelty audit and because the R0 benchmark reproduction and preregistration gates are not yet complete.

Classification: **official public code verified; immutable R0 reproduction not yet performed**.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- unknown correspondence between intervention environments and latent nodes makes non-language identification impossible;
- a general nonlinear observation map alone creates a need for language grounding;
- score or density differences across environments cannot recover causal variables without semantic labels;
- naming a recovered intervention environment or latent component with language constitutes joint identification;
- language-assisted performance above an unverified score-based baseline demonstrates a new causal-grounding principle;
- next-state prediction, task success, action accuracy, graph recovery, or environment classification establishes raw-utterance equivalence;
- a learned pairing between utterances and already identifiable latent nodes removes semantic relabeling ambiguity.

The paper also creates a concrete applicability audit for SILG. Before claiming a language-specific contribution, the reconstruction must determine whether the benchmark provides intervention diversity analogous to one hard intervention per node, two unpaired hard interventions per node, soft-intervention discrepancy, or unknown multi-node intervention conditions. If one of these applies, the corresponding non-language score-based recovery is prior art. If none applies, failure of the theorem assumptions cannot be replaced by behavioral success as proof of identifiability.

## Identifiability counterexample: perfect score-based recovery without semantic joint identification

Assume a score-based CRL procedure perfectly recovers latent variables \(Z=(Z_1,\ldots,Z_n)\), the latent DAG \(G\), and the set of intervention targets for every environment, up to the theorem's permitted component-wise transformations and permutation.

Let raw utterances be \(U\), let \(Q\) be the unknown utterance-equivalence relation, let \(P\) be a semantic partition of intervention targets, and let

\[
d:U/Q\to P
\]

be the denotation map.

Construct Model A with \((Z,G,P,Q,d)\). Construct Model B by applying a nontrivial permutation \(\pi\) to the recovered latent-node labels and target blocks, recoding utterance classes correspondingly, and replacing the denotation map with

\[
d'=\pi\circ d.
\]

Transform the language encoder/generator by the same permutation while leaving the observational decoder and recovered score structure expressed in the permuted coordinates.

The models can preserve:

- every observational and interventional distribution;
- all observed and latent score functions up to coordinate relabeling;
- the recovered latent DAG and transitive closure up to isomorphism;
- intervention-target detection and environment pairing;
- LSCALE-I or GSCALE-I objectives;
- next-state prediction, action accuracy, and task success;
- utterance likelihood, paraphrase accuracy, and language-shuffle gaps;
- every evaluation that depends only on the recovered component and not on an externally fixed denotation.

Nevertheless, the semantic assignment of raw utterance classes to intervention targets differs between the models. Thus:

> Perfect score-based recovery of latent causal variables, graph structure, and unknown intervention targets does not identify raw-language equivalence or its semantic denotation into the intervention-target partition.

The ambiguity is not removed by human-readable target names if those names and the learned language encoder are part of the jointly fitted system. It is removed only by information whose denotation is fixed outside the model and which is not invariant under the same target/utterance relabeling.

## Necessary boundary for a surviving language contribution

Let \(S_{SCRL}\) contain all information recoverable by the strongest applicable score-based CRL baseline: latent variables, graph, score differences, intervention environments, target incidence, state/action/outcome history, and completed trajectories. Let \(P_{residual}\) be the target distinction that remains after quotienting by the score-based theorem's allowed transformations.

A necessary information condition is

\[
I(P_{residual};L\mid S_{SCRL})>0.
\]

This is still insufficient. Adoption requires a preregistered external language law that breaks every remaining joint automorphism of target blocks, utterance classes, and the language encoder. Language must not merely:

- name a node or environment already recoverable from score differences;
- reveal the intervention target through action labels, reward, or completed outcome;
- restate an environment identifier;
- provide a class label whose semantics is learned only through the same latent alignment objective;
- improve finite-sample optimization while leaving the population equivalence class unchanged.

## Updated decision for RQ-001

**NARROWED BEYOND SCORE-BASED IDENTIFIABILITY AND ACHIEVABILITY — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest applicable score-based CRL algorithm and quotienting out all latent variables, graph structure, and intervention-target information identifiable from observational/interventional score differences, can a preregistered externally fixed language law identify a residual raw-utterance equivalence and intervention-target partition while eliminating every joint relabeling that preserves the complete non-language and language observable law?

Adoption now requires at minimum:

1. a precise mapping from SILG episodes to observational and interventional environments;
2. an audit of hard/soft, single-node/multi-node, score-estimation, smoothness, invertibility, and intervention-diversity assumptions;
3. immutable reproduction of the relevant LSCALE-I, GSCALE-I, or UMNI-CRL baseline from an exact official-code commit;
4. the maximal non-language partition and graph recoverable under the applicable theorem;
5. a concrete countermodel pair with identical score-based observables but different residual target/utterance partitions;
6. language information unavailable from environment identity, states, actions, rewards, outcomes, and completed trajectories;
7. a denotation anchor fixed before fitting;
8. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
9. direct partition-recovery metrics rather than task success or graph accuracy alone;
10. language-blind, state-only, target-label-shuffle, outcome-shuffle, and environment-label-shuffle controls on identical instances;
11. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- score-based latent/graph/unknown-target recovery: prior art under explicit assumptions
- official author code: verified
- immutable public baseline reproduction: not yet performed
- raw-language equivalence identification: not established
- semantic intervention-target joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
