# Causal Identifiability Audit C045

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced.

## Primary work newly audited

### Towards Causal Representation Learning with Observable Sources as Auxiliaries

Kwonho Kim, Heejeong Nam, Inwoo Hwang, and Sanghack Lee. arXiv:2509.19058, first submitted 23 September 2025.

Primary records:

- arXiv: https://arxiv.org/abs/2509.19058
- arXiv HTML: https://arxiv.org/html/2509.19058
- arXiv version audited: `2509.19058v1`

The paper studies causal representation learning when one or more true latent sources are already observed or can be extracted from the observation and are then used as auxiliary variables. Unlike standard nonlinear-ICA auxiliary-variable settings, the observed source participates in the same data-generating process and may directly affect the observation mixing.

The paper's main result identifies the remaining unobserved latent sources only up to conditionally independent subspaces, invertible transformations within those subspaces, and subspace permutations. It also proposes selecting the subset of observed sources that induces the finest conditional-independence partition according to a known latent causal graph, then fitting a volume-preserving flow with a graph-informed structural constraint.

This is directly relevant to RQ-001 because language, parser outputs, entity IDs, action targets, environment descriptors, or trajectory-derived variables can easily be treated as observable auxiliaries. Any resulting improvement in causal factor recovery must therefore be separated from discovery of raw-language equivalence or discovery of a hidden intervention-target partition.

## Assumption, observation, and guarantee comparison

### Data-generating and supervision assumptions

The audited setting assumes:

- observations `x = g(z)` generated from latent causal sources `z`;
- an arbitrary smooth invertible nonlinear mixing function before the additional volume-preserving restriction is imposed;
- a known latent Bayesian network `G` encoding conditional-independence relationships among the sources;
- a non-empty subset of true latent sources `z_o` that is already observed or extractable;
- conditional factorization of the remaining latent variables into independent subspaces after conditioning on a selected observed-source subset;
- a volume-preserving mixing/encoder condition, `|det J_g(z)| = 1`;
- a variability/rank condition requiring sufficiently many observed-source values so that the relevant derivative vectors are linearly independent;
- access to observed-source values during training;
- no requirement to infer the observed source itself from unrestricted raw language.

These assumptions are much stronger than merely observing language and trajectories. In particular, the known graph and known observable-source identity already specify which variable participates in the causal system and how conditioning on it changes recoverability.

### Identifying object

The paper identifies the unobserved latent sources up to:

- invertible transformations within each conditionally independent subspace;
- permutations of those subspaces.

It does not identify:

- an unrestricted equivalence relation over raw utterances;
- which language forms should count as the same observable source;
- a latent intervention-target partition absent from the supplied graph and source annotations;
- a unique denotation from utterance classes to latent target blocks;
- semantics inside a recovered subspace;
- an anti-recoding anchor eliminating simultaneous relabeling of observed sources, latent subspaces, utterance classes, and decoders.

### Observable-source selection guarantee

When several true latent sources are observed, the paper uses the known causal graph and Bayes-ball reasoning to choose a subset whose conditioning induces the finest partition of the unobserved sources. This strengthens recoverability, but the partition is derived from:

1. the supplied identity of observed latent sources;
2. the supplied latent causal graph;
3. graph-implied conditional independences.

It is not discovery of raw-language equivalence. If an instruction parser, simulator field, entity table, target index, or human annotation provides the candidate observable source, the semantic grouping has already entered through the observation contract.

### Boundary for SILG/J-CRe3

For SILG/J-CRe3, the following fields must be treated as observable-source supervision or possible leakage rather than evidence of semantic joint identification:

- gold entity IDs or target indices;
- action destination or manipulated-object index;
- simulator variable names;
- grammar production IDs;
- parser slots or semantic frames;
- environment/template IDs;
- dynamics labels;
- outcome or terminal-success fields;
- completed trajectories;
- target-aligned visual channels;
- instruction-family or paraphrase-group labels;
- pretrained embeddings already trained on the target vocabulary;
- any extracted variable whose extraction procedure used gold semantics.

