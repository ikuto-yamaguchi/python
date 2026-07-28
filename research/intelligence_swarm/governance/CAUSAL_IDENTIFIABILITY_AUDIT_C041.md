# Causal Identifiability Audit C041

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Learning Unknown Intervention Targets in Structural Causal Models from Heterogeneous Data

Yuqin Yang, Saber Salehkaleybar, and Negar Kiyavash. AISTATS 2024, Proceedings of Machine Learning Research 238:3187–3195.

Primary records:

- PMLR: https://proceedings.mlr.press/v238/yang24d.html
- paper PDF: https://proceedings.mlr.press/v238/yang24d/yang24d.pdf
- OpenReview workshop record: https://openreview.net/forum?id=x9XRiwXNnm
- official repository: https://github.com/Yuqin-Yang/LIT
- audited repository commit: `b9ba3968cd60c494cd67df8821332e0766426819`

The paper studies unknown soft-intervention targets in a multi-environment structural causal model. An intervention changes the distribution of an endogenous variable's exogenous noise while preserving the causal DAG and structural functions. The learner observes environment-indexed joint distributions over observed variables but is not given the intervention targets.

The proposed Locating Intervention Target (LIT) procedure has two stages:

1. a contrastive recovery phase uses the environment index as an auxiliary variable and recovers the exogenous noises whose distributions change across environments, up to permutation and component-wise invertible transformation;
2. a matching phase uses conditional-independence relations to associate recovered changing noises with observed variables.

This is directly relevant to RQ-001 because it establishes that a substantial portion of unknown-target identification is already possible without language.

## Assumption, observation, and guarantee comparison

### Structural setting

The audited setting assumes or uses:

1. a fixed acyclic causal graph across environments;
2. fixed structural functions across environments;
3. soft interventions represented only by changes in exogenous-noise distributions;
4. observed environment identity;
5. environment-indexed distributions over observed variables;
6. exponential-family changing noises for the contrastive-identification argument;
7. a universal-approximation contrastive regression model;
8. either an invertible SCM mixing function under causal sufficiency or a stronger partial-invertibility/conditional-independence condition with latent variables;
9. enough environments, with `min(D - 1, |O|) >= |T|`, for the stated nonparametric recovery result;
10. T-faithfulness of the recovered-noise/observed-variable augmented graph for matching;
11. conditional-independence tests in the matching stage;
12. no raw language, instruction semantics, denotation law, or pretrained language model.

### Recovery guarantee

Under the paper's recovery assumptions, the changing exogenous noises can be recovered up to permutation and component-wise strictly monotonic transformations with measure one.

This guarantee already excludes the following proposed novelty claims:

- heterogeneous environments with unknown intervention targets require language to expose the changing causal sources;
- unknown soft interventions cannot be localized without supplied target names;
- an environment-conditioned representation of changed mechanisms is itself a new language-grounding principle;
- language dynamics pretraining is necessary to identify which exogenous factors vary across environments.

### Matching guarantee under causal sufficiency

Under causal sufficiency and T-faithfulness, LIT uniquely identifies the observed intervention-target set using the recovered noises and a quadratic number of conditional-independence tests.

Therefore, under these assumptions, even the target indices—not merely a latent representation—are identifiable without language.

### Guarantee with latent confounders

With latent confounders, the paper does not claim unique observed-target recovery. LIT returns a graphically characterized candidate intervention-target set that is a superset of the true observed targets. A recovered changing noise may correspond to a latent variable and therefore need not match any observed variable.

This is the relevant surviving boundary for RQ-001:

- language is not needed for the causally sufficient case covered by LIT;
- with latent confounding, the residual ambiguity is a candidate-set ambiguity induced by observational and graphical equivalence;
- a language channel can count as identification evidence only if it separates members inside that residual candidate set using information unavailable from environment, state, action, outcome, and completed trajectories;
- improved target prediction or narrower candidate sets do not by themselves prove joint identification of raw-utterance equivalence and a latent target partition.

## Official-code audit

The PMLR record links the author repository `Yuqin-Yang/LIT`. The audited main-branch commit is:

`b9ba3968cd60c494cd67df8821332e0766426819`

The repository contains:

- `demo.py` covering three paper settings;
- linear Gaussian causal-sufficiency experiments;
- nonlinear causal-sufficiency experiments;
- linear Gaussian latent-confounding experiments;
- contrastive recovery code;
- intervention-target localization code;
- synthetic data generation and evaluation utilities;
- a pinned subset of Python dependencies.

The README specifies:

```text
pip install -r requirements.txt
python demo.py
```

Pinned dependencies include:

- `matplotlib==3.5.2`
- `numpy==1.23.0`
- `jax==0.3.14`
- `jaxlib==0.3.14`
- `distrax==0.1.2`
- `scikit-learn==1.1.1`
- `dm-haiku==0.0.7`
- `optax==0.1.2`
- `seaborn==0.11.2`

Several dependencies are not version-pinned (`causallearn`, `causaldag`, `conditional_independence`, `wandb`, and `plotly`). The repository has no release, lockfile, container digest, dataset checksum manifest, paper-table command map, three-seed manifest, expected output checksums, or resource profile.

Classification:

> **paper-specific official demo code verified at an immutable commit; immutable R0 reproduction package not yet established**

