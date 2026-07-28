# Causal Identifiability Audit C050

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, old A–E toy mechanism, operation/goal hypothesis, memory mechanism, branch, or PR chain was introduced. No experiment was started.

## Primary work newly audited

### Synthetic Potential Outcomes and Causal Mixture Identifiability

Bijan Mazaheri, Chandler Squires, and Caroline Uhler. AISTATS 2025.

Primary records:

- PMLR: https://proceedings.mlr.press/v258/mazaheri25a.html
- OpenReview: https://openreview.net/forum?id=J1CJaSnmKg
- official code: https://github.com/csquires/synthetic-potential-outcomes-aistats2025
- audited official commit: `e947c1a7682c58aa377418678e3085676af166bd`

The paper separates four levels of latent heterogeneity recovery: individual heterogeneous treatment effects, full mixture-model recovery, mixtures of treatment effects (MTEs), and average treatment effects (ATEs). Its central contribution is Synthetic Potential Outcomes (SPOs), which uses observable higher-order multilinear moments to identify causal-response mixtures without requiring full recovery of the underlying latent mixture model.

This is directly relevant to RQ-001 because a latent intervention partition may be defined operationally by equal causal response. The paper shows that such response classes and their probabilities can be identifiable under assumptions weaker than full latent-class identification. Therefore, grouping latent populations or targets by intervention response, and recovering a causal-response partition without full latent semantics, is prior art.

It does **not** receive raw language, infer an utterance equivalence relation, discover a denotation map, or prove that a causal-response class is the unique semantic target class.

## Assumption, observation, and guarantee comparison

Let:

- `U` be an unobserved finite mixture class with `k` values;
- `T in {0,1}` be treatment;
- `Y(t)` be the potential outcome under treatment `t`;
- `R = Y(1) - Y(0)` be the treatment response;
- `X` and `Z` be observed proxy/control variables;
- `M[·]` denote observable moments.

### ATE guarantee

The paper's Theorem 1 identifies `E[R]` by SPOs under:

1. `Z ⟂ Y | T,U`;
2. `X ⟂ T | U`;
3. `M[Z,X | T=t]` is full rank for both treatment values.

This identifies the average causal response while allowing latent mixture structure to remain unidentified.

### MTE guarantee

Theorem 2 identifies the mixture support `E[R | U]` and mixture weights `P[U]` under:

1. `Z ⟂ Y | T,U`;
2. `X ⟂ (Y,T) | U`;
3. `M[Z,X | T=t]` is full rank for both treatment values.

SPOs construct moments of the unobserved response distribution. With distinct response values, Theorem 3 invokes finite moment-mixture recovery: `P[U]` and the distinct values of `E[R | U]` are uniquely recoverable from moments through order `2k-1`, up to permutation of the latent mixture labels.

### What is guaranteed

Under the stated conditional-independence, rank, finite-mixture, and distinct-response assumptions, the observable law can identify:

- the ATE;
- a finite set of distinct latent treatment-response values;
- the probability mass of each response value;
- a causal-response grouping that can be coarser than full mixture-model recovery.

Thus, a latent partition defined only by equal intervention response can be identifiable even when the entire latent data-generating mixture is not.

### What is not guaranteed

The framework does not identify:

- which raw utterances are equivalent;
- whether two utterances with equal response are synonyms or distinct meanings with aliased effects;
- a language-derived treatment or intervention target;
- a target partition finer than equality of the observed response functional;
- the number of semantically distinct targets inside one equal-response component;
- a denotation from utterance classes to response components;
- latent mixture labels beyond permutation;
- semantic identity across systems, environments, or response functionals;
- elimination of joint recoding of utterance classes, response components, target blocks, and denotations.

The paper identifies a distribution of causal responses, not the semantic ontology that generated those responses.

## Prior-art boundary added to the novelty matrix

The following claims are now excluded from the novelty space:

