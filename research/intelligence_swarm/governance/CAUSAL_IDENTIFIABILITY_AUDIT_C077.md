# Causal Identifiability Audit C077

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code suitability audit, and (d) an identifiability/applicability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C076 left the following admissible gate:

> Can an existing public pipeline estimate state-action transition confidence regions, preserve action identity and all preregistered non-semantic consequences, and then return `merge`, `separate`, or `unidentified` relative to the exact-model Storm B4 quotient without creating a new architecture?

C077 audits the strongest obvious composition:

1. construct an interval Markov decision process (IMDP) from empirical transition confidence intervals;
2. compute an IMDP bisimulation quotient;
3. interpret that quotient as the finite-sample B4 target partition.

## Primary prior art

Primary papers:

- Vahid Hashemi, Holger Hermanns, Lei Song, K. Subramani, Andrea Turrini, and Piotr Wojciechowski, *Compositional Bisimulation Minimization for Interval Markov Decision Processes*, LATA 2016, DOI `10.1007/978-3-319-30000-9_9`.
- Vahid Hashemi, Andrea Turrini, Ernst Moritz Hahn, Holger Hermanns, and Khaled Elbassioni, *Polynomial-Time Alternating Probabilistic Bisimulation for Interval MDPs*, SETTA 2017, DOI `10.1007/978-3-319-69483-2_2`.

The 2016 work defines probabilistic bisimulation for IMDPs by comparing, after quotienting by a candidate relation, the convex sets of feasible successor distributions. General checking/minimisation is coNP-complete, with polynomial cases under additional conditions.

The 2017 work defines an alternating probabilistic bisimulation for competitive controller-versus-uncertainty semantics, proves preservation of relevant probabilistic temporal properties, and gives a polynomial-time computation based on the special polytope structure.

Therefore the central correction is:

> Bisimulation minimisation for action-bearing interval MDPs is existing prior art; uncertainty-valued transition models do not by themselves require a new quotient architecture.

The following claims are removed from possible novelty:

- that interval-valued transition uncertainty cannot be included in an action-conditioned bisimulation;
- that convex uncertainty sets cannot be compared at the quotient level;
- that IMDP minimisation is absent from formal verification;
- that competitive controller/uncertainty semantics has no bisimulation theory;
- that exact point probabilities are universally required before a quotient can be computed.

## Assumption, object, and guarantee comparison

| Object | IMDP bisimulation prior art | LBQ001 finite-sample B4 requirement |
|---|---|---|
| Input | an already constructed finite IMDP with interval transition constraints | sampled controlled trajectories plus a preregistered confidence construction |
| Actions | explicit action/nondeterministic choices | every admissible action identity must be retained; missing coverage must be reported |
| Uncertainty | feasible transition polytopes supplied as model data | statistical confidence sets that cover the unknown true kernel with declared probability |
| Consequences | atomic propositions and selected rewards/labels supplied to the initial partition | all codebook-independent sensors, costs, availability, terminal and held-out consequences |
| Output | equivalence/minimisation of the supplied uncertainty model | `merge`, `separate`, or `unidentified` for the unknown true B4 partition |
| Preservation target | PCTL/PCTL-like properties under the chosen uncertainty semantics | direct agreement with the complete-model Storm quotient, with abstention under ambiguity |
| Statistical guarantee | not supplied merely by the bisimulation theorem | finite-sample coverage, family-wise confidence accounting, and margin/stability contract |
| Semantic object | no `Q` or `d` recovery | language-blind `P` only; `Q,d` remain separate later gates |

## Key distinction: ambiguity-model equivalence is not true-model identification

An IMDP represents a set of admissible transition kernels. Its bisimulation asks whether states are equivalent relative to the whole uncertainty structure and the selected uncertainty semantics.

LBQ001 asks a different question:

> What is the bisimulation/full-consequence partition of the single unknown true MDP that generated the data?

These objects coincide only under additional conditions. A correct quotient of a confidence-set model can be more conservative or differently structured than the quotient of the unknown point model.

