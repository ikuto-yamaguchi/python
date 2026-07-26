# Causal Identifiability Audit C040

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### The Mechanistic Emergence of Symbol Grounding in Language Models

Shuyu Wu, Ziqiao Ma, Xiaoxi Luo, Yidong Huang, Josue Torres-Fonseca, Freda Shi, and Joyce Y. Chai. ICML 2026; earlier versions appeared at CogInterp @ NeurIPS 2025 and as an ICLR 2026 submission.

Primary records:

- arXiv: https://arxiv.org/abs/2510.13796
- ICML publication page: https://sled.eecs.umich.edu/publication/wu-2026-emergence/
- OpenReview workshop record: https://openreview.net/forum?id=b4rjIlubQk
- OpenReview ICLR submission record: https://openreview.net/forum?id=BViZkEr0IA
- NeurIPS workshop page: https://neurips.cc/virtual/2025/129715

The paper studies whether symbol grounding can emerge in autoregressive language models without an explicit grounding objective. Its controlled corpora contain environmental context and linguistic forms, and the models are trained with standard causal language modeling. The authors analyze developmental checkpoints and identify middle-layer computations and attention heads that aggregate environmental information before predicting linguistic tokens.

The empirical claim is mechanistic and causal in the intervention-on-computation sense: replacing or perturbing selected aggregate-head activations raises target-token surprisal more than matched control interventions. The phenomenon is reported for Transformer and Mamba-style state-space models, including a multimodal visual-dialogue extension, but not for the tested unidirectional LSTM setting.

## Assumption, observation, and guarantee comparison

The audited setting assumes or uses:

1. a controlled corpus in which environmental tokens or visual regions are paired with linguistic forms;
2. target words selected with sufficient frequency in both environmental and linguistic contexts;
3. autoregressive next-token prediction as the only training objective;
4. known locations of environmental and linguistic tokens in the constructed examples;
5. model checkpoints across training to measure the developmental trajectory;
6. internal saliency, attention-flow, probing, and activation-intervention analyses;
7. repeated training with five random seeds in the paper's main controlled experiments;
8. explicit human-verified or generated context templates rather than discovery of an unrestricted interaction ontology;
9. behavioral grounding scores defined through prediction of linguistic forms from environmental context;
10. causal evidence defined as a change in model prediction after intervention on identified internal components.

These observations support a claim that particular internal computations causally mediate environment-conditioned linguistic prediction. They do **not** establish population identifiability of:

- an unknown equivalence relation over unrestricted raw utterances;
- an unknown latent intervention-target partition;
- a unique denotation map from utterance classes to target blocks;
- a causal representation of environment dynamics under unknown intervention targets;
- a semantic ontology invariant to simultaneous relabeling of environmental symbols, linguistic symbols, and internal features;
- a language contribution that cannot be reconstructed from the supplied environmental context.

Accordingly, the paper creates an important prior-art boundary but not a solution to RQ-001:

- emergent environment-to-language predictive dependence is existing work;
- locating an internal circuit that causally mediates prediction is existing work;
- behavioral and mechanistic evidence for symbol grounding does not by itself identify a unique denotation;
- intervention on model activations is not the same estimand as intervention-target identification in a latent external causal system;
- successful visual or textual grounding under a supplied correspondence structure is not discovery of raw-language equivalence and latent target blocks jointly.

## Official-code audit

The primary paper, project page, OpenReview records, supplementary material link, author pages, and targeted repository search were checked on 2026-07-26.

A paper-specific public repository with all of the following was not verified:

- immutable source commit;
- exact dataset-generation scripts and generated corpus checksums;
- dependency lockfile or container digest;
- commands mapping to every table and figure;
- all five-seed manifests and checkpoint checksums;
- resource profiles for training and intervention analysis.

The ICLR OpenReview record exposes supplementary material, and the paper describes architectures, corpus construction, checkpoint sampling, and five-seed repetition. Those materials are enough to audit the methodological claim, but they are not yet an immutable R0 reproduction package under this repository's contract.

Classification:

> **primary paper and supplementary record verified; paper-specific immutable official-code reproduction package not verified**

No experiment was started in this cycle. If an official repository becomes available, reproduction must pin its commit and dataset artifacts, freeze transitive dependencies, map every reported result to a command, and save model bytes, peak RSS, wall time, CPU inference/intervention latency, raw logs, five original seeds plus the R0 three-seed compatibility subset, and checksums.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- grounding-like behavior can emerge from next-token prediction over paired environmental and linguistic contexts;
- middle-layer representations can concentrate environment-conditioned linguistic information;
- attention heads or state-space components can aggregate environmental evidence used for language prediction;
- activation intervention can establish that an internal component causally contributes to a linguistic prediction;
- developmental checkpoint analysis can trace the emergence of grounding behavior;
- environmental-to-linguistic prediction can generalize across Transformer, state-space, and multimodal settings;
- a failure of the tested LSTM to show the same mechanism is evidence for architecture-dependent mediation;
- mechanistic grounding scores, target-token surprisal, probes, saliency, or intervention effects can be used as direct evidence that raw utterance equivalence and a latent intervention-target partition were uniquely recovered.

## Identifiability counterexample: causally necessary grounding circuit with nonidentified semantics

Let `E` be the supplied environmental context, `U` the linguistic token or utterance, and `H` the internal aggregate representation used by the model. Suppose the trained model satisfies

