# Causal Identifiability Audit C036

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Learning Causal Response Representations through Direct Effect Analysis

Homer Durand, Gherardo Varando, and Gustau Camps-Valls. Proceedings of the Forty-first Conference on Uncertainty in Artificial Intelligence, PMLR 286:1135–1166, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v286/durand25a.html
- paper PDF: https://raw.githubusercontent.com/mlresearch/v286/main/assets/durand25a/durand25a.pdf
- OpenReview: linked from the PMLR record
- official software: https://github.com/homerdurand/DEA_2025

The paper studies a known treatment variable, a multidimensional response, and a conditioning set. Direct Effect Analysis (DEA) learns response-space directions that retain the strongest direct treatment effect after adjustment. It connects conditional-independence testing and causal representation learning through a generalized eigenvalue problem.

The work supplies statistical and optimization guarantees for the learned response direction: the largest generalized eigenvalue admits an F-distribution bound for conditional-independence testing, while the selected direction is optimal under the paper's assumptions in signal-to-noise ratio and Fisher information. This is a response-representation result for a supplied treatment; it is not a theorem that discovers an unknown raw-language equivalence relation or an unknown intervention-target partition.

## Assumption, observation, and guarantee comparison

The DEA setting exposes or fixes:

1. a treatment variable whose identity is already specified;
2. a multidimensional response whose projection is to be learned;
3. a conditioning set used to adjust competing explanations;
4. regression residuals or generalized covariance quantities from which the test statistic is constructed;
5. an estimand tied to direct treatment influence on response directions.

The guarantee concerns the existence and optimality of a response projection that maximizes evidence against conditional independence, together with a testable null distribution under the stated model conditions.

The audited work does **not** jointly identify:

- an equivalence relation over raw utterances;
- a partition of latent intervention targets whose labels are unknown;
- a unique denotation map between utterance classes and target blocks;
- the treatment variable itself when treatment identity is hidden behind unconstrained language;
- an external anti-recoding anchor that removes simultaneous relabeling of treatment labels, response directions, target blocks, and language classes.

For RQ-001 this distinction is decisive. If a SILG instruction is first converted into a supplied treatment label, descriptor, action target, or environment identifier, DEA may recover a response direction associated with that supplied variable. That does not show that the raw instruction equivalence or semantic target partition was discovered.

## Official-code audit

The PMLR software link resolves to the author repository `homerdurand/DEA_2025`. The repository contains:

- `direct_effect_analysis.py`;
- generalized covariance and partial-ridge helpers;
- several experiment notebooks, including dynamical-adjustment and noise-behavior studies;
- a minimal README linking the paper.

The repository is public and paper-specific, but it has no release and the visible project structure does not provide an immutable dependency lock, a complete command-line reproduction entry point, or a packaged three-seed benchmark protocol. It is therefore classified as:

> **official public code verified; immutable R0 reproduction package not yet established**

No experiment was started in this cycle. Reproduction requires pinning an exact commit, reconstructing notebook dependencies, identifying the exact paper figures/tables produced by each notebook, and preregistering metrics before any adaptation to SILG.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- learning response-space directions maximally affected by a known treatment;
- using conditional-independence residuals to construct a causal response representation;
- selecting a projection by generalized eigenvalue decomposition;
- optimizing direct-effect signal-to-noise ratio or Fisher information;
- testing whether a supplied language-derived treatment affects a multidimensional state representation;
- interpreting a language-conditioned response direction as discovery of raw-language equivalence;
- treating direct-effect significance, next-state prediction, action accuracy, or task success as evidence that a latent target partition was identified;
- claiming a new language-grounding principle merely because language helps isolate a response direction.

The surviving question must concern identification of the treatment/equivalence structure itself, not only identification of a response representation conditional on a supplied treatment variable.

## Identifiability counterexample: perfect direct-effect representation with nonidentified utterance and target partitions

Let raw utterances be \(U\), let \(Q\) be an unknown equivalence relation over those utterances, and let \(P\) be an unknown latent intervention-target partition. Suppose an externally supplied preprocessing map produces a treatment variable

