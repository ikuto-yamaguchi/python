# Causal Identifiability Audit C078

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code suitability audit, and (d) an identifiability/applicability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C077 sharpened the missing language-blind B4 estimator to the following epistemic output for each candidate state pair:

- `merge` if every point MDP in the simultaneous confidence set places the pair in the same exact Storm B4 block;
- `separate` if every point MDP in the confidence set separates the pair;
- `unidentified` otherwise.

C078 audits whether existing parametric probabilistic model checking and parameter synthesis can provide that all/none classification without a new architecture.

The strongest obvious public candidate is the parametric engine in Storm (`storm-pars`), together with the parameter-synthesis literature represented by Junges et al., *Parameter synthesis for Markov models: covering the parameter space* and the associated Storm/PROPhESY tool line.

## Primary prior art

Primary references:

- Sebastian Junges, Erika Ábrahám, Christian Hensel, Nils Jansen, Joost-Pieter Katoen, Tim Quatmann, and Matthias Volk, *Parameter synthesis for Markov models: covering the parameter space*, Formal Methods in System Design 62, 2024.
- Nils Jansen, Sebastian Junges, and Joost-Pieter Katoen, *Parameter Synthesis in Markov Models: A Gentle Survey*, 2022.
- Tim Quatmann, Christian Dehnert, Nils Jansen, Sebastian Junges, and Joost-Pieter Katoen, *Parameter Synthesis for Markov Models: Faster Than Ever*, ATVA 2016.
- Christian Dehnert et al., *PROPhESY: A PRObabilistic ParamEter SYnthesis Tool*, CAV 2015.

The existing theory and tools already support, for parametric DTMCs and pMDPs:

- proving that all parameter valuations in a region satisfy a supplied temporal/reward property;
- proving that no valuation in a region satisfies it;
- partitioning parameter space into accepting, rejecting, and inconclusive regions;
- computing rational solution functions for selected quantitative properties;
- feasibility search and approximate parameter-space coverage;
- parameter lifting and monotonicity analyses under published assumptions.

Therefore the following claims are removed from possible novelty:

- that universal/existential quantification over a transition-parameter region is absent from probabilistic model checking;
- that an SMT or region-splitting backend for Markov-model parameters must be invented;
- that a confidence set cannot be represented as a parametric probabilistic model;
- that three-way region classification is itself new;
- that symbolic rational transition functions cannot be analysed by a public tool.

## Exact public implementation pin

Existing Storm pin retained:

- repository: `stormchecker/storm`;
- commit: `80a18e088a0d627befe2e3667b000672c0bc43d5`;
- parametric CLI entry point: `src/storm-pars-cli/storm-pars.cpp`.

At this commit, the parametric CLI imports and dispatches functionality for:

- feasibility;
- region verification;
- parameter-space partitioning;
- solution functions;
- sampling;
- monotonicity;
- parametric DTMC and MDP simplification.

The file also applies ordinary bisimulation as a preprocessing transformation when requested. This establishes that parametric analysis and bisimulation preprocessing coexist in the public codebase.

It does not establish that Storm synthesises the parameter valuations for which a candidate pair belongs to the greatest full-consequence bisimulation relation.

## Assumption, object, and guarantee comparison

| Object | Existing parameter synthesis | Required LBQ001 three-valued B4 estimator |
|---|---|---|
| Input model | pMC/pMDP with rational transition functions over named parameters | simultaneous statistical confidence set over every action/consequence row |
| Query | supplied PCTL/reward/quantitative property | membership of a pair in the greatest full-consequence bisimulation quotient |
| Region answer | all valuations satisfy, all violate, or mixed/unknown for that property | all point MDPs merge, all separate, or both possibilities remain |
| Relation | property is fixed before synthesis | candidate equivalence relation is itself unknown and valuation-dependent |
| Partition | parameter-space partition for one property | state-space quotient for every compatible point MDP |
| Consequences | labels/rewards encoded in the model and property | all preregistered codebook-independent sensors, costs, availability, terminal and held-out consequences |
| Statistical meaning | none unless a confidence construction is supplied externally | simultaneous coverage and declared error probability are mandatory |
| Semantic output | no `Q` or `d` | language-blind `P` only; `Q,d` remain later gates |

