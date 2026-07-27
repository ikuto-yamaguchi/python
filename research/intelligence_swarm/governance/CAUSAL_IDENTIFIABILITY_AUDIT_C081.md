# Causal Identifiability Audit C081

## Scope and guardrails

- Canonical branch only: `research/intelligence-swarm-reconstruction-001`.
- No new architecture and no extension of legacy A–E toy mechanisms.
- C responsibility remains joint identifiability of raw-language equivalence `Q`, latent intervention-target partition `P`, and denotation `d`.
- This run completes (a) prior-art-matrix refinement, (b) theorem/assumption comparison, (c) public-code suitability audit, and (d) an identifiability counterexample.
- Numerical execution is not started; model size, peak RSS, runtime, and seeds `17 / 29 / 43` remain mandatory once execution begins.

## Decision-relevant question

C080 left a gate based on multinomial transition-vector testing: can existing statistical tests provide simultaneous pairwise `equal / different / unresolved` decisions and thereby recover the exact finite-sample B4 partition?

The decision-critical distinction is between:

1. non-tolerant equality/closeness testing, which separates `p=q` from `TV(p,q) >= epsilon`;
2. tolerant testing, which separates `TV(p,q) <= epsilon_1` from `TV(p,q) >= epsilon_2`; and
3. exact finite-sample certification that `p=q`, which the proposed B4 `merge` label would require if the target remains the exact Storm quotient.

## Primary prior art and assumption audit

Primary sources:

- Tuğkan Batu, Lance Fortnow, Ronitt Rubinfeld, Warren D. Smith, and Patrick White, *Testing Closeness of Discrete Distributions*, JACM 2013, DOI `10.1145/2432622.2432626`.
- Ilias Diakonikolas and Daniel M. Kane, *A New Approach for Testing Properties of Discrete Distributions*, FOCS 2016 / arXiv `1601.05557`.
- Clément L. Canonne, Ayush Jain, Gautam Kamath, and Jerry Li, *The Price of Tolerance in Distribution Testing*, COLT 2022 / arXiv `2106.13414`.
- Gregory Valiant and Paul Valiant, *An Automatic Inequality Prover and Instance Optimal Identity Testing*, SICOMP lineage; ECCC TR13-111 provides the instance-wise identity-testing formulation.

These results establish efficient identity and closeness testers under a promised gap. Typical guarantees have the form:

- accept with high probability when `p=q` or `TV(p,q) <= epsilon_1`;
- reject with high probability when `TV(p,q) >= epsilon_2`;
- no guarantee inside the indifference region.

Tolerant testing explicitly makes the positive region nonzero (`epsilon_1 > 0`) and incurs a substantial sample-complexity price. This is directly relevant to B4: a finite-sample test can certify an approximate behavioural block under a preregistered tolerance and separation gap, but that is not the exact greatest bisimulation quotient used by the Storm oracle.

Consequently, the following are removed from possible novelty:

- multinomial identity testing under an `epsilon`-far alternative;
- two-sample closeness testing for unknown discrete distributions;
- tolerant equality testing with a nonzero near region;
- sample-optimal or instance-adaptive detection of separated transition vectors;
- using a union bound or multiplicity correction to obtain simultaneous `different` decisions over finitely many state-action pairs.

What these results do not supply is finite-sample proof of exact equality for unrestricted multinomial parameters.

## Counterexample: exact merge is not finitely certifiable

Consider a binary successor variable under one action. For state `s`, let

`P(x | s,a) = 1/2`.

For state `t`, consider two models:

- Model A: `P(x | t,a) = 1/2`;
- Model B: `P(x | t,a) = 1/2 + eta`, for arbitrarily small `eta > 0`.

The exact B4/Storm quotient merges `s,t` in Model A and separates them in Model B.

For every finite sample size `n`, there are count vectors with positive probability under both models. More strongly, for every fixed test with nontrivial type-I control and every finite `n`, sufficiently small `eta` makes the two induced sample laws arbitrarily close. Therefore no finite-sample procedure can uniformly certify exact equality against all `eta > 0` alternatives.

A failure to reject `p=q` is not evidence that `p=q`; it only means the observed data did not separate the distributions at the test's resolution. Simultaneous testing and adaptive allocation do not remove this boundary. They can control false discoveries or family-wise error for detected differences, but they cannot convert an unresolved pair into a sound exact merge without additional structure.

Hence a statistically sound three-valued exact-partition output is asymmetric:

- `separate`: possible when a confidence set excludes equality or a test rejects under a preregistered family-wise guarantee;
- `unidentified`: required whenever both equality and sufficiently close unequal models remain compatible;
- `merge`: unavailable at finite time for unrestricted real-valued multinomial parameters, unless exact equality is imposed by symbolic parameter tying, a known generative constraint, or a nonzero equivalence tolerance that changes the estimand.

This is an observation-level impossibility, not an architecture limitation.

## Sequential and adaptive sampling boundary

Adaptive state-action sampling can improve allocation and stop early for clearly different pairs. It does not change the exact-equality obstruction. Under alternatives `eta -> 0`, any finite stopping rule that sometimes returns exact `merge` with nonzero probability can return the same result on a sufficiently close unequal model with nonzero probability.

Any finite-time guarantee therefore needs one of the following contracts:

1. a minimum separation promise `TV(p,q) = 0` or `TV(p,q) >= Delta`;
2. an approximate quotient definition with `TV(p,q) <= epsilon_merge` treated as merge and `TV(p,q) >= epsilon_split` treated as separate;
3. symbolic equality constraints shared across states;
4. permanent abstention for pairs whose confidence region intersects the equality boundary.

The first and second options alter the scientific claim and must be preregistered. The fourth option is the only distribution-free route compatible with the exact Storm quotient.

