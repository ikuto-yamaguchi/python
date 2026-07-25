# Causal Identifiability Audit C025

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, or branch was introduced.

## Primary work newly audited

### Mechanistic Independence: A Principle for Identifiable Disentangled Representations

Stefan Matthes, Zhiwei Han, and Hao Shen. ICLR 2026 Poster; arXiv:2509.22196.

Primary records:

- arXiv: https://arxiv.org/abs/2509.22196
- OpenReview: https://openreview.net/forum?id=0VVdai71xb
- ICLR record: https://iclr.cc/virtual/2026/poster/10011933

The work defines latent factors by how they act on observed variables rather than by independence of their latent distributions. It introduces support-, sparsity-, and higher-order mechanistic-independence criteria, proves identifiability of latent subspaces under nonlinear and even non-invertible mixing, and characterises recoverable subspaces as connected components of an induced graph.

A dedicated author-maintained reproduction repository was not located from the primary records or targeted repository search. No empirical reproduction was started.

## What this prior art establishes

The following cannot be treated as novel contributions of RQ-001:

- identifying latent subspaces from how factors act on observables;
- replacing latent statistical independence by mechanistic independence;
- using support or sparsity of factor-to-observation effects as an identification signal;
- identifying subspaces under nonlinear, non-invertible mixing;
- graph-theoretically recovering factor groupings as connected components;
- claiming that language is required merely because latent factors are statistically dependent;
- treating a factor name or verbal description as the source of a grouping that is already recoverable from effect structure.

## What this prior art does not establish

The work does not identify:

- raw-utterance equivalence classes;
- an unknown intervention-target partition from language;
- a joint utterance/target denotation map;
- externally fixed semantic anchors;
- interactive grounding through actions and feedback;
- a theorem that language refines mechanistically indistinguishable latent subspaces;
- a finite-sample language-grounding guarantee.

## Theorem/assumption comparison

| Dimension | Mechanistic Independence | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Identification signal | Factor action on observed variables | External language contrast after strongest non-language statistics | Show language is not measurable from the action structure |
| Mixing | Nonlinear and possibly non-invertible | Raw observations plus trajectories/interactions | State the residual ambiguity after applying mechanistic criteria |
| Recoverable object | Latent subspaces / connected components | Raw-language equivalence plus residual target partition | Prove a strict refinement of the mechanistic partition |
| Distributional assumptions | Does not require latent statistical independence | Population language channel may be dependent | Dependence alone cannot justify language necessity |
| Guarantee | Identifiability under support/sparsity/higher-order criteria | Joint denotational and target identification | Supply an anti-recoding anchor and joint theorem |
| Evaluation | Recovery of mechanistically defined subspaces | Partition recovery plus prospective transfer | Do not infer identification from prediction/task success alone |

## Prior-art matrix refinement

The novelty matrix must separate:

1. statistical disentanglement;
2. mechanistic disentanglement from factor effects;
3. intervention-target recovery from environments;
4. language annotation of an already identifiable factor;
5. language-based strict refinement of a residual mechanistically indistinguishable block;
6. joint identification of raw-utterance equivalence and the refined target partition.

Mechanistic Independence covers category 2. Existing unknown-intervention CRL covers substantial parts of category 3. RQ-001 can remain potentially novel only in categories 5 and 6.

## Counterexample: perfect language prediction without refinement beyond mechanistic components

Let latent variables `Z=(Z1,Z2)` act on observations through a generator `X=g(Z)`. Suppose the support/sparsity pattern of the partial effects of `Z1` and `Z2` places them in the same mechanistic connected component `C`, so the strongest applicable non-language theorem identifies only `C` and not an internal split.

Let language be generated only from the component label:

`L ~ p(L | C)`.

Construct two candidate internal partitions `P={{Z1},{Z2}}` and `P'={{h1(Z1,Z2)},{h2(Z1,Z2)}}`, where the transformation is invertible within `C` and preserves every observable factor-action support, sparsity relation, trajectory distribution, and intervention outcome available to the learner. Transform the language encoder/decoder jointly so both candidates induce the same distribution over utterances.

Then both models can have identical:

- observation and trajectory likelihood;
- next-state prediction;
- action accuracy and task success;
- mechanistic-independence scores;
- graph connected components;
- utterance prediction and paraphrase accuracy;
- language-shuffle performance gap.

Yet they disagree about raw-utterance equivalence and the fine target partition inside `C`.

Therefore:

> Language that only names or predicts a mechanistically identifiable component does not refine the residual latent partition, and perfect behavioural or linguistic prediction does not establish joint identification.

A necessary condition for refinement is

`I(P_residual ; L_anchor | M(X,T,A,E)) > 0`,

where `M` is the strongest mechanistic/non-language sufficient statistic. This is not sufficient: the language law must also be externally fixed so it cannot be transformed jointly with the representation and partition.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After applying the strongest support-, sparsity-, higher-order mechanistic-independence and unknown-intervention criteria, can a preregistered external language law distinguish a concrete countermodel pair that remains inside the same mechanistically identifiable component, and thereby jointly identify raw-utterance equivalence and a strict refinement of the residual intervention-target partition?

This formulation is **not adopted**.

## Adoption requirements added by C025

Before adoption, the candidate must provide:

1. the exact mechanistic-independence criterion applicable to the observation model;
2. the maximal non-language partition/component recovered under that criterion;
3. a concrete pair of models with identical observations, trajectories, interventions, and mechanistic graph but different internal target partitions;
4. a language contrast that distinguishes that pair and is not measurable from factor-effect support, sparsity, derivatives, trajectories, actions, environment identity, outcomes, or completed interactions;
5. an externally fixed denotational anchor immune to joint recoding;
6. a strict refinement or joint-identification theorem;
7. an impossibility theorem when language only labels the recovered mechanistic component;
8. direct comparison against mechanistic-independence and unknown-intervention baselines;
9. preregistered unseen-form, composition, target-combination, dynamics, and system splits;
10. leakage controls and public baseline reproduction before architecture work;
11. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND MECHANISTIC-INDEPENDENCE IDENTIFIABILITY — NOT ADOPTED

Latent statistical dependence, nonlinear mixing, or non-invertibility do not by themselves create a role for language: mechanistic action structure can already identify latent subspaces under explicit criteria. RQ-001 survives only if an external language law strictly separates targets that remain indistinguishable after the strongest mechanistic and intervention-based non-language criteria.

No experiment or architecture is authorised by this result.

## Resource accounting

No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable in this cycle and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, theorem/assumption comparison, counterexample, public-code availability audit
- mechanistic subspace identification without language: established prior art under explicit criteria
- language naming a mechanistic component as joint identification: rejected
- RQ-001: further narrowed, not adopted
- public capability baseline: not yet accepted as reproduced in this audit track
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
