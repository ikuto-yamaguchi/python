# Phase 18d-7: locally stationary Viterbi program induction

## Motivation

Phase 18d-3 through 18d-6 used an exact disjoint-cover search to partition mixed records into latent programs. That is scientifically clean for small campaigns, but exact cover is exponential in the worst case and is not a plausible large-stream learning mechanism.

Phase 18d-7 replaces exact cover at the large stage with a dynamic program. It assumes that nearby records often share a latent behavior, analogous to local topical or task persistence in a sequence.

## Input and state library

A small Phase 18d-6 calibration stream still identifies the UTF-8 delimiter roles and private-use numeric codebook. The large experiment then receives 252 byte records arranged as 21 locally stationary blocks. Task IDs, task count, and block boundaries are not supplied to the learner.

The frozen DSL is enumerated once through cost three and deduplicated by behavior on a finite probe set. This yields 130 candidate states across numeric and string signatures.

## Dynamic program

For state `z_t` and record `x_t`, the objective is

`program_cost(z_0) + sum emission(z_t, x_t) + lambda * sum [z_t != z_(t-1)]`.

An exact prediction has zero emission cost, a wrong prediction has a fixed penalty, and incompatible signatures have infinite cost. Because every switch has the same penalty, the best and second-best previous states are sufficient. Inference therefore uses `O(NK)` time and `O(NK)` backpointers rather than global exact cover.

## Identification controls

- With switch penalty zero, spurious identity-like programs can explain individual records and the recovered audit labels degrade.
- Randomly shuffling the stream destroys local stationarity and also degrades recovery.
- Doubling the record stream must approximately double measured Viterbi operations.
- Empty input, ambiguous context, and a behavior outside the used library must abstain.

These controls show that local persistence is an actual source of identification, not decorative regularization.

## Continual learning

The initial stream contains seven latent behaviors. Twelve appended byte records introduce `MIN2` after the learner is frozen. The same candidate library and Viterbi algorithm must discover an eighth used behavior with no source change, while preserving the initial behavior fingerprint.

## Claim boundary

This phase removes large-stage exact-cover dependence only under a locally stationary context assumption. A small codec-calibration prefix still uses Phase 18d-6 exact cover. The primitive DSL, UTF-8 atom family, switch/error penalties, complete support records, and evaluation protocol remain human-designed. Arbitrary interleaving, natural-language context learning, open primitive invention, and LLM-like pretraining are not solved.
