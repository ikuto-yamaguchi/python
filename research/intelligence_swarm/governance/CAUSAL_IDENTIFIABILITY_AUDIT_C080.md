# Causal Identifiability Audit C080

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code availability audit, and (d) an applicability/identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C079 established that probabilistic-bisimulation relations can be synthesised with automata-learning techniques in parameterised systems, but that an accepted witness need not equal the greatest full-consequence quotient.

The next question is whether the active learner itself closes the missing greatest-relation and finite-sample three-valued-identification gate.

## Primary prior art and exact assumption audit

Primary source:

- Chih-Duo Hong, Anthony W. Lin, Rupak Majumdar, and Philipp Rümmer, *Probabilistic Bisimulation for Parameterized Systems (with Applications to Verifying Anonymous Protocols)*, CAV 2019, DOI `10.1007/978-3-030-25540-4_27`.

Section 6 describes active automata learning of a regular probabilistic-bisimulation relation. The procedure assumes:

1. a bounded-branching probabilistic transition system;
2. a decidable checker for whether a proposed relation is a valid probabilistic bisimulation; and
3. a procedure that computes, for every configuration length `n`, the greatest probabilistic bisimulation on the finite length-`n` restriction.

The third item is decision-critical. The learner uses finite-length greatest-bisimulation computations to answer the relation-membership/equivalence obligations needed by learning. Therefore the method does not infer the primitive greatest relation from noisy trajectories or statistical confidence sets; it assumes exact finite-instance greatest-relation access as a subroutine.

Consequently, the following claims are removed from possible novelty:

- regular relation synthesis from exact membership/equivalence-style information;
- combining active automata learning with a decidable probabilistic-bisimulation verifier;
- lifting exact finite-instance greatest-bisimulation computations into a regular relation over a parameterised family;
- learning a compact symbolic witness once exact finite restrictions are already decidable.

But the following is not supplied by this prior art:

- finite-sample recovery of the greatest quotient;
- statistical `merge / separate / unidentified` output over a confidence set;
- action-complete full-consequence partition recovery from trajectories;
- recovery of `Q`, `P`, or `d`.

## Relation to PAC active automata learning

Relevant adjacent prior art includes:

- Franz Mayr et al., *A Congruence-based Approach to Active Automata Learning from Neural Language Models*, ICGI 2023, PMLR 217;
- Hua Mao et al., *Learning Markov Decision Processes for Model Checking*, 2012/2013;
- Giovanni Bacci et al., *Active Learning of Markov Decision Processes using Baum-Welch algorithm*, 2021.

These works show that probabilistic automata or MDP-like models can be approximated from queries or observed traces, and that sampling-based equivalence tests can support PAC-style behavioural learning. This removes any novelty claim based only on active probabilistic-model learning.

However, PAC closeness of generated traces or transition estimates is not exact recovery of a discrete greatest-bisimulation quotient. A partition theorem still needs coverage and a separation/stability margin, or it must abstain when multiple quotients remain compatible with the observations.

## Counterexample: approximate equivalence oracle cannot certify exact quotient

Consider two states `s` and `t`, one action `a`, and two physically distinct successor blocks `x` and `y`.

Let

- `P(x | s,a) = 1/2`,
- `P(x | t,a) = 1/2 + eta`,

with the remaining probability going to `y`.

Model A has `eta = 0`, so `s` and `t` may be merged by the exact full-consequence quotient.

Model B has an arbitrarily small `eta > 0`, so exact probabilistic bisimulation separates them.

For every finite query or trajectory budget and every nonzero sampling tolerance, an `eta` can be chosen small enough that the same observed sample transcript has positive probability under both models and a PAC/conformance oracle accepts the same hypothesis with the allowed error.

Therefore:

- acceptance by a sampling-based equivalence oracle does not prove exact merge;
- failure to find a counterexample does not prove bisimilarity;
- a learned minimal approximate automaton need not have the same blocks as the exact Storm quotient;
- the sound finite-sample answer is `unidentified` unless confidence bounds exclude either `eta = 0` or all `eta != 0` under a preregistered margin contract.

