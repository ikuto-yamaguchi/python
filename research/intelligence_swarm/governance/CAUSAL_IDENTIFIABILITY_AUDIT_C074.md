# Causal Identifiability Audit C074

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code suitability audit, and (d) an identifiability/scope counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C073 fixed Storm as an exact-model B4 oracle and left a separate finite-sample B4 estimator unresolved.

C074 asks:

> Does the public implementation of Kiefer and Tang's approximate bisimulation minimisation satisfy the finite-sample LBQ001-B4 observation contract for action-conditioned MDPs with a complete preregistered consequence family?

## Primary prior art

Primary paper:

- Stefan Kiefer and Qiyi Tang, *Approximate Bisimulation Minimisation*, FSTTCS 2021, DOI `10.4230/LIPIcs.FSTTCS.2021.48`.
- Primary publication record: `https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FSTTCS.2021.48`.

The paper studies labelled Markov chains (LMCs) whose transition probabilities may be perturbed or estimated by sampling. It defines approximate quotients through exact bisimilarity of a nearby perturbed model and gives polynomial-time minimisation algorithms. The experiments test whether the quotient structure of an unperturbed LMC can be recovered from sampled or perturbed transition laws.

Official source code declared by the publication:

- repository: `qiyitang71/approximate-quotienting`
- pinned commit: `6d4ea07894e92e8d1987031a1240248da4cb24d6`
- repository record: `https://github.com/qiyitang71/approximate-quotienting`

The pinned README states that both implemented algorithms take an approximation LMC `M_epsilon` and an error parameter `epsilon_2`. It provides `runSmall.sh` and `runLarge.sh`, evaluates PRISM-derived LMCs, and generates five approximate LMCs for each error configuration.

## What the prior art establishes

The audited work establishes an important positive result that was missing from C073's exact-oracle-only boundary:

> Finite-sample or perturbed transition estimates do not automatically make quotient recovery hopeless. Under an LMC observation model and an appropriate perturbation tolerance, approximate partition refinement can recover the structure of the original exact bisimulation quotient in evaluated cases, with formal perturbation guarantees for the approximate quotient notion.

Therefore the following claims are removed from possible novelty:

- that any low-probability unobserved transition makes approximate quotient recovery categorically impossible;
- that only a complete exact transition matrix can support a useful bisimulation quotient;
- that sampling-based approximate partition refinement is a new causal-grounding mechanism;
- that recognising a latent quotient after small transition perturbations is itself new.

C073's counterexample remains valid as a statement about unrestricted finite samples: two models may fit the same finite data and have different exact quotients. C074 refines that statement: recovery becomes possible only after adding an explicit perturbation/statistical observation contract and accepting an approximate-quotient target.

## Assumption and guarantee comparison

| Object | Kiefer–Tang implementation | LBQ001 finite-sample B4 requirement |
|---|---|---|
| Controlled model | labelled Markov chain | action-conditioned MDP or controlled history-state model |
| Input uncertainty | sampled/perturbed successor distribution with chosen error tolerance | finite trajectories with action, all preregistered consequences, and uncertainty accounting |
| Retained labels | fixed LMC labels | complete non-semantic consequence signature, including sensor, cost, action availability, terminal consequence, and held-out channels |
| Output | approximate LMC quotient | estimator of the Storm B4 MDP quotient |
| Action-conditioned branching | absent in the paper's implementation contract | mandatory |
| Unknown state/history representation | not addressed | may be required by the benchmark observation contract |
| Direct partition metrics against exact oracle | quotient-size/structure experiments | ARI, AMI, pairwise F1, VI, block-count error |
| Three-seed resource bundle | five perturbations are described, but not LBQ001 seeds/resources | mandatory seeds `17 / 29 / 43`, model bytes, RSS, time, digests |
| Identifies `Q` or `d` | no | no; only supplies language-blind `P` estimate |

## Suitability decision

The official implementation is admissible as:

> **B4-LMC finite-sample/perturbation diagnostic and prior-art reference**

