# Causal Identifiability Audit C085

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) an applicability/identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, wall time, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C084 established that globally transitive robust/perturbation-aware quotients already exist for labelled Markov chains, but left open whether action identity itself remained outside executable prior art. This run asks whether action-conditioned MDP bisimulation has a current theorem and public implementation suitable for the LBQ001-B4 stack, and whether that closes the finite-sample full-consequence partition gate.

## Primary prior art

### Suilen and Pérez, CONCUR 2026

*On the Complexity of Robust Markov Decision Processes and Bisimulation Metrics* is accepted at CONCUR 2026 and available as arXiv `2604.26748`.

For a finite discounted MDP `M=(S,A,P,R,γ)`, the paper uses the fixed-point bisimulation metric

`F_K(d)(s,s') = max_a [(1-γ)|R(s,a)-R(s',a)| + γ D_K(d)(P(s,a),P(s',a))]`,

where `D_K` is the Kantorovich distance induced by the current pseudometric. The maximum is taken over the same named action in both states, so action identity is preserved rather than marginalised.

The paper constructs an `(s,a)`-rectangular robust MDP over state pairs `(s,s')`. Its uncertainty set for each paired state and action is the coupling polytope between `P(s,a)` and `P(s',a)`, and its immediate reward is the scaled action-specific reward difference. Theorem 5.6 proves that the optimal robust value of this constructed RMDP is exactly the MDP bisimulation metric.

The work also provides:

- a robust-policy-evaluation result in polynomial time for `(s,a)`-rectangular RMDPs;
- an NP upper bound for the corresponding threshold problem;
- robust policy iteration with polynomial-time behavior for fixed discount factor under the stated representation;
- an empirical comparison of robust bounded value iteration and robust policy iteration;
- an author repository implementing the reduction and experiments.

This removes the following from possible novelty:

- preserving action identity in a recursively defined MDP bisimulation metric;
- computing the metric through an RMDP reduction;
- using Kantorovich couplings recursively over successor-state distances;
- applying robust policy iteration to compute an action-conditioned bisimulation metric;
- claiming that mature action-conditioned executable prior art is absent.

## Public-code pin

Official repository:

- repository: `marnixrs/bisimRMDP`
- pinned commit: `e95595b8a856e666d0fd0fd751e7d331c872f8a3`
- paper command declared by README: `python experiments.py`

The pinned README requires an available Gurobi license and a Python virtual environment. The pinned dependency file fixes:

- `gurobipy==13.0.1`
- `gymnasium==1.3.0`
- `numpy==2.4.4`
- `scipy==1.17.1`
- plus supporting packages.

The paper reports FrozenLake experiments and repeats randomized robust-policy-iteration runs over ten seeds. It reports wall-clock statistics for those runs, but the repository does not expose an LBQ001 manifest, partition metrics, dataset/result digests, peak RSS instrumentation, or the required seeds `17 / 29 / 43`.

Classification:

> official action-conditioned bisimulation-metric implementation and immutable commit are now pinned; it is an exact known-model metric baseline, not a finite-sample full-consequence partition estimator.

No unofficial reimplementation is promoted.

## Assumption and guarantee comparison

### What the theorem supplies

Under a fully specified finite discounted MDP, the construction supplies:

- universal comparison over named actions through the outer `max_a`;
- recursive comparison of successor distributions using Kantorovich distance;
- a globally defined pseudometric over all state pairs;
- exact equality between that metric and a robust-value fixed point;
- an executable robust-policy-iteration route;
- distance zero as the ordinary action-conditioned bisimulation equivalence induced by the selected reward and transition law.

This directly corrects C084's residual suggestion that action-preserving recursive MDP prior art might be unavailable.

### What it does not supply for LBQ001-B4

The theorem and implementation assume the point MDP is already known. They do not supply:

- statistical estimation of `P(s,a)` from finite trajectories;
- confidence-valid `merge / separate / unidentified` outputs;
- abstention for uncovered state-action pairs;
- a preregistered perturbation or tolerance model;
- a discrete partition-recovery guarantee under metric-estimation error;
- action availability as a separate consequence channel unless encoded into the model;
- independent sensors, physical cost, terminal physical consequence, or held-out consequence unless explicitly encoded into reward/state labels;
- leakage checks preventing gold target ontology from entering those encodings;
- raw-language quotient `Q` or denotation `d`.

Therefore the code is suitable as an additional exact-model reference, not as the empirical B4 solution.

## Counterexample 1: exact action-conditioned metric can still be too coarse for full consequence

Consider states `s,t` with identical action sets and, for every action:

- identical task reward;
- identical successor-state distribution;
- identical terminal outcome under the MDP state representation.

Assume an independently calibrated physical sensor emits `0` at `s` and `1` at `t`, but this sensor is not included in reward, labels, or state transition observations passed to the metric implementation.

Then the fixed-point bisimulation metric is exactly zero:

- reward difference is zero;
- Kantorovich successor distance is zero recursively;
- all named actions agree.

The LBQ001 full-consequence oracle must nevertheless separate `s,t` because a preregistered non-semantic physical consequence differs.

Thus:

> exact recovery of the standard action-conditioned MDP bisimulation metric does not identify the full-consequence B4 partition unless every admissible consequence channel is included in the model specification.

Adding the sensor to a label or reward can repair the estimand, but only after the encoding is preregistered and checked for semantic leakage.

## Counterexample 2: exact metric computation does not establish finite-sample identifiability

Let two candidate point MDPs be consistent with the same finite trajectory dataset.