## Counterexample 1: truly equivalent states can be separated by unequal confidence sets

Let true states `s` and `t` have exactly the same action-conditioned transition and full-consequence law. Suppose the behaviour process visits `s` often and `t` rarely.

For one action and one successor block, valid finite-sample confidence intervals may be:

- at `s`: `[0.48, 0.52]`;
- at `t`: `[0.20, 0.80]`.

Both intervals contain the same true probability `0.5`, so the unknown true MDP places `s,t` in the same B4 block.

However, the supplied uncertainty polytopes are not equal. An IMDP bisimulation based on equality/matching of feasible quotient distributions can separate the states because the uncertainty models differ.

Therefore:

> Separation in the confidence-set IMDP can reflect unequal information, not a true behavioral distinction.

Interpreting every IMDP split as `separate` would create false semantic/target distinctions caused solely by sample-count imbalance.

## Counterexample 2: identical confidence sets do not prove true equivalence

Let the confidence construction return the same broad interval polytope for `s` and `t`, for example `[0,1]` over a binary successor consequence, because both state-action pairs are weakly sampled.

Two point MDPs are compatible with the same supplied IMDP:

1. model A: `s` and `t` have identical true transition laws and are B4-equivalent;
2. model B: `s` reaches consequence `x` with probability `0.1` while `t` reaches it with probability `0.9`, so they are not B4-equivalent.

The interval model and its IMDP quotient are identical in both cases. Hence an IMDP merge cannot be interpreted as identification of the true point-model merge.

Therefore:

> Equality of ambiguity sets is not sufficient evidence that the unknown true kernels are equal.

## Counterexample 3: overlap is not a three-valued identification rule

For two state-action rows with confidence sets `C_s` and `C_t`, mere overlap does not determine the partition:

- some pairs of kernels in `C_s × C_t` may be quotient-equivalent;
- other pairs may be quotient-distinct.

This is exactly the `unidentified` case required by LBQ001. Standard IMDP bisimulation minimisation does not automatically return the epistemic three-way classification:

- `merge`: all statistically admissible true models force equivalence;
- `separate`: all statistically admissible true models force distinction;
- `unidentified`: both possibilities remain.

Computing this classification requires quantification over the joint confidence set and consistency constraints, not only minimisation of one interval model under its operational uncertainty semantics.

## Confidence-set construction is an additional theorem obligation

Even a correct IMDP bisimulation implementation does not establish that empirical intervals form a simultaneous confidence region for the true MDP.

A valid finite-sample B4 pipeline must separately freeze:

1. state-action coverage assumptions;
2. interval or polytope construction;
3. dependence handling from multinomial rows;
4. family-wise or simultaneous coverage across all rows and consequences;
5. treatment of zero-count actions;
6. consequence-channel confidence accounting;
7. a separation/margin rule for converting uncertainty into a partition decision;
8. explicit abstention when the rule cannot decide.

Independent coordinate-wise intervals may also admit probability combinations inconsistent with the simplex or ignore shared-parameter dependencies. This can enlarge the uncertainty set and change the quotient.

## Public-code suitability audit: Storm

Existing canonical pin retained from C073:

- repository: `stormchecker/storm`;
- commit: `80a18e088a0d627befe2e3667b000672c0bc43d5`;
- exact-model API: `src/storm/api/bisimulation.h`.

Storm supports interval and parametric models in its broader modelling/model-checking ecosystem and its DRN format can encode interval models. This does not imply that the pinned bisimulation implementation accepts interval-valued sparse MDPs.

At the pinned commit, `src/storm/storage/bisimulation/BisimulationDecomposition.cpp` explicitly instantiates the decomposition for:

- `storm::models::sparse::Dtmc<double>`;
- `storm::models::sparse::Ctmc<double>`;
- `storm::models::sparse::Mdp<double>`.

The implementation compares exact numeric transition/reward data for those instantiated model types. No paper-specific IMDP alternating-bisimulation executable, command, or interval-valued decomposition instantiation was confirmed in the pinned Storm path.

Thus Storm remains admissible as:

