# Optimizer–Architecture Coupling Study

## Why this experiment exists

The sequence-architecture map showed that short-distribution validation and length extrapolation can prefer different model families. It also showed that a lightly trained tiny model is not a reliable architecture ranking.

A second confound remains: every architecture was trained with AdamW. Recent sequence-model work often changes architecture and optimizer together, making it unclear whether a reported gain belongs to the recurrence, the memory rule, or the update geometry.

## Hypothesis

A sequence mechanism is not a stable candidate intelligence principle when its apparent advantage disappears or reverses under a reasonable optimizer change.

The experiment crosses four sequence mechanisms with two optimizer regimes:

- GRU;
- one-layer causal Transformer;
- RWKV-7 x070 mechanism probe;
- gated DeltaNet mechanism probe;
- AdamW;
- Muon-style orthogonalized momentum for matrix parameters, with AdamW retained for vectors and normalization parameters.

## Controls

- identical model constructors to the architecture-map PR;
- identical training examples, answer-weighted language objective, seeds and validation episodes;
- 512 and 2048 training episodes;
- seeds 1, 7 and 19;
- 12 epochs;
- ordinary validation and depth-18 length extrapolation reported separately;
- parameter count, serialized bytes, peak RSS, training time, state bytes, full-pass token time, candidate count and state reads recorded;
- gradient norm and a parameter-update proxy recorded to expose unstable or ineffective optimizer regimes.

## Counterexamples

The hypothesis is weakened when architecture ordering remains stable across optimizers and data scales. It is supported when rankings reverse, when one optimizer helps only one family, or when an optimizer lowers training loss without improving held-out state use.

Muon in this directory is a compact Newton–Schulz mechanism probe. It is not claimed to be an exact reproduction of every current Muon implementation or training recipe.

## Claim boundary

This study does not establish free Japanese dialogue, instruction following, reading, reasoning, planning, causal or counterfactual reasoning, long dialogue, continual learning, or weak-phone deployment.

`highschool_level_passed=false`

`native_japanese_communication_passed=false`

`weak_smartphone_verified=false`

`completion=false`
