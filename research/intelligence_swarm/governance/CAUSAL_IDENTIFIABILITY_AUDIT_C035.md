# Causal Identifiability Audit C035

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + assumption/guarantee comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Generative Intervention Models for Causal Perturbation Modeling

Nora Schneider, Lars Lorch, Niki Kilbertus, Bernhard Schölkopf, and Andreas Krause. Proceedings of the 42nd International Conference on Machine Learning, PMLR 267:53388–53412, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/schneider25a.html
- arXiv: https://arxiv.org/abs/2411.14003
- OpenReview: https://openreview.net/forum?id=FgNYqzjVLg
- Author publication page: https://noraschneider.github.io/publications/

The paper studies perturbations whose affected causal mechanisms are unknown while observable perturbation features are available. A Generative Intervention Model (GIM) learns a map from those features to a distribution over atomic interventions in a jointly estimated causal model. It is evaluated on synthetic systems and scRNA-seq drug perturbations, including prediction for held-out perturbation features.

This is directly relevant to RQ-001 because natural-language instructions, descriptions, or learned language embeddings can be treated as perturbation features. Therefore, mapping a descriptor to an unknown intervention distribution and transferring to unseen descriptors is not by itself a new language-grounding or causal-identification principle.

## Assumption, observation, and guarantee comparison

The observable ingredients of the GIM setting are:

1. samples from multiple perturbation conditions;
2. an observed feature vector describing each perturbation;
3. observational or control data;
4. a jointly fitted causal generative model;
5. held-out perturbation descriptors for out-of-distribution effect prediction.

The learned intervention model maps a perturbation feature vector to a distribution over atomic intervention choices and their parameters. Its practical guarantee is predictive and mechanistic: it can model distribution shifts under unseen descriptors and can recover useful intervention-mechanism assignments on the studied systems.

The audited work does **not** establish the candidate RQ's stronger statement. In particular, the paper does not provide a theorem that jointly identifies:

- an unknown equivalence relation over raw natural-language utterances;
- a latent intervention-target partition;
- a unique denotation map between those two unknown partitions;
- an anti-recoding anchor that removes simultaneous relabeling of descriptors, intervention components, and the language encoder.

The distinction is essential. Perturbation features are supplied observations. The method learns their relationship to causal interventions; it does not infer which raw strings must be semantically equivalent from an otherwise unconstrained language channel.

For SILG applicability, any R0.2 or later claim must record whether the instruction representation is:

- a supplied target label;
- a fixed externally pretrained embedding;
- a jointly learned text encoder;
- a descriptor computable from environment identity, action target, reward, or completed trajectory;
- genuinely external information unavailable from the non-language episode.

A descriptor-to-intervention model is prior art in the first four cases unless a stricter residual-identifiability theorem is supplied.

## Official-code audit

The PMLR record links the paper, PDF, and OpenReview entry but does not list a software link. The authors' publication page likewise lists the paper and PDF without a paper-specific code repository. A title-based GitHub repository search returned no dedicated repository.

Classification: **primary paper verified; paper-specific official implementation not verified**.

No reproduction experiment was started. Starting an unofficial reimplementation would violate the current baseline-first and preregistration gates and would add a new implementation family without immutable provenance.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- learning a map from observed perturbation or instruction features to unknown intervention mechanisms;
- representing one perturbation as a distribution or mixture over atomic interventions;
- jointly fitting a causal generative model and a descriptor-conditioned intervention model;
- predicting effects for unseen perturbation descriptors;
- using natural-language embeddings as perturbation features;
- interpreting learned intervention probabilities as evidence that raw utterance equivalence was identified;
- treating held-out descriptor prediction, task success, or intervention-target accuracy as proof of semantic joint identification;
- claiming a new language-dynamics principle merely because language helps predict a causal distribution shift.

The surviving question must concern information in language that cannot be reduced to a supplied or jointly fitted perturbation feature and that provably removes a residual observational equivalence class.

## Identifiability counterexample: perfect descriptor-conditioned intervention prediction without raw-language equivalence

Let raw utterances be \(U\). Let a text encoder produce perturbation features

\[
R=e(U),
\]

and let a GIM learn