- grouping latent populations according to intervention response rather than covariate similarity;
- identifying causal-response mixtures without identifying the full latent mixture model;
- synthetically constructing potential-outcome moments from observable proxy moments;
- using higher-order multilinear moments to recover a finite mixture of treatment effects;
- recovering response-component probabilities and distinct response values up to permutation;
- defining a hierarchy between ATE, MTE, full mixture, and individual-effect identifiability;
- claiming semantic target discovery merely because latent response classes are recovered;
- claiming raw-language equivalence merely because utterances induce the same identified treatment effect.

The surviving novelty candidate must recover distinctions that remain after the strongest response-equivalence partition supported by all legitimate intervention/outcome channels has been fixed.

## Theorem/assumption boundary for RQ-001

Define:

- `Q`: an unknown equivalence relation over raw utterances;
- `P`: an unknown latent intervention-target partition;
- `d: U_raw/Q -> P`: denotation;
- `F = {f_j}`: the family of legitimate causal-response functionals observable under all preregistered interventions, outcomes, and environments;
- `P_F`: the coarsest target partition that separates targets whenever any `f_j` gives a different response.

SPO-style results can identify parts of `P_F` under their proxy, rank, finite-mixture, and distinctness assumptions. They do not imply that `P_F` equals the semantic target partition `P`.

If two semantic targets have identical response vectors under every available `f_j`, they occupy the same block of `P_F`. No estimator based only on those response functionals can decide whether the block contains one meaning or several semantically distinct but response-aliased meanings.

A necessary condition for a language observation to refine `P_F` is:

\[
I(P_{residual}; U_{raw} \mid S_{nonlang}, F) > 0,
\]

where `S_nonlang` includes all legitimate state, action, reward, trajectory, environment, entity, parser, schema, proxy, treatment, and outcome information.

This is not sufficient. The joint observations must additionally eliminate every transformation that changes `Q`, `P`, or `d` while preserving all response moments, language distributions, interactions, and task behavior.

## Identifiability counterexample: identical causal-response mixture, different semantics

Assume unlimited data and oracle estimation. Let two latent semantic targets `p1` and `p2` have identical potential-outcome response vectors under every available treatment, outcome, environment, and proxy channel:

\[
(E[R_j | p1])_{j=1}^m = (E[R_j | p2])_{j=1}^m.
\]

Construct Model A:

- `p1` and `p2` are one semantic target block `p`;
- raw forms `u1` and `u2` are synonyms in one utterance class;
- the class denotes `p`.

Construct Model B:

- `p1` and `p2` are distinct semantic target blocks;
- `u1` and `u2` belong to distinct utterance classes;
- each class denotes its corresponding target;
- the two targets remain causally response-aliased under all available response functionals.

Models A and B can preserve:

- the complete observable distribution of `T,Y,X,Z`;
- every observable multilinear moment used by SPOs;
- all constructed moments of `R` through arbitrary order;
- the ATE;
- the complete identified MTE support and weights after merging equal response values;
- all conditional-independence and full-rank conditions;
- the language sequence distribution;
- next-state prediction;
- action accuracy and task success;
- language-shuffle gaps when both forms carry the same control information;
- every official SPO output and plot.

Nevertheless, `Q_A != Q_B`, `P_A != P_B`, and the denotation maps differ. Therefore:

> Perfect identification of every causally distinguishable response component does not identify semantic distinctions inside a response-equivalence class, raw-language equivalence, or the denotation between language and latent targets.

A further permutation symmetry remains even when all response values are distinct: simultaneously permuting response-component labels, target labels, utterance classes, and denotation preserves the observable law and all MTE estimates. An external cross-system anchor is required to assign semantic identity rather than an arbitrary component index.

## Consequence for interactive language grounding

Interactive interventions can expand the response family `F` and refine `P_F`. This is useful: an utterance pair that was outcome-equivalent under one task may become distinguishable under a new intervention or question.

However, interaction supports joint identification only when the experiment supplies genuinely separating response functionals. Repeatedly collecting more trajectories under the same aliased response law does not remove the ambiguity. A valid interactive grounding benchmark must therefore:

1. preregister a separating family of interventions and outcomes;
2. compute the non-language response-equivalence partition first;
3. identify which candidate semantic distinctions remain aliased;
4. test whether language predicts held-out interventions that split those residual blocks;
5. compare against alternative utterance/target partitions with identical observed response mixtures;
6. use an independently fixed anchor to eliminate component-label permutation.

