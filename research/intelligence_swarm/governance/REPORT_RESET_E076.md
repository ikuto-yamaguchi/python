# RESET-E076 — Official-contract infrastructure qualification result

Date: 2026-07-27

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001` only. A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。既存stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。

## SILG/RTFM infrastructure result

Run `30258965674` / job `89954109262` completed. Immutable artifact `8650362356` was preserved with digest `sha256:975d5c6223637f48c3e358d51ead0470e3f97b01826e2cd6e216fd484b8f8750` and size `61,174,640` bytes.

The short seed-1 segment retained the pinned public sources and official sampling defaults:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- `model=multi`, `stateful=false`
- actors `30`, batch `24`, unroll `80`, threads `4`
- learning rate `0.0005`, RMSprop, gradient clip `40`
- train `rtfm_train_s1`, validation `rtfm_test_s1`

Verified:

- official command parity
- exact official `job.tar` preservation
- checkpoint model state equals exported model state
- optimizer state: 73 entries, one parameter group
- scheduler and frame counter present
- checkpoint frames `40,320`
- checkpoint bytes `39,266,613`
- checkpoint SHA-256 `1ce3a0590611d8d26ef06330e7f5eca43e9c13deafb8d41bf3570eadaa754675`

Resource result:

- peak RSS `9,305,052 KiB`
- wall `631.66 s`
- throughput `63.83 frames/s`
- projected 100M-frame wall `18.13 runner-days` for one entropy/seed run

The infrastructure qualification is rejected only because the official checkpoint does not preserve RNG state or the exact learner-batch state. Therefore one-step resume equivalence is unverified.

Formal classification:

> **`resume_equivalence_instrumentation_gap`**

This is not an optimizer failure, public-baseline failure, or capability failure. It does not recognize a new mechanism, intelligence principle, or capability progress.

## Next single fix

Instrument only the missing resume evidence:

1. capture Python, NumPy and Torch RNG states at a checkpoint boundary;
2. capture or deterministically fingerprint the exact learner batch consumed by the next update;
3. restore model, optimizer, scheduler, frame counter and RNG state;
4. replay exactly one update from the same batch;
5. require exact equality of resulting model tensors, optimizer slots, scheduler/frame state and scalar losses.

The model, source pins, optimizer, official sampling defaults, split and capability evaluation remain unchanged. No new mechanism family or toy hypothesis is introduced.

## Controls and evaluation contract

This run is infrastructure-only. Random was recorded as a plumbing probe. Language-blind, state-only and language-shuffle are explicitly not applicable here and remain mandatory for the later official capability reproduction. D015〜D035 remain frozen.

## Prior-art boundary

Mind Dreamer (ICML 2026) uses active causal interventions on latent world-model manifolds and reports faster sparse-reward learning. This makes active latent-state intervention, adversarially generated intervention anchors, and relay-value propagation insufficient by themselves for RQ-001 novelty. It is not a substitute for SILG/J-CRe3 reproduction, and no paper result is imported as capability evidence.

RQ-001 remains narrowed and not adopted.

## Formal status

- immutable R0.1 short-horizon screening artifacts: **8**
- official-contract infrastructure artifact: **1, rejected on resume evidence only**
- official SILG 100M-frame reproduction: **0**
- competent external baseline reproduction: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected/closed**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
