# Causal Identifiability Audit C082

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code suitability audit, and (d) an identifiability/applicability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C081 split the empirical B4 gate into:

1. exact mode, where finite samples can soundly return `separate / unidentified` and can return `merge` only under symbolic equality; and
2. approximate mode, where `merge / separate / unidentified` is defined using preregistered tolerances `epsilon_merge < epsilon_split`.

The next question is whether existing anytime-valid confidence-sequence or e-process implementations already provide the sequential statistical component needed for approximate B4 under adaptive monitoring.

## Primary prior art

Primary sources:

- Michael Lindon and Alan Malek, *Anytime-Valid Inference for Multinomial Count Data*, NeurIPS 2022 / arXiv `2011.03567`.
- Steven R. Howard, Aaditya Ramdas, Jon McAuliffe, and Jasjeet Sekhon, *Time-uniform, nonparametric, nonasymptotic confidence sequences*, Annals of Statistics 2021 / arXiv `1810.08240`.
- Paul Mineiro and Steven R. Howard, *Time-uniform confidence bands for the CDF under nonstationarity*, NeurIPS 2023.

Lindon–Malek give sequential tests and confidence sequences for multinomial probability vectors and contrasts, with validity under optional stopping and continued monitoring. Howard et al. provide generic time-uniform confidence-sequence machinery, and Mineiro–Howard extend time-uniform distributional estimation to adaptively generated and potentially nonstationary observations under explicit weighting/conditional-law assumptions.

Consequently, the following are removed from possible novelty:

- optional-stopping-safe monitoring of multinomial counts;
- anytime-valid point-null testing for multinomial probability vectors;
- confidence sequences for multinomial probabilities and contrasts;
- repeated looks without ordinary fixed-horizon multiplicity inflation;
- time-uniform confidence bounds for bounded means or distributional functionals;
- using an e-process or confidence sequence to stop early when a pair is clearly separated.

These results are statistical components. They do not by themselves compute a greatest controlled full-consequence quotient.

## Assumption and guarantee comparison

### What anytime-valid inference guarantees

A confidence sequence `(C_t)_{t>=1}` satisfies a guarantee of the form

`Pr(theta in C_t for all t >= 1) >= 1-alpha`.

An e-process or sequential test can reject a fixed null while controlling Type-I error despite optional stopping. For multinomial data, this can be applied to a state-action successor/consequence vector when the observation process satisfies the paper's sampling assumptions.

This is useful for B4 separation:

- if the confidence region for a difference excludes the approximate-merge set, `separate` can be certified;
- if it lies inside a preregistered approximate-merge set, an approximate `merge` may be certified only if the confidence construction controls the entire relevant distance functional;
- otherwise the result is `unidentified`.

### What it does not guarantee

The cited guarantees do not automatically provide:

- action coverage for actions that the behavior policy never selects;
- simultaneous validity over all state pairs, actions, consequence channels, and adaptive revisits without an explicit error-allocation rule;
- a partition-consistent transitive closure of pairwise decisions;
- exact equality certification for unrestricted real-valued multinomial parameters;
- greatest-quotient recovery rather than isolated pairwise tests;
- codebook-independent selection of the consequence channels;
- identification of `Q` or `d`.

Optional-stopping validity and adaptive data collection are different issues. A test may remain valid when inspected repeatedly, while still being uninformative because a required state-action pair is never sampled.

## Counterexample 1: anytime validity does not create action coverage

Consider two states `s,t` and two actions `a,b`. The logging policy always chooses `a`.

Under `a`, both states have identical reward, successor, sensor, cost, and terminal-consequence laws.

For unobserved action `b`, two point MDPs are consistent with the complete observed stream:

- Model A: `s` and `t` also have identical `b`-consequence laws;
- Model B: their `b`-consequence laws differ by total variation one.

An anytime-valid multinomial test on the observed `a` stream may run forever with valid Type-I control. It cannot distinguish Models A and B because no `b` sample exists. Storm's complete-model B4 oracle merges the states in Model A and separates them in Model B.

Therefore:

> time-uniform validity does not identify the action-complete B4 partition without a generative sampler, forced exploration, or an explicit permanent-abstention rule for uncovered actions.

## Counterexample 2: marginal pairwise confidence does not produce a valid partition

Let three states `s1,s2,s3` have true pairwise distances near a tolerance boundary. Suppose pairwise procedures are run independently at level `alpha` and return:

- `s1 ~ s2` as approximate merge;
- `s2 ~ s3` as approximate merge;
- `s1` versus `s3` as separate.

This is not an equivalence relation. Taking transitive closure merges a pair that was certified separate; refusing closure leaves no partition.

A valid B4 estimator therefore needs a global partition rule, not merely pairwise p-values. The rule must preregister:

- a family-wise or simultaneous confidence event over every tested state-action-consequence comparison;
- how pairwise uncertainty maps to blocks;
- how transitivity violations trigger abstention or block refinement;
- whether the estimand is a threshold graph, complete-linkage quotient, or another explicitly defined tolerance-indexed object.

Without this contract, “approximate bisimulation partition” is underdefined.

## Counterexample 3: nonstationary averages need not equal a stationary target law

Suppose the consequence distribution under a state-action pair changes over time because the environment, policy population, or hidden context drifts. A time-uniform confidence sequence may validly estimate a running average conditional distribution. That does not imply the existence or recovery of a single stationary transition kernel required by the point-MDP Storm oracle.