> **the exact complete-point-model B4 oracle**

but is not yet established as:

> **an executable empirical-confidence IMDP bisimulation plus epistemic abstention pipeline**.

The 2017 paper reports prototype implementations, but this run did not confirm an accessible author-managed immutable repository and commit implementing the published alternating IMDP algorithm.

## Suitability decision

IMDP bisimulation prior art is admissible as:

> **the theorem reference showing that action-conditioned uncertainty-model quotienting already exists**.

It is not admissible, without further statistical and epistemic machinery, as:

> **the missing LBQ001 finite-sample estimator of the unknown true full-consequence partition**.

The proposed composition `empirical confidence intervals -> IMDP bisimulation -> partition` fails the contract because:

1. unequal confidence widths can split truly equivalent states;
2. equal/broad confidence sets can merge states whose true kernels differ;
3. standard IMDP equivalence concerns the supplied ambiguity model, not all/none quantification for true-model identification;
4. confidence validity and simultaneous coverage are external obligations;
5. the pinned Storm bisimulation code path is an exact `double` point-model implementation, not a confirmed IMDP alternating-bisimulation executable;
6. no `Q` or `d` is identified.

## Consequence for RQ-001

This run narrows only the language-blind target side.

The remaining admissible B4 estimator specification is now sharper:

- construct a simultaneous codebook-independent confidence set for the complete action/consequence law;
- compare all point MDPs consistent with that set;
- return `merge` only when every consistent MDP places a pair in the same Storm B4 block;
- return `separate` only when every consistent MDP separates the pair;
- otherwise return `unidentified`;
- verify monotonicity as data increase and confidence sets contract;
- never interpret uncertainty-width differences as target semantics.

This may be computationally expensive. Complexity or implementation inconvenience does not justify replacing the all/none rule with ordinary IMDP minimisation.

## Decision

**NARROWED: INTERVAL-MDP BISIMULATION IS EXISTING PRIOR ART, BUT BISIMULATION OF A SUPPLIED CONFIDENCE-SET MODEL DOES NOT IDENTIFY THE UNKNOWN TRUE B4 PARTITION; THE PINNED STORM PATH IS AN EXACT POINT-MODEL ORACLE, NOT THE REQUIRED THREE-VALUED EMPIRICAL PIPELINE — NOT ADOPTED.**

The baseline stack is refined to:

1. DeepMDP B3 reward/transition control;
2. Storm exact complete-point-MDP B4 oracle;
3. Kiefer–Tang finite-sample/perturbed LMC diagnostic;
4. Tao–Xu–You action-conditioned finite-sample metric theory;
5. Dadashi/PLOFF offline support pseudometric diagnostic;
6. Hashemi et al. IMDP bisimulation theorem reference;
7. still missing: a pinned executable that constructs simultaneous full-consequence confidence sets and returns `merge`, `separate`, or `unidentified` for the true-point-model quotient.

## Next admissible work

1. audit robust/uncertain probabilistic-model tools for universal and existential equivalence checks across a confidence set, rather than ordinary IMDP minimisation;
2. determine whether parameter synthesis or SMT over paired candidate quotient constraints can supply the all/none classification without a new architecture;
3. document a no-fit matrix for Storm, PRISM, and available IMDP prototype tools at exact commits;
4. preregister simultaneous multinomial confidence regions and zero-count-action abstention;
5. keep consequence channels independent of language, target IDs, parser slots, simulator names, rewards derived from semantic labels, and evaluator codebooks;
6. start no numerical experiment until exact commands, seeds `17 / 29 / 43`, model bytes, peak RSS, wall time, dataset digest, result digest, coverage, and abstention output are frozen.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code suitability audit: completed.
- Identifiability/applicability counterexamples: completed.
- Action-conditioned IMDP bisimulation: existing prior art.
- Confidence-set-model quotient equals true-model quotient: rejected without additional conditions.
- Storm exact complete-model B4 oracle: retained.
- Pinned executable IMDP alternating-bisimulation path: not confirmed.
- Three-valued true-partition estimator: not selected.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
