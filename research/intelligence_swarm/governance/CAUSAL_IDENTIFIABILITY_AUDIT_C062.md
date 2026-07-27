# Causal Identifiability Audit C062

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- C responsibility: determine whether joint identification of raw-language equivalence and a latent intervention-target partition is open relative to prior work and identifiable under the available observations.
- No new architecture.
- No extension of legacy A–E toy mechanisms.
- No novelty, intelligence-principle, or capability-progress claim.
- This run completes: (a) prior-art matrix refinement, (b) theorem/assumption/observation/guarantee comparison, and (d) an identifiability counterexample. It also audits official public code; numerical reproduction is not started.

## Primary work audited

Armin Kekić, Bernhard Schölkopf, and Michel Besserve, **“Targeted Reduction of Causal Models,”** UAI 2024, PMLR 244.

Primary sources:

- Paper: https://proceedings.mlr.press/v244/kekic24a.html
- Paper PDF: https://raw.githubusercontent.com/mlresearch/v244/main/assets/kekic24a/kekic24a.pdf
- Official code: https://github.com/akekic/targeted-causal-reduction

Targeted Causal Reduction (TCR) learns a low-dimensional causal model that preserves information relevant to a supplied target phenomenon in a high-dimensional intervenable simulator. It uses shift interventions and an information-theoretic objective, and gives an identifiability result for continuous variables under the paper's intervention and regularity assumptions.

TCR therefore addresses discovery of compact causal factors for explaining a fixed target phenomenon. It does not infer an unknown raw-language equivalence relation, does not discover which linguistic distinctions constitute the target phenomenon, and does not identify a denotation from utterance classes to latent intervention blocks.

## Prior-art matrix refinement

| Candidate contribution | Status after C062 | Reason |
|---|---|---|
| Learning a compact causal explanation of a selected phenomenon from interventional simulator data | Existing | TCR directly optimizes a high-level causal reduction for a supplied target. |
| Using shift interventions to identify target-relevant continuous causal factors | Existing under assumptions | TCR provides an identifiability result for its continuous reduction setting. |
| Information-theoretic selection of causes most relevant to a target | Existing | This is the central TCR objective. |
| Producing interpretable high-level causal factors from complex simulators | Existing empirical contribution | TCR demonstrates this on synthetic and mechanical systems. |
| Treating a language-conditioned outcome as the target of a causal reduction | Direct application, not a new principle | Replacing the supplied target variable with a language-conditioned score does not discover the language codebook. |
| Jointly identifying raw-language equivalence, an unknown target partition, and denotation | Not established | TCR presupposes the target phenomenon and intervention interface used to define relevance. |
| Eliminating simultaneous recoding of language classes, target coordinates, intervention labels, and decoder/interface bookkeeping | Not established | TCR identifiability is internal to the selected causal-reduction problem and does not provide an external semantic anchor. |

Accordingly, “target-relevant causal factor discovery,” “information-theoretic causal reduction,” and “shift-intervention identification” cannot alone support novelty for RQ-001.

## Assumption / observation / guarantee comparison

### Targeted Causal Reduction

**Supplied or fixed**

- A low-level intervenable simulator or causal model.
- A target phenomenon or target random variable to be explained.
- An intervention family, specifically shift interventions in the identifiability analysis.
- A definition of which low-level intervention and target responses enter the reduction objective.
- Continuous-variable and regularity assumptions required by the theorem.

**Observed or generated**

- Samples from low-level interventions.
- The resulting target response.
- Training signals derived from intervention information and target relevance.

**Guaranteed under the theorem assumptions**

- Identification of a target-relevant high-level causal reduction within the equivalence class declared by the theorem.
- Recovery of compact causes sufficient for the selected target-reduction objective.

**Not guaranteed or directly evaluated**

