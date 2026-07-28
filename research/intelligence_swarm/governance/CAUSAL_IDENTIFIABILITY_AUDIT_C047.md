# Causal Identifiability Audit C047

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Coarsening Causal DAG Models

Francisco Madaleno, Pratik Misra, and Alex Markham. Proceedings of the Fifth Conference on Causal Learning and Reasoning, PMLR 323:1318–1344, 2026.

Primary records:

- PMLR: https://proceedings.mlr.press/v323/madaleno26b.html
- arXiv: https://arxiv.org/abs/2601.10531
- OpenReview: https://openreview.net/forum?id=thKdqE58Sb
- official code: https://github.com/Alex-Markham/repare

The paper studies causal abstraction directly at the graph level. Rather than first recovering a fine-grained DAG and then grouping its nodes, it defines a lattice of partitions and learns an interventional coarsening from observational and interventional datasets whose intervention targets are unknown. The proposed Recursive Partition Refinement algorithm, RePaRe, is proved consistent under its graphical and testing assumptions.

This is directly relevant to RQ-001 because it shows that an intervention-induced latent partition and an abstract causal graph can be recovered without language, without target names, and without first identifying every fine-grained variable.

## Assumption, observation, and guarantee comparison

### Coarsening object

For a fine-grained DAG `G = (V,E)`, a coarsening is defined by a surjection `chi: V -> V'`. Directed edges between distinct parts are inherited from the fine graph. The admissible coarsenings form a partition-refinement lattice.

The interventional setting uses:

- observational samples and samples from multiple intervention environments;
- unknown intervention targets;
- statistical tests for which observed variables change under each intervention;
- graphical relations between intervention descendants and candidate partition parts;
- tests for directed adjacency between recovered parts;
- a sufficiently informative intervention family for the intended coarsening;
- standard large-sample consistency conditions for the employed tests.

The learning target is an abstract partition and abstract DAG justified by the interventional data. It is not an externally named semantic partition.

### Identifiability and consistency boundary

The paper establishes graphical identifiability results for interventional coarsenings and gives a provably consistent algorithm for directly recovering them. Its central practical contribution is therefore stronger than merely clustering similar variables: the recovered blocks are constrained by causal ancestry, descendants, and intervention responses.

The guarantee does not identify:

- unrestricted raw-utterance equivalence classes;
- a human-semantic name for each recovered block;
- distinctions inside a block that the available intervention family does not refine;
- a unique denotation from utterance classes to coarsening parts;
- an anti-recoding anchor preventing simultaneous relabeling of partition parts, utterance classes, and language encoders.

### Relevance to SILG / J-CRe3

Before language can be credited with discovering a target partition, the benchmark must first compute the finest coarsening recoverable from legitimate non-language signals. In particular, the following cannot be treated as language-specific progress if RePaRe or an equivalent non-language procedure can recover them:

- grouping state variables with indistinguishable intervention-descendant signatures;
- recovering an abstract intervention-target block from multi-environment transition changes;
- learning a coarse causal graph whose nodes correspond to behaviorally or dynamically similar variables;
- selecting a target block without knowing its human-readable name;
- improving task success by acting on the correct coarse block;
- recovering a partition only up to block permutation.

If SILG exposes simulator variable indices, entity tables, target arrays, environment templates, parser slots, or completed trajectories, those channels must be audited separately because they may make the coarsening easier than the raw-language problem.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- directly learning an abstract causal DAG from interventional data;
- learning a partition without recovering the fine-grained DAG first;
- identifying causal blocks under unknown intervention targets;
- using a partition-refinement lattice as the search space;
- refining blocks from intervention-descendant signatures;
- combining observational and interventional tests to recover a coarse causal model;
- obtaining a consistent estimator for an intervention-induced abstraction;
- treating coarse target recovery as evidence that raw-language equivalence was identified;
- treating a human-readable name attached after recovery as semantic joint identification.

The surviving RQ must concern distinctions that remain inside the finest non-language interventional coarsening and must explain how language removes the remaining automorphisms rather than merely naming recovered blocks.

## Official-code and reproducibility audit

The authors provide paper-specific official code at `Alex-Markham/repare`.

Repository state inspected on 2026-07-26. The exact commit SHA was not exposed by the available repository connector during this run, so immutable execution is not claimed yet. The inspected README blob SHA is:

`123097b085d11b5d8f12dff2ef25c71b2436e5d3`

The repository provides:

- `PartitionDagModelIvn` in `src/repare/repare.py`;
- unit tests;
- a Snakemake workflow under `src/expt/workflow/Snakefile`;
- `pyproject.toml` and `uv.lock`;
- a hash-pinned `requirements.txt`;
- Nix/devenv files;
- a quick test command, `uv run pytest tests/`;
- a Figure 1(a) reproduction command running 330 experiments;
- a full reproduction command, `uv run snakemake all --cores all --forceall`;
- automatic download of the third-party Causal Chambers dataset;
- reported CPU runtime of about 10 minutes for Figure 1(a) and under one hour for the full workflow, depending on CPU.

Classification:

> **paper-specific official code, lockfiles, hash-pinned requirements, tests, and reproduction workflow verified; exact commit pin and R0 resource/checksum bundle remain incomplete**

No experiment was started in this audit. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are therefore not applicable in this cycle.

## Identifiability counterexample: recovered coarsening with non-identified language denotation

Let:

- `X` be the complete observational and interventional data;
- `I` be the set of intervention environments with unknown fine-grained targets;
- `Pi*` be the finest interventional coarsening identifiable from `(X,I)` under the paper conditions;
- `G_Pi` be the corresponding abstract DAG;
- `U` be raw utterances;
- `Q` be an unknown equivalence relation over utterances;
- `P` be a proposed semantic intervention-target partition;
- `d: U/Q -> P` be a denotation map.

