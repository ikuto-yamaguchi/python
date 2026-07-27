# Causal Identifiability Audit C075

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) an applicability/identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C074 established that Kiefer–Tang provides a finite-sample approximate-quotient estimator only for action-marginal labelled Markov chains, leaving an action-conditioned finite-sample B4 estimator unresolved.

C075 asks:

> Does the sampling-based generalized bisimulation metric of Tao, Xu, and You close the action-conditioned finite-sample LBQ001-B4 gate?

## Primary prior art

Primary paper:

- Zhenyu Tao, Wei Xu, and Xiaohu You, *A Generalized Bisimulation Metric of State Similarity between Markov Decision Processes: From Theoretical Propositions to Applications*, NeurIPS 2025.
- Primary publication record: `https://proceedings.neurips.cc/paper_files/paper/2025/hash/458567910b6d21f438f22aa20c036723-Abstract-Conference.html`.
- Primary paper PDF: `https://proceedings.neurips.cc/paper_files/paper/2025/file/458567910b6d21f438f22aa20c036723-Paper-Conference.pdf`.

The paper defines a generalized bisimulation metric (GBSM) between states belonging to two finite MDPs with a shared action space:

`d((s,M1),(s',M2)) = max_a {|R1(s,a)-R2(s',a)| + gamma W1(P1(.|s,a),P2(.|s',a);d)}`.

It proves fixed-point existence and convergence, symmetry, an inter-MDP triangle inequality, bounds on optimal-value differences, and applications to aggregation and sampling-based estimation.

## What the prior art establishes

The central correction to C074 is:

> Action-conditioned finite-sample estimation of bisimulation-style state distances is not generally missing from prior art.

For every state-action pair, the paper estimates the transition distribution from `K` samples and derives a high-probability error bound between the true GBSM and the GBSM computed from empirical transition laws. It gives an explicit closed-form sample complexity of the form

`K >= -ln(alpha/2) * gamma^2 * Rbar^2 * |S|^2 / (2 epsilon^2 (1-gamma)^4)`

for each state-action pair, under the paper's finite-state bounded-reward assumptions.

Therefore the following claims are removed from possible novelty:

- that action-conditioned MDP similarity cannot be estimated from finite samples;
- that only action-marginal LMC methods have explicit finite-sample quotient-related guarantees;
- that empirical transition matrices cannot support a controlled bisimulation metric with a closed-form sample requirement;
- that comparing an original MDP to an empirical or aggregated MDP through a bisimulation metric is new;
- that finite-sample error must remain merely asymptotic in this setting.

## Assumption and guarantee comparison

| Object | Tao–Xu–You GBSM | LBQ001 finite-sample B4 requirement |
|---|---|---|
| Controlled model | finite MDP | finite MDP or controlled history-state model |
| Action identity | retained explicitly through `max_a` | mandatory |
| Input sampling | `K` successor samples for every state-action pair | finite trajectories; coverage may be nonuniform and policy-dependent |
| Reward | known/bounded reward function | reward is only one consequence channel and may be excluded from principal B4 labels |
| Transition estimator | empirical categorical distribution per state-action pair | estimator must account for uncertainty and incomplete coverage |
| Output | real-valued GBSM distances and approximation bounds | direct partition estimate against the Storm B4 oracle |
| Partition threshold | not uniquely supplied by the theorem | preregistered, statistically justified merge rule required |
| Complete consequence family | reward plus successor-state law | independent sensors, cost, action availability, terminal and held-out consequences |
| Unknown representation | states are already indexed | latent/history states may be unknown |
| Semantic objects `Q,d` | not identified | not expected from B4, but B4 must estimate language-blind `P` |
| Public implementation | no training/evaluation code declared by the paper | exact public implementation pin preferred before execution |
| Three-seed resource bundle | not supplied | seeds `17 / 29 / 43`, bytes, RSS, time, and digests mandatory |

## Suitability decision

The theorem is admissible as:

> **the action-conditioned finite-sample error contract for an empirical finite-MDP B4 metric reference**

It is not yet admissible as:

> **the principal executable LBQ001 finite-sample B4 partition estimator**

The paper closes the theorem-level gap left by C074, but not the implementation and partition-recovery gaps.

## Why a metric estimator is not automatically a quotient estimator

The theorem controls the numerical error of a real-valued metric. LBQ001 requires recovery of a discrete partition.

Suppose the true metric contains two state-pair distances:

- `d(s1,s2) = delta - eta`;
- `d(t1,t2) = delta + eta`.

A proposed partition rule merges pairs whose estimated distance is at most `delta`. If the uniform metric estimation error is `epsilon >= eta`, an estimate within the theorem's valid error band may place either pair on either side of the threshold. Thus the metric estimate can be accurate while the recovered partition is wrong.

A finite-sample partition guarantee additionally requires a positive separation margin:

`min_between_block d - max_within_block d > 2 epsilon`,

or an equivalent stability condition. The audited GBSM theorem does not itself assert such a semantic/full-consequence block margin or prescribe the LBQ001 threshold.

Therefore:

> A finite-sample guarantee for metric estimation does not by itself identify the exact B4 quotient.

## Counterexample: reward/transition distance can miss a preregistered consequence

Consider states `s` and `t` with identical action availability, reward, and successor-state distributions for every action. They differ only in an independent calibrated sensor consequence `z`, preregistered as part of the B4 consequence family but not represented in the GBSM reward or successor-state identity.

Then the audited GBSM can assign distance zero to `s` and `t`, and its empirical estimate can converge perfectly to zero with arbitrary sample size. The LBQ001-B4 oracle must nevertheless separate the states because their complete non-semantic consequence signatures differ.

Encoding `z` into a state label or reward can repair this only if that augmentation is preregistered and codebook-independent. Otherwise it risks converting the full-consequence requirement into an evaluator-defined label.

Thus:

> Perfect action-conditioned GBSM estimation is insufficient for B4 unless every preregistered consequence channel is explicitly and non-semantically represented in the controlled model.

## Coverage boundary

The closed-form sample requirement assumes samples for each state-action pair. Passive trajectories generated by a behaviour policy need not provide this coverage. If a relevant action has zero or very low probability in a state, no finite trajectory count alone yields the required per-pair empirical transition estimate without an exploration or generative-model assumption.

Consequently, the result supplies a valid generative-model/per-state-action sampling contract, not a universal guarantee for arbitrary logged interactive trajectories.

## Public-code availability audit

The NeurIPS proceedings, paper PDF, OpenReview record, and public author/conference records were checked. The paper's reproducibility checklist states that it is a theory paper involving simple numerical computations and declares no training/evaluation code. No paper-specific official public repository or immutable implementation commit was confirmed in this run.

Confirmed:

- primary peer-reviewed paper;
- explicit action-conditioned finite-MDP definition;
- fixed-point and sampling-error theory;
- closed-form per-state-action sample complexity;
- numerical computations described in the paper.

Not available as a pinned public reproduction bundle:

- official paper-specific repository and commit;
- canonical executable estimator;
- dependency lock or container;
- generated-MDP and empirical-transition digests;
- partition-threshold protocol;
- direct ARI/AMI/pairwise-F1/VI scoring against Storm;
- complete-consequence augmentation contract;
- seeds `17 / 29 / 43` and resource instrumentation.

No numerical execution was started.

## Consequence for RQ-001

This prior art does not identify raw-language equivalence `Q`, denotation `d`, or external semantic orientation. Its relevance is to the language-blind `P` gate:

1. it removes the claim that action-conditioned finite-sample metric estimation lacks explicit theory;
2. it supplies a candidate statistical error contract for an empirical finite-MDP baseline;
3. it leaves direct quotient recovery dependent on margin/stability assumptions;
4. it leaves complete-consequence encoding and coverage assumptions unresolved;
5. it does not supply a public immutable implementation suitable for immediate reproduction.

## Decision

**NARROWED: ACTION-CONDITIONED FINITE-SAMPLE GBSM ESTIMATION HAS EXPLICIT PRIOR-ART GUARANTEES, BUT AN EXECUTABLE FULL-CONSEQUENCE PARTITION ESTIMATOR STILL REQUIRES COVERAGE, CONSEQUENCE AUGMENTATION, AND A SEPARATION-MARGIN CONTRACT — NOT ADOPTED.**

The baseline gate is refined to:

1. DeepMDP B3 reward/transition control;
2. Storm exact-model B4 MDP oracle;
3. Kiefer–Tang LMC finite-sample diagnostic;
4. Tao–Xu–You GBSM as the action-conditioned finite-sample metric-theory reference;
5. a still-missing pinned executable that converts empirical full-consequence controlled models into a partition with a preregistered stability/margin guarantee.

## Next admissible work

1. audit public implementations of finite-MDP bisimulation metrics that retain action identity and can accept augmented non-semantic consequence labels;
2. determine whether a public implementation can be used unchanged with Storm-compatible exact states and empirical per-state-action transition counts;
3. preregister the metric-to-partition separation margin and confidence rule before execution;
4. freeze the DeepMDP compatibility manifest and Storm oracle input format;
5. if no immutable implementation satisfies the contract, document the no-fit matrix before writing any compatibility implementation;
6. begin numerical execution only after the executable, coverage contract, consequence encoding, and partition rule are frozen.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code availability audit: completed.
- Applicability/identifiability counterexample: completed.
- Action-conditioned finite-sample metric theory: existing prior art.
- Explicit closed-form sample complexity: existing prior art under per-state-action sampling.
- Full-consequence partition estimator: not selected.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
