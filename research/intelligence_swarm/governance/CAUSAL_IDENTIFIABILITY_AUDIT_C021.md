# Causal Identifiability Audit C021

Date: 2026-07-25
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **latest-primary-work prior-art refinement + theorem/assumption comparison + identifiability counterexample + public-code availability audit**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark, memory mechanism, or branch was introduced.

## Primary work newly audited

### Beyond identifiability: Learning causal representations with few environments and finite samples

Inbeom Lee, Tongtong Jin, and Bryon Aragam, arXiv:2603.25796, first posted 2026-03-26.

Primary source:

- arXiv: https://arxiv.org/abs/2603.25796

The paper studies high-dimensional linear causal representation learning with an unknown full-column-rank linear decoder, an unknown linear latent SEM, and multiple environments produced by unknown multi-node interventions. It moves beyond population identifiability and gives finite-sample guarantees for recovering the latent graph, decoder/representations, and intervention targets.

No author-linked official implementation was located from the arXiv record or targeted repository search at audit time. Therefore no public-code reproduction was started in this cycle.

## Exact theorem boundary relevant to RQ-001

The observed variables satisfy `X = BZ`, where `B` is unknown and full column rank, and `Z` follows an unknown linear SEM. Environment `k` intervenes on an unknown target set `I(k)`.

The central design assumption is a strongly separating intervention family: for every pair of latent variables, there are environments that intervene on one but not the other in both directions. With an observational environment and the paper's paired noise-scale conditions, Theorem 2.1 identifies, up to scale and label permutation:

1. the latent causal graph;
2. the causal representations;
3. the decoder;
4. every unknown intervention target set.

Corollary 2.2 states that `K = Theta(log d)` environments suffice. The paper further supplies nonasymptotic consistency/error guarantees rather than only a population-level uniqueness statement.

## Theorem/assumption comparison

| Dimension | Lee, Jin, and Aragam 2026 | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Mixing | Unknown full-rank linear decoder | Intended nonlinear/perceptual observations | Language cannot claim novelty for solving the already-covered linear class |
| Latent dynamics | Unknown linear acyclic SEM | General interactive dynamics | State the exact model class not covered by the finite-sample theorem |
| Interventions | Unknown multi-node targets | Unknown latent intervention partition | Distinguish failure of strong separation from mere absence of target labels |
| Number of environments | Logarithmic in latent dimension | Potentially few language-described environments | Show language reduces requirements below the non-language design boundary or handles a class where it fails |
| Identified object | Graph, representations, decoder, and targets | Raw-language equivalence jointly with target partition | Prove language identifies an additional object, not merely predicts already identifiable targets |
| Guarantee | Finite-sample recovery under stated conditioning/separation assumptions | Population joint identifiability plus eventual estimation | Supply both an anti-recoding theorem and a statistically estimable procedure |
| Language | Absent | Discrete stochastic channel | Establish residual information after conditioning on all environment covariance information |

## Prior-art matrix refinement

The following claims are no longer admissible as novel language-grounding claims in the audited linear class:

- unknown multi-node intervention targets require language to be recovered;
- a large number of individually targeted environments is necessary;
- target labels or target descriptions are required for finite-sample consistency;
- recovering the intervention incidence matrix from environment shifts is a language-specific contribution;
- language improves identifiability merely because it names which mechanisms changed;
- empirical target-prediction gains establish a finer partition than the strongly separating non-language estimator.

## Counterexample: target-descriptive language is redundant under strong separation

Let `E` denote the environment index and let `S(E)` be the intervention-incidence signature recoverable from the family of environment covariance changes under the audited assumptions. Let raw language be generated as

`L ~ p(L | S(E))`.

Suppose two language systems use different utterance forms and paraphrase distributions but induce the same conditional law over the already recoverable target signature. Because the non-language estimator consistently recovers `S(E)`, the latent graph, decoder, and target sets, adding `L` cannot shrink the causal-model equivalence class.

Formally, for every admissible model in this theorem class,

