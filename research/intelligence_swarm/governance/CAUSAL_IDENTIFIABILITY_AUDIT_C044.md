# Causal Identifiability Audit C044

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Towards the Causal Complete Cause of Multi-Modal Representation Learning

Jingyao Wang, Siyu Zhao, Wenwen Qiang, Jiangmeng Li, Changwen Zheng, Fuchun Sun, and Hui Xiong. Proceedings of the 42nd International Conference on Machine Learning, PMLR 267:65738–65775, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/wang25ey.html
- OpenReview: https://openreview.net/forum?id=9c4YYoBS4N
- arXiv: https://arxiv.org/abs/2407.14058
- project page: https://wangjingyao07.github.io/C3R.github.io/
- official code: https://github.com/WangJingyao07/Multi-Modal-Base
- audited official-code commit: `78870761ab7948f80f9d5e08188ef5229b12904d`

The paper defines a multi-modal representation as a Causal Complete Cause (`C^3`) when it is both causally sufficient and causally necessary for the prediction target. It introduces an instrumental variable to identify the proposed quantity under settings where conventional exogeneity and monotonicity assumptions may fail, estimates sufficiency through a real-world branch, estimates necessity through a hypothetical counterfactual branch, and uses the resulting `C^3` risk as a plug-and-play regularizer.

This is relevant to RQ-001 because language, state, vision, action history, or trajectory summaries may be treated as modalities and a learned representation may be shown to be sufficient and necessary for task prediction. Such a result is stronger than ordinary modality consistency, but it is not automatically identification of raw-language equivalence or of a latent intervention-target partition.

## Assumption, observation, and guarantee comparison

### Identifying object

The paper's identifying object is a causal sufficiency/necessity functional of a learned representation relative to an observed prediction target. The relevant distinction for RQ-001 is:

- **causal completeness for prediction:** a representation contains information sufficient for the outcome and whose removal changes the outcome;
- **raw-language equivalence:** an unknown equivalence relation over unrestricted utterances;
- **latent intervention-target partition:** an unknown partition of causal targets or target mechanisms;
- **denotation:** a unique mapping from utterance classes to target blocks.

Only the first is directly identified or regularized by `C^3`.

### Observation contract

The audited method assumes a supervised multi-modal prediction setting containing:

- multiple observed modalities;
- a prediction target or task label;
- a learned multi-modal representation;
- an instrumental-variable construction used to identify sufficiency under the relaxed setting;
- a counterfactual or hypothetical branch used to estimate necessity;
- model and gradient access for the proposed risk estimator.

It does not infer an unrestricted language equivalence relation from raw utterances, and it does not infer a latent intervention-target partition whose labels are absent from the observation contract.

For SILG/J-CRe3, the following quantities must therefore be treated as potential supervised or proxy information rather than evidence of joint semantic identification:

- task-success labels;
- action targets;
- reward and terminal outcome;
- environment IDs;
- modality labels or modality-specific encoders;
- pretrained text or vision encoders;
- gold target indices;
- completed trajectories;
- counterfactual targets generated from gold simulator state;
- an instrumental variable derived from metadata correlated with target identity.

### Guarantee boundary

Under the paper's assumptions, `C^3` identifies and measures whether a representation is causally sufficient and necessary for the prediction target, and `C^3` regularization is intended to improve multi-modal task representations. The result does not establish:

- discovery of raw utterance equivalence classes;
- discovery of a hidden intervention-target partition;
- a unique denotation between language classes and target blocks;
- elimination of simultaneous relabeling of modalities, representation coordinates, target blocks, utterance classes, and the decoder;
- identification when the instrumental variable is itself a semantic target proxy;
- identification in policy-dependent sequential interaction without a formal reduction to the paper's prediction setting.

Consequently, high task success, lower `C^3` risk, or a representation that is both sufficient and necessary for the output cannot by itself be counted as evidence for RQ-001.

## Official-code audit

