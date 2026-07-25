# Causal Identifiability Audit C027

Date: 2026-07-26
Track: C — causal grounding / identifiability
Stage: R0 Research Reconstruction

## Cycle outcome

Completed: **prior-art matrix refinement + empirical assumption/reproduction comparison + public-code availability audit + identifiability counterexample**.

No new architecture, toy mechanism, operation/goal hypothesis, intervention ontology, benchmark variant, or branch was introduced.

## Primary work newly audited

### Sanity Checking Causal Representation Learning on a Simple Real-World System

Juan L. Gamella, Simon Bing, and Jakob Runge. ICML 2025, PMLR 267:18143–18169.

Primary records:

- PMLR: https://proceedings.mlr.press/v267/gamella25a.html
- paper: https://arxiv.org/abs/2502.20099
- official code: https://github.com/simonbing/CRLSanityCheck
- benchmark data: Causal Chambers `lt_crl_benchmark_v1`

The work evaluates representative contrastive, multiview, and temporal/interventional CRL methods on a controlled optical system whose causal inputs are known. Despite deliberately favorable conditions, all evaluated families fail to reliably recover the ground-truth causal factors on the real system. Most already fail on a simpler semi-synthetic decoder ablation. The authors isolate violations or sensitivity of mixing-function assumptions and expose a gap between population identifiability claims and practical recovery.

The official repository is public and provides an MIT-licensed implementation, recursive submodules for the evaluated methods, a conda `environment.yml`, automatic dataset access through `causalchamber`, and explicit commands for Contrastive CRL, Multiview CRL, and CITRIS on both real and semi-synthetic data. The repository is therefore a concrete public baseline candidate rather than merely a paper-only comparison.

No reproduction was started in this cycle because R0.1/R0.2 execution and artifact qualification remain the active empirical gate. The repository must be pinned to an immutable commit, including every submodule SHA, before any future reproduction claim.

## What this prior art establishes

The following cannot be treated as evidence for RQ-001 or as sufficient progress:

- citing a population identifiability theorem without reproducing its method on a controlled system;
- reporting strong next-state prediction, reconstruction, disentanglement, or task performance without ground-truth factor recovery;
- assuming that a benchmark satisfies theoretical intervention conditions while leaving the observation mixing map unaudited;
- treating success on a researcher-authored synthetic generator as evidence that the same representation is identifiable under a physical observation process;
- interpreting a language-shuffle gap as recovery of a causal partition when non-language CRL baselines cannot recover known factors on a simpler system;
- claiming that language resolves an ambiguity unless the non-language failure mode is first localized to a specific residual equivalence class rather than optimization, decoder mismatch, finite-sample error, or violated assumptions;
- introducing a new architecture before an official public baseline and its semi-synthetic control are reproduced.

## What this prior art does not establish

The work does not identify:

- an unknown equivalence relation over raw utterances;
- an unknown latent intervention-target partition jointly with that utterance relation;
- a denotation anchor that eliminates joint recoding;
- a theorem showing that language strictly refines a residual causal equivalence class;
- whether language can repair a precisely characterized non-language identifiability failure rather than merely improve optimization;
- an interactive language-grounding guarantee under the requested leakage exclusions.

It is an empirical falsification and reproducibility boundary, not a positive joint-identification result.

## Assumption and evidence comparison

| Dimension | CRL Sanity Check | Current RQ-001 candidate | Remaining burden |
|---|---|---|---|
| Ground truth | Known physical control variables | Unknown raw-language classes and residual target partition | Provide direct partition ground truth or an equivalent falsifiable oracle |
| Intervention signal | Controlled interventions / views in a physical chamber | Unknown target interventions plus language | Separate target uncertainty from observation-mixing failure |
| Observation map | Real optical mixing and semi-synthetic decoder ablation | SILG/J-CRe3 symbolic or rendered observations | Audit whether the benchmark decoder satisfies each theorem’s assumptions |
| Baselines | Contrastive CRL, Multiview CRL, CITRIS | Strongest non-language CRL plus language candidate | Reproduce public baselines before adding architecture |
| Evidence | Factor recovery on real and semi-synthetic systems | Joint recovery of two unknown partitions | Downstream success is insufficient; score partition recovery directly |
| Failure diagnosis | Synthetic decoder ablation distinguishes optimization/assumption failures | Language may appear to help for many non-identification reasons | Add matched decoder and optimization controls |
| Guarantee | No new positive identification theorem; empirical stress test | Strict joint-identification theorem required | A performance gain cannot substitute for trivial residual automorphism proof |

## Prior-art matrix refinement

The novelty matrix must now distinguish at least four empirical levels:

1. a theorem’s population identifiability claim;
2. faithful recovery on the theorem’s own synthetic setting;
3. recovery under a matched semi-synthetic decoder ablation;
4. recovery on a controlled physical system with known factors.

