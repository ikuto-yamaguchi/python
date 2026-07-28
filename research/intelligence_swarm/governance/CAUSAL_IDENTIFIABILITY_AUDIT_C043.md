# Causal Identifiability Audit C043

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Causal Representation Learning Made Identifiable by Grouping of Observational Variables

Hiroshi Morioka and Aapo Hyvärinen. Proceedings of the 41st International Conference on Machine Learning, PMLR 235:36249–36293, 2024. arXiv:2310.15709.

Primary records:

- PMLR: https://proceedings.mlr.press/v235/morioka24a.html
- arXiv: https://arxiv.org/abs/2310.15709
- OpenReview: https://openreview.net/forum?id=SL6V527p1F
- official code: https://github.com/hmorioka/GCaRL

The paper establishes a non-language identifiability route for causal representation learning that requires neither temporal structure, interventions, nor weak supervision. Its identifying signal is a known grouping structure in the observed variables: the observation vector is divided into groups whose members share latent causal parents through the grouped mixing structure. The authors also give a self-supervised estimator consistent with the model and report experiments including synthetic settings, gene-regulatory-network recovery, and 3dIdent image observations.

This is directly relevant to RQ-001 because benchmark instructions, state fields, object slots, modality blocks, or parser-produced token groups may accidentally provide exactly the kind of grouping side information that makes part of the representation problem identifiable without discovering raw-language equivalence or latent intervention-target semantics.

## Assumption, observation, and guarantee comparison

### Identifying structure

The audited setting relies on a grouped observation model rather than intervention metadata. The relevant distinction for RQ-001 is:

- **supplied grouping:** the learner is told or architecturally given which observed coordinates belong to each group;
- **discovered raw-language equivalence:** the learner must infer from unrestricted utterances which expressions are equivalent;
- **semantic target grounding:** inferred utterance classes must be uniquely matched to intervention-target blocks.

Only the first is part of the G-CaRL identification setup.

The paper's contribution therefore removes the following broad claims from the novelty space:

1. causal representations always require interventions or temporal transitions;
2. nonlinear observations cannot be handled without language supervision;
3. grouping observed fields or modalities to recover latent causal variables is a new language-grounding principle;
4. robustness to latent confounders or causal cycles uniquely motivates a language channel;
5. self-supervised recovery from grouped observations constitutes discovery of raw utterance semantics.

### Observation contract

The learner observes grouped low-level variables generated from latent causal variables. The grouping is structural side information. It is not inferred as an unrestricted equivalence relation over raw strings.

For SILG/J-CRe3, the following must therefore be treated as possible supplied-group leakage rather than semantic discovery:

- separately encoded instruction segments;
- object, attribute, relation, and action slots;
- fixed token-type IDs;
- observation dictionaries with semantic field names;
- modality-specific encoders whose boundaries correspond to latent roles;
- entity tables or target-index arrays;
- parser outputs, templates, grammar productions, or canonicalized command forms;
- shared identifiers joining utterances to environment objects.

If any such grouping is available to a model but unavailable to language-blind or state-only controls, an apparent language advantage may arise from grouping supervision rather than raw-language equivalence identification.

### Guarantee boundary

Under the paper assumptions, the grouped observation structure is sufficient for identifiable causal representation learning and statistically consistent estimation. The result does not establish:

- discovery of the grouping itself from unrestricted raw language;
- identification of paraphrase or denotation classes inside an observed group;
- a unique mapping from language classes to intervention-target blocks;
- elimination of simultaneous relabeling of group identities, latent coordinates, target blocks, and language classes;
- identifiability in sequential policy-dependent environments without a formal mapping to the grouped observation model.

Thus a benchmark cannot count recovery of latent variables from architecturally supplied token/state groups as evidence for RQ-001.

## Official-code audit

The author repository `hmorioka/GCaRL` explicitly identifies itself as the official implementation of the ICML 2024 paper. It contains:

- `gcarl_training.py`;
- `gcarl_evaluation.py`;
- `gcarl/` model code;
- `gcarl_3dident/` image-setting code;
- helper functions under `subfunc/`;
- parameter selections for Simulation1, Simulation2, GRN, and 3dIdent;
- an Apache-2.0 license.

The documented execution interface is:

```text
python gcarl_training.py
python gcarl_evaluation.py
```

The repository only states `Python3` and `Pytorch` as requirements. It does not provide:

- pinned Python or PyTorch versions;
- a dependency lockfile;
- a container image;
- a release tag;
- a three-seed manifest;
- expected result checksums;
- model-byte, peak-RSS, runtime, or CPU-latency records;
- an immutable benchmark bundle matching R0 reporting requirements.

Classification:

> **paper-specific official code verified; immutable R0 reproduction package not established**

No experiment was started in this audit. A future public-baseline reproduction must first pin the repository commit, interpreter and dependency versions, dataset artifacts, simulation configuration, seeds, expected outputs, and resource instrumentation. Model size, RSS, runtime, and three-seed reporting become mandatory once that reproduction starts.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded:

- identifying causal representations from known groups of observational variables;
- self-supervised CRL without temporal data, intervention data, or weak labels under a grouped mixing assumption;
- using known modality or field grouping as an identifying signal;
- treating parser slots or typed observation fields as if they were discovered language equivalence classes;
- interpreting grouped-observation recovery as unique semantic denotation;
- using task success or latent probes to bypass direct evaluation of raw-utterance and target partitions.

