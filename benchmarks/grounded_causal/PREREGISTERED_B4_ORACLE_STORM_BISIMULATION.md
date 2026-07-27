# Preregistered B4 Oracle: Storm Strong Probabilistic Bisimulation

## Purpose

This manifest freezes an exact, language-blind oracle reference for LBQ001-B4. It does not introduce a new architecture and it is not a learned trajectory baseline.

The oracle answers a narrower question:

> Given the complete finite controlled transition model and the complete preregistered non-semantic consequence labels, what is the coarsest strong probabilistic-bisimulation quotient that preserves them?

The resulting partition is the reference operational quotient against which learned or sample-based estimators may later be evaluated.

## Primary theory

The operational equivalence follows the probabilistic model-minimization line represented by:

- Robert Givan, Thomas Dean, Matthew Greig, *Equivalence notions and model minimization in Markov decision processes*, Artificial Intelligence 147(1–2), 2003.

States may be merged only when their retained labels/consequences agree and, for every admissible action, their transition probability mass into every current equivalence block agrees. Iterative partition refinement yields the coarsest stable quotient for the declared model and retained observations.

## Public implementation pin

- Repository: `stormchecker/storm`
- Commit: `80a18e088a0d627befe2e3667b000672c0bc43d5`
- API entry point: `src/storm/api/bisimulation.h`
- Sparse deterministic decomposition: `DeterministicModelBisimulationDecomposition`
- Sparse nondeterministic/MDP decomposition: `NondeterministicModelBisimulationDecomposition`
- Bisimulation type: `Strong`

The pinned API supports sparse DTMC, CTMC, and MDP models and invokes the corresponding bisimulation decomposition before returning the quotient.

## Allowed oracle inputs

The oracle may read only quantities declared before model construction:

- finite state or history-state index used solely for model enumeration;
- admissible action identity;
- exact action-conditioned transition probabilities;
- complete preregistered non-semantic consequence vector;
- consequence-preserving state labels derived mechanically from that vector;
- action availability and preregistered physical cost when part of the declared consequence family.

## Forbidden semantic inputs

The oracle must not read:

- raw language, tokens, or language embeddings;
- parser output or semantic slots;
- gold semantic target ID, object name, role name, or simulator variable name;
- target mask derived from the semantic ontology;
- reward, reference structure, evaluator, or labels generated from a target codebook unless that channel was independently preregistered as a physical consequence;
- denotation labels or utterance–target pairs.

A deliberately semantic-label-initialized quotient may be run only as a leakage positive control and cannot support an identification claim.

## Consequence-label construction

Let `c(s)` denote the complete preregistered consequence signature of state/history-state `s`. The initial partition must separate states whenever `c(s) != c(t)`.

The consequence signature must include every channel designated by LBQ001-B4, for example:

- independent sensor outputs;
- physical cost;
- action availability;
- terminal physical consequence;
- held-out consequence channels that are permitted to define the operational quotient.

Reward-only labeling is classified as B3, not B4.

Continuous consequence values must be discretized only by a thresholding/binning rule fixed before examining semantic labels. The exact rule and digest must be recorded.

## Oracle output

Required outputs:

- state-to-block assignment;
- quotient block count;
- quotient transition model;
- retained consequence signature per block;
- exact Storm commit and command/build manifest;
- input-model digest;
- output-partition digest.

The output partition is named `P_B4_oracle`. It is an operational quotient, not an externally named semantic ontology.

## Mandatory validation cases

Before use on the research benchmark, the harness must pass:

1. **Reward/transition alias split**: two states identical in reward and transition but different in an independent B4 consequence must remain separate.
2. **True bisimulation merge**: two states with identical retained consequences and identical action-conditioned probability mass into all quotient blocks must merge.
3. **Action-sensitive split**: states equal under one action but different under another must remain separate.
4. **Consequence-channel ablation**: removing the distinguishing B4 channel must cause the expected merge.
5. **Semantic-label shuffle invariance**: shuffling unused semantic labels must not change the oracle partition.
6. **Language injection rejection**: the build/evaluation harness must fail its leakage scan if language-derived features enter the model labels.

## Resource contract

Execution uses seeds `17`, `29`, and `43` for model generation, although the exact quotient algorithm itself should be deterministic for an identical serialized input model.

For every generated model and seed, record:

- serialized input model size;
- number of states, actions, transitions, and consequence channels;
- peak RSS;
- quotient wall time;
- build/runtime environment;
- exact command;
- input and output digests.

A seed disagreement after matching input digests is a reproducibility failure.

## Scope limitation

Storm receives the complete transition model. Therefore this oracle does **not** establish that `P_B4` can be recovered from finite sampled trajectories. It provides:

- a precise target partition for direct ARI/AMI/VI/pairwise-F1 evaluation;
- an implementation check for the declared consequence family;
- a ceiling/reference for B3 and future sample-based B4 estimators.

It cannot evaluate raw-language equivalence `Q` or denotation `d`.

## Decision rule

- If the complete consequence model still yields a quotient coarser than the claimed semantic target ontology, the finer ontology is not operationally identifiable under the preregistered consequence family.
- If a learned language-conditioned partition is finer than `P_B4_oracle`, it requires an independent held-out consequence that was not used to define the oracle; otherwise the extra split is not accepted as target identification.
- Matching `P_B4_oracle` is necessary for a full-consequence quotient recovery claim but is not sufficient for joint identification of `Q`, `P`, and `d`.