PMLR and OpenReview link the author repository `WangJingyao07/Multi-Modal-Base` as official code. The repository describes itself as an open-source multi-modal codebase containing the ICML 2025 implementation. At audited commit `78870761ab7948f80f9d5e08188ef5229b12904d`, it contains:

- multi-modal backbones and fusion models;
- text, image, audio, and task-specific preprocessing;
- training entry points;
- dataset instructions for IEMOCAP, CREMA-D, MVSA-Single, Food-101, BRATS-2021, and NYU-Depth V2;
- a documented Python 3.9 Conda environment;
- a template `requirements.txt` path and an alternative unpinned pip install list;
- single-card training commands and seed arguments;
- local `bert-base-uncased` assets and image/audio backbones.

The repository does not provide an immutable R0 reproduction package. In particular, the public instructions do not establish:

- a fully pinned dependency lock;
- a container digest;
- immutable dataset checksums and split manifests;
- an exact paper-table-to-command map;
- a canonical three-seed manifest;
- expected raw-log checksums;
- model bytes, peak RSS, training wall time, or CPU inference latency;
- a no-pretrained-language-model configuration suitable for the R0.1/R0.2 comparison without an explicit preregistered adaptation.

Classification:

> **paper-specific official code verified at an immutable commit; immutable R0 reproduction package not established**

No experiment was started in this audit. Model size, peak RSS, training time, CPU latency, and three-seed reporting are therefore not applicable in this cycle. Any future reproduction must first preregister the exact model, pretrained-encoder policy, dataset artifact, split, seed set, command, expected outputs, and resource instrumentation.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- learning representations that are causally sufficient and necessary for a supervised multi-modal target;
- measuring causal sufficiency and necessity of a representation with an instrumental-variable and counterfactual construction;
- regularizing multi-modal representations using a causal-completeness risk;
- using language as one observed modality in a causal sufficiency/necessity objective;
- interpreting task-critical language features as newly identified raw-language equivalence classes;
- interpreting prediction-critical target features as a uniquely recovered latent intervention partition;
- using task success, representation ablation, or counterfactual prediction as a substitute for direct partition recovery.

The surviving RQ must distinguish prediction-relative causal completeness from semantic joint identifiability.

## Identifiability counterexample: causally complete prediction with non-identified semantics

Let raw utterances be `U`, state/trajectory observations be `X`, the supervised output be `Y`, and a learned multi-modal representation be

\[
R = f(U,X).
\]

Assume `R` is perfectly causally sufficient and necessary for `Y` according to the audited `C^3` criterion. Let `Q` be an unknown equivalence relation over utterances, `P` an unknown intervention-target partition, and

\[
d: U/Q \rightarrow P
\]

be the denotation map.

Construct Model A with `(Q,P,d,f,g)`, where `g` maps `R` to the output. Construct Model B by applying a nontrivial bijection `pi` to target blocks and a corresponding invertible transformation `h` to the representation coordinates, while simultaneously changing the utterance partition to `Q'`, setting `P' = pi(P)`, defining `d' = pi o d`, and replacing the encoder/decoder by

\[
f' = h \circ f, \qquad g' = g \circ h^{-1}.
\]

The instrumental-variable and counterfactual branches can be transformed consistently. Both models can therefore preserve:

- the complete joint distribution of observed modalities and `Y`;
- task success and action accuracy;
- causal sufficiency of the representation;
- causal necessity of the representation;
- `C^3` risk and its generalization bound;
- real-world-branch and hypothetical-branch predictions;
- representation-ablation effects;
- next-state and outcome prediction;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps that depend only on prediction information.

Nevertheless, the raw-utterance equivalence relation, target partition, and denotation differ.

Therefore:

> A representation can be perfectly causally sufficient and necessary for the task output while raw-language equivalence, the latent intervention-target partition, and their denotation remain non-identified. Prediction-relative causal completeness does not eliminate joint semantic recoding.

A simpler partition-refinement counterexample also remains. Two utterances can have identical effects on every observed task label and every available counterfactual output. One model merges them into one semantic class; another keeps them separate but maps both classes to prediction-equivalent target mechanisms. `C^3` cannot decide between these models because its estimand is relative to the observed output, not to an independently anchored semantic partition.

