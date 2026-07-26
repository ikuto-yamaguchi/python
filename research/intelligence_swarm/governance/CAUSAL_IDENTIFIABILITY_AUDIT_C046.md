# Causal Identifiability Audit C046

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Intervening to Learn and Compose Causally Disentangled Representations

Alex Markham, Isaac Hirsch, Jeri A. Chang, Liam Solus, and Bryon Aragam. Proceedings of the Fifth Conference on Causal Learning and Reasoning, PMLR 323:1481–1525, 2026.

Primary records:

- PMLR: https://proceedings.mlr.press/v323/markham26a.html
- arXiv: https://arxiv.org/abs/2507.04754
- OpenReview: https://openreview.net/forum?id=4P08CBsSw7
- official code: https://github.com/Alex-Markham/context-module
- data supplement: https://doi.org/10.5281/zenodo.20098448

The paper adds a context module to an arbitrary encoder–decoder model. Concepts are represented as linear projections of black-box embeddings, an intervention layer uses slices corresponding to observational and single-concept interventional contexts, and an expressive layer maps generic latent noise into concept-specific exogenous variables. The model is evaluated by single-concept intervention and held-out multi-concept composition, primarily through generated-sample distribution metrics.

This is directly relevant to RQ-001 because it demonstrates that concept-conditioned intervention modules, compositional OOD generation, and identifiable concept representations are already prior art when concept variables and single-concept intervention contexts are supplied.

## Assumption, observation, and guarantee comparison

### Supplied concept and intervention structure

The audited setting assumes:

- observations `x` and black-box embeddings `e` with `x = f(e)`;
- an explicitly enumerated set of concepts `c_1, ..., c_dc`;
- concept values or concept-associated samples sufficient to train concept-specific contexts;
- a noisy linear representation relation `c_j = C_j e + epsilon_j`;
- rows of each `C_j` drawn from a linearly independent set;
- an injective and differentiable observation map `f`;
- single-node interventions on every concept `c_j`;
- intervention-context identity sufficient to select the corresponding context slice;
- concept dimensionalities and tensor slicing fixed by design;
- no requirement to infer the concept inventory or intervention-context partition from unrestricted raw language.

The practical architecture does not recover a full latent causal DAG. It uses a reduced-form SEM-like intervention layer and learns observational plus concept-specific contexts. The paper explicitly distinguishes this from full causal-graph reconstruction.

### Identifiability guarantee

Theorem 3.3 states, under the linear-independence, injectivity, differentiability, and single-node intervention assumptions, that the concept representations `C_j` and the latent concept distribution `p(c)` are identifiable.

The guarantee identifies representations for already specified concepts under already partitioned concept interventions. It does not identify:

- which raw utterances belong to the same concept class;
- whether two language forms denote the same intervention;
- an unknown inventory of latent intervention targets;
- a partition of trajectories into previously unknown intervention-target blocks;
- a unique denotation from unrestricted utterance classes to concept slices;
- semantics finer than the supplied concept and intervention-context indexing;
- an anti-recoding anchor preventing simultaneous relabeling of concepts, contexts, utterances, and decoder coordinates.

### Practical evaluation boundary

The paper measures concept intervention and OOD composition through generated-distribution quality. Successful held-out composition is stronger than ordinary reconstruction, but it still evaluates correctness relative to supplied concept slots and intervention labels.

For RQ-001, the following cannot be counted as discovery of raw-language equivalence or a latent target partition:

- assigning each instruction family to a predeclared concept slice;
- selecting a context tensor slice using a gold target or parser-derived concept ID;
- training on single-target intervention labels and evaluating unseen combinations;
- showing improved OOD generation after concept interventions;
- recovering linear probes for supplied concepts;
- obtaining a language-shuffle gap when the unshuffled language determines a supplied context index;
- treating concept compositionality as evidence that the concept inventory itself was identified.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- attaching an intervention-aware context module to an arbitrary encoder–decoder;
- extracting linearly represented concepts from black-box embeddings;
- learning observational and single-concept interventional contexts in a shared reduced-form model;
- composing learned concept interventions for OOD generation;
- end-to-end training or fine-tuning of an existing model with such a module;
- identifying representations of supplied concepts under single-concept interventions;
- using OOD concept composition as evidence of causal disentanglement;
- using a concept-conditioned generative module as a language-grounding mechanism when the concept/context assignment is supplied;
- claiming joint semantic identification from correct intervention generation under gold concept indexing.

