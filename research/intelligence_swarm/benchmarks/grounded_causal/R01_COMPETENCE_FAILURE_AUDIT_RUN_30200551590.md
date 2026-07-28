# R0.1 competence failure audit — run 30200551590

## Decision

**R0.2 remains blocked. Classification: `optimization_or_policy_competence_failure`.**

This audit records a completed immutable R0.1 run rather than introducing a new mechanism, architecture, operation hypothesis, or goal hypothesis.

## Immutable provenance

- GitHub Actions run: `30200551590`
- Source branch: `research/intelligence-swarm-reconstruction-001`
- Source head: `891ff7caa42a4077e7b7d6d4e1d54e0a2d091918`
- Artifact: `r01-silg-rtfm-matched-30200551590`
- Artifact id: `8632386082`
- Artifact digest: `sha256:f7cf661e7db9a5dc8c922d9a4fa10b3e355ee8a22de0406267aad3dbcbc53d25`
- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Environment: `silg:rtfm_train_s1-v0`
- Evaluation environment: `silg:rtfm_test_s1-v0`
- Model: official SILG `multi` recurrent
- Pretrained language model: none
- Seeds: `1`, `7`, `19`

## Training and resource evidence

Each seed requested 131,072 frames and terminated at the first complete learner-update boundary, 131,080 frames (`batch_size=2`, `unroll_length=20`).

| Seed | Frames | Wall time (s) | Peak RSS (KiB) | Checkpoint bytes | State bytes |
|---:|---:|---:|---:|---:|---:|
| 1 | 131,080 | 948.042 | 1,347,912 | 39,266,677 | 19,693,911 |
| 7 | 131,080 | 942.202 | 1,132,624 | 39,266,677 | 19,693,911 |
| 19 | 131,080 | 958.047 | 1,183,440 | 39,266,677 | 19,693,990 |

Model audit:

- Parameters: `4,916,915`
- Trainable parameters: `4,916,915`
- State-dict bytes: `19,694,385`
- CPU forward latency: `4.44475517 ms/step`
- Total training wall time: `2,851.02675 s`

All three training jobs and checkpoint exports completed successfully. Therefore this run is not an install, schema, checkpoint, frame-accounting, resource-evidence, or checksum failure.

## Same-instance matched evaluation

Evaluation used 20 fixed episodes per method and seed for:

- Correct recurrent
- Random valid-action policy
- Language-blind
- State-only
- Language-shuffle

Aggregate qualification metrics:

| Metric | Correct | Random | Difference |
|---|---:|---:|---:|
| Win rate | 0.016667 | 0.066667 | -0.050000 |
| Mean return | -1.727333 | -1.151333 | -0.576000 |

Control win rates:

- Language-blind: `0.016667`
- State-only: `0.016667`
- Language-shuffle: `0.016667`
- Random: `0.066667`

The exact qualification failures were:

- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

## Diagnosis bounded by the reconstruction contract

The recurrent policy completed training but remained nearly indistinguishable from the language ablations and below the random valid-action policy. Its mean episode lengths were also substantially longer than random on the same instances, so the return deficit is not explained by random receiving harder episodes. This is competence failure under the fixed 131,072-frame screening budget, not evidence for an Environment-first advantage.

The run does **not** justify bypassing the R0.1 gate and does not justify changing the model family. The next permitted work is limited to auditing the faithful reproduction path:

1. compare the exact official command/defaults against the harness overrides (`num_actors`, `batch_size`, `unroll_length`, `entropy_cost`, deterministic actor/validation seeding);
2. verify recurrent-state reset/detach and checkpoint restore during matched evaluation;
3. record predicted-action histograms, valid-action-mask interaction, entropy, and termination causes per seed;
4. change only one demonstrated harness mismatch, then repeat the identical matched evaluation.

No R0.2 task-success, next-state, action-accuracy, or dynamics-transfer result may be recognized until Correct exceeds Random under the qualification contract.

## Claims

- R0.1 public baseline competence: **not reproduced**
- R0.2 Environment-first comparison: **not started**
- Entity/language-form transfer on RTFM S1: **not applicable**
- Dynamics transfer: **not measured**
- New architecture: **none**
- Novelty: **not claimed**
- Intelligence principle: **not claimed**
- Capability progress: **not claimed**
