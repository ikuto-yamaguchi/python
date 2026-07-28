# Causal Identifiability Audit C038

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Identifying biological perturbation targets through causal differential networks

Menghua Wu, Umesh Padia, Sean H. Murphy, Regina Barzilay, and Tommi Jaakkola. International Conference on Machine Learning, 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/wu25v.html
- paper PDF: https://raw.githubusercontent.com/mlresearch/v267/main/assets/wu25v/wu25v.pdf
- official code: https://github.com/rmwu/cdn
- audited official-code commit: `14fa0aa66428252924f19f01ea2389acdf789fb4`

The paper studies direct identification of intervention targets from paired observational and interventional datasets. Its practical setting includes thousands of observed variables, relatively few samples per intervention, and biological systems that may violate classical causal-discovery assumptions.

The proposed Causal Differential Network (CDN) first infers noisy causal graphs for observational and perturbed systems, then learns a supervised mapping from graph differences and additional statistical features to the set of intervened variables. The graph and target-prediction modules are trained jointly. The method is evaluated on synthetic soft and hard interventions and seven single-cell transcriptomics datasets.

## Assumption, observation, and guarantee comparison

The audited method uses or exposes:

1. an observational dataset and an interventional dataset for each perturbation instance;
2. observed variables whose indices define the target candidate set;
3. supervised ground-truth intervention-target labels during training;
4. simulated training distributions designed to resemble biological interventions;
5. graph estimates and graph-difference features rather than a fully correct identified causal graph;
6. additional statistical features derived from observational/interventional samples;
7. a discriminative set-prediction objective for soft or hard intervention targets;
8. train/validation/test splits over synthetic and biological perturbations.

Its empirical guarantee is target-prediction performance under the paper's supervised data-generating and split protocol. It does **not** provide population identifiability of raw-language semantics, nor does it establish that predicted target labels are unique latent causal variables under arbitrary hidden mixing.

The work does establish a strong prior-art boundary for RQ-001: unknown perturbation-target prediction from observational/interventional distribution changes, including soft and hard interventions, is already an explicit public baseline. Language is not required for that target-detection task when supervised target examples and observed candidate variables are available.

The audited work does **not** jointly identify:

- an unknown equivalence relation over raw utterances;
- a latent target partition when target indices or supervised labels are not externally fixed;
- a unique denotation map from utterance classes to intervention targets;
- latent targets hidden behind an unrestricted unknown observation mixing;
- semantic distinctions among utterances that induce the same conditional target distribution;
- an external anti-recoding anchor fixing the meanings of target labels.

## Official-code audit

PMLR directly links `rmwu/cdn` as software. The repository identifies itself as the official ICML 2025 implementation and, at audited commit `14fa0aa66428252924f19f01ea2389acdf789fb4`, contains:

- Python 3.10 installation instructions;
- NumPy `1.26.4`;
- PyTorch `2.4.1` and torchvision `0.19.1` with CUDA 11.8 wheels;
- PyTorch Lightning `2.4.0`;
- TorchMetrics `1.4.1`;
- causal-learn `0.1.3.8`;
- training and inference shell entry points;
- synthetic and biological split CSVs;
- downloadable datasets and pretrained checkpoints;
- synthetic, Perturb-seq, and Sci-Plex configurations.

The repository states that training used one NVIDIA A6000 GPU and recommends 10–20 workers per GPU. It also marks itself as under construction, has no release, and leaves paper result tables as `TBD`. The install instructions pin several major packages but do not provide a complete lockfile, container digest, expected output hashes, three-seed command manifest, CPU resource profile, or end-to-end paper-table reproduction script.

Classification:

> **official public code and pretrained assets verified; paper-specific immutable R0 reproduction package not yet established**

No experiment was started in this cycle. A later reproduction must pin the audited commit, Figshare asset checksums, exact config, dataset split, checkpoint, target metric, seeds, model bytes, peak RSS, wall time, and CPU inference latency before execution.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- predicting unknown soft or hard intervention targets from observational/interventional distribution changes;
- learning target prediction from noisy causal-graph differences;
- jointly training a graph estimator and target-set classifier;
- using additional distributional features to compensate for imperfect causal graphs;
- evaluating held-out perturbation targets or unseen biological contexts;
- treating accurate intervention-target prediction as evidence that raw utterance equivalence has been identified;
- treating a language descriptor attached to a perturbation as a new identification principle when it merely supplies supervised target-correlated features;
- using target F1, action accuracy, next-state prediction, task success, or language-shuffle gaps as substitutes for direct recovery of both the utterance partition and latent target partition.