A language-conditioned method may legitimately use such an auxiliary in a supervised baseline, but it must not be described as discovering raw utterance equivalence from interaction.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- using an observed or extracted causal source as an auxiliary variable for CRL;
- selecting among multiple observed sources to maximize latent recoverability using a known causal graph;
- recovering unobserved causal factors up to conditionally independent subspaces through observable-source conditioning;
- using a volume-preserving flow to obtain identifiability in this observable-source setting;
- interpreting language, parser outputs, entity IDs, or environment descriptors as auxiliary variables;
- claiming semantic grounding merely because such auxiliaries improve disentanglement, next-state prediction, action accuracy, or task success;
- treating recovery of an auxiliary-conditioned latent subspace as recovery of raw-language equivalence;
- treating a supplied source identity as a discovered intervention-target partition.

The surviving RQ must concern distinctions that remain after all legitimately supplied observable sources and graph information have been conditioned on.

## Official-code audit

The arXiv primary record and paper text were searched for a paper-specific code link. The arXiv record does not list an official repository, and a title-based GitHub repository search did not identify an author-controlled paper-specific implementation.

Classification:

> **primary paper and algorithmic description verified; paper-specific official implementation not verified**

No unofficial reimplementation was started. The proposed implementation combines a volume-preserving flow, conditional likelihood factorization, graph-informed structural neural networks, and a graph-based observable-selection procedure. Reimplementing it before a preregistered adaptation and baseline contract would create avoidable degrees of freedom.

No experiment was started in this audit. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are therefore not applicable in this cycle.

## Identifiability counterexample: supplied observable source with non-identified semantics

Let:

- `X` be the high-dimensional observation;
- `Z = (Z_o, Z_h)` be the latent causal sources;
- `Z_o` be an observed source supplied to the learner;
- `Z_h` be the remaining hidden sources;
- `U` be the raw instruction;
- `Q` be an unknown equivalence relation over utterances;
- `P` be an unknown fine-grained intervention-target partition;
- `d: U/Q -> P` be the denotation map.

Assume the audited theorem's conditions hold and conditioning on `Z_o` identifies `Z_h` up to subspace-wise invertible transformations and permutations. Let one identified hidden subspace `C` contain two fine-grained targets `p_1` and `p_2` that are not separated by the conditional-independence partition.

Construct Model A with utterance partition `Q`, target partition `P`, observed source `Z_o`, representation `h(X,Z_o)`, and denotation `d`.

Construct Model B by:

- applying a nontrivial invertible map within subspace `C`;
- swapping or otherwise re-partitioning `p_1` and `p_2` inside `C`;
- replacing `Q` by a different utterance partition `Q'`;
- transforming the denotation to `d'` consistently;
- transforming the language encoder, latent decoder, and policy accordingly;
- leaving the supplied observed source `Z_o` and its conditional-independence relations unchanged.

Both models can preserve:

- the complete joint law of `(X,Z_o)`;
- all graph-implied conditional independences;
- the selected observable-source subset;
- the conditional likelihood and volume-preserving-flow objective;
- the recovered subspace partition;
- reconstruction and latent-disentanglement scores;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood and paraphrase accuracy;
- language-shuffle gaps that depend only on the supplied auxiliary or recovered subspace.

Nevertheless, the raw-utterance equivalence relation, fine-grained target partition, and denotation differ.

Therefore:

> Perfect observable-source-assisted CRL does not identify raw-language equivalence or the fine-grained intervention-target partition inside the recovered subspaces. A supplied or extracted source can improve recoverability while leaving semantic joint recoding intact.

A second failure mode occurs when an extracted auxiliary is itself a function of the gold target:

\[
A = r(U,X,T_{gold}).
\]