Assume RePaRe recovers `Pi*` and `G_Pi` perfectly.

Construct Model A with utterance partition `Q`, semantic target partition `P`, and denotation `d`.

Construct Model B by:

- applying a nontrivial permutation to the recovered coarsening parts;
- applying the same permutation to the abstract DAG node labels;
- relabeling the semantic target blocks;
- replacing `Q` by a different utterance partition `Q'` compatible with the same observed language-conditioned behavior;
- transforming the denotation, language encoder, policy, and decoder consistently;
- preserving every numerical environment, trajectory, action, reward, and outcome assignment.

Both models can preserve:

- every observational and interventional distribution;
- all intervention-descendant indicators;
- the recovered partition-refinement path;
- the final coarsening `Pi*` up to relabeling;
- the abstract DAG and all tested adjacencies;
- RePaRe's statistical decisions;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood;
- paraphrase accuracy;
- language-shuffle gaps whose effect is mediated by selecting the correct numerical block.

Nevertheless, `Q`, `P`, and the external denotation differ.

Therefore:

> Recovering the finest intervention-identifiable causal coarsening with unknown targets does not identify raw-language equivalence or the semantic meaning of the recovered blocks. It determines an abstract causal partition relative to the observed intervention law, not a unique denotation.

A stronger within-block counterexample remains. Suppose two fine-grained targets have identical intervention-descendant signatures and cannot be separated by any available environment. One model treats utterances referring to them as synonyms for one coarse intervention; another treats them as distinct meanings with observationally equivalent effects. RePaRe, all task metrics, and all trajectory likelihoods remain equal. Thus no language-conditioned learner can claim population identification of the finer distinction unless the language channel contains an independently fixed contrast unavailable from the complete non-language law.

## Necessary boundary for a surviving language contribution

Let `S_RP` contain all information available from the strongest RePaRe-style baseline:

- observational and interventional distributions;
- environment identities;
- intervention-descendant signatures;
- the finest identifiable coarsening and abstract DAG;
- state, action, reward, outcome, and complete trajectory information;
- entity, parser, target, grammar, schema, and template metadata;
- all policies and predictors trained on those signals.

Let `P_residual` be a target distinction strictly finer than the identifiable coarsening. A necessary information condition is:

\[
I(P_{residual}; L \mid S_{RP}) > 0.
\]

This is still insufficient. The language law must be fixed independently before fitting and must remove every coarsening-preserving transformation of target blocks, utterance classes, denotation, language encoder, abstract-node labels, policy, and decoder.

An admissible anchor cannot merely be:

- the recovered numerical block ID;
- a fine-variable index or simulator variable name;
- a parser slot or grammar production;
- an entity, object, destination, or action-target index;
- environment or intervention-template identity;
- reward, terminal success, outcome, or completed trajectory;
- a human-readable block label whose mapping was supplied;
- a pretrained embedding trained on the same aligned target vocabulary.

## Required controls and evaluation consequences

Any future language-assisted coarsening experiment must compare identical domain × seed × instance cells for at least:

1. random;
2. language-blind;
3. state-only;
4. language-form shuffle;
5. target-label shuffle;
6. outcome shuffle;
7. environment-label shuffle;
8. recovered-block permutation fixed per run;
9. RePaRe coarsening versus true supplied partition versus no partition;
10. parser/entity/target/template metadata removed;
11. direct recovery of utterance partition, residual target partition, and denotation.

Task success and abstract-DAG accuracy are secondary. The primary identification test must distinguish countermodels that have the same finest interventional coarsening and abstract graph but disagree about the within-block target distinction and utterance equivalence.

## Updated decision for RQ-001

**NARROWED BEYOND UNKNOWN-TARGET INTERVENTIONAL COARSENING IDENTIFIABILITY — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest causal coarsening and abstract DAG identifiable from all legitimate non-language observational and interventional data with unknown targets, can a preregistered externally fixed language law identify a strictly finer residual target distinction together with raw-utterance equivalence while eliminating every coarsening-preserving target/utterance/denotation relabeling?

Adoption now requires at minimum:

1. an explicit mapping from SILG/J-CRe3 variables and environments to the coarsening assumptions;
2. an inventory of all target, entity, parser, schema, template, and trajectory information;
3. computation or faithful approximation of the finest non-language interventional coarsening;
4. an exact-commit, dependency-locked, three-seed reproduction of RePaRe or a preregistered reason it is inapplicable;
5. a concrete pair of countermodels with the same finest coarsening and abstract DAG but different residual target and utterance partitions;
6. language information not reconstructible from environment, state, action, reward, outcome, parser, entity, target, schema, or completed trajectory;
7. a denotational anchor fixed before fitting;
8. proof that the residual coarsening-preserving automorphism group is nontrivial without the anchor and trivial with it;
9. direct metrics for utterance partition, residual target partition, and denotation;
10. identical-instance random, language-blind, state-only, environment-shuffle, block-permutation, target-label-shuffle, outcome-shuffle, and language-shuffle controls;
11. immutable model-byte, RSS, wall-time, CPU-latency, raw-log, split, seed, and checksum manifests after experiment start;
12. preregistration before any architecture or mechanism is introduced.

## Status

- RQ-001: further narrowed; not adopted
- unknown-target interventional causal coarsening: prior art under the paper assumptions
- paper-specific official code: verified
- exact official commit pin: pending; README blob pinned in this audit
- immutable public baseline reproduction: not started
- raw-language equivalence identification: not established
- residual within-coarsening target identification: not established
- semantic joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