\[
q(I,\theta\mid R),
\]

where \(I\) is an atomic intervention target and \(\theta\) its intervention parameters. Let the causal model generate outcomes through

\[
p(X'\mid X,I,\theta).
\]

Assume this model predicts every observed and held-out perturbation distribution perfectly.

Now suppose two distinct raw utterances \(u_1\) and \(u_2\) receive the same feature value, \(e(u_1)=e(u_2)\). Model A may place them in one utterance-equivalence class, while Model B may place them in two distinct classes that happen to share the same intervention distribution. All observable perturbation and outcome laws remain identical.

A stronger ambiguity also remains when the encoder is learned. Apply a nontrivial bijection \(\pi\) to intervention components and define

\[
q'(I,\theta\mid R)=q(\pi^{-1}(I),\theta\mid R).
\]

Transform the latent causal coordinates, intervention decoder, and denotation map by the same bijection. If the language encoder is jointly fitted, its internal classes can be recoded correspondingly. The two systems can preserve:

- every observational and perturbational distribution;
- held-out perturbation prediction;
- intervention-target probabilities up to relabeling;
- causal graph likelihood;
- next-state prediction;
- action accuracy and task success;
- utterance likelihood and paraphrase accuracy;
- descriptor-, target-label-, and outcome-shuffle gaps;
- every metric that does not use an externally fixed denotation.

Nevertheless, the raw-utterance equivalence relation and its semantic alignment to intervention targets differ.

Therefore:

> Perfect prediction of perturbation effects from language or other perturbation features does not identify raw-language equivalence, and perfect recovery of a descriptor-conditioned intervention mixture does not uniquely identify its semantic target partition.

This counterexample also shows why language-form transfer is not enough. Generalization from one surface form to another may demonstrate predictive invariance under the learned encoder while leaving multiple incompatible utterance partitions observationally equivalent.

## Necessary boundary for a surviving language contribution

Let \(S_{GIM}\) include all information available to the strongest descriptor-conditioned intervention baseline:

- perturbation features;
- environment identity;
- observational and perturbed states;
- actions, rewards, and outcomes;
- completed trajectories;
- the fitted causal graph;
- inferred intervention mixtures and parameters.

Let \(P_{residual}\) be the target distinction that remains after conditioning on \(S_{GIM}\). A necessary information condition is

\[
I(P_{residual};L\mid S_{GIM})>0.
\]

This remains insufficient. Adoption requires a language law fixed before fitting that eliminates every joint automorphism of:

- raw utterance classes;
- perturbation-feature values;
- intervention components;
- target blocks;
- the language encoder and denotation map.

Language must not merely encode a perturbation descriptor, environment ID, target label, intended action, observed outcome, or completed solution trajectory.

## Updated decision for RQ-001

**NARROWED BEYOND DESCRIPTOR-CONDITIONED GENERATIVE INTERVENTION MODELING — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest descriptor-conditioned intervention model and conditioning on all perturbation features and non-language episode information, can a preregistered externally fixed language law identify a residual raw-utterance equivalence and intervention-target partition while eliminating every joint recoding that preserves the complete descriptor-conditioned perturbation law?

Adoption now requires at minimum:

1. an explicit mapping from SILG instructions to perturbation descriptors and intervention environments;
2. separation of supplied descriptors, pretrained embeddings, jointly learned embeddings, and raw utterance equivalence;
3. the maximal target partition recoverable by a descriptor-conditioned causal intervention baseline;
4. a concrete countermodel pair with identical descriptor-conditioned perturbation laws but different utterance and target partitions;
5. language information unavailable from environment identity, state, action, reward, outcome, and completed trajectories;
6. a denotation anchor fixed before model fitting;
7. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
8. direct recovery metrics for both partitions rather than perturbation prediction or task success alone;
9. language-blind, state-only, descriptor-shuffle, target-label-shuffle, outcome-shuffle, and environment-label-shuffle controls on identical instances;
10. immutable public-baseline reproduction when official code becomes verifiable;
11. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- descriptor-conditioned intervention prediction: prior art
- paper-specific official code: not verified
- public baseline reproduction: not started
- raw-language equivalence identification: not established
- semantic intervention-target joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