If conditioning on `A` separates latent factors, the separation can be entirely caused by target information already present in `A`. Removing raw language while retaining `A` may preserve performance. Such a result is supervised factor recovery or leakage, not interactive semantic identification.

## Necessary boundary for a surviving language contribution

Let `S_OA` contain all information available from the strongest observable-auxiliary baseline:

- all legitimately observed latent sources;
- the known or estimated causal graph used for source selection;
- selected conditioning variables;
- state, action, reward, outcome, environment, and trajectory information;
- parser, entity, target, schema, grammar, and template metadata;
- the maximally recoverable auxiliary-conditioned latent partition;
- all predictions and policies trained from those quantities.

Let `P_residual` be the target distinction remaining after conditioning on `S_OA`. A necessary information condition is:

\[
I(P_{residual}; L \mid S_{OA}) > 0.
\]

This is still insufficient. The externally fixed language law must also eliminate every within-subspace transformation and simultaneous relabeling of utterance classes, target blocks, observed-source labels, latent coordinates, denotation, encoders, decoders, and policy that preserves the full observed law.

An admissible anchor cannot merely be:

- the identity of the observed source;
- a parser slot;
- an entity or target index;
- a graph node name;
- an environment/template label;
- reward, outcome, action target, or completed trajectory;
- a human-readable target name;
- a pretrained embedding trained on aligned labels.

## Required controls and evaluation consequences

Any future observable-source adaptation must compare identical domain × seed × instance cells for at least:

1. random;
2. language-blind;
3. state-only;
4. language-form shuffle;
5. target-label shuffle;
6. outcome shuffle;
7. observed-source shuffle;
8. random observed-source subset;
9. all observed sources versus graph-selected sources;
10. extracted auxiliary with gold-semantic inputs removed;
11. direct recovery of utterance partition, residual target partition, and denotation.

The evaluation contract must record the complete provenance of every auxiliary variable, including its raw inputs, extraction procedure, supervision, training split, pretrained assets, and whether it is reconstructible from gold target, action, reward, outcome, environment ID, or completed trajectory.

## Updated decision for RQ-001

**NARROWED BEYOND OBSERVABLE-SOURCE AUXILIARY CRL — NOT ADOPTED**

The surviving candidate is:

> After applying the strongest observable-source auxiliary CRL, conditioning on every legitimately supplied or extractable source and the graph information used to select it, and fixing the maximally recoverable auxiliary-conditioned latent subspaces, can a preregistered externally fixed language law discover raw-utterance equivalence and the residual intervention-target partition while eliminating every within-subspace and utterance/source/target/denotation joint recoding preserved by the complete observed interaction law?

Adoption now requires at minimum:

1. a complete inventory of all observed or extracted sources in SILG/J-CRe3;
2. a formal separation between supplied observable-source identity and discovered raw-language equivalence;
3. a proof or empirical audit of which conditional-independence partition each source induces;
4. a no-language observable-source baseline and a no-observable-source language baseline;
5. an immutable official-code reproduction, or if code remains unavailable, a preregistered faithful-reimplementation contract;
6. exact data, dependency, split, seed, command, checksum, model-byte, RSS, wall-time, and CPU-latency manifests after experiment start;
7. identical-instance random, language-blind, state-only, source-shuffle, target-label-shuffle, outcome-shuffle, and language-shuffle controls;
8. direct recovery metrics for utterance partition, residual target partition, and denotation;
9. a concrete countermodel pair preserving the complete observable-source-conditioned law but differing in both partitions;
10. language information not reconstructible from source identity, graph, parser, target, state, action, reward, outcome, environment, or completed trajectory;
11. a denotational anchor fixed before fitting;
12. proof that the residual joint automorphism group is nontrivial without the anchor and trivial with it;
13. preregistration before any architecture or mechanism is introduced.

## Status

- RQ-001: further narrowed; not adopted
- observable-source auxiliary CRL: prior art under the paper assumptions
- paper-specific official code: not verified
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