## Central obstruction: the greatest bisimulation is not a fixed property template

For a fixed candidate equivalence relation `R`, probabilistic bisimulation can be written as equality constraints over transition mass into each `R`-block, plus equality of retained consequences.

For a point MDP `M_theta`, a pair `(s,t)` belongs to the greatest bisimulation relation only if there exists a stable relation containing the pair. The stable relation may change as `theta` changes.

Hence the desired predicate is structurally of the form:

> for every `theta` in confidence region `Theta`, there exists a greatest stable partition `Pi_theta` such that `s` and `t` share a block.

The relation or partition is not fixed before parameter synthesis. A standard Storm parameter-verification query instead fixes a formula first and asks which valuations satisfy that formula.

Encoding equality relative to one preregistered partition `Pi` answers only:

> are the transition/consequence constraints for this particular `Pi` valid throughout the region?

It does not answer whether another coarser or finer stable partition exists for each valuation, nor whether `(s,t)` lies in the greatest quotient for every valuation.

## Counterexample 1: one fixed candidate partition gives the wrong universal answer

Consider states `s`, `t`, and successor states `x`, `y` with distinct retained physical labels. Let a parameter `p` range over `[0,1]`.

- from `s`, action `a` reaches `x` with probability `p` and `y` with probability `1-p`;
- from `t`, action `a` reaches `x` with probability `1-p` and `y` with probability `p`.

Because `x` and `y` have distinct retained consequences, `s` and `t` are bisimilar exactly when `p = 1/2`.

A parameter-synthesis query can detect the equality condition for the fixed successor partition `{x},{y}`. But the LBQ001 output over a confidence interval containing `1/2` and another value is `unidentified`, since compatible point models include both merge and separate cases.

Checking only a nominal point gives either merge or separate. Checking only whether the equality can hold gives existential merge. Checking only whether it holds throughout gives non-universal merge. The required three-way output needs both universal and existential results tied to the greatest quotient.

## Counterexample 2: the stable partition changes with the parameter valuation

Let successor states `x` and `y` have the same retained consequence labels, but parameter-dependent outgoing transitions:

- at `p = 0`, `x` and `y` are behaviorally identical and may merge;
- at `p > 0`, a held-out physical consequence reachable from `x` but not `y` makes them distinct.

Now the correct partition used to test `s` versus `t` changes with `p`.

A formula generated from the partition valid at `p = 0` is unsound for `p > 0`. A formula generated from the finer partition for `p > 0` can be unnecessarily restrictive at `p = 0`.

Thus the B4 decision cannot generally be reduced to one fixed collection of rational equalities without also solving the valuation-dependent partition problem.

## Counterexample 3: topology changes break graph-preserving shortcuts

Confidence regions commonly include zero-probability boundaries for poorly sampled transitions. At such boundaries, the support graph can change.

Storm's parametric workflow explicitly distinguishes graph-preserving assumptions and warns when parameter regions intersect values such as `0` or `1`. Bisimulation classes can change discontinuously when an edge appears or disappears.

A graph-preserving parameter-lifting proof over an interior region cannot automatically certify the quotient on a confidence set that includes topology-changing boundaries. Excluding those boundaries would be statistically invalid unless the confidence construction itself proves a positive lower bound.

## Complexity and enumeration boundary

One generic reduction would enumerate candidate state partitions, encode each partition's stability constraints, and use parameter synthesis to determine where each is valid.

This is not a new architecture in the neural sense, but it is not an existing pinned end-to-end B4 estimator either. The number of set partitions is the Bell number, and candidate relations interact with MDP actions, retained consequences, zero-probability topology changes, and greatest-fixed-point selection.

Even after enumeration, the implementation must still:

1. select the greatest stable quotient for each valuation;
2. quantify whether the queried pair merges in all, none, or some compatible valuations;
3. preserve dependencies among confidence parameters rather than replacing them with an invalid Cartesian box;
4. account for simultaneous statistical coverage;
5. return abstention for unresolved regions.

Parameter synthesis is an admissible backend component, not by itself the missing pipeline.