A language-assisted method cannot claim identification merely by outperforming an end-to-end baseline at level 2. It must first show that the strongest applicable non-language baseline is faithfully reproduced, then localize the remaining ambiguity, and finally demonstrate that the language channel removes that exact ambiguity at levels 3–4 or an equally diagnostic public system.

The CRL Sanity Check therefore becomes a required empirical comparator class in the novelty matrix. It does not make RQ-001 old, but it raises the evidence bar: any apparent language advantage must survive a decoder/mixing ablation and direct factor-partition recovery.

## Counterexample: language gain caused by decoder mismatch, not joint identification

Let latent causal factors be `Z`, observed inputs be `X = g(Z)`, the true target partition be `P`, and raw utterances be `U`. Suppose a non-language CRL method is identifiable when `g` belongs to a theoretical class `G`, but the physical or benchmark decoder `g_real` lies outside `G`.

Construct two candidate systems:

- System A uses partition `P` and decoder `g_real`;
- System B uses a different partition `P'` related by a nontrivial latent recoding `h`, with decoder `g'_real = g_real o h^{-1}`.

Both systems induce the same observation, action, transition, and outcome distribution. Now let language contain a feature correlated with a directly observable rendering artifact or environment ID rather than an externally fixed denotation of `P`.

A language-assisted learner can improve:

- next-state prediction;
- action accuracy;
- task success;
- representation alignment;
- language-shuffle gap;
- even linear probing of the researcher’s labels;

by using that feature to compensate for decoder mismatch or finite-sample optimization. The gain can be identical under Systems A and B, while their raw-utterance equivalence and target partitions differ.

Therefore:

> A language advantage over a failing CRL baseline does not establish joint identification. Unless the non-language baseline succeeds on a matched semi-synthetic decoder and the remaining ambiguity is explicitly characterized, language may only repair model misspecification, optimization, or observation mixing.

The earlier anti-recoding condition must be paired with an empirical adequacy condition. Let `M*` be the strongest verified non-language representation obtained after public-baseline reproduction and decoder ablation. A language claim is admissible only if it distinguishes a preregistered countermodel pair that remains equivalent under `M*`, not merely a pair that the chosen baseline failed to optimize.

## Updated admissible RQ

The surviving candidate is narrowed to:

> After faithfully reproducing the strongest public non-language CRL baselines on both their synthetic assumptions and a matched semi-synthetic/physical sanity check, can an externally fixed and preregistered language law eliminate a specifically characterized residual joint automorphism over raw-utterance equivalence and intervention-target partition, rather than compensating for decoder mismatch, optimization failure, or finite-sample error?

This formulation is **not adopted**.

## Adoption requirements added by C027

Before adoption, the candidate must provide:

1. an immutable reproduction of at least one representative public CRL baseline and its official semi-synthetic control;
2. exact source, submodule, dependency, dataset, seed, and split pins;
3. direct factor/partition recovery metrics, not only task success or prediction;
4. a decoder/mixing ablation that separates theorem-assumption failure from optimization failure;
5. a concrete residual countermodel pair after the strongest verified non-language baseline;
6. proof that the language contrast is not derivable from rendering artifacts, environment IDs, intervention incidence, actions, outcomes, or completed trajectories;
7. an externally fixed denotation anchor and proof that the residual joint automorphism group is trivial;
8. true-language, language-blind, state-only, target-label-shuffle, outcome-shuffle, and rendering/decoder-control comparisons on identical instances;
9. preregistered rejection criteria when the public baseline itself is not reproduced;
10. model bytes, peak RSS, training wall time, CPU inference latency, raw logs, checksums, and seeds `1/7/19` once an experiment begins.

## Decision on RQ-001

### Decision: NARROWED BEYOND EMPIRICALLY VERIFIED CRL RECOVERY — NOT ADOPTED

The candidate remains potentially distinct only if language removes a residual equivalence class that persists after faithful public-baseline reproduction and diagnostic decoder/mixing controls. Language improving a failing or misspecified CRL baseline is not evidence of joint identification.

No experiment or architecture is authorised by this result.

## Resource accounting

No model experiment was started. Model bytes, peak RSS, training wall time, CPU inference latency, and three-seed reporting are not applicable in this cycle and remain mandatory once an experiment begins.

## Status

- completed this cycle: prior-art refinement, empirical assumption/reproduction comparison, public-code audit, counterexample
- official public code: verified available; reproduction not started in this cycle
- empirical recovery gap between CRL theory and controlled real systems: established by prior work
- language gain over an unreproduced or failing baseline: rejected as identification evidence
- RQ-001: further narrowed, not adopted
- new architecture: none
- novelty: not established
- intelligence principle: not discovered
- capability progress: not recognized
- high-school-level intelligence: not achieved