The surviving RQ must concern the discovery and anchoring of the concept/intervention partition itself, not learning a module after that partition has entered through labels, contexts, parser outputs, or tensor indexing.

## Official-code and reproducibility audit

The authors provide paper-specific official code at `Alex-Markham/context-module`.

Audited commit:

`71a9df3d8424922b9f6bc1e669096538d2604d90`

The repository provides:

- the context-module implementation in `src/conceptualizer/conceptualizer.py`;
- a lightweight VAE integration;
- a Snakemake workflow for the paper experiments;
- `pyproject.toml` and `uv.lock`;
- a hash-pinned `requirements.txt`;
- a full-workflow command, `uv run snakemake all --forceall --cores 8`;
- a test command, `uv run snakemake test --cores 8`;
- downloadable datasets with published checksums through Zenodo;
- links to the 3DIdent generator and NVAE integration.

The full workflow comprises 1,024 jobs and 350 training or fine-tuning jobs. The repository states that complete reproduction requires a few hundred GPU hours. Its test target downloads the quad dataset, trains one model, requires a GPU, and takes about 90 minutes on an H100.

Classification:

> **paper-specific official code, lockfile, hash-pinned requirements, workflow, and dataset checksums verified; no R0 public-baseline reproduction started because the official test is GPU-only and far outside the current baseline contract**

The availability of unusually strong reproducibility assets strengthens the prior-art boundary. It does not justify adapting this architecture to SILG before R0 baseline reproduction and preregistration.

No experiment was started in this audit. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are therefore not applicable in this cycle.

## Identifiability counterexample: supplied concept contexts with non-identified language denotation

Let:

- `X` be observations;
- `E` be black-box embeddings;
- `C = {c_1, ..., c_m}` be the supplied concept inventory;
- `K in {0,1,...,m}` be the supplied observational/intervention context index;
- `U` be raw utterances;
- `Q` be an unknown equivalence relation over utterances;
- `P` be an unknown semantic intervention-target partition;
- `d: U/Q -> P` be a denotation map.

Assume the paper's theorem conditions hold and the concept representations `C_j` and latent concept distribution are perfectly identified for each supplied concept and intervention context.

Construct Model A using utterance partition `Q`, semantic target partition `P`, context assignment `K`, concept representations, and denotation `d`.

Construct Model B by:

- applying a nontrivial permutation `pi` to concept indices and context slices;
- permuting the corresponding rows or blocks of the concept representation;
- replacing `P` with `P' = pi(P)`;
- replacing the utterance partition with a different `Q'` and transforming the denotation to `d'`;
- transforming the language encoder, intervention-context selector, reduced-form tensor, latent decoder, and policy consistently;
- preserving which training instances are assigned to each numerical context after the joint recoding.

Both models can preserve:

- the complete observational and interventional distribution of `X`;
- the embedding distribution;
- the noisy linear concept representation equations;
- the identifiable matrices and distributions up to the joint relabeling;
- the context-module training objective;
- reconstruction quality;
- single-concept intervention quality;
- held-out multi-concept OOD generation;
- sliced-Wasserstein scores;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps that depend on selecting the correct supplied numerical context.

Nevertheless, `Q`, `P`, and the external semantic denotation differ.

Therefore:

> Identifying supplied concept representations and composing their intervention contexts does not identify raw-language equivalence or the semantic intervention-target partition. The theorem fixes representations relative to an indexed concept/intervention design; it does not fix what those indices mean.

A stronger within-context counterexample also remains. Suppose two raw utterance classes always select the same supplied concept context and induce the same conditional distribution over all observed trajectories. One model may merge them as synonyms while another keeps them as distinct meanings with observationally equivalent effects. All context-module objectives and OOD composition metrics remain equal. Thus even exact concept-context recovery need not determine the raw utterance equivalence relation.