The surviving RQ must explicitly deny the model any grouping that encodes the answer unless that grouping is itself the preregistered object of recovery and is scored directly.

## Identifiability counterexample: perfect grouped CRL with non-identified language semantics

Let the observed variables be partitioned into supplied groups

\[
\mathcal G = \{G_1,\ldots,G_m\},
\]

and suppose a G-CaRL-compatible estimator perfectly recovers latent causal components

\[
Z=(Z_1,\ldots,Z_m)
\]

and their causal structure from the grouped observations.

Let raw utterances `U` have an unknown equivalence relation `Q`, let intervention targets have a partition `P`, and let

\[
d: U/Q \rightarrow P
\]

be the denotation map.

Construct two models:

- Model A uses `(Q,P,d)`;
- Model B applies a nontrivial permutation `pi` to supplied group identities, recovered latent coordinates, and target blocks, uses a different utterance partition `Q'`, and sets `d' = pi o d` while transforming the language encoder, decoder, and policy consistently.

Both models can preserve:

- the supplied observation-group membership;
- the full grouped observation distribution;
- the latent causal graph up to the allowed relabeling;
- the G-CaRL contrastive/self-supervised objective;
- reconstruction and latent recovery scores;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps that depend only on group-level information.

Nevertheless, the raw-utterance equivalence relation and semantic target alignment differ.

Therefore:

> Perfect identification of causal representations from supplied observational groups does not identify the grouping of raw utterances, the residual intervention-target partition, or their denotation. Group labels, latent coordinates, target blocks, and utterance classes can remain jointly relabelable.

A stronger within-group counterexample also remains. Two raw expressions can occupy the same supplied token/modality group and induce the same complete benchmark behavior while one model merges them into one semantic class and another keeps them distinct. Group-based CRL cannot decide between those partitions because both yield the same grouped observation law.

## Leakage implication for R0

Before using SILG/J-CRe3 as evidence for RQ-001, the evaluation contract must record and compare all group information supplied to every condition. At minimum, it must reject or separately label runs where the candidate model receives:

- semantic field names or typed slots absent from controls;
- target-index-aligned entity arrays;
- parser or grammar group IDs;
- instruction segmentation tied to action/target roles;
- shared object identifiers linking language and state;
- group-specific encoders whose partition is derived from gold semantics.

Required ablations include:

1. raw token stream with no semantic grouping;
2. true grouping supplied;
3. grouping predicted only from train data;
4. random grouping with matched group sizes;
5. group-label shuffle;
6. language-blind and state-only controls on identical instances;
7. target-label and outcome shuffles;
8. direct adjusted-rand/index or pairwise-F1 recovery metrics for both utterance and target partitions.

A gain that disappears when true grouping is removed is evidence for supplied grouping utility, not for joint identification.

## Necessary boundary for a surviving language contribution

Let `S_group` contain all information available from the strongest grouped-observation baseline:

- the complete supplied grouping;
- grouped observation distributions;
- recovered latent components and graph up to allowed transformations;
- state, action, reward, outcome, environment, split, and completed trajectories;
- all parser, schema, entity, and modality metadata;
- all predictions derived from those quantities.

Let `P_residual` be the target distinction remaining after conditioning on `S_group`. A necessary information condition is

\[
I(P_{residual};L\mid S_{group}) > 0.
\]

This remains insufficient. The preregistered language law must also eliminate every simultaneous relabeling or within-group reparameterization of observation groups, latent components, target blocks, utterance classes, denotation, and language encoder that preserves the complete observed law.

An admissible anchor cannot merely be:

- a supplied group name;
- a parser slot;
- an entity or target index;
- an environment ID;
- a reward, outcome, action target, or completed trajectory;
- a human-readable label whose target correspondence is given by the dataset rather than discovered.

## Updated decision for RQ-001

**NARROWED BEYOND GROUPED-OBSERVATION CRL IDENTIFIABILITY — NOT ADOPTED**

The surviving candidate is:

> After applying the strongest causal representation learner using every legitimately supplied observation grouping and conditioning on its recovered representation, graph, schema, environment, state, action, reward, outcome, and trajectory information, can a preregistered externally fixed language law discover raw-utterance equivalence and the residual intervention-target partition while eliminating every grouping/latent/target/utterance/denotation automorphism preserved by the full observed law?

Adoption now requires at minimum:

1. a complete inventory of grouping information present in SILG/J-CRe3 observations, instructions, parsers, schemas, and entity tables;
2. a formal separation between supplied observation groups and the unknown raw-utterance equivalence to be recovered;
3. an immutable three-seed reproduction of official G-CaRL or a preregistered faithful reproduction contract if direct transfer is impossible;
4. exact dependency, split, dataset, and seed manifests plus model bytes, peak RSS, wall time, CPU latency, raw logs, and checksums after experiment start;
5. direct comparison of true-group, predicted-group, no-group, random-group, and group-shuffle conditions;
6. a concrete countermodel pair with identical complete grouped observation and interaction laws but different residual utterance and target partitions;
7. language information not reconstructible from group membership, parser output, state, action, reward, outcome, environment ID, or completed trajectories;
8. a denotational anchor fixed before fitting;
9. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
10. direct recovery metrics for utterance partition, residual target partition, and denotation;
11. preregistration before any new architecture or mechanism.

## Status

- RQ-001: further narrowed; not adopted
- grouped-observation CRL identifiability: prior art under the paper assumptions
- official paper-specific code: verified
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
