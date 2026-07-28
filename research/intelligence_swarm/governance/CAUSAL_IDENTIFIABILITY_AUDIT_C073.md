# Causal Identifiability Audit C073

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement and (b) theorem/assumption comparison, and freezes a public exact oracle for the LBQ001-B4 operational quotient.
- Numerical model execution is not started; model size, peak RSS, runtime, and three-seed measurements remain mandatory when execution begins.

## Decision-relevant question

C072 established that the official DeepMDP implementation is admissible only as LBQ001-B3 because it preserves reward and transition structure rather than the full preregistered consequence family.

C073 asks:

> Is there an existing public, non-neural implementation that computes the complete-consequence operational quotient without introducing a new architecture, and what exactly would such a reproduction prove?

## Primary theory

Primary prior art:

- Robert Givan, Thomas Dean, Matthew Greig, *Equivalence notions and model minimization in Markov decision processes*, Artificial Intelligence 147(1–2), 2003.

The relevant object is a probabilistic/MDP bisimulation-style quotient. Starting from distinctions that must be retained, partition refinement merges states only when their retained labels agree and their action-conditioned transition probability mass into every quotient block agrees.

For a finite fully specified model, this yields the coarsest stable behavioral partition under the declared labels and controlled transition law.

## Public implementation selected

Public implementation:

- repository: `stormchecker/storm`
- pinned commit: `80a18e088a0d627befe2e3667b000672c0bc43d5`
- API: `src/storm/api/bisimulation.h`

The pinned source exposes strong bisimulation minimization for sparse DTMC, CTMC, and MDP models. The API dispatches to deterministic or nondeterministic bisimulation decomposition, computes the decomposition, and returns the quotient.

A separate preregistration was added:

- `benchmarks/grounded_causal/PREREGISTERED_B4_ORACLE_STORM_BISIMULATION.md`

## Classification within LBQ001

Storm is selected as:

> **B4 exact-model oracle/reference quotient**

It is not selected as:

> **B4 finite-sample learned estimator**

The distinction is essential.

Storm receives an explicit complete transition model and state labels. It can compute the exact quotient induced by those supplied quantities. It does not infer the transition law or consequence channels from finite trajectories.

## Consequence encoding

Let `c(s)` be the complete preregistered non-semantic consequence signature for state or history-state `s`.

The initial partition supplied to the exact quotient must preserve every difference in `c(s)`, including any preregistered:

- independent sensor response;
- physical cost;
- action availability;
- terminal physical consequence;
- held-out consequence channel admitted into the operational definition.

A reward-only signature remains B3. It cannot be relabeled as B4.

No language, parser slot, target name, target mask, simulator semantic variable, or codebook-derived evaluator may enter the signature.

## Theorem/assumption comparison

| Object | DeepMDP B3 | Storm B4 oracle | RQ-001 joint identification |
|---|---|---|---|
| Input model | sampled/constructed reward-transition training data | complete finite controlled model | raw language plus unknown intervention structure |
| Retained consequences | reward and latent transition objective | all explicitly supplied preregistered consequence labels and transition probabilities | unknown `Q`, unknown `P`, unknown `d` |
| Output | learned task-relative representation/model | exact strong-bisimulation quotient | language equivalence, target partition, and coupling |
| Guarantee scope | reward/transition/value approximation | exact quotient of the supplied finite model | joint semantic/causal identifiability |
| Learns unknown dynamics from samples | yes, approximately | no | required in realistic setting |
| Uses language | no | no | yes, but without semantic leakage |
| Identifies external semantic orientation | no | no | required only if claimed explicitly |

## Prior-art refinement

C073 removes the following from possible novelty claims:

- computing a coarsest finite MDP partition that preserves declared labels and controlled transitions;
- using exact partition refinement as a language-blind operational quotient;
- treating multiple physical consequences as labels that must be preserved by model minimization;
- using a public probabilistic model checker to construct a bisimulation quotient.

These are existing theory and implementation capabilities.

## New boundary established

### Exact quotient recovery is not finite-sample identification

Consider two candidate finite MDPs that agree on every sampled trajectory but differ on an unobserved low-probability transition. Their exact bisimulation quotients may differ.

Storm can distinguish them only after one complete model is supplied. From the finite sample alone, both models remain compatible.

Therefore:

> Successful Storm quotient construction proves correctness relative to the supplied complete model; it does not prove that the quotient is identifiable or recoverable from the available sampled trajectories.

This prevents a full-model oracle from being misreported as a public baseline reproduction of unknown-target causal learning.

### The quotient is only as non-semantic as its labels

If the supplied state labels encode gold target identity, parser output, simulator role names, or a target-derived evaluator, Storm will preserve those distinctions exactly.

The resulting quotient may be mathematically correct while being semantically leaked.

Therefore the label-construction pipeline, not only the minimization algorithm, is part of the identification audit.

### Operational quotient still does not identify `Q` or `d`

Even perfect recovery of the complete-consequence quotient `P_B4_oracle` does not establish:

- which raw utterances are equivalent;
- which utterance class denotes which quotient block;
- external names, units, orientation, or human semantic convention.

It provides a direct language-blind target partition against which those later claims can be tested.

## Mandatory oracle validation

The preregistration requires:

1. reward/transition-aliased states separated by an independent B4 consequence;
2. true bisimilar states merged;
3. action-sensitive states separated;
4. expected merge after consequence-channel ablation;
5. semantic-label shuffle invariance;
6. rejection of language-derived model labels.

These checks ensure the oracle computes the declared operational quotient rather than a hidden semantic partition.

## Resource and seed status

Execution has not started.

When it starts, generated models use seeds:

- `17`
- `29`
- `43`

For each input model, mandatory records include:

- serialized model size;
- numbers of states, actions, transitions, and consequence channels;
- peak RSS;
- quotient wall time;
- exact command and environment;
- input/output digests.

The exact algorithm should be deterministic for identical serialized input. A seed disagreement after matching input digests is a reproduction failure.

## Decision

**NARROWED TO A THREE-PART EXECUTION GATE: DEEPMDP B3, STORM EXACT-MODEL B4 ORACLE, AND A SEPARATE FINITE-SAMPLE B4 ESTIMATOR — NOT ADOPTED.**

The next admissible work is:

1. freeze the minimal DeepMDP B3 compatibility/runtime manifest;
2. construct the preregistered complete-consequence finite models and run the pinned Storm oracle;
3. select an existing public finite-sample estimator for the same B4 quotient, or prove that no audited candidate satisfies the observation contract;
4. report direct partition recovery against `P_B4_oracle` with seeds `17`, `29`, and `43` and all resource/result digests;
5. only after these baselines may a new architecture be considered under a separate preregistration.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public exact B4 oracle pin: completed.
- Storm classification: exact-model B4 oracle only.
- DeepMDP classification: B3 reward/transition control only.
- Finite-sample B4 estimator: pending.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory when execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