Task success or MTE recovery alone is insufficient.

## Official-code and reproducibility audit

The PMLR record links the paper-specific official repository `csquires/synthetic-potential-outcomes-aistats2025`. The audited official head commit is:

`e947c1a7682c58aa377418678e3085676af166bd`

The repository contains:

- source code for SPO estimation;
- ATE and MTE experiment directories;
- collection and plotting scripts;
- a setup shell script;
- documented replication entry points.

The README states Python 3.9 compatibility and reports that the published experiments should run in approximately 1–2 minutes. The documented commands are:

- `run experiments/ate_experiment/collect_results_ate.py`
- `run experiments/ate_experiment/plot_results_ate.py`
- `run experiments/mte_experiment/collect_results_mte.py`
- `run experiments/mte_experiment/plot_results_mte.py`

Reproducibility limitations visible in the audited public state:

- environment setup is delegated to `setup.sh` rather than an immutable lockfile;
- no container or Nix environment is documented;
- no dataset or generated-data checksum manifest is documented;
- no canonical three-seed manifest is documented in the README;
- no raw-result checksum bundle is published;
- no peak RSS, model bytes, CPU latency, or wall-time measurement contract is documented;
- no direct raw-language or interactive-grounding task exists in the official experiments.

Classification:

> **paper-specific official code and exact commit verified; lightweight reproduction commands are documented; immutable dependency, seed, resource, and checksum contract is not established**

No experiment was started in this cycle. Model size, peak RSS, wall time, CPU latency, and three-seed measurements are therefore not applicable yet.

## Required controls before any adoption

A future joint-identification experiment must include identical domain × seed × instance cells for at least:

1. official SPO ATE and MTE baselines;
2. full-mixture recovery where its stronger assumptions hold;
3. non-language response-equivalence partition recovery;
4. language-blind unknown-target baseline;
5. state-only, trajectory-only, outcome-only, and proxy-only baselines;
6. random or untrained utterance encoder;
7. utterance-form shuffle preserving treatment-response mixtures;
8. response-component permutation;
9. target-block permutation;
10. equal-MTE countermodels with different semantic partitions;
11. direct recovery metrics for `Q`, `P`, and `d` rather than only ATE/MTE error;
12. held-out interventions designed to split residual response-alias blocks;
13. an independently fixed cross-system anchor and an ablation proving removal of the residual automorphism.

## Updated decision for RQ-001

**NARROWED BEYOND CAUSAL-RESPONSE MIXTURE IDENTIFIABILITY — NOT ADOPTED**

The surviving candidate is:

> After recovering the finest target partition identifiable from every legitimate non-language causal-response functional, can a codebook-free, preregistered interactive language law split only those residual response-aliased blocks that are distinguishable under held-out interventions, jointly recover raw-utterance equivalence and residual target partition, and eliminate all utterance/target/response-component/denotation recodings without supplied semantic labels?

Adoption now requires at minimum:

1. formal definition of the complete legitimate response family;
2. exact computation or bound for the finest non-language response-equivalence partition;
3. separation of response-component recovery from semantic target recovery;
4. countermodels with identical ATEs, MTEs, response moments, and task behavior but different semantics;
5. held-out interactive interventions that separate the proposed residual classes;
6. direct metrics for utterance partition, residual target partition, and denotation;
7. a cross-system anchor fixed before partition fitting;
8. proof of the residual automorphism group before and after the anchor;
9. exact-commit, dependency, split, seeds `1,7,19`, resource, and checksum manifests before baseline execution;
10. preregistration before architecture or mechanism changes.

## Status

- RQ-001: further narrowed; not adopted
- causal-response mixture identification: prior art under stated assumptions
- ATE and MTE identification from proxy moments: prior art
- semantic partition inside response-equivalent components: not identified
- raw-language equivalence identification: not established
- latent intervention-target partition identification by language: not established
- semantic joint identification: not established
- paper-specific official code: verified
- exact official commit: pinned
- public baseline reproduction: not started
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