## Necessary boundary for a surviving language contribution

Let `S_CM` contain all information available from the strongest context-module baseline:

- supplied concept inventory and values;
- context indices and intervention labels;
- concept-conditioned samples;
- black-box embeddings;
- identified linear concept representations;
- observational and interventional generated distributions;
- state, action, reward, outcome, environment, and trajectory information;
- parser, entity, target, grammar, schema, and template metadata;
- all trained context selectors and policies.

Let `P_residual` be the target distinction remaining after conditioning on `S_CM`. A necessary information condition is:

\[
I(P_{residual}; L \mid S_{CM}) > 0.
\]

This remains insufficient. The language law must be fixed independently before fitting and must eliminate every simultaneous permutation or reparameterization of concept indices, context slices, utterance classes, target blocks, denotation, embeddings, reduced-form tensors, decoders, and policies that preserves the full observed law.

An admissible anchor cannot merely be:

- a numerical concept or context index;
- a parser slot or instruction-family ID;
- a target/object/entity index;
- an action destination;
- a simulator variable name;
- reward, success, outcome, or completed trajectory;
- a held-out concept combination generated from the same supplied slots;
- a human-readable label whose target mapping was supplied;
- a pretrained embedding trained on aligned concept names.

## Required controls and evaluation consequences

Any future context-module adaptation must compare identical domain × seed × instance cells for at least:

1. random;
2. language-blind;
3. state-only;
4. language-form shuffle;
5. target-label shuffle;
6. outcome shuffle;
7. context-index shuffle;
8. concept-slot permutation fixed per run;
9. gold concept contexts versus predicted contexts versus no contexts;
10. context selector with parser, entity, target, and outcome inputs removed;
11. direct recovery of utterance partition, residual target partition, and denotation.

OOD composition and task success must remain secondary metrics. The primary identification test must distinguish models that generate equally good held-out combinations but disagree about the utterance equivalence relation or semantic target partition.

## Updated decision for RQ-001

**NARROWED BEYOND IDENTIFIABLE INTERVENTION-CONTEXT CONCEPT MODELS — NOT ADOPTED**

The surviving candidate is:

> After applying the strongest identifiable context-module baseline with every legitimately supplied concept and single-concept intervention context, and after fixing all concept representations and compositional generation laws identifiable from those contexts, can a preregistered externally fixed language law discover raw-utterance equivalence and the residual intervention-target partition while eliminating every concept/context/utterance/target/denotation joint recoding preserved by the complete interaction law?

Adoption now requires at minimum:

1. a complete inventory of concept identities, context indices, parser outputs, target labels, and intervention metadata in SILG/J-CRe3;
2. a formal separation between supplied concept/context membership and discovered raw-language equivalence;
3. a fixed mapping from SILG interventions to the theorem's single-concept intervention assumptions, including violations;
4. reproduction of the official context-module test or an explicitly justified decision not to use it as an R0 baseline;
5. an immutable adaptation and data contract before any SILG implementation;
6. exact dependency, split, seed, command, checksum, model-byte, RSS, wall-time, and CPU-latency manifests after experiment start;
7. identical-instance random, language-blind, state-only, context-shuffle, concept-slot-permutation, target-label-shuffle, outcome-shuffle, and language-shuffle controls;
8. direct recovery metrics for utterance partition, residual target partition, and denotation;
9. a concrete countermodel pair preserving all supplied-context and compositional-generation laws while differing in both partitions;
10. language information not reconstructible from concept labels, context indices, parser, target, state, action, reward, outcome, environment, or completed trajectory;
11. a denotational anchor fixed before fitting;
12. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
13. preregistration before any architecture or mechanism is introduced.

## Status

- RQ-001: further narrowed; not adopted
- identifiable supplied-concept intervention models: prior art under the paper assumptions
- paper-specific official code: verified
- official reproducibility assets: lockfile, hash-pinned requirements, workflow, and dataset checksums verified
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