Two systems can share the same running average while having different context-conditional controlled laws and therefore different intervention-target partitions under a context-aware B4 definition.

Thus:

> robustness to continuous monitoring or specified nonstationarity does not justify collapsing a nonstationary process into a stationary semantic target ontology.

The target parameter and stationarity/context contract must be fixed before execution.

## Public-code audit

### `gostevehoward/confseq`

Pinned repository:

- repository: `gostevehoward/confseq`
- commit: `5ffe733ca2447a2e28c2c91f3b00086173f2ab2c`

The package provides uniform boundaries, confidence sequences, betting-based procedures, and always-valid p-values through C++/Python and partial R interfaces. PyPI exposes release `0.0.11` and describes Python 3.7–3.10 test coverage for that release.

Suitability:

- suitable as a time-uniform scalar/bounded-functional inference backend;
- suitable for optional-stopping-safe separation diagnostics;
- not a direct multinomial two-sample full-vector partition implementation;
- not an action-coverage manager;
- not a greatest-quotient or transitivity-enforcing algorithm;
- no canonical LBQ001 command, dataset digest, seeds, RSS, or partition metrics.

### Lindon–Malek paper code status

The NeurIPS paper and supplementary material are public. This audit did not confirm a paper-authored immutable implementation repository. A later third-party package, `assuncaolfi/savvi`, implements methodology influenced by the paper, but it is not treated as the canonical author implementation and is not pinned as the primary B4 baseline in this run.

Classification:

> public anytime-valid inference software exists and can serve as a sequential confidence backend, but no audited package is an end-to-end action-complete, full-consequence, tolerance-indexed B4 partition estimator.

No numerical run is started because the global approximate-partition estimand and error-allocation contract are not yet frozen.

## Prior-art matrix update

| Candidate | Time-uniform validity | Optional stopping | Multinomial/full distribution | Action coverage | Global partition consistency | Exact/approximate role | C classification |
|---|---:|---:|---:|---:|---:|---|---|
| Lindon–Malek multinomial inference | yes | yes | multinomial vectors/contrasts | no | no | point-null and confidence inference | sequential statistical prior art |
| Howard et al. `confseq` | yes | yes | bounded means and generic boundaries | no | no | backend primitives | public confidence backend |
| Mineiro–Howard CDF bands | yes | yes | distributional CDF target | weighting/overlap required | no | time-varying average distribution | nonstationary diagnostic prior art |
| Required approximate B4 estimator | must be simultaneous | must be valid | all preregistered consequences | required or abstain | required | `epsilon_merge / epsilon_split` quotient | not yet selected |

## Decision

> **NARROWED BEYOND ANYTIME-VALID MULTINOMIAL AND DISTRIBUTIONAL INFERENCE — OPTIONAL-STOPPING-SAFE CONFIDENCE SEQUENCES AND E-PROCESSES ARE EXISTING PRIOR ART AND CAN SUPPORT EARLY SEPARATION OR TOLERANCE-BASED ABSTENTION, BUT THEY DO NOT CREATE ACTION COVERAGE, DO NOT BY THEMSELVES ENFORCE A GLOBALLY CONSISTENT GREATEST PARTITION, AND DO NOT TURN A NONSTATIONARY AVERAGE LAW INTO A STATIONARY TARGET ONTOLOGY — NOT ADOPTED.**

C081's impossibility boundary remains unchanged: exact finite-sample merge is unavailable without symbolic tying. Approximate mode is executable in principle only after the global tolerance-indexed partition and simultaneous error contract are specified.

## Consequence for RQ-001

This run concerns only recovery of a language-blind approximate `P`. It does not identify `Q` or `d`.

Even a statistically valid approximate B4 partition can be coupled to raw language only after showing that:

- the language-side quotient uses a compatible and independently justified tolerance;
- cross-system samples contain observable dependence beyond target IDs, parser slots, rewards, or evaluator codebooks;
- context drift and polysemy are not silently averaged into artificial equivalence classes;
- direct `Q`, `P`, and `d` metrics improve under held-out independent consequences.

## Next gate

1. Amend LBQ001 with an explicit approximate-mode estimand, not merely pairwise distance thresholds.
2. Choose a global partition construction that cannot return non-transitive pairwise decisions.
3. Freeze simultaneous error allocation across state pairs, actions, channels, and time.
4. Require generative action coverage or permanent abstention for uncovered state-action pairs.
5. Separate stationary-point-MDP and context-indexed/nonstationary estimands.
6. Only then pin a minimal `confseq`-based command or another public backend and execute seeds `17 / 29 / 43` with model size, peak RSS, wall time, and input/output digests.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code suitability audit: complete;
- identifiability/applicability counterexamples: complete;
- anytime-valid multinomial inference: existing prior art;
- time-uniform confidence sequences: existing prior art;
- exact equality boundary from C081: unchanged;
- action coverage from optional-stopping validity: rejected;
- pairwise tests as a complete partition estimator: rejected;
- executable global approximate B4 estimator: not yet selected;
- numerical execution: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://proceedings.neurips.cc/paper_files/paper/2022/hash/12f3bd5d2b7d93eadc1bf508a0872dc2-Abstract-Conference.html
- https://arxiv.org/abs/2011.03567
- https://arxiv.org/abs/1810.08240
- https://proceedings.neurips.cc/paper_files/paper/2023/hash/148bbc25b934211d80435b5cad5a7198-Abstract-Conference.html
- https://github.com/gostevehoward/confseq
- https://pypi.org/project/confseq/
