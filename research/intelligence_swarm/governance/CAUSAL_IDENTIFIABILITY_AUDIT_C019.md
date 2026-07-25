# Causal Identifiability Audit C019

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Generative Intervention Models for Causal Perturbation Modeling

Nora Schneider, Lars Lorch, Niki Kilbertus, Bernhard Schölkopf, and Andreas Krause, ICML 2025, PMLR 267:53388–53412.

Primary sources:

- paper record: https://proceedings.mlr.press/v267/schneider25a.html
- paper PDF: https://raw.githubusercontent.com/mlresearch/v267/main/assets/schneider25a/schneider25a.pdf
- arXiv: https://arxiv.org/abs/2411.14003
- OpenReview record: https://openreview.net/forum?id=FgNYqzjVLg

The PMLR and OpenReview records state that the method learns a map from observed perturbation features to distributions over atomic interventions in a jointly estimated causal model, and evaluates prediction of distribution shifts for unseen perturbation features. The experiments include synthetic data and single-cell drug perturbation data.

As of this audit, the paper record, author publication page, OpenReview record, and targeted GitHub searches did not expose a corresponding official implementation repository. Therefore no public baseline reproduction was started in this cycle. This absence is recorded as a code-availability limitation, not evidence against the paper.

## Precise overlap with RQ-001

The paper occupies a large part of the apparent novelty space behind the broad RQ.

It already addresses the setting in which:

- an external perturbation has observed features;
- the mechanisms modified by that perturbation are unknown;
- a model maps perturbation features to a distribution over atomic interventions;
- the causal model and perturbation-to-intervention map are estimated jointly;
- generalisation to unseen perturbation features is evaluated.

Accordingly, the following are not novel contributions by themselves:

- conditioning unknown-target intervention inference on a feature vector;
- replacing a drug descriptor or other perturbation descriptor with an encoded utterance;
- learning a feature-to-target distribution jointly with a causal predictive model;
- predicting unseen perturbation outcomes from perturbation features;
- interpreting a learned intervention distribution as a mechanistic explanation without an identifiability theorem.

If raw language is merely embedded into a feature vector and then passed to a GIM-like perturbation encoder, the resulting method is a language-conditioned instance of an existing feature-to-intervention modelling family. It does not establish joint identification of raw-language equivalence classes and a latent intervention partition.

## Theorem/assumption comparison

| Dimension | Generative Intervention Model | Remaining RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Perturbation input | Observed perturbation feature vector | Raw, discrete, stochastic, variable-length utterance | Define a population language channel and equivalence relation rather than silently treating an embedding as observed ground-truth semantics |
| Intervention target | Distribution over atomic interventions in a jointly estimated causal model | Unknown latent intervention-target partition | Prove that the partition is identified, not merely useful for prediction |
| Generalisation | Distribution-shift prediction for unseen perturbation features | Unseen utterance form, composition, target combination, and system | Separate semantic compositional transfer from ordinary feature-space interpolation or extrapolation |
| Guarantee | Predictive and mechanistic empirical performance; the audited records do not state a theorem identifying the latent target partition from perturbation features | Population-level joint identifiability | Supply an explicit equivalence class and a uniqueness theorem |
| Language equivalence | Not the identified object | Unknown paraphrase/polysemy equivalence | Prevent utterance-ID, descriptor-ID, and environment-ID lookup |
| Symmetry | Joint causal model and intervention generator are learned | Language must break residual latent symmetries | Give an anchor that cannot be jointly recoded with the causal model and perturbation generator |

This comparison creates a strict distinction between three claims:

1. **Outcome prediction:** perturbation features help predict the post-perturbation distribution.
2. **Mechanism attribution:** the fitted model assigns probability to latent atomic interventions.
3. **Identifiability:** every observationally equivalent admissible model induces the same target partition up to a stated allowed equivalence.

The first does not imply the second, and neither implies the third.

## Counterexample: perfect unseen-perturbation prediction without target-partition identification

Let the observed pre-perturbation state be `X`, perturbation feature be `U`, and post-perturbation observation be `Y`. Consider two latent causal models.

### Model M1