It is not admissible as:

> **the principal LBQ001 finite-sample B4 estimator for controlled MDPs**

The mismatch is structural rather than cosmetic. An MDP quotient requires comparison of successor mass for every action and preservation of action availability. Marginalising actions into an LMC can merge states whose controlled laws differ.

## Counterexample: LMC reduction can erase the B4 distinction

Consider states `s` and `t`, actions `a` and `b`, and terminal consequence-labelled states `x` and `y`.

- From `s`: action `a` reaches `x` with probability 1 and action `b` reaches `y` with probability 1.
- From `t`: action `a` reaches `y` with probability 1 and action `b` reaches `x` with probability 1.
- `x` and `y` have different preregistered physical consequence labels.

Under the action-conditioned B4 MDP law, `s` and `t` are not bisimilar: the consequences differ for each fixed action.

Now erase the action identity and form an LMC using a uniform behaviour policy. Both `s` and `t` then transition to `x` and `y` with probability `1/2` each. Their LMC successor distributions are identical, so an LMC quotient may merge them perfectly even with infinite data and zero transition-estimation error.

Therefore:

> Perfect finite-sample recovery of the action-marginal LMC quotient does not imply recovery of the controlled B4 quotient.

The same failure occurs when action availability is part of the consequence signature but is omitted from the LMC label.

## Consequence for RQ-001

This candidate does not identify raw-language equivalence `Q`, target denotation `d`, or external semantic orientation. Its useful role is narrower:

1. it supplies an official sampling/perturbation baseline for quotient recovery in the uncontrolled LMC special case;
2. it provides a lower-complexity diagnostic for whether the data-generation and partition metrics can detect approximate quotient recovery;
3. it prevents the project from misclassifying all finite-sample quotient estimation as unresolved;
4. it does not close the controlled finite-sample B4 gate.

## Public-code reproducibility audit

Confirmed at the pinned repository state:

- official paper-linked repository;
- exact commit pin;
- Java implementation;
- small- and large-model shell entry points;
- PRISM-derived model list;
- explicit perturbation/error grids;
- five generated approximations per original LMC and error setting;
- public experimental-results link.

Not yet frozen for this branch:

- Java runtime version;
- build/dependency lock;
- immutable container;
- canonical command manifest without manual script editing;
- input-model and output-result digests;
- model size and peak RSS instrumentation;
- exact wall time;
- LBQ001 seeds `17 / 29 / 43`;
- direct ARI/AMI/pairwise-F1/VI scoring against the Storm oracle;
- an MDP/action-conditioned extension covered by the cited theorem and official code.

No execution was started in this run.

## Decision

**NARROWED: A PUBLIC FINITE-SAMPLE APPROXIMATE-QUOTIENT ESTIMATOR EXISTS FOR LABELLED MARKOV CHAINS, BUT IT DOES NOT SATISFY THE ACTION-CONDITIONED LBQ001-B4 CONTRACT — NOT ADOPTED.**

The three-part gate is refined to four explicit references:

1. DeepMDP B3 reward/transition control;
2. Storm exact-model B4 MDP oracle;
3. Kiefer–Tang approximate-quotienting as an LMC finite-sample diagnostic;
4. a still-missing public finite-sample estimator for the full action-conditioned B4 quotient.

## Next admissible work

1. audit public MDP-specific approximate-bisimulation/state-aggregation estimators with finite-sample guarantees and official code;
2. reject candidates that only learn reward-relative metrics, deterministic-only similarities, or action-marginal LMC quotients;
3. if no candidate satisfies the contract, document the exhausted candidate matrix rather than silently implementing a new estimator;
4. separately freeze the DeepMDP compatibility manifest and Storm oracle input format;
5. begin numerical execution only after an existing estimator is selected or the no-fit result is preregistered.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Official public-code audit: completed.
- Identifiability/scope counterexample: completed.
- LMC finite-sample approximate quotienting: existing prior art.
- Action-conditioned finite-sample B4 estimator: still pending.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