`L ⟂ P_residual | S(E), X, E`,

and the theorem leaves no residual target partition beyond scale and label permutation. Language may improve finite-sample prediction or provide human-readable names, but it does not add population identifiability.

Therefore:

> In a strongly separating linear intervention design where targets are already finitely recoverable from environment statistics, raw language that only describes those targets is an annotation channel, not a joint-identification channel.

## Stronger boundary for interactive language

Interaction is not sufficient by itself. If a query response is a stochastic function of the environment index, recovered incidence signature, current observation, or completed transition, it remains redundant with the non-language sufficient statistics.

For language to contribute a genuinely new identification result, it must do at least one of the following under a formally stated model class:

1. replace a missing strongly separating intervention contrast and still identify a distinction that the non-language environments cannot separate;
2. identify under nonlinear mixing or dynamics where the audited linear finite-sample theorem does not apply;
3. fix semantic labels beyond unavoidable permutation through an external denotational anchor;
4. reduce a proved environment/sample complexity lower bound, rather than only improve an empirical metric.

## New impossibility condition

If the available environment family is not strongly separating, language cannot repair it when the language law is measurable with respect to the same non-separating incidence code.

Let latent variables `i` and `j` have identical intervention-membership vectors across all environments. If

`p(L | E, Z) = p(L | E, S(E))`

and the language channel assigns the same distribution to environments that do not distinguish `i` from `j`, then exchanging or mixing `i` and `j` within the remaining admissible equivalence class leaves the full law of `(X, E, L)` unchanged. Thus language must contain an externally anchored contrast that is absent from the environment incidence design; paraphrases of the same deficient design do not suffice.

## Updated admissible RQ

The remaining candidate is narrowed to:

> When the non-language intervention design fails a stated separation condition or the observation/dynamics class lies outside existing finite-sample CRL results, can an externally anchored population language channel supply a missing contrast that strictly shrinks the residual causal equivalence class and jointly identifies raw-utterance equivalence with a refined intervention-target partition, with an estimator and finite-sample guarantee?

This formulation is **not adopted**. It remains a preregistration candidate only.

## Adoption requirements added by C021

Before adoption, the candidate must provide:

1. an explicit countermodel showing which target distinction remains unidentified after applying the strongest applicable non-language estimator;
2. a language observation assumption that is not measurable with respect to environment identity, incidence signatures, observations, actions, outcomes, or completed trajectories;
3. an externally fixed contrast that breaks the residual symmetry;
4. a theorem proving strict equivalence-class reduction beyond scale/label permutation or the applicable quotient;
5. an impossibility result when the language contrast is removed or made incidence-measurable;
6. an estimator with finite-sample or consistency analysis, not only a population argument;
7. direct comparison against non-language strongly separating and deliberately non-separating designs;
8. unseen utterance-form, composition, target-combination, and system splits;
9. public baseline reproduction and one preregistered central claim before any architecture work;
10. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED TO LANGUAGE-SUPPLIED MISSING SEPARATION BEYOND FINITE-SAMPLE UNKNOWN-TARGET CRL — NOT ADOPTED

Unknown multi-node targets, logarithmically many environments, and finite-sample target recovery are already covered in a meaningful linear class without language. The surviving research question must operate beyond that theorem boundary and demonstrate that language supplies a genuinely missing, externally anchored separation rather than labels an incidence structure recoverable from environment statistics.

No experiment or architecture is authorised by this result.

## Resource accounting

This cycle is a theorem, assumption, prior-art, code-availability, and counterexample audit only. No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable here and remain mandatory once an experiment begins.

## Status

- completed this cycle: 2026 primary-work refinement, theorem/assumption comparison, code-availability audit, and strong-separation language-redundancy counterexample
- unknown multi-target recovery as a novel language contribution: rejected in the audited linear class
- logarithmic-environment target recovery as a novel language contribution: rejected in the audited linear class
- RQ-001: further narrowed, not adopted
- public capability baseline: not reproduced
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