There are two atomic latent mechanisms, `Z1` and `Z2`. The perturbation generator maps `U` to intervention weights

`q_1(I | U)`

over interventions on `{Z1, Z2}`.

### Model M2

Define an invertible latent reparameterisation

`W = H(Z)`

that mixes the two latent mechanisms, and define a transformed structural model and transformed intervention generator

`q_2(I' | U) = H_# q_1(I | U)`,

where `H_#` is the push-forward of the intervention distribution through the reparameterisation. Choose the transformed decoder so that both models generate the same observed post-perturbation law:

`p_1(Y | X, U) = p_2(Y | X, U)`

for every training and unseen perturbation feature `U`.

Both models can therefore have identical:

- training likelihood;
- post-perturbation distribution prediction;
- unseen-feature generalisation;
- intervention sparsity score;
- feature-to-intervention consistency;
- perturbation-feature shuffle gap.

Nevertheless, their atomic intervention coordinates and target partitions differ. The intervention generator has been recoded together with the latent causal model, so observed perturbation features do not select one partition.

The ambiguity is even simpler when two latent mechanisms have identical observable effects. A model with two separate targets and a model with one merged target can induce the same `p(X,Y | U)` for every `U`. Perfect outcome prediction then cannot determine whether the true intervention acts on one primitive mechanism, two jointly acting mechanisms, or a merged abstraction.

Therefore:

> Predicting unseen perturbation effects from observed features is not sufficient evidence that the latent intervention-target partition is identified.

## Consequence for raw language

Replacing `U` by a raw utterance `L` does not remove the ambiguity if a language encoder `e(L)` and intervention generator are learned jointly. For any invertible recoding of the latent intervention coordinates, the perturbation generator can be transformed accordingly while preserving

`p(X, Y, L)`.

Paraphrase consistency, language-shuffle degradation, high action accuracy, or successful unseen-utterance prediction may show that language is useful. They do not show that raw-language equivalence and the latent target partition are jointly identified.

Language can shrink the causal equivalence class only if its denotation is externally constrained in a way that cannot be absorbed into a joint recoding of:

- the language encoder;
- the perturbation-to-intervention generator;
- the latent causal variables;
- the observation decoder.

## Updated admissible RQ

The remaining admissible formulation is narrowed to:

> After accounting for feature-conditioned generative intervention models, can a preregistered population language channel with externally fixed denotational constraints jointly identify raw-utterance equivalence classes and a residual latent intervention-target partition, rather than merely learning a predictive utterance-to-intervention distribution that is jointly recodable with the causal model?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Additional adoption requirements

Before adoption, the candidate must provide:

1. a formal distinction between predictive intervention attribution and partition identifiability;
2. the exact residual equivalence class after allowing joint recoding of language encoder, intervention generator, latent model, and decoder;
3. an externally fixed language-denotation constraint not derived from outcome, target label, environment ID, or completed trajectory;
4. a theorem showing strict uniqueness of the target partition up to a stated admissible equivalence;
5. an impossibility theorem when the denotational anchor or target-separation condition is removed;
6. direct comparison against a feature-conditioned generative intervention baseline, not only language-blind or state-only controls;
7. unseen-form, unseen-composition, unseen-target-combination, and unseen-system splits;
8. public baseline reproduction with dependency versions, model bytes, peak RSS, wall time, CPU latency, raw logs, checksums, and three seeds before any new architecture proposal.

## Decision on RQ-001

### Decision: NARROWED TO ANCHORED JOINT IDENTIFICATION BEYOND FEATURE-CONDITIONED GENERATIVE INTERVENTION MODELS — NOT ADOPTED

Feature-to-unknown-intervention modelling and unseen-perturbation prediction already exist as a public research direction. Raw language cannot be claimed as a new causal-identification principle merely by replacing perturbation features with text embeddings or by producing interpretable target probabilities.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is a paper, code-availability, theorem-boundary, and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison, public-code availability audit, and joint-recoding counterexample
- feature-conditioned unknown-target intervention prediction as a novel raw-language contribution: rejected
- unseen perturbation prediction as partition-identifiability evidence: rejected
- official code: not located from the primary records and targeted GitHub search; reproduction not started
- RQ-001: narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
