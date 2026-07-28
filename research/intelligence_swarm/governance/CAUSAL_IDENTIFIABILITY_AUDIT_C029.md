# Causal Identifiability Audit C029

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Causal Representation Learning from General Environments under Nonparametric Mixing

Ignavier Ng, Shaoan Xie, Xinshuai Dong, Peter Spirtes, and Kun Zhang. AISTATS 2025, PMLR 258:3700–3708.

Primary records:

- PMLR: https://proceedings.mlr.press/v258/ng25a.html
- OpenReview: https://openreview.net/forum?id=S8lfepB2fz
- official code: https://github.com/ignavierng/crl-general-environments

The work studies latent causal variables observed through an unknown nonparametric mixing function across multiple **general environments**. Unlike intervention-specific CRL results, it does not require the environment changes to be labelled as single-node, coupled, or hard interventions. Instead, identifiability is driven by sufficiently rich changes in latent causal mechanisms across environments, expressed through derivative-based variability conditions up to third order.

The main guarantee is substantially stronger than the remaining broad RQ-001 intuition: under the paper's structural and sufficient-change assumptions, the latent DAG can be fully recovered and latent variables can be identified up to the theorem's minor indeterminacies even when the mixing function and latent causal mechanisms are nonlinear and nonparametric.

The official repository is public and linked from the PMLR record. It contains a runnable command (`python main.py --case=fork`), source files, and example datasets. However, the repository currently exposes only a very small three-commit history, no release, no environment or requirements lockfile, and no immutable dependency specification in the README. Therefore it is valid public code but not yet an immutable, dependency-complete reproduction package under the R0 contract.

## What this prior art establishes

The following are no longer admissible novelty claims for RQ-001:

- recovering latent causal variables from multiple unlabeled or weakly specified environments;
- claiming that unknown intervention type or unknown target labels make language necessary;
- identifying a latent DAG under nonlinear latent mechanisms and nonparametric observation mixing;
- using generic environment variation, rather than known single-node interventions, as the identification signal;
- treating language as a novel source of environment labels when environment-indexed mechanism changes already suffice;
- naming an already identified latent variable or mechanism with language and calling that joint grounding;
- using next-state prediction, environment classification, or task transfer as evidence that language supplied a new identifiable causal distinction.

If the distinctions denoted by language are already recoverable from the family of environment-conditioned distributions, then language is annotation, compression, or finite-sample side information—not a new population-identification source.

## What this prior art does not establish

The work does not identify:

- an unknown equivalence relation over raw utterance forms;
- a joint denotation map between utterance classes and intervention-target blocks;
- target semantics external to the environment-conditioned observational distributions;
- an interactive grounding law under action/outcome/completed-trajectory leakage exclusions;
- the residual partition when the sufficient-change conditions fail;
- elimination of a simultaneous recoding of language classes and any residual latent blocks;
- finite-sample recovery guarantees for the requested raw-language/target joint partition.

The paper's environments are observed as distinct datasets. It uses changes across those datasets as supervision. It therefore cannot by itself justify discovering utterance equivalence or denotation from raw language.

## Assumption and guarantee comparison

| Dimension | Ng et al. 2025 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Environment signal | Multiple observed environments with sufficiently varying mechanisms | Language plus state/action/transition data under hidden intervention targets | Show language adds distinctions not recoverable from environment-conditioned distributions |
| Intervention labels | No requirement for known single-node/coupled/hard intervention labels | Target partition unknown | Unknown labels alone are not a novelty source |
| Mixing | Unknown nonparametric mixing | Symbolic/rendered state and language channels | State admissible decoder and cross-channel assumptions |
| Latent mechanisms | Nonlinear ANM/heteroscedastic families under sufficient derivative variability | General action-conditioned dynamics | Prove equivalent sufficient-change conditions or document failure |
| Guarantee | Full latent DAG recovery and latent identification up to minor indeterminacies | Joint raw-utterance and residual target partition identification | Eliminate joint language/target automorphisms |
| Supervision | Environment identity is observed | No hand-authored language group or target ontology | Avoid encoding target identity through environment metadata |
| Evidence | Direct latent/DAG recovery experiments | Partition recovery plus transfer | Task success alone remains insufficient |

## Prior-art matrix refinement

The novelty matrix must now distinguish:

1. **general-environment CRL** — environment-indexed mechanism changes identify latent variables and DAGs without known intervention types;
2. **environment-label prediction** — language predicts or describes which environment generated a sample;
3. **residual-identifiability assistance** — language supplies information absent from all environment-conditioned transition distributions;
4. **joint causal denotation identification** — raw utterance equivalence and residual target partition are jointly recovered with an externally fixed anti-recoding law.