- Recovery of a raw-expression equivalence relation `Q`.
- Recovery of an unknown semantic intervention-target partition `P`.
- Recovery of a denotation map `d: Q -> P`.
- Discovery of whether two target-relevant factors are semantically one class or two classes.
- Selection of the external meaning of a recovered high-level coordinate.
- Elimination of recodings involving the supplied target, intervention interface, language encoder, and evaluator.

### RQ-001

RQ-001 is stronger because neither side of the correspondence may be silently supplied. It asks whether observations determine:

1. which raw utterances are semantically equivalent;
2. which latent intervention targets form the same semantic block; and
3. which utterance block denotes which target block.

TCR starts after a target phenomenon and intervention semantics have already been fixed well enough to define its objective. Using a parser, reward function, simulator variable, or outcome label to choose that target transfers the unresolved codebook into the supplied target definition.

## Target-definition supervision and leakage boundary

For an RQ-001 experiment, the following must be treated as supplied supervision or potential leakage if used to define the TCR target:

- gold target or entity identity;
- simulator variable names;
- parser slots or semantic frames;
- action arguments containing a target index;
- reward or terminal-success labels generated from the target codebook;
- completed trajectories selected by known target identity;
- target-specific outcome classifiers trained on gold semantics;
- language embeddings pretrained with the same denotation labels;
- intervention schedules indexed by the hidden target label.

A language-conditioned target score is not an independent semantic anchor when the score was itself produced by a language model or parser sharing the candidate codebook.

## Identifiability counterexample 1: perfect target reduction with a different denotation

Let `Q` be raw-utterance classes, `Z` low-level causal variables, `P` a latent target partition, `Y` the supplied target phenomenon, `I` the intervention interface, and `d: Q -> P` the denotation.

Assume an oracle TCR learner perfectly identifies a minimal high-level factor `H(Z)` for predicting or explaining `Y` under every allowed shift intervention.

Choose a non-trivial bijection `pi` on target blocks. Construct a second model by simultaneously transforming:

- target blocks and their labels;
- intervention arguments and intervention logging;
- raw-language classes;
- denotation, with `d' = pi o d`;
- the language encoder and target-conditioned decoder;
- the target-dependent simulator/evaluator interface.

Couple the two systems through `pi`. Then all quantities used by TCR can be preserved:

- the joint law of intervention samples and target responses;
- the information-theoretic objective;
- the learned high-level dimension;
- target prediction and explanation scores;
- interventional sufficiency of the reduction;
- downstream action, reward, and task-success metrics computed through the recoded interface.

Nevertheless, a raw utterance class denotes a different external target block. Thus perfect TCR recovery does not uniquely identify `d` when target and intervention bookkeeping may be jointly recoded.

## Identifiability counterexample 2: target-relevance equivalence does not imply semantic equivalence

Consider two latent candidates `p1` and `p2` whose interventions induce exactly the same distribution of the supplied target `Y` under every allowed context and shift magnitude. TCR correctly treats them as indistinguishable for the selected phenomenon.

Two semantic models remain observationally equivalent:

- Model A merges `p1` and `p2` into one semantic block and treats `u1` and `u2` as synonyms.
- Model B keeps two semantic blocks and treats `u1` and `u2` as different meanings, while assigning identical target-response laws to both.

Both models have the same TCR objective, reduction, intervention-response data, prediction performance, and downstream target score. Yet their `Q` and `P` differ. TCR therefore identifies at most a quotient induced by relevance to the supplied phenomenon, not the complete semantic ontology inside each quotient cell.

## Identifiability counterexample 3: multiple target phenomena can still leave a joint automorphism

Suppose TCR is run for a family of target phenomena `Y1, ..., Ym`, and every target-relevant reduction is recovered perfectly. If a non-trivial group action simultaneously permutes latent targets, utterance classes, intervention arguments, and the entire target family while preserving their joint interventional response law, every TCR result remains unchanged.

