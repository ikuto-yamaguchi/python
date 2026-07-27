# Causal Identifiability Audit C079

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) an applicability/identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C078 established that ordinary parametric Markov-model synthesis treats the queried property as fixed, whereas membership in a greatest full-consequence bisimulation quotient is valuation-dependent.

The next question is whether this overstates the gap: has prior work already synthesised the bisimulation relation itself, rather than requiring a human-supplied candidate relation?

## Primary prior art

Primary sources:

- Chih-Duo Hong, Anthony W. Lin, Rupak Majumdar, and Philipp Rümmer, *Probabilistic Bisimulation for Parameterized Systems (with Applications to Verifying Anonymous Protocols)*, CAV 2019, DOI `10.1007/978-3-030-25540-4_27`.
- Chih-Duo Hong, Anthony W. Lin, Philipp Rümmer, and Rupak Majumdar, *Probabilistic Bisimulation for Parameterized Anonymity and Uniformity Verification*, IEEE Transactions on Software Engineering 51(6), 2025; preprint `arXiv:2505.09963`.
- Technical report `arXiv:2011.02413`.

These works address parameterized probabilistic systems: infinite families of finite-state systems indexed by a size parameter such as the number of protocol participants.

Their framework:

- specifies systems and candidate probabilistic bisimulation relations in a decidable first-order theory of regular structures;
- encodes proof obligations for probabilistic bisimulation;
- checks the candidate relation automatically;
- uses automata-learning techniques to synthesise candidate regular bisimulation relations for the reported anonymity and uniformity case studies.

Therefore, the following broad claims are removed from possible novelty:

- that probabilistic bisimulation relations always have to be manually supplied;
- that greatest-equivalence-style relation synthesis has no prior art;
- that automata learning cannot be combined with deductive probabilistic-bisimulation checking;
- that a symbolic relation over an infinite family of finite probabilistic systems cannot be learned automatically;
- that automated relation synthesis plus theorem checking is absent from public formal-methods research.

## Correction to C078

C078 stated the obstruction as: existing parameter synthesis fixes the property before synthesis, while the desired greatest relation is unknown.

That remains correct for the audited Storm/PROPhESY parameter-region workflow, but it is not a universal statement about all formal methods.

Hong et al. show that a candidate probabilistic bisimulation relation can be generated automatically by a learner and then discharged against logical proof rules. Thus:

> unknown-relation synthesis itself is existing prior art under a regular-relation hypothesis class and a suitable verification/learning interface.

The remaining B4 gap must be stated more narrowly.

## Assumption, object, and guarantee comparison

| Object | Hong et al. relation synthesis | Required LBQ001 three-valued B4 estimator |
|---|---|---|
| Parameterization | system size / regular configurations | uncertain numerical transition and consequence laws from finite samples |
| State space | infinite family represented by regular structures | fixed finite target/state set with a simultaneous confidence set |
| Relation class | regular relation representable by the learner | greatest full-consequence probabilistic bisimulation for each point MDP |
| Synthesis signal | verification counterexamples / learning queries | statistical observations and confidence-consistent point models |
| Guarantee | learned candidate satisfies encoded bisimulation proof obligations | pair merges in all, separates in all, or differs across compatible point MDPs |
| Quantification | all system sizes/configurations represented by the regular theory | all numerical valuations in the statistical confidence set |
| Greatest relation | not the central reported guarantee; a proving relation sufficient for the target property | exact greatest quotient membership is the requested output |
| Consequence channels | protocol observations needed for anonymity/uniformity | all preregistered codebook-independent sensors, costs, availability, terminal and held-out consequences |
| Statistics | no finite-sample confidence construction | simultaneous coverage and abstention are mandatory |
| Semantic output | no `Q` or `d` | language-blind `P` only; `Q,d` remain later gates |

## Central boundary: proof-relation synthesis is not confidence-set quotient identification

A learned bisimulation witness can be sufficient to prove a property without being the greatest bisimulation relation.

For B4, the requested pairwise output is defined by the exact greatest quotient of every point MDP in the confidence set:

- `merge` if the pair is in the greatest quotient for every compatible point MDP;
- `separate` if it is outside the greatest quotient for every compatible point MDP;
- `unidentified` otherwise.

A learner that finds one valid relation containing a pair establishes existential witness information for a particular model or symbolic family. Failure to find such a relation does not establish non-bisimilarity unless the hypothesis class and learning procedure are complete for all valid relations. Likewise, a proving relation that omits a bisimilar pair is still a valid bisimulation relation but does not recover the greatest quotient.

## Counterexample 1: a valid learned relation can under-approximate the greatest quotient

Let a point MDP have four states `s,t,x,y`, with `s` and `t` behaviorally identical and `x` and `y` behaviorally identical.

The greatest bisimulation has blocks `{s,t}` and `{x,y}`.

However, the identity relation is also a valid probabilistic bisimulation. A verifier accepts it, and a learner optimised only to find a sufficient proof witness may return it.

Thus:

- verification succeeds;
- the relation is sound;
- the greatest quotient is not recovered;
- direct partition metrics against Storm B4 can be wrong.

Therefore automated synthesis of a valid bisimulation witness does not by itself satisfy the B4 partition-recovery contract.

## Counterexample 2: hypothesis-class incompleteness confounds `separate`

Suppose two states are bisimilar, but every regular relation in the learner's current hypothesis class either omits the pair or violates another proof obligation.

The learner may fail to produce a witness containing the pair even though a valid non-regular or larger regular representation exists.

Interpreting learner failure as `separate` is unsound.

For the required three-valued output, `separate` needs a proof that no bisimulation relation can contain the pair for any compatible point model, not merely that the selected learner failed.

