# Causal Identifiability Audit C042

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Beyond identifiability: Learning causal representations with few environments and finite samples

Inbeom Lee, Tongtong Jin, and Bryon Aragam. arXiv:2603.25796v1, submitted 2026-03-26.

Primary records:

- arXiv: https://arxiv.org/abs/2603.25796
- arXiv HTML: https://arxiv.org/html/2603.25796
- DOI record: https://doi.org/10.48550/arXiv.2603.25796

This paper closes a major gap between population identifiability and finite-sample estimation for a linear causal factor model with unknown, multi-node latent interventions. It gives a constructive estimator and nonasymptotic guarantees for recovering the latent causal graph, decoder/mixing matrix, causal representations, and unknown intervention targets using a logarithmic number of environments.

This is directly relevant to RQ-001 because it removes the following possible refuge for a language-specific claim: that unknown intervention targets may be identifiable only asymptotically or only with one environment per latent variable, while a language channel is needed to make finite-data recovery practical.

## Assumption, observation, and guarantee comparison

### Structural model

The audited setting assumes:

1. a linear latent SEM, `Z = A^T Z + nu`, with an acyclic latent graph;
2. a linear observation map `X = BZ`;
3. a full-column-rank decoder `B`, without decoder sparsity or pure-child assumptions;
4. independent latent noises;
5. an observational environment and multiple interventional environments;
6. unknown, possibly multi-node intervention-target sets `I(k)`;
7. intervention by zeroing incoming structural coefficients for targeted nodes and changing the corresponding noise structure;
8. two noise-scale conditions used to recover the latent graph;
9. a strongly separating intervention design: every pair of latent nodes is separated in both directions by the intervention family;
10. `K = O(log d)` environments in the regime emphasized by the paper;
11. full environment identities and environment-indexed samples;
12. sub-Gaussian observed data for finite-sample bounds;
13. no raw language, instruction semantics, denotation law, or pretrained language model.

The setting is much narrower than SILG: SILG observations and transition dynamics are nonlinear, sequential, discrete/structured, policy-dependent, and do not automatically provide the two covariance-scale design or strongly separating latent interventions assumed here. Therefore the theorem cannot be transferred to SILG without an explicit assumption audit.

### Population guarantee

Under the model and intervention-design assumptions, the paper identifies:

- the latent causal graph up to label permutation;
- the causal representations up to scale and label permutation;
- the decoder up to scale and label permutation;
- each unknown intervention-target set up to label permutation.

It also shows that logarithmically many environments suffice and are information-theoretically optimal in the stated regime.

### Finite-sample guarantee

The paper moves beyond an existence theorem. Its estimator uses second-order statistics and proceeds by:

1. reconstructing unknown intervention-target sets from intersections of covariance column spaces;
2. recovering decoder columns from combinations of environments;
3. recovering latent variables through the decoder pseudoinverse;
4. learning the latent graph through a generalized eigenvalue construction;
5. controlling empirical subspace-intersection error through projection perturbation and eigen-counting arguments.

Thus the following claims are excluded from the novelty space:

- finite samples inherently prevent non-language recovery of unknown multi-node intervention targets;
- one needs `Omega(d)` environments unless language supplies target names;
- practical unknown-target recovery is absent even in linear CRL;
- language is needed to turn population identifiability into a statistically consistent estimator;
- recovering targets, decoder, representations, and graph from few environments is itself a new language-grounding principle.

### Remaining scope boundary

The guarantee remains limited to a linear latent factor model with a highly structured intervention design and covariance information. It does not identify:

- an unrestricted raw-utterance equivalence relation;
- a denotation map from utterance classes to target blocks;
- semantic names of recovered latent coordinates;
- target partitions finer than those supported by the intervention design;
- language-specific distinctions after conditioning on the recovered graph, decoder, latent representation, and target sets.

## Official-code audit

The arXiv record, paper text, author names, and targeted repository searches were checked. No paper-specific author repository with all of the following was verified:

- an implementation of the projection/eigen-counting estimator;
- an immutable commit referenced by the paper;
- dependency lock or container;
- simulation/data-generation commands mapped to paper results;
- expected checksums;
- three-seed manifest;
- model/RSS/runtime measurements.

Classification:

> **primary paper and constructive algorithm verified; paper-specific official implementation not verified**

No unofficial reimplementation was started. Starting one now would violate the current rule against introducing new implementation families before public baseline reproduction and preregistration. A future reproduction is permitted only after either an author implementation is found and pinned or a preregistered faithful reimplementation contract is approved.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded:

- finite-sample recovery of linear causal representations from unknown multi-node interventions;
- logarithmic-environment recovery under a strongly separating intervention design;
- covariance-subspace reconstruction of unknown intervention-target sets;
- simultaneous recovery of decoder, latent graph, representations, and target sets without language;
- using finite-data target recovery as evidence that language is necessary for identifiability;
- treating better target recovery or sample efficiency from language as proof of raw-language equivalence identification;
- treating recovery up to label permutation as recovery of semantic denotation.