No experiment was started in this cycle. A future reproduction must first freeze every unpinned dependency, record the Python/OS/JAX CPU compatibility constraints, map demo outputs to the paper's figures and tables, and save model bytes, peak RSS, wall time, CPU inference/localization latency, raw logs, three seeds, split provenance, and checksums.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- recovering changing exogenous noises from heterogeneous environments without target labels;
- using environment identity as an auxiliary contrastive variable;
- identifying unknown soft-intervention targets under causal sufficiency;
- matching recovered changing noises to observed variables through conditional-independence tests;
- returning a graphically justified candidate superset under latent confounding;
- treating environment-conditioned target localization as evidence that raw-language equivalence was discovered;
- treating a language-assisted reduction in candidate-set size as proof of semantic joint identification;
- using target F1, task success, next-state prediction, or language-shuffle gaps as substitutes for direct recovery of both partitions and their denotation.

## Identifiability counterexample: language narrows a latent-confounded candidate set without identifying semantics

Let `O` be the observed variables, `H` latent confounders, `E` the environment index, and `C(E)` the LIT candidate intervention-target set under latent confounding. Suppose the non-language procedure correctly guarantees

\[
T_O(E) \subseteq C(E),
\]

but cannot distinguish two observed candidates `X_1` and `X_2` because the complete heterogeneous observational law and augmented-graph conditional independences are identical under two latent-confounded SCMs.

Construct two models:

- Model A: the true observed target is `X_1`, and utterance class `q_1` denotes `X_1`;
- Model B: the true observed target is `X_2`, and a relabeled utterance class `q'_1` denotes `X_2`.

Simultaneously transform:

- the latent confounder coordinates;
- the recovered changing-noise coordinate;
- the two candidate target blocks;
- the raw-utterance equivalence classes;
- the denotation map;
- the language encoder and decoder.

Choose the language generator so that it depends only on statistics already available from environment identity, observed trajectory, action, reward, outcome, and the unordered candidate set `C(E)`.

The two models can then preserve:

- every environment-indexed observed distribution;
- every contrastive recovery objective;
- the recovered changing-noise representation up to the allowed transformation;
- every conditional-independence relation used by LIT;
- the same candidate target set;
- target-candidate recall;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood;
- paraphrase accuracy;
- language-blind and language-shuffle gaps that depend only on candidate-set information.

Yet the true observed target, raw-utterance equivalence, and semantic denotation differ.

A language-assisted classifier may even choose the correct candidate on the finite benchmark if an utterance token is correlated with an environment ID or target-specific surface feature. This improves target accuracy but does not establish population identification: the correlation may be a benchmark code, and target/utterance labels may still be jointly permuted.

Therefore:

> Reducing a latent-confounded LIT candidate superset with language is not joint identification unless the language law supplies an externally fixed distinction unavailable from the complete heterogeneous non-language law and eliminates every residual target/utterance relabeling.

## Necessary boundary for a surviving language contribution

Let `S_LIT` contain all information available to the strongest LIT-style non-language analysis:

- all environment-indexed observed distributions;
- environment identities;
- recovered changing exogenous-noise coordinates up to allowed transformations;
- all augmented-graph conditional independences;
- the LIT candidate target set;
- state, action, reward, outcome, split, and completed trajectories;
- all predictions and evaluation statistics derived from these quantities.

Let `P_residual` denote the target distinction remaining inside the candidate set after conditioning on `S_LIT`. A necessary information condition for a language-specific contribution is

\[
I(P_{residual};L\mid S_{LIT})>0.
\]

This remains insufficient. The language law must be fixed before fitting and must break every simultaneous transformation of candidate target blocks, latent-confounder coordinates, changing-noise coordinates, utterance classes, language encoders/decoders, and denotation maps that preserves the complete observed and interventional law.

An admissible anchor cannot consist only of:

- environment IDs;
- candidate target indices produced by LIT;
- observed-variable names that can be permuted with target blocks;
- reward, success, action target, outcome, or completed trajectory;
- language generated from those same variables;
- human-readable labels whose target correspondence is supplied by the benchmark.

## Updated decision for RQ-001

**NARROWED BEYOND HETEROGENEOUS-DATA UNKNOWN-TARGET IDENTIFICATION — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest heterogeneous-data unknown-target identifier and conditioning on its recovered changing noises, graph relations, candidate target set, environment, state, action, reward, outcome, and trajectory information, can a preregistered externally fixed language law jointly identify raw-utterance equivalence and the residual target partition while eliminating every latent-confounder/target/utterance/denotation relabeling that preserves the complete data law?

Adoption now requires at minimum:

1. a formal mapping from SILG/J-CRe3 environment changes to the soft-intervention and fixed-mechanism assumptions used by LIT;
2. an immutable three-seed reproduction of official LIT at the audited commit with all transitive dependencies, logs, checksums, model bytes, peak RSS, wall time, and CPU latency;
3. explicit verification of invertibility or the latent-confounder recovery condition, environment-count sufficiency, exponential-family variation, and T-faithfulness;
4. the maximal target set or candidate partition recoverable without language;
5. a concrete pair of latent-confounded models with the same heterogeneous observed law and LIT output but different residual target partitions;
6. language information unavailable from environment ID, observed variables, state, action, reward, outcome, target-correlated surface features, and completed trajectories;
7. a denotational anchor fixed before fitting;
8. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
9. direct recovery metrics for raw-utterance equivalence, residual target partition, and denotation rather than target F1 or task success alone;
10. language-blind, state-only, environment-label-shuffle, target-label-shuffle, outcome-shuffle, and candidate-set-shuffle controls on identical instances;
11. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- heterogeneous-data recovery of changing exogenous noises: prior art
- unknown soft-intervention target identification under causal sufficiency: prior art
- latent-confounded candidate target supersets: prior art
- official paper-specific demo code: verified at immutable commit
- immutable R0 reproduction: not started
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