- In `M0`, two states have identical transition laws for every action, so their bisimulation distance is zero.
- In `Mη`, one transition probability differs by an arbitrarily small `η>0`, so their exact distance is positive.

The official implementation returns the correct metric when supplied with either complete point model. It does not determine which point model generated the finite data. For any finite sample budget, sufficiently small `η` leaves overlapping finite-sample laws.

Therefore:

> an exact known-model metric solver is an oracle for the supplied MDP, not evidence that the true unknown quotient is identifiable from finite samples.

C081's boundary remains: exact empirical merge cannot be certified uniformly without symbolic tying or a preregistered approximate-equivalence gap.

## Counterexample 3: metric thresholding is not automatically a partition

A pseudometric satisfies the triangle inequality, but the threshold relation `d(s,t) <= ε` need not be transitive. For example, distances may satisfy

- `d(s1,s2)=0.6ε`,
- `d(s2,s3)=0.6ε`,
- `d(s1,s3)=1.2ε`.

All distances are metric-consistent, yet pairwise thresholding merges the first two pairs and separates the endpoints. Connected-component closure would merge endpoints whose distance exceeds the threshold; complete-linkage would split one of the near pairs.

Therefore an approximate B4 partition still requires a globally specified quotient objective or diameter/stability contract. Computing a high-quality action-conditioned metric alone does not select the semantic partition.

## Counterexample 4: supplied reward can encode target leakage

The metric treats reward difference as an observable state-action distinction. If reward is generated from:

- gold target ID;
- parser semantic slot;
- simulator object or role name;
- target mask;
- semantic evaluator output;

then distance zero/nonzero preserves a supplied ontology rather than discovering it. The metric theorem remains valid, but the resulting partition is invalid evidence for `P`.

LBQ001 may use only preregistered non-semantic consequence channels, and the leakage scan remains mandatory.

## Prior-art matrix update

| Candidate | Global/recursive | Action-conditioned | Exact known-model computation | Finite-sample identification | Full-consequence by default | Public immutable code | C classification |
|---|---:|---:|---:|---:|---:|---:|---|
| Suilen–Pérez CONCUR 2026 | yes | yes | yes, metric via RMDP | no | no; reward/transition only unless augmented | yes, `e95595b...` | exact action-conditioned metric baseline |
| Storm B4 oracle | yes | yes | yes, greatest exact quotient | no | only supplied non-semantic labels/model | yes, pinned in C073 | exact partition oracle |
| Fatmi et al. CAV 2025 | yes | no, LMC | yes under robust-LMC estimand | no | no | implementation declared, pin unresolved | robust LMC prior art |
| Required empirical approximate B4 | yes | yes | n/a | yes with coverage and abstention | yes | not selected | remaining gate |

## Decision

> **NARROWED BEYOND ACTION-CONDITIONED MDP BISIMULATION-METRIC COMPUTATION — AN OFFICIAL CONCUR 2026 REDUCTION AND EXECUTABLE IMPLEMENTATION NOW PROVIDE A PINNED EXACT KNOWN-MODEL BASELINE, BUT THEY DO NOT PROVIDE FINITE-SAMPLE FULL-CONSEQUENCE PARTITION IDENTIFICATION, COVERAGE ABSTENTION, OR LANGUAGE–TARGET COUPLING — NOT ADOPTED.**

The remaining B4 problem is no longer “find an action-preserving recursive metric.” That component is prior art and executable. The remaining problem is to define and estimate a leakage-free full-consequence controlled quotient under finite data, with a globally coherent approximate-partition contract and permanent abstention for uncovered actions.

## Consequence for RQ-001

This run concerns only the language-blind target-side quotient `P`. Even a perfect action-conditioned metric or exact point-model quotient would not identify:

- raw-language equivalence `Q`;
- whether language distinctions finer than the behavioral quotient are externally justified;
- denotation `d: Q -> P`;
- external semantic orientation.

The candidate joint RQ remains unadopted until both quotients and their relative coupling are directly identified without target IDs, parser outputs, simulator names, semantic reward, or evaluator codebooks.

## Next gate

1. Add the pinned Suilen–Pérez implementation to the exact-model baseline inventory, but do not execute until a canonical runtime/resource manifest is committed.
2. Decide whether B4 approximate mode targets metric-diameter blocks, robust exact bisimilarity, or perturbation-repair equivalence; these are different estimands.
3. Audit prior art for action-conditioned approximate bisimulation partitions, not merely metrics, with a global diameter/stability guarantee.
4. Require explicit encoding of all preregistered non-semantic consequence channels and verify that action availability is preserved.
5. Keep exact empirical mode asymmetric: `separate / unidentified`, with `merge` only under symbolic tying.
6. Execute seeds `17 / 29 / 43` only after the estimator, tolerance, coverage, leakage, and partition contracts are fixed; record serialized model size, parameter count, peak RSS, training/evaluation wall time, hardware/software environment, exact command/commit, and dataset/result digests.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code availability audit: complete;
- applicability/identifiability counterexamples: complete;
- action-conditioned recursive MDP bisimulation metric: existing prior art;
- official immutable implementation pin: complete;
- exact known-model metric baseline: selected;
- finite-sample full-consequence partition estimator: not selected;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://arxiv.org/abs/2604.26748
- https://confest-2026.github.io/concur/accepted-papers
- https://github.com/marnixrs/bisimRMDP
- https://github.com/marnixrs/bisimRMDP/commit/e95595b8a856e666d0fd0fd751e7d331c872f8a3