Adding more targets only improves identification when at least one target or measurement law is fixed independently of the candidate semantic recoding. A collection of targets generated from the same simulator codebook does not automatically supply that asymmetry.

## Consequence for the candidate RQ

TCR strengthens the negative boundary:

> Identifying the most important causal factors for a supplied phenomenon is not the same as identifying which raw-language distinctions and latent intervention distinctions are semantically valid, nor which language class denotes which target block.

The remaining positive question must explicitly separate three layers:

1. the finest target-relevance quotient identifiable from all legitimate non-language interventions;
2. the finest raw-language quotient identifiable from language dynamics;
3. an independently fixed cross-system measurement or intervention law capable of removing the residual joint automorphism between those quotients.

## Official public-code audit

The PMLR page links the official repository:

- Repository: `akekic/targeted-causal-reduction`
- Audited main commit: `559fb61a972349c065345c5e30f579617ccef30c`
- Package metadata version: `0.0.1a1`
- Python requirement: `>=3.11`

The repository provides:

- a public Python package;
- an MIT license;
- a `tcr` command-line entry point;
- source modules for causal models, data generators, reductions, simulators, and Lightning training;
- tests and a GitHub Actions directory;
- source and development installation instructions;
- PyPI installation instructions.

Reproducibility limitations observed from the public package metadata and README:

- dependencies are lower-unbounded names rather than an immutable lock with hashes;
- the package metadata declares both a static version and a dynamic version attribute pointing to `my_package.VERSION`, which requires verification in a clean build;
- the default example writes Weights & Biases logs and is not documented as an offline deterministic reproduction command;
- no canonical paper-wide three-seed manifest is supplied;
- no raw-result checksum bundle is supplied;
- model bytes, peak RSS, wall time, and CPU latency are not part of the published reproduction contract;
- no direct `Q`, `P`, or `d` recovery evaluation exists.

A numerical public-baseline reproduction is not started in C062. The official implementation is suitable for a later preregistered packaging/reproduction run, but it is not a language-grounding baseline by itself.

## Decision

**NARROWED BEYOND IDENTIFIABLE TARGETED CAUSAL REDUCTION — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest target-relevance quotient identifiable from all legitimate shift/interventional observations and the finest raw-language quotient identifiable from language dynamics, can a preregistered cross-system probe family whose identity, units, and response law are fixed independently of the simulator target codebook reduce the residual joint automorphism to the declared harmless equivalence and thereby identify `Q`, residual `P`, and `d` without parser, target-label, reward, or evaluator leakage?

## Required next evidence before adoption

1. Enumerate every target variable, outcome score, intervention argument, parser output, and evaluator field used in the grounded-causal benchmark.
2. Separate target-relevance partitions from semantic target partitions.
3. Write the residual automorphism group after the strongest TCR-style non-language reduction and language-only quotient are recovered.
4. Define external probes whose identity, direction, scale, and response law are independent of the target codebook.
5. Construct matched countermodels with identical TCR reductions and task success but different `Q`, `P`, or `d`.
6. Preregister direct partition and denotation metrics, including merge/split errors inside a target-relevance quotient.
7. Reproduce a competent public baseline before adding any architecture.
8. Once experiments begin, report model bytes, peak RSS, wall time, and three fixed seeds.

## Status after C062

- RQ-001: further narrowed; not adopted.
- Targeted causal reduction for a supplied phenomenon: existing research.
- Shift-intervention identifiability of target-relevant factors: existing under assumptions.
- Raw-language equivalence: not identified.
- Latent semantic target partition: not jointly identified.
- Denotation: not identified.
- Official public code: confirmed.
- Exact official commit: confirmed.
- Public baseline reproduction in this run: not started.
- New architecture: none.
- Legacy A–E toy mechanisms: unchanged.
- Experiment started: no.
- Model size / RSS / runtime / three seeds: not yet applicable.
- Novelty: not established.
- Intelligence principle: none.
- Capability progress: not recognized.