\[
p(U\mid E)=p(U\mid H(E)),
\]

and intervention on the identified aggregate heads changes `H(E)` and significantly increases target-token surprisal. Thus, the circuit is genuinely causally necessary for the measured prediction.

Now let `Q` be an equivalence relation over raw utterances, `P` a partition of latent environmental or intervention targets, and

\[
d:U/Q\rightarrow P
\]

an unknown denotation map.

Choose any nontrivial bijection `\pi` over target blocks. Construct a second model by transforming consistently:

- target blocks by `P' = \pi(P)`;
- utterance classes by a corresponding relabeling `Q'`;
- the denotation map by `d' = \pi\circ d`;
- environmental token identities or visual-region labels;
- language-token identities;
- the relevant internal aggregate coordinates;
- the output decoder.

This transformation can preserve:

- the complete joint distribution of constructed environmental and linguistic sequences;
- next-token likelihood and target-token surprisal;
- behavioral grounding scores;
- layer-wise saliency and attention-flow patterns up to relabeling;
- the identity and causal necessity of aggregate heads;
- activation-patching and ablation effect sizes;
- checkpoint-wise developmental curves;
- multimodal grounding accuracy;
- paraphrase or language-form transfer that depends only on the same predictive sufficient statistic.

Yet the semantic alignment between utterance classes and target blocks is different.

A second ambiguity survives even without global relabeling. Suppose two raw utterance families `u_1` and `u_2` always induce the same environmental predictive sufficient statistic in the controlled corpus:

\[
p(E\mid u_1)=p(E\mid u_2),
\qquad
p(U_{next}\mid E,u_1)=p(U_{next}\mid E,u_2).
\]

One model may place them in one equivalence class while another keeps them separate and maps both to the same environmental target. All behavioral scores and all activation interventions on the aggregate circuit remain identical. The experiment contains no contrast that decides whether the forms are genuinely synonymous, extensionally aliased on the benchmark, or distinct outside the observed contexts.

Therefore:

> A model component can be causally necessary for environment-conditioned language prediction while raw-language equivalence, the latent intervention-target partition, and the denotation between them remain nonidentified.

Mechanistic causal mediation establishes **how a chosen prediction is computed**. It does not establish that the external semantic partition used to describe that computation is unique.

## Necessary boundary for a surviving language contribution

Let `S_MECH` contain all information available to the strongest mechanistic-grounding baseline:

- the complete environmental and linguistic training corpus;
- known environmental-token and language-token positions;
- all model checkpoints;
- hidden states, attention maps, state-space activations, probes, and saliency;
- all activation-patching, ablation, and control-intervention outcomes;
- visual regions or supplied environmental objects;
- state, action, reward, outcome, environment identity, and completed trajectories;
- all predictions and grounding scores derived from those observations.

Let `P_residual` be the target distinction remaining after conditioning on `S_MECH`. A necessary information condition for a language-specific contribution is

\[
I(P_{residual};L\mid S_{MECH})>0.
\]

This is still insufficient. The language law must be fixed before fitting and must eliminate every simultaneous relabeling of environmental targets, utterance classes, internal aggregate features, decoders, and denotation maps that preserves the complete behavioral and mechanistic-intervention law.

In particular, an anchor cannot consist only of:

- the same environmental tokens or visual regions used to train the predictor;
- target words generated from those contexts;
- attention or saliency maps;
- model-internal causal interventions;
- environment IDs, action targets, rewards, outcomes, or completed trajectories;
- human-readable names whose correspondence can be permuted together with the target blocks.

## Updated decision for RQ-001

**NARROWED BEYOND MECHANISTIC EMERGENCE OF SYMBOL GROUNDING — NOT ADOPTED**

The only remaining candidate is:

> After conditioning on the strongest behavioral and mechanistic account of environment-to-language prediction, can a preregistered externally fixed language law jointly identify raw-utterance equivalence and a residual latent intervention-target partition while eliminating every target/utterance/internal-feature/decoder relabeling that preserves the complete prediction and causal-intervention law?

Adoption now requires at minimum:

1. a formal separation among model-internal activation interventions, external environment interventions, latent intervention targets, raw utterances, and denotations;
2. an immutable reproduction of the audited grounding study if official code becomes available, including exact corpora, checkpoints, five seeds, dependencies, raw logs, and checksums;
3. the maximal utterance and target partition recoverable from behavioral prediction and internal causal intervention alone;
4. a concrete pair of models with identical corpus likelihood, grounding scores, activation-intervention effects, and task behavior but different utterance and target partitions;
5. language information unavailable from environmental tokens, visual regions, state, action, reward, outcome, environment identity, completed trajectories, and model-internal activations;
6. a denotational anchor fixed before model fitting;
7. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
8. direct recovery metrics for raw-utterance equivalence, latent target partition, and denotation rather than surprisal, probe accuracy, saliency, or task success alone;
9. language-blind, state-only, environmental-token-shuffle, target-label-shuffle, outcome-shuffle, and activation-control interventions on identical instances;
10. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- mechanistic emergence of environment-conditioned symbol grounding: prior art
- primary paper and supplementary record: verified
- paper-specific immutable official-code reproduction: not verified
- raw-language equivalence identification: not established
- latent target partition identification: not established
- semantic joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
