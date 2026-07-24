# Causal Identifiability Audit C006

Date: 2026-07-25

## Scope

This cycle adds no architecture and no synthetic mechanism. It completes two reconstruction tasks:

1. a theorem/assumption comparison for when language can refine a trajectory-only causal equivalence class;
2. a public-benchmark qualification audit for Gate I.

## Conditional-information requirement

Let:

- `X` be all non-linguistic information available to the learner: state trajectory, actions, history, reward, time, policy phase and environment identity;
- `L` be episode-aligned raw language;
- `M` be the benchmark-defined mechanism/intervention class, evaluated only up to the finest intervention-supported causal abstraction and joint permutation.

A necessary condition for language to improve identifiability beyond trajectory-only CRL is:

`I(M; L | X) > 0`.

If `M` and `L` are conditionally independent given `X`, then the posterior over mechanism classes is unchanged:

`p(M | X, L) = p(M | X)`.

Therefore no learner, regardless of architecture, can use language to split a trajectory-only equivalence class. Predictive gains caused by environment ID, reward density, task family, policy phase or episode progress do not satisfy Gate I because those variables belong in `X`.

This is only a necessary condition. Positive conditional information does not by itself prove semantic or causal identification. Gate I additionally requires:

1. a benchmark-defined mechanism variation not authored by this project;
2. a characterized trajectory-only equivalence class;
3. refinement under correct language;
4. no refinement under within-context language shuffle;
5. preservation under meaning-preserving paraphrase;
6. held-out mechanism prediction or online capability improvement;
7. permutation/abstraction-aware scoring;
8. reproduction across at least two environment families and seeds 1, 7 and 19.

## Relation to prior art

The remaining claim cannot be stated as any of the following, because each is already covered by prior work:

- unknown intervention-target recovery;
- causal abstraction under subset interventions;
- multimodal shared-latent identifiability;
- mapping perturbation features to intervention distributions;
- causal sufficiency/necessity of multimodal representations;
- environment-first or language-conditioned dynamics pretraining;
- estimating the causal effect of a language change on an outcome.

The only potentially distinct empirical claim is incremental identifiability: language removes a mechanism ambiguity that remains after conditioning on all non-linguistic trajectory information.

## Gate-I public benchmark qualification

| Benchmark | Raw episode language | Interactive/temporal trajectory | Independent mechanism variation | Ground-truth target or justified abstraction | Held-out mechanism split | Permutation-aware scoring possible | Gate-I qualified |
|---|---:|---:|---:|---:|---:|---:|---:|
| SILG / RTFM | yes | yes | no | no | no | no | no |
| J-CRe3 | yes, Japanese dialogue | temporal video/dialogue | no intervention family | reference annotations only | no | no | no |
| CausalTriplet | no natural-language instruction stream | paired visual observations | yes | supplied intervention structure | limited | yes | no |
| ACCESS | natural-language event descriptions | no interactive trajectory | abstract event-causal pairs | annotated event relation | OOD lexical/abstraction tests, not mechanism intervention | partial | no |
| MIB | language-model tasks | model-internal activation traces, not environment trajectories | benchmark-defined model interventions | causal variables/pathways inside fixed models | task/model splits | yes | no |
| SILG + researcher-authored intervention labels | yes | yes | authored by this project | authored by this project | configurable | configurable | prohibited |

No audited benchmark satisfies all Gate-I requirements. In particular:

- SILG remains valid for Gate L, but has no latent intervention-family ground truth.
- J-CRe3 is useful for Japanese grounding realism but is not a mechanism-change benchmark.
- CausalTriplet supplies intervention structure but lacks the raw interactive language view needed by the claim.
- ACCESS tests abstract event causality in text but not intervention-conditioned environment dynamics.
- MIB concerns causal structure inside language models, not the language-to-world intervention partition.

## Decision

### Empirical Gate I

Status: **UNAVAILABLE ON AUDITED PUBLIC BENCHMARKS**.

Do not create a synthetic benchmark or add handwritten mechanism labels to SILG. That would reintroduce the ontology the reconstruction explicitly forbids.

### RQ-001-N5

> On an independently defined public mechanism-change benchmark, does episode-aligned raw language contain mechanism information conditional on the complete non-linguistic trajectory, and does that information strictly refine the trajectory-only causal equivalence class while improving held-out mechanism capability under shuffle, paraphrase and permutation-aware controls?

Status: **NARROWED, NOT ADOPTED; EMPIRICAL TRACK BLOCKED BY BENCHMARK UNAVAILABILITY**.

The empirical claim must be rejected if no qualifying public benchmark is identified after the novelty audit. A theory-only route may remain, but it must state explicit observability and intervention assumptions and must prove either an impossibility result or a sufficient condition stronger than `I(M;L|X)>0`.

## Program consequences

1. Continue SILG only for Gate L and public capability reproduction.
2. Do not interpret R0.2 language gains as Gate I evidence.
3. Do not start hidden-intervention-target ablations on SILG.
4. Search only for independently defined public mechanism-change datasets with aligned raw language.
5. If none is found, formally close empirical Gate I and preregister a theory-only question.
6. No new architecture is authorized.

## Sources checked

- Li et al., *On the Identifiability of Causal Abstractions*, AISTATS 2025.
- Varici et al., *Score-based Causal Representation Learning: Linear and General Transformations*, JMLR 2025.
- Schneider et al., *Generative Intervention Models for Causal Perturbation Modeling*, ICML 2025.
- Wang et al., *Towards the Causal Complete Cause of Multi-Modal Representation Learning*, ICML 2025.
- Durand et al., *Learning Causal Response Representations through Direct Effect Analysis*, UAI 2025.
- Lin et al., *Isolated Causal Effects of Natural Language*, ICML 2025.
- Benhamza et al., *Identifiable Multimodal CRL under Partial Latent Sharing*, 2026.
- Zhong et al., *SILG*, NeurIPS 2021.
- Ueda et al., *J-CRe3*, 2024.
- Liu et al., *CausalTriplet*, CLeaR 2023.
- Vo et al., *ACCESS*, 2025.
- Mueller et al., *MIB*, ICML 2025.