This is an observation-level non-identifiability result, not an architecture limitation.

## Completeness boundary

With an ideal exact teacher, finite deterministic automata learning can identify a minimal target automaton. That result does not transfer automatically to stochastic B4 partition recovery because:

- numerical equality of probability vectors is not finitely decidable without a gap or symbolic exact access;
- unobserved actions leave action-complete controlled behaviour unidentified;
- full-consequence labels must be codebook-independent and completely observed;
- exact equivalence queries are unavailable in the intended empirical setting;
- the Hong learner obtains the required exact finite relations from an external greatest-bisimulation procedure.

Thus active learning is a query-allocation layer, not a replacement for the missing statistical identification contract.

## Public-code availability audit

The CAV paper and technical report specify the learning/checking method, but this run did not confirm a paper-specific immutable public repository implementing the complete probabilistic-bisimulation relation learner.

LearnLib is a public active-automata-learning framework, but its published model inventory is centred on deterministic automata/transducer learners and does not by itself provide the Hong probabilistic-bisimulation verifier, the exact finite-length greatest-relation oracle, or the required confidence-set three-valued B4 output.

Classification:

> theorem and active-learning construction are public; a pinned end-to-end implementation satisfying the empirical B4 contract is not confirmed.

## Prior-art matrix update

| Candidate | Exact teacher/model | Learns unknown model/relation | Greatest quotient guarantee | Finite-sample abstention | Action-complete full consequence | C classification |
|---|---:|---:|---:|---:|---:|---|
| Storm point-MDP minimisation | yes | no | yes, supplied point model | no | yes if encoding is complete | B4 oracle |
| Hong et al. regular relation synthesis | exact verifier plus exact finite greatest relations | regular witness | not independently; oracle-dependent | no | depends on supplied system/observation relation | symbolic lifting prior art |
| PAC/conformance automata learning | sampled | approximate model/congruence | no exact guarantee without margin | approximate confidence only | generally no | diagnostic/model-learning prior art |
| Required empirical B4 estimator | sampled/confidence set | yes | pairwise greatest-quotient membership | yes: merge/separate/unidentified | yes | still pending |

## Decision

> **NARROWED: ACTIVE AUTOMATA LEARNING OF REGULAR PROBABILISTIC BISIMULATIONS IS PRIOR ART, BUT THE HONG CONSTRUCTION ASSUMES EXACT FINITE-LENGTH GREATEST-BISIMULATION COMPUTATION; PAC OR SAMPLING-BASED EQUIVALENCE TESTS CANNOT CERTIFY THE EXACT FULL-CONSEQUENCE QUOTIENT WITHOUT COVERAGE AND A SEPARATION OR ABSTENTION CONTRACT — NOT ADOPTED.**

This is a stronger and more precise boundary than C079: unknown-relation synthesis exists, but its positive result is oracle-relative and does not close the empirical identification problem.

## Next gate

1. Stop treating active relation learning as a candidate replacement for the greatest-quotient oracle.
2. Audit statistical equality-testing and sequential-testing results for multinomial transition vectors under adaptive state-action sampling.
3. Determine whether existing public code can return simultaneous pairwise `equal / different / unresolved` decisions with family-wise coverage.
4. Require action coverage and a preregistered minimum separation for any finite-time exact-partition claim.
5. Compose only existing components: confidence construction, equality/separation tester, and pinned Storm oracle; do not introduce a learned architecture.
6. Before execution, freeze exact commands, data digests, consequence encoding, seeds `17 / 29 / 43`, model size, peak RSS, and wall-time measurement.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code availability audit: complete;
- identifiability/applicability counterexample: complete;
- active regular probabilistic-bisimulation synthesis: existing prior art;
- exact finite greatest-relation oracle dependence: confirmed;
- PAC model learning as exact quotient recovery: rejected;
- executable three-valued finite-sample B4 estimator: not selected;
- public numerical reproduction: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.