## Identifiability counterexample: perfect target prediction with nonidentified utterance semantics

Let `X^0` and `X^1` denote observational and interventional samples. Let `T` be the externally indexed target set used by the supervised CDN learner. Suppose a predictor perfectly recovers

\[
p(T\mid X^0,X^1)=1
\]

for every benchmark instance.

Now add raw utterances `U` and an unknown utterance equivalence relation `Q`. Assume utterances affect evaluation only through the already recoverable target statistic:

\[
U \sim p(U\mid T), \qquad (X^0,X^1) \perp U \mid T.
\]

Construct two semantic models:

- Model A uses utterance partition `Q`, target partition `P`, and denotation `d:U/Q\rightarrow P`.
- Model B splits or merges utterance classes differently, uses `Q'\neq Q`, and simultaneously applies a nontrivial relabeling `\pi` to the target blocks, giving `P'=\pi(P)` and `d'=\pi\circ d`.

Transform the language encoder/generator and target decoder consistently. Both models can preserve:

- the full observational/interventional sample law;
- noisy graph estimates and graph-difference features;
- the supervised target labels after corresponding relabeling;
- target precision, recall, F1, and ranking metrics;
- soft/hard intervention classification;
- held-out perturbation prediction;
- next-state prediction, action accuracy, and task success;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps whenever the shuffle preserves `p(U|T)`.

Nevertheless, their raw-utterance equivalence relations and semantic target alignments differ.

A stronger ambiguity occurs when several raw utterance classes induce the same target distribution. Even with externally fixed target indices and perfect target recovery, the data identify at most the coarsening induced by `p(T|U)`. They cannot determine whether two utterances are semantically equivalent in every intervention context, merely extensionally identical on the observed target-prediction task, or accidentally aliased by the finite benchmark.

Therefore:

> Perfect supervised recovery of soft and hard perturbation targets from observational/interventional differences does not identify raw-language equivalence, a latent intervention-target partition hidden behind unknown mixing, or a unique semantic denotation between them.

## Necessary boundary for a surviving language contribution

Let `S_CDN` contain all information available to the strongest CDN-style baseline:

- observational and interventional sample distributions;
- observed candidate-variable indices;
- graph estimates and graph-difference features;
- statistical shift features;
- supervised target labels available during training;
- environment identity and dataset split;
- state, action, reward, outcome, and completed trajectory information;
- predicted soft/hard target probabilities.

Let `P_residual` be the target distinction remaining after conditioning on `S_CDN`. A necessary information condition is

\[
I(P_{residual};L\mid S_{CDN})>0.
\]

This remains insufficient. The language law must be fixed before fitting and must prevent simultaneous relabeling of utterance classes, target blocks, denotation, and the language encoder. It must add a distinction unavailable from target-correlated distribution changes, target supervision, observed variable names, environment IDs, actions, rewards, outcomes, and completed trajectories.

## Updated decision for RQ-001

**NARROWED BEYOND SUPERVISED CAUSAL-DIFFERENTIAL INTERVENTION-TARGET PREDICTION — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest supervised and non-language perturbation-target predictors to all observational/interventional distributions and conditioning on graph-difference, target-label, environment, state, action, reward, outcome, and trajectory information, can a preregistered externally fixed language law jointly identify a residual raw-utterance equivalence and latent intervention-target partition while eliminating every joint recoding that preserves the complete target-prediction law?

Adoption now requires at minimum:

1. a formal distinction among observed variable indices, supervised target labels, raw utterances, inferred utterance classes, and latent intervention-target blocks;
2. an immutable reproduction of `rmwu/cdn` at an exact commit with checksummed pretrained assets and datasets;
3. a benchmark-specific comparison of supervised target detection, unsupervised target detection, language-blind, state-only, target-label-shuffle, outcome-shuffle, and environment-label-shuffle controls on identical instances;
4. the maximal target partition recoverable from observational/interventional differences without language semantics;
5. a concrete countermodel pair with identical target-prediction laws but different utterance and latent target partitions;
6. language information unavailable from graph differences, target-correlated features, observed variable names, state, action, reward, outcome, and completed trajectories;
7. a denotation anchor fixed before model fitting;
8. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
9. direct partition-recovery metrics for both raw utterances and latent targets rather than target F1 or task success alone;
10. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- supervised causal-differential intervention-target prediction: prior art
- official public code and pretrained assets: verified
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