## Identifiability counterexample: finite-sample-consistent target recovery without semantic identification

Let the non-language estimator consistently recover, up to a permutation `pi`, the tuple

\[
(G, B, Z, \{I(k)\}_{k=1}^{K}).
\]

Let raw utterances `U` be generated conditionally on the recovered target set and environment:

\[
U \sim p(U\mid I(k),k).
\]

Construct two models:

- Model A has utterance equivalence `Q`, target partition `P`, and denotation `d: U/Q -> P`;
- Model B applies a nontrivial permutation `pi` to latent coordinates and target blocks, uses a different utterance partition `Q'`, and sets `d' = pi o d` while transforming the language encoder/generator accordingly.

Transform simultaneously:

- latent coordinates;
- decoder columns;
- graph labels;
- every intervention-target set;
- raw-utterance classes;
- denotation map;
- language encoder and generator.

Both models preserve:

- every environment-indexed observed distribution;
- every population covariance;
- every empirical covariance law;
- all subspace-intersection dimensions;
- projection/eigen-counting outputs;
- finite-sample recovery rates;
- recovered graph, decoder, representation, and targets up to the theorem's allowed permutation/scale;
- next-state prediction, action accuracy, and task success whenever the policy is transformed consistently;
- utterance likelihood, paraphrase accuracy, and language-shuffle gaps that depend only on the relabeled targets.

Nevertheless, the raw-utterance equivalence classes and their semantic correspondence to intervention targets differ.

Therefore:

> Finite-sample-consistent recovery of latent variables, graph, decoder, and unknown intervention targets does not identify raw-language equivalence or semantic denotation; the theorem's permitted label permutation is precisely a residual ambiguity that language must externally anchor rather than merely predict.

A language-assisted method may improve finite-sample target accuracy while leaving this ambiguity untouched. Such an improvement can be statistical regularization, side information, or target-code prediction rather than joint semantic identification.

## Necessary boundary for a surviving language contribution

Let `S_FS` contain all information recoverable by the strongest applicable finite-sample non-language procedure:

- environment-indexed samples and covariances;
- intervention-design signatures;
- recovered target sets;
- recovered decoder and latent representation up to allowed transformations;
- recovered latent graph;
- state, action, reward, outcome, split, and completed trajectories;
- all predictions and uncertainty measures derived from them.

Let `P_residual` be the target distinction remaining after conditioning on `S_FS`. A necessary information condition is

\[
I(P_{residual};L\mid S_{FS}) > 0.
\]

This is not sufficient. The language law must be fixed before fitting and must eliminate every simultaneous permutation/scale/reparameterization of latent coordinates, target blocks, utterance classes, denotation, and language encoder that preserves the complete finite-sample data law.

An admissible anchor cannot be only:

- an environment ID;
- a recovered latent index;
- a target label jointly permutable with that index;
- reward, action target, outcome, success, or completed trajectory;
- language generated from those quantities;
- a benchmark-provided human-readable name whose correspondence is supplied rather than discovered.

## Updated decision for RQ-001

**NARROWED BEYOND FINITE-SAMPLE UNKNOWN MULTI-TARGET CRL — NOT ADOPTED**

The surviving candidate is:

> After applying the strongest finite-sample non-language CRL estimator and conditioning on its recovered graph, decoder, representations, target sets, environment, state, action, reward, outcome, and trajectory information, can a preregistered externally fixed language law jointly identify raw-utterance equivalence and the residual intervention-target partition while eliminating every label/scale/denotation automorphism allowed by the complete finite-sample data law?

Adoption now requires at minimum:

1. a formal mapping from SILG/J-CRe3 to the linear factor, intervention, two-noise-scale, and strongly separating assumptions;
2. verification of which assumptions fail and the maximal non-language partition still recoverable;
3. an immutable official reproduction, or a separately preregistered faithful reproduction only if official code is conclusively unavailable;
4. three seeds, exact split and environment manifests, model bytes, peak RSS, training/estimation wall time, CPU latency, raw logs, and checksums after experiment start;
5. a concrete finite-sample countermodel pair with the same complete non-language data law and estimator output but different residual target partitions;
6. language information not reconstructible from environment IDs, recovered targets, state, action, reward, outcome, or completed trajectories;
7. a denotational anchor fixed before model fitting;
8. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
9. direct recovery metrics for utterance partition, residual target partition, and denotation;
10. language-blind, state-only, environment-label-shuffle, target-label-shuffle, outcome-shuffle, and denotation-shuffle controls on identical instances;
11. preregistration before any new architecture or mechanism.

## Status

- RQ-001: further narrowed; not adopted
- finite-sample unknown multi-target CRL: prior art in the stated linear setting
- logarithmic-environment recovery: prior art under strong separation
- official paper-specific code: not verified
- public baseline reproduction: not started
- raw-language equivalence identification: not established
- residual latent target partition identification: not established
- semantic joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
