# RESET-E065 — Unroll-80 run visibility repair and active execution tracking

Date: 2026-07-27
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- No new toy hypothesis.
- No new mechanism family.
- No separate branch or stacked PR base.
- Existing stacked draft PRs remain a negative-results archive.
- Work remains limited to public benchmark reproduction, prior-art audit, evaluation contract, and retained rejection of the hidden intervention-target empirical track.

## R0.1 active experiment

The active single-factor experiment remains:

- `unroll_length: 20 → 80`

Fixed:

- official SILG `multi`
- `stateful=true`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- frames `131072`
- seeds `1/7/19`
- fixed train/test split
- identical evaluation instances
- Random / Language-blind / State-only / Language-shuffle

The push-triggered workflow exists and is correctly wired, but the existing locator did not include it. The locator matrix and path trigger were extended in commit `746d527a0d760cc4e910e13d8913c040ee8afd5f`.

Locator evidence:

- locator run `30228319127`: success
- locator job `89862351857`: success
- detected unroll-80 run `30226976064`
- run number `2`
- execution head `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- status at integration: `pending`
- jobs at integration: `0`
- artifacts at integration: `0`

This is an execution-state observation, not a performance result. No duplicate unroll-80 run is issued while the detected run remains pending, queued, or in progress.

If the run remains jobless because of Actions capacity, policy, or scheduling, the next action is restricted to the dispatch/concurrency/permission blocker. Model, data, seed, split, and screening factor must remain unchanged.

If the run executes, it must preserve and verify:

- `--stateful` and `--unroll_length 80` in every seed command
- LSTM `core.*` weights in every checkpoint
- non-zero recurrent-state diagnostics
- Correct / Random / Language-blind / State-only / Language-shuffle on identical instances
- model/checkpoint bytes, RSS, training wall, CPU latency
- seeds, split, actual frames, logs, dependency lock, SHA-256
- leakage=false and prediction provenance
- official continuous-stream / fresh-instance parity
- unchanged qualification gate

A valid negative result rejects unroll shortage as the sole cause but does not close the cycle. Exactly one next learner-optimization factor must be selected from learning rate, gradient clipping, or optimizer/checkpoint restore using preserved evidence.

## Prior-art audit

The 2026 DCAN work on multimodal personality understanding combines:

- back-door adjustment using a prototype demographic-confounder dictionary;
- front-door adjustment using a learned mediator dictionary for latent and unobserved bias;
- accuracy and fairness evaluation;
- an author-linked public repository and DMSP dataset.

Therefore the following are excluded from RQ-001 novelty by themselves:

- dual back-door/front-door multimodal deconfounding;
- prototype confounder dictionaries;
- learned mediator intervention for unobserved bias;
- fairness gains from causal adjustment.

The author-linked repository is `Sabrina-han/DCAN`. Exact commit, dependencies, dataset checksum, commands, seeds, raw outputs, and immutable numerical reproduction remain incomplete. DCAN is not a substitute for SILG interactive policy competence or J-CRe3 real-world Japanese reference resolution.

RQ-001 decision:

> **FURTHER NARROWED BEYOND DUAL BACK-DOOR/FRONT-DOOR MULTIMODAL DECONFOUNDING — NOT ADOPTED**

## Evaluation and leakage

D015–D035 remain frozen. No new auditor was added. Every valid R0.1 bundle must still include matched controls, resource provenance, seed/split/frame identity, checksums, prediction provenance, and leakage results.

## Formal state

- immutable R0.1 artifacts: **5**
- competent learned external baseline: **0**
- active unroll-80 screening: **run 30226976064 pending; no result recognized**
- J-CRe3 numerical reproduction: **0**
- R0.2 qualified reproduction: **0**
- R0.3: **rejected and retained**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not found**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