Items 1 and 2 are not a new RQ-001 contribution. Only item 4 remains a candidate, and only after item 3 is shown by a concrete countermodel pair.

Any future experiment must compare at least:

- strongest non-language general-environment CRL baseline;
- environment identity supplied;
- environment identity removed;
- language supplied;
- language-blind and state-only controls;
- target-label shuffle and outcome shuffle;
- environment-label shuffle within seed/domain/split/condition cells;
- direct latent/partition recovery rather than task success alone.

## Counterexample: language restates an identifiable environment signature

Let `E` be the observed environment identity, `X` the observations, `Z` the latent causal variables, `G` the latent DAG, `P` a proposed intervention-target partition, and `L` language.

Assume the environment family satisfies the sufficient-change conditions of general-environment CRL, so that the collection of distributions `{p(X | E=e)}` identifies `(Z,G)` up to the theorem's permitted indeterminacies.

Now let language be generated only from an identifiable environment statistic:

`L ~ p(L | s(E))`,

where `s(E)` can be recovered from the environment-conditioned observational or transition distributions.

Construct two models:

- Model A uses target partition `P` and utterance equivalence `Q`;
- Model B uses a different target partition `P'` and utterance equivalence `Q'`, but preserves the same `(Z,G)`, the same environment distributions, and the same language law after jointly recoding the target and utterance labels.

Both models can have identical:

- `p(X | E)` and transition distributions;
- recovered latent variables and DAG;
- next-state prediction;
- action accuracy and task success;
- environment classification;
- language prediction and paraphrase accuracy;
- language-shuffle performance gap.

Yet `P != P'` and `Q != Q'`.

Therefore:

> Language that merely names, predicts, or paraphrases environment distinctions already identifiable from general-environment variation does not jointly identify raw-language equivalence or an intervention-target partition.

A second failure occurs when sufficient-change conditions do not hold. If two residual target blocks induce exactly the same family of environment-conditioned distributions and language is itself generated from those distributions, language cannot distinguish them. It is observationally redundant by construction.

## Necessary residual-information condition added by C029

Let `S_GE` denote the strongest sufficient statistic available from all allowed environment identities, observations, actions, transitions, outcomes, and non-language general-environment CRL estimands.

Language can contribute to a residual target partition only if:

`I(P_residual ; L | S_GE) > 0`.

This is necessary but not sufficient. Adoption also requires a preregistered external denotation law that prevents simultaneous recoding of:

- utterance equivalence classes;
- residual latent/target blocks;
- environment labels or signatures;
- the denotation map connecting them.

The residual joint automorphism group must be proven trivial.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After applying general-environment CRL under the strongest valid sufficient-change assumptions, can a preregistered, externally fixed language law distinguish a concrete pair of models that have identical environment-conditioned observation and transition distributions but different residual intervention-target partitions, while simultaneously identifying raw-utterance equivalence and eliminating all joint language/target recodings?

This formulation is **not adopted**.

## Adoption requirements added by C029

Before adoption, the candidate must provide:

1. an explicit audit of whether the observed environments satisfy the general-environment sufficient-change assumptions;
2. the maximal latent/DAG/target abstraction recoverable by the strongest non-language general-environment baseline;
3. a countermodel pair with identical environment-conditioned observation and transition distributions but different residual target partitions;
4. a population language law that distinguishes that pair without environment-ID, reward, action-target, outcome, or completed-trajectory leakage;
5. an externally fixed denotation anchor defined before observing predictions or outcomes;
6. a proof that the residual joint automorphism group is trivial;
7. an impossibility theorem when language only predicts or paraphrases identifiable environment signatures;
8. immutable reproduction of the official public baseline with pinned commit and dependencies;
9. environment-supplied, environment-blind, language-blind, state-only, target-label-shuffle, outcome-shuffle, and environment-label-shuffle controls on identical instances;
10. direct latent, DAG, utterance-partition, and target-partition recovery metrics;
11. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND GENERAL-ENVIRONMENT NONPARAMETRIC CRL — NOT ADOPTED

The candidate remains potentially distinct only if language separates target distinctions that remain observationally identical after the strongest valid general-environment CRL analysis. Merely labelling environments, mechanisms, or already identified latent variables is prior art or annotation.

No experiment or architecture is authorised by this result.

## Resource accounting

No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable in this cycle and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art matrix refinement, theorem/assumption comparison, official-code audit, counterexample
- general-environment nonparametric CRL: established by prior work under sufficient-change assumptions
- official public code: located
- immutable dependency-complete reproduction package: not established
- raw-language equivalence identification: not established
- residual target-partition identification: not established
- RQ-001: further narrowed, not adopted
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