## Public-code no-fit result

### Storm `storm-pars`

Admissible as:

- public parametric DTMC/pMDP analysis backend;
- region verification, feasibility, partitioning, and solution-function engine;
- possible solver component for fixed candidate constraints.

Not confirmed as:

- synthesis of valuations for greatest-bisimulation membership;
- automatic enumeration of valuation-dependent quotients;
- all/none classification for a state pair over a statistical confidence set;
- simultaneous multinomial confidence construction;
- full-consequence B4 encoding and leakage audit;
- `merge`/`separate`/`unidentified` output relative to the exact Storm point-model quotient.

### PROPhESY tool line

Admissible as:

- prior-art evidence for SMT-backed safe/unsafe parameter regions and rational-function analysis.

Not confirmed in this run as:

- a currently pinned immutable public implementation of greatest-bisimulation parameter synthesis;
- a direct B4 partition estimator;
- a statistical confidence-to-quotient pipeline.

## Consequence for RQ-001

The language-blind target side is narrowed again.

It is no longer defensible to claim that universal/existential analysis over confidence-region parameters is missing. Existing parameter-synthesis systems provide powerful parts of that machinery.

The remaining gap is specifically:

> an executable, pinned reduction from simultaneous full-consequence confidence sets to valuation-dependent greatest-bisimulation membership, with universal and existential quantification, topology-change handling, and explicit abstention.

Even if this gap is closed, it identifies only the language-blind behavioral target quotient `P`. It does not establish raw-language equivalence `Q`, denotation `d`, external semantic orientation, or novelty of joint identification.

## Decision

**NARROWED: PARAMETRIC MARKOV-MODEL VERIFICATION AND REGION SYNTHESIS ALREADY PROVIDE UNIVERSAL/EXISTENTIAL PROPERTY ANALYSIS, BUT THE SUPPLIED PROPERTY IS FIXED WHILE THE GREATEST FULL-CONSEQUENCE BISIMULATION QUOTIENT IS PARAMETER-DEPENDENT; PINNED STORM-PARS IS A POSSIBLE BACKEND, NOT THE REQUIRED THREE-VALUED B4 PARTITION ESTIMATOR — NOT ADOPTED.**

The baseline stack is refined to:

1. DeepMDP B3 reward/transition control;
2. Storm exact complete-point-MDP B4 oracle;
3. Kiefer–Tang finite-sample/perturbed LMC diagnostic;
4. Tao–Xu–You action-conditioned finite-sample metric theory;
5. Dadashi/PLOFF offline support pseudometric diagnostic;
6. Hashemi et al. IMDP bisimulation theorem reference;
7. Storm/PROPhESY parameter-synthesis backend reference;
8. still missing: a pinned executable reduction that quantifies greatest full-consequence quotient membership across every confidence-consistent point MDP and returns `merge`, `separate`, or `unidentified`.

## Next admissible work

1. audit symbolic probabilistic-bisimulation and SMT tools for direct synthesis of parameter valuations under which a pair belongs to a greatest bisimulation;
2. determine whether an existing partition-refinement algorithm over semialgebraic parameter regions avoids explicit Bell-number partition enumeration;
3. produce an exact-commit no-fit matrix for Storm `storm-pars`, PRISM parametric checking, PROPhESY, and probabilistic-bisimulation synthesis prototypes;
4. preregister a statistically valid simultaneous multinomial/polytope confidence construction, including zero-count actions and topology-changing boundaries;
5. freeze a codebook-independent full-consequence model encoding compatible with the exact Storm oracle;
6. do not execute numerical experiments until exact commands, seeds `17 / 29 / 43`, model bytes, peak RSS, wall time, dataset digest, result digest, coverage, and abstention output are fixed.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code suitability audit: completed.
- Identifiability/applicability counterexamples: completed.
- Parametric Markov-model universal/existential property analysis: existing prior art.
- Greatest-bisimulation membership as a fixed supplied property: rejected in general.
- Storm `storm-pars` as a backend component: retained.
- Storm `storm-pars` as end-to-end three-valued B4 estimator: not established.
- Pinned executable greatest-bisimulation parameter-synthesis pipeline: not selected.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
