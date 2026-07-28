# Causal Identifiability Audit C037

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + theorem/assumption comparison + official-code audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, branch, or PR chain was introduced.

## Primary work newly audited

### Identifiable Exchangeable Mechanisms for Causal Structure and Representation Learning

Patrik Reizinger, Siyuan Guo, Ferenc Huszár, Bernhard Schölkopf, and Wieland Brendel. International Conference on Learning Representations, 2025.

Primary records:

- ICLR proceedings: https://proceedings.iclr.cc/paper_files/paper/2025/hash/9b91ee0da3bcd61905fcd89e770168fc-Abstract-Conference.html
- paper PDF: https://proceedings.iclr.cc/paper_files/paper/2025/file/9b91ee0da3bcd61905fcd89e770168fc-Paper-Conference.pdf
- official code identified in the paper: https://github.com/rpatrik96/IEM
- parent implementation used by the experiments: https://github.com/syguo96/Causal-de-Finetti

The paper introduces Identifiable Exchangeable Mechanisms (IEM), a probabilistic framework unifying causal discovery, independent component analysis, and causal representation learning through exchangeable non-i.i.d. data. Its main message is that variation across exchangeable groups can make causal structure or latent representations identifiable even when ordinary i.i.d. observations would not.

For bivariate causal discovery, the paper separates two sufficient sources of non-i.i.d. variation:

- **cause variability**: the marginal mechanism of the cause varies across exchangeable groups while the effect-given-cause mechanism stays fixed;
- **mechanism variability**: the effect-given-cause mechanism varies while the cause distribution stays fixed.

Under the paper's representation assumptions, either form can identify the bivariate causal direction. The paper also shows a duality for Time-Contrastive Learning: representation identification driven by changing source distributions can be re-expressed as identification driven by changing observation mechanisms.

## Assumption, observation, and guarantee comparison

The IEM setting relies on or exposes:

1. sequences grouped by an exchangeable non-i.i.d. data-generating process;
2. latent de Finetti-style parameters governing either source/cause distributions or conditional mechanisms;
3. repeated samples within environments or exchangeable groups;
4. a fixed distinction between which quantities count as sources, mechanisms, observations, and auxiliary environment variables;
5. variability conditions strong enough to distinguish alternative causal directions or latent components;
6. in the bivariate theorem, no unrestricted hidden confounding and a model class compatible with the stated exchangeable factorizations;
7. for TCL-style representation results, the usual conditional factorization and sufficient-variability assumptions inherited from identifiable nonlinear ICA.

The guarantees concern:

- distinguishing the bivariate causal direction under cause or mechanism variability;
- identifying latent sources in TCL-type models under sufficient exchangeable non-i.i.d. variation;
- transferring the same identification argument between source variability and mechanism variability.

The audited work does **not** jointly identify:

- an unknown equivalence relation over raw utterances;
- an unknown latent intervention-target partition;
- a unique denotation map from utterance classes to target blocks;
- the exchangeable grouping itself when group membership is latent and may be jointly recoded with language;
- an external semantic anchor that fixes the names or meanings of recovered components;
- fine-grained target distinctions that induce the same exchangeable source/mechanism law.

For RQ-001, this matters because a language variable can act as an auxiliary group identifier, environment descriptor, or observed source of non-i.i.d. variation without identifying the semantic equivalence classes of raw language. If utterances are first grouped into environments and those groups satisfy IEM/TCL variability, the resulting latent recovery is conditional on that grouping; it is not evidence that the grouping itself was discovered or uniquely grounded.

## Official-code audit

The paper explicitly points to `rpatrik96/IEM`. The repository is a public fork of `syguo96/Causal-de-Finetti` and contains:

- `bivariate_experiment.py`;
- `multivariate_experiment.py`;
- `main.py`;
- `src/` and `experiments/` directories;
- `requirements.txt`;
- synthetic experiments for cause and mechanism variability.

The paper reports bivariate experiments over 100, 200, 300, 400, and 500 environments, two samples per environment, and 100 repeated seeds. It compares the causal-de-Finetti procedure with FCI, GES, NOTEARS, DirectLiNGAM, and a random baseline.

However, the repository README still describes the parent Causal de Finetti paper rather than an immutable IEM reproduction package. No release is published, and the visible repository does not provide a lockfile, container, exact paper-figure command manifest, model/resource logging contract, or R0-style three-seed artifact bundle. It is therefore classified as:

> **official public code verified; paper-specific immutable reproduction package not yet established**

No experiment was started in this cycle. Before reproduction, the exact repository commit, dependency versions, modified data generator, figure-to-command mapping, seed protocol, and expected output hashes must be pinned.

## Prior-art boundary added to the novelty matrix

The following claims are excluded from the novelty space:

- using exchangeable non-i.i.d. environments to identify causal direction;
- identifying representations from variation across source distributions;
- identifying representations from variation across observation mechanisms;
- treating source variability and mechanism variability as dual identification signals;
- using an instruction or language descriptor as an auxiliary environment variable for nonlinear-ICA-style identification;
- claiming that environment-conditioned language dynamics pretraining is new merely because it exploits non-i.i.d. groups;
- interpreting recovery of latent sources from supplied utterance groups as discovery of raw-language equivalence;
- treating causal-direction accuracy, next-state prediction, action accuracy, task success, or language-shuffle gaps as direct evidence that utterance and target partitions were jointly identified.