## Instrumental-variable leakage implication

The instrumental variable can only strengthen RQ-001 evidence if it is external, preregistered, and does not encode the target or denotation through benchmark metadata. The evaluation contract must reject or separately label runs where the instrument is derived from:

- gold target identity;
- semantic parser output;
- action label or destination index;
- environment template ID;
- simulator-internal causal variable names;
- reward or terminal success;
- completed trajectory;
- modality identity whose partition is aligned with the target;
- pretrained embedding trained on the same target vocabulary.

Otherwise, identification may come from supplied target information rather than raw-language grounding.

Required comparisons before any RQ claim include:

1. random;
2. language-blind;
3. state-only;
4. language-form shuffle;
5. target-label shuffle;
6. outcome shuffle;
7. instrument shuffle;
8. instrument-with-target-metadata removed;
9. direct recovery metrics for both utterance and target partitions;
10. identical domain × seed × instance cells for all conditions.

## Necessary boundary for a surviving language contribution

Let `S_C3` contain all information available from the strongest causal-complete multi-modal predictor:

- all observed modalities;
- the learned representation;
- task labels and predictions;
- the instrumental variable;
- real-world and hypothetical-branch outputs;
- state, action, reward, outcome, environment, and completed trajectories;
- all supplied schema, target, modality, and parser metadata.

Let `P_residual` be the target distinction remaining after conditioning on `S_C3`. A necessary information condition is

\[
I(P_{residual};L \mid S_{C3}) > 0.
\]

This is still insufficient. The preregistered language law must also eliminate every joint relabeling or invertible recoding of utterance classes, target blocks, representation coordinates, modality identities, instruments, denotation, encoder, and decoder that preserves the complete observed and counterfactual prediction law.

An admissible anchor cannot merely be a task label, instrument derived from target metadata, environment name, parser slot, pretrained embedding, human-readable target label, reward, outcome, action target, or completed trajectory.

## Updated decision for RQ-001

**NARROWED BEYOND CAUSALLY COMPLETE MULTI-MODAL PREDICTION — NOT ADOPTED**

The surviving candidate is:

> After applying the strongest causally sufficient-and-necessary multi-modal predictor and conditioning on all of its observed modalities, instruments, representations, counterfactual predictions, environment, state, action, reward, outcome, schema, and trajectory information, can a preregistered externally fixed language law discover raw-utterance equivalence and the residual intervention-target partition while eliminating every utterance/target/representation/modality/instrument/denotation automorphism preserved by the full prediction law?

Adoption now requires at minimum:

1. a formal distinction between prediction-relative `C^3` and semantic partition identification;
2. a complete inventory of task labels, instruments, modality boundaries, parser metadata, and target-correlated fields in SILG/J-CRe3;
3. an immutable three-seed reproduction of the official `C^3` code or a preregistered faithful adaptation contract;
4. explicit handling of pretrained language/vision encoders and a no-pretrained-language-model baseline;
5. exact dataset, split, seed, dependency, command, and checksum manifests plus model bytes, peak RSS, wall time, and CPU latency after experiment start;
6. random, language-blind, state-only, language-shuffle, target-label-shuffle, outcome-shuffle, and instrument-shuffle controls on identical instances;
7. direct recovery scores for utterance partition, residual target partition, and denotation;
8. a concrete countermodel pair with identical complete prediction and counterfactual laws but different partitions;
9. language information not reconstructible from labels, instruments, state, action, reward, outcome, environment ID, schema, or completed trajectories;
10. a denotational anchor fixed before fitting;
11. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
12. preregistration before any new architecture or mechanism.

## Status

- RQ-001: further narrowed; not adopted
- causal-complete multi-modal representation learning: prior art under the paper assumptions
- official paper-specific code: verified at commit `78870761ab7948f80f9d5e08188ef5229b12904d`
- immutable public baseline reproduction: not started
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