## Counterexample 3: size-parameter universality does not quantify transition uncertainty

Consider the C078 family where `s` reaches physical outcome `x` with probability `p` and `t` reaches it with probability `1-p`.

A regular relation learner may reason uniformly over every system size `n`, but if `p` is left as an uncertain statistical parameter, the pair merges only at `p=1/2`.

A confidence interval containing `1/2` and another value still requires `unidentified`.

Universality over `n` does not imply universality over the statistical confidence region for `p`.

## Counterexample 4: anonymity equivalence is not full-consequence B4

A relation sufficient to prove that two protocol executions expose the same public observation can intentionally abstract away internal physical or diagnostic consequences.

Two states may be equivalent for anonymity but differ on a preregistered independent sensor, cost, action availability, or held-out consequence.

Such a relation is valid for the security property yet too coarse for LBQ001-B4.

Thus the retained observation/consequence signature must be fixed before relation synthesis and audited for semantic leakage.

## Public-code availability audit

The primary CAV paper, technical report, and 2025 TSE extension are publicly accessible.

The papers report automated synthesis using standard automata-learning components and decidable first-order reasoning. In this run, no paper-specific immutable public repository and exact commit implementing the full reported pipeline was confirmed through the connected GitHub search or the authors' publication pages.

Classification:

> primary theorem and automated-synthesis method are public; a paper-specific immutable executable baseline was not pinned in this run.

This is a provenance limitation, not evidence that the method does not exist.

## No-fit result for the current B4 gate

Hong et al. are admissible as:

- prior-art evidence that unknown probabilistic bisimulation relations can be synthesised automatically;
- a theorem/assumption reference for learner-plus-verifier relation synthesis;
- a warning that C078's fixed-property obstruction is backend-specific, not universal.

They are not confirmed as:

- a finite-sample estimator from trajectories;
- a simultaneous multinomial confidence-set constructor;
- a solver for greatest quotient membership over every numerical valuation;
- a complete `merge` / `separate` / `unidentified` classifier;
- a full-consequence Storm-compatible partition producer;
- a public immutable executable baseline with seeds and resource instrumentation.

## Consequence for RQ-001

The language-blind target-side gap is narrowed again.

It is no longer defensible to claim that relation synthesis is missing in general. Existing work learns symbolic probabilistic bisimulation witnesses for parameterized systems.

The remaining gap is specifically:

> a pinned executable procedure that is complete for greatest full-consequence quotient membership, quantifies over every statistically compatible numerical point MDP, distinguishes universal merge from universal separation and mixed cases, handles topology changes, and abstains when finite data are insufficient.

Even closing this gap identifies only language-blind behavioral `P`. It does not establish raw-language equivalence `Q`, denotation `d`, external semantic orientation, or novelty of their joint identification.

## Decision

**NARROWED BEYOND AUTOMATED REGULAR PROBABILISTIC-BISIMULATION RELATION SYNTHESIS: UNKNOWN-RELATION LEARNING IS PRIOR ART, BUT A SOUND WITNESS RELATION IS NOT NECESSARILY THE GREATEST FULL-CONSEQUENCE QUOTIENT, LEARNER FAILURE DOES NOT PROVE SEPARATION, AND SIZE-PARAMETER UNIVERSALITY DOES NOT PROVIDE STATISTICAL CONFIDENCE-SET QUANTIFICATION — NOT ADOPTED.**

The baseline stack is refined to:

1. DeepMDP B3 reward/transition control;
2. Storm exact complete-point-MDP B4 oracle;
3. Kiefer–Tang finite-sample/perturbed LMC diagnostic;
4. Tao–Xu–You action-conditioned finite-sample metric theory;
5. Dadashi/PLOFF offline support pseudometric diagnostic;
6. Hashemi et al. IMDP bisimulation theorem reference;
7. Storm/PROPhESY parameter-synthesis backend reference;
8. Hong et al. regular probabilistic-bisimulation relation-synthesis theorem reference;
9. still missing: a pinned executable and statistically complete greatest-full-consequence three-valued B4 estimator.

## Next admissible work

1. inspect the 2025 TSE supplementary artifacts and author pages for an immutable implementation pin;
2. audit whether active-automata-learning frameworks can be made complete for the finite point-MDP greatest relation rather than merely producing a witness;
3. distinguish exact finite-state partition refinement, learned regular witness relations, and confidence-set universal quotient membership in the no-fit matrix;
4. preregister simultaneous multinomial confidence regions and a coverage-aware abstention rule;
5. freeze a codebook-independent full-consequence encoding compatible with Storm exact oracle outputs;
6. do not execute numerical experiments until exact commands, seeds `17 / 29 / 43`, model bytes, peak RSS, wall time, dataset digest, result digest, coverage, and abstention output are fixed.

## Status

- Prior-art matrix refinement: completed.
- Theorem/assumption comparison: completed.
- Public-code availability audit: completed.
- Identifiability/applicability counterexamples: completed.
- Automated regular probabilistic-bisimulation witness synthesis: existing prior art.
- C078 fixed-property obstruction as a universal claim: corrected.
- Valid witness relation as greatest quotient: rejected.
- Learner failure as proof of separation: rejected.
- Statistical confidence-set three-valued B4 estimator: not selected.
- Paper-specific immutable implementation for Hong et al.: not confirmed.
- Public numerical reproduction: not started.
- Model size, RSS, runtime, three seeds: mandatory after execution starts; not yet applicable.
- New architecture: none.
- Legacy A–E toy mechanism: none added.
- RQ-001: narrowed and not adopted.
- Novelty: not established.
- Intelligence principle: not discovered.
- Capability progress: not claimed.