The surviving question must concern discovery and semantic fixation of the grouping/partition itself after the strongest exchangeability-based non-language explanation has been removed.

## Identifiability counterexample: perfect exchangeability-based recovery with nonidentified language and target partitions

Let raw utterances be \(U\), let \(Q\) be an unknown equivalence relation over utterances, and let \(P\) be an unknown latent intervention-target partition. Suppose an observed auxiliary variable

\[
E=r(U)
\]

assigns each utterance to an exchangeable group. Assume that, conditional on \(E\), the state/observation process satisfies all IEM or TCL variability conditions and therefore a non-language learner perfectly recovers the relevant latent sources or causal direction.

Construct two semantic models:

- Model A uses utterance partition \(Q\), target partition \(P\), and denotation map \(d:U/Q\rightarrow P\).
- Model B uses different partitions \(Q'\neq Q\) and \(P'\neq P\), while preserving the same observed group assignment \(r(U)=E\) for every utterance.

Within each exchangeable group, split or merge utterance classes arbitrarily. Simultaneously relabel the latent target blocks and transform the language encoder/decoder and denotation map so that the complete environment-conditioned law remains unchanged.

Both models then have the same:

- exchangeable-group membership;
- source and mechanism variability statistics;
- environment-conditioned observation and transition distributions;
- bivariate causal-direction estimate;
- TCL/IEM latent representation up to the theorem's allowed transformations;
- next-state prediction;
- action accuracy;
- task success;
- utterance likelihood and paraphrase prediction whenever these depend only on \(E\) and the recovered representation;
- language-shuffle gap when shuffling is restricted to preserving the same group-level sufficient statistics.

Nevertheless, their raw-utterance equivalence relations and fine-grained intervention-target partitions differ.

A second ambiguity remains when the environment/group variable is learned jointly from language. Apply a nontrivial bijection to environment labels, latent target blocks, utterance classes, and the language encoder at the same time. All exchangeable distributions and IEM/TCL objectives remain invariant. Human-readable environment names do not remove this symmetry unless their denotation is fixed externally before fitting.

Therefore:

> Perfect causal or representation identification from exchangeable non-i.i.d. variation does not identify the raw-language equivalence relation, the fine-grained latent intervention-target partition, or their semantic alignment when the grouping and denotation may be jointly recoded.

## Necessary boundary for a surviving language contribution

Let \(S_{IEM}\) contain all information available to the strongest exchangeability-based baseline:

- exchangeable group or environment identity;
- within-group sample distributions;
- cause and mechanism variability statistics;
- recovered latent sources or causal direction;
- state, action, reward, outcome, and completed trajectories;
- next-state and policy sufficient statistics.

Let \(P_{residual}\) be the target distinction remaining after conditioning on \(S_{IEM}\). A necessary information condition is

\[
I(P_{residual};L\mid S_{IEM})>0.
\]

This is still insufficient. Adoption requires a preregistered external denotation law that prevents simultaneous relabeling of exchangeable groups, utterance classes, latent components, target blocks, and the language encoder. Language must provide distinctions unavailable from group identity, environment statistics, source/mechanism variability, state transitions, intended actions, rewards, outcomes, or completed trajectories.

## Updated decision for RQ-001

**NARROWED BEYOND EXCHANGEABILITY-BASED STRUCTURE AND REPRESENTATION IDENTIFIABILITY — NOT ADOPTED**

The only remaining candidate is:

> After applying the strongest IEM/TCL-style exchangeability-based learner and conditioning on all group, environment, state, action, reward, outcome, and trajectory information, can a preregistered externally fixed language law identify a residual raw-utterance equivalence and latent intervention-target partition while eliminating every joint relabeling that preserves the complete exchangeable data law?

Adoption now requires at minimum:

1. a formal distinction among raw utterances, observed group labels, inferred environments, action targets, and latent intervention targets;
2. an immutable reproduction of the official IEM/Causal-de-Finetti implementation at exact commits;
3. a benchmark-specific audit of exchangeability, within-group sample counts, and cause/mechanism variability;
4. the maximal latent/causal partition recoverable from exchangeable non-i.i.d. data without language semantics;
5. a concrete countermodel pair with identical exchangeable environment-conditioned laws but different utterance and target partitions;
6. language information unavailable from environment identity, state, action, reward, outcome, and completed trajectories;
7. a denotation anchor fixed before model fitting;
8. proof that the residual joint automorphism group is trivial with the anchor and nontrivial without it;
9. direct recovery metrics for both partitions rather than causal-direction accuracy or task success alone;
10. language-blind, state-only, environment-label-shuffle, target-label-shuffle, outcome-shuffle, and within-group language-shuffle controls on identical instances;
11. preregistration before any new architecture or mechanism is authorized.

## Status

- RQ-001: further narrowed; not adopted
- exchangeability-based causal/representation identification: prior art
- official public code: verified
- immutable public baseline reproduction: not started
- raw-language equivalence identification: not established
- semantic intervention-target joint identification: not established
- new architecture: none
- experiment started: no
- resource reporting: not applicable; no experiment started
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