## Public-code suitability audit

Public implementations exist for two-sample hypothesis tests and equality-testing workflows. A relevant modern example is:

- `i-gao/model-equality-testing`, associated with Gao, Liang, and Guestrin, *Model Equality Testing: Which Model Is This API Serving?* The package exposes two-sample statistics and permutation p-values and asks whether to reject `P=Q`.

General scientific Python libraries also provide chi-square, likelihood-ratio, permutation, and contingency-table tests. These are useful `different / not-rejected` diagnostics.

However, their API semantics are not the B4 three-valued contract:

- a p-value above threshold is not an exact-equality certificate;
- permutation tests control rejection under the null but do not establish the null;
- ordinary multiple-testing correction controls false rejection, not false merge;
- none of the audited interfaces returns a sound exact `merge` for unrestricted multinomial transition laws;
- none directly computes the greatest full-consequence partition with action coverage and codebook-independent consequence channels.

Classification:

> public equality/closeness-test implementations are suitable as separation diagnostics and power controls, not as exact-merge certifiers or complete B4 partition estimators.

No public-code numerical execution is started in this run because the estimand must first be corrected.

## Prior-art matrix update

| Candidate | Positive hypothesis | Negative hypothesis | Exact merge certificate | Abstention/gap | Action-complete B4 | C classification |
|---|---|---|---:|---:|---:|---|
| Non-tolerant identity/closeness testing | `p=q` | `TV >= epsilon` | no | implicit indifference below `epsilon` | pairwise only | separation prior art |
| Tolerant testing | `TV <= epsilon_1` | `TV >= epsilon_2` | no; approximate equivalence | explicit gap | pairwise only | approximate-quotient prior art |
| Multiple-testing correction | nulls not rejected/rejected | controlled error family | no | unresolved pairs remain | no quotient closure | error-control component |
| Sequential/adaptive testing | same hypotheses with adaptive samples | separated alternatives | no without a gap | can stop or abstain | coverage-dependent | allocation component |
| Storm point-MDP minimisation | exact supplied probabilities | exact symbolic comparison | yes for supplied model | no sampling | yes if encoding complete | exact B4 oracle |
| Required empirical exact B4 estimator | sampled trajectories | unknown exact point MDP | impossible finite-time merge without structure | must abstain | intended yes | target contract must be revised |

## Decision

> **NARROWED: MULTINOMIAL IDENTITY, CLOSENESS, TOLERANT, AND MULTIPLE-TESTING METHODS ARE EXISTING PRIOR ART AND CAN CERTIFY SEPARATION UNDER A GAP, BUT NO FINITE-SAMPLE TEST CAN UNIFORMLY CERTIFY EXACT EQUALITY AGAINST ARBITRARILY CLOSE ALTERNATIVES; THEREFORE AN EXACT THREE-VALUED B4 ESTIMATOR MAY SOUNDLY RETURN `SEPARATE` OR `UNIDENTIFIED`, WHILE FINITE-TIME `MERGE` REQUIRES SYMBOLIC TYING OR A PREREGISTERED APPROXIMATE-EQUIVALENCE MARGIN — NOT ADOPTED.**

This removes the search for a generic finite-sample exact-merge tester as an invalid gate. The remaining choice is scientific, not architectural: preserve the exact Storm quotient and accept permanent abstention for equality-boundary pairs, or redefine B4 as a tolerance-indexed approximate quotient.

## Consequence for RQ-001

This result only concerns the language-blind recovery of `P`. It does not identify raw-language equivalence `Q` or denotation `d`.

Even if an approximate B4 partition is recovered under `epsilon_merge / epsilon_split`, joint identification still requires:

- a language-side quotient with an equally explicit tolerance contract;
- a cross-system coupling law not derived from target IDs, parser slots, rewards, or evaluator codebooks;
- direct evaluation of `Q`, `P`, and `d` rather than task success;
- proof that tolerance-induced merge/split choices do not manufacture the desired ontology.

## Next gate

1. Update LBQ001 so the exact and approximate estimands are not conflated.
2. Retain Storm as the exact point-model oracle.
3. Define two permissible empirical outputs:
   - exact mode: `separate / unidentified`, with `merge` only from symbolic tying;
   - approximate mode: `merge / separate / unidentified` under preregistered `epsilon_merge < epsilon_split`.
4. Audit confidence-sequence and multinomial two-sample implementations for time-uniform separation and abstention, not exact equality certification.
5. Freeze family-wise error, action-coverage, consequence-channel, and minimum-separation contracts before any run.
6. Only after the estimand is fixed, pin commands and execute seeds `17 / 29 / 43` with model size, peak RSS, wall time, and input/output digests.

## Current status

- prior-art matrix refinement: complete;
- theorem/assumption comparison: complete;
- public-code suitability audit: complete;
- identifiability counterexample: complete;
- multinomial identity/closeness testing: existing prior art;
- tolerant equivalence testing: existing prior art;
- finite-sample exact equality certification: rejected without structural tying;
- generic exact three-valued B4 estimator target: invalid as previously stated;
- exact empirical mode: separate/unidentified only unless equality is symbolic;
- approximate empirical mode: requires preregistered tolerance gap;
- numerical execution: not started;
- new architecture: none;
- legacy A–E toy mechanism: none added;
- RQ-001: further narrowed, not adopted;
- novelty, intelligence-principle, and capability-progress claims: none.

## Sources

- https://doi.org/10.1145/2432622.2432626
- https://arxiv.org/abs/1601.05557
- https://arxiv.org/abs/2106.13414
- https://eccc.weizmann.ac.il/report/2013/111/
- https://github.com/i-gao/model-equality-testing