\[
T=a(U).
\]

Let \(Y\in\mathbb{R}^d\) be the multidimensional response and \(Z\) the conditioning variables. Assume DEA recovers an optimal direction \(v^\star\) such that \(v^{\star\top}Y\) maximizes the adjusted direct-effect criterion of \(T\) on \(Y\).

Construct two candidate semantic models:

- Model A uses utterance partition \(Q\), target partition \(P\), and denotation map \(d:U/Q\rightarrow P\).
- Model B uses different partitions \(Q'\neq Q\) and \(P'\neq P\), while preserving the same supplied treatment value \(a(U)\) for every observed utterance.

Within each treatment cell, split or merge raw utterance classes arbitrarily and simultaneously recode the latent target blocks. Choose the response decoder so that

\[
p(Y,Z,T)
\]

is unchanged. Because DEA only receives \(T\), \(Y\), and \(Z\), both models have the same:

- generalized covariance matrices;
- generalized eigenvalues and eigenvectors;
- conditional-independence test statistic and p-value;
- direct-effect signal-to-noise ratio;
- Fisher information of the selected projection;
- next-state prediction and action accuracy when downstream policies use \(T\) and \(v^{\star\top}Y\);
- task success;
- treatment-label and outcome-shuffle gaps whenever the same supplied treatment cells are preserved.

Nevertheless, the raw-utterance equivalence and latent target partition differ.

A second ambiguity remains even when treatment labels are learned jointly. Apply a nontrivial bijection \(\pi\) to treatment/target blocks and transform the language encoder, denotation map, and response decoder by the same bijection. The complete observational law and DEA objective remain invariant. Human-readable treatment names do not remove this symmetry unless their denotation is externally fixed before fitting.

Therefore:

> Perfect recovery of a direct-effect response representation for a supplied or jointly recoded treatment does not identify the raw-language equivalence relation, the latent intervention-target partition, or their semantic alignment.

## Necessary boundary for a surviving language contribution

Let \(S_{DEA}\) contain all information available to the strongest direct-effect baseline:

- supplied or inferred treatment values;
- multidimensional responses;
- conditioning variables;
- state, action, reward, outcome, and completed trajectories;
- environment identity;
- optimal direct-effect projections and their test statistics.

Let \(P_{residual}\) be the target distinction remaining after conditioning on \(S_{DEA}\). A necessary information condition is

\[
I(P_{residual};L\mid S_{DEA})>0.
\]

This condition is still insufficient. Adoption requires a preregistered denotation law that makes every joint automorphism of utterance classes, treatment labels, response coordinates, and target blocks trivial. Language must not be a restatement of a supplied treatment, intended action, environment identity, reward, observed effect, or completed trajectory.

## Updated decision for RQ-001

**NARROWED BEYOND KNOWN-TREATMENT DIRECT-EFFECT RESPONSE IDENTIFICATION — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest known-treatment direct-effect response learner and conditioning on all state, action, response, outcome, and treatment information, can a preregistered externally fixed language law identify a residual raw-utterance equivalence and latent intervention-target partition while eliminating every joint recoding that preserves the complete adjusted treatment-response law?

Adoption now requires at minimum:

1. a formal distinction among raw instructions, supplied treatment labels, inferred treatment variables, action targets, and environment identifiers;
2. an immutable reproduction of the official DEA implementation at an exact commit;
3. the maximal response representation and target distinction recoverable from known-treatment direct-effect analysis;
4. a concrete countermodel pair with identical adjusted treatment-response laws but different utterance and target partitions;
5. language information unavailable from treatment, state, action, reward, outcome, and completed trajectories;
6. a denotation anchor fixed before model fitting;
7. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
8. direct recovery metrics for both partitions rather than direct-effect significance or task success alone;
9. language-blind, state-only, treatment-label-shuffle, target-label-shuffle, outcome-shuffle, and environment-label-shuffle controls on identical instances;
10. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- known-treatment direct-effect response identification: prior art
- official public code: verified
- immutable public baseline reproduction: not started
- raw-language equivalence identification: not established
- semantic intervention-target joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
