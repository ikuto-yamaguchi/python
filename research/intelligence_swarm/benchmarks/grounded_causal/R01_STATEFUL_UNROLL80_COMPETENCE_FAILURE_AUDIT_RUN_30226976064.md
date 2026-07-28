# R0.1 stateful + unroll-80 competence failure audit — run 30226976064

## Scope

This record preserves the completed single-factor R0.1 screening that changed only:

- `unroll_length: 20 -> 80`

The following remained fixed:

- SILG commit `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` model
- `stateful=true`
- entropy cost `0.05`
- actors `2`
- threads `1`
- batch size `2`
- requested frames `131072`
- seeds `1 / 7 / 19`
- train/test split
- matched evaluation instances
- Correct / Random / Language-blind / State-only / Language-shuffle controls

No architecture, operation, goal, task, or representation hypothesis was introduced.

## Immutable workflow evidence

- GitHub Actions run: `30226976064`
- execution head: `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- job: `unroll80-screening`
- artifact ID: `8640762353`
- artifact name: `r01-silg-rtfm-unroll80-30226976064`
- artifact size: `91,615,226 bytes`
- artifact digest: `sha256:4e7fbacc077121d3fd09db1f6b7ec19a00942f8dc4cbf29b6cb9fd6eb18c9f4c`

Training, matched controls, recurrent diagnostics, official-evaluation parity, resource capture, dependency capture, and artifact upload all completed. The unchanged qualification gate rejected the bundle.

## Qualification result

Classification:

`optimization_or_policy_competence_failure`

Failures:

- `correct_not_above_random_win_rate`
- `correct_not_above_random_return`

Three-seed aggregate:

| metric | Correct | Random | Correct - Random |
|---|---:|---:|---:|
| win rate | 0.033333 | 0.066667 | -0.033333 |
| mean return | -1.805999 | -1.151333 | -0.654666 |

Control win rates:

| method | win rate |
|---|---:|
| Correct | 0.033333 |
| Random | 0.066667 |
| Language-blind | 0.033333 |
| State-only | 0.000000 |
| Language-shuffle | 0.033333 |

Therefore `unroll_length=20` shortage is rejected as the sole explanation for the failed R0.1 competence gate.

## Model and execution resources

- parameters: `6,200,115`
- trainable parameters: `6,200,115`
- state-dict bytes: `24,828,505`
- CPU forward latency: `8.24688742 ms/step`
- checkpoint frames: `131,200` for all three seeds, equal to the first complete `batch_size * unroll_length = 160` frame learner-update boundary at or above 131,072

Per-seed training evidence:

| seed | wall time (s) | peak RSS (KiB) | checkpoint bytes | model-state bytes |
|---:|---:|---:|---:|---:|
| 1 | 1479.478226 | 1699780 | 49534085 | 24827943 |
| 7 | 1479.020233 | 1467976 | 49534085 | 24827943 |
| 19 | 1560.066752 | 2498024 | 49534085 | 24828026 |

## Policy and recurrent-state diagnostics

All selected actions were valid under the official action mask. The recurrent path was active, so this is not a recurrence-disabled artifact.

| seed | wins / 20 | used actions | masked entropy mean | recurrent L2 before mean | recurrent L2 after mean |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 / 20 | 4 | 1.361110 | 1.733313 | 1.765367 |
| 7 | 0 / 20 | 3 | 1.246355 | 1.708052 | 1.758331 |
| 19 | 1 / 20 | 3 | 1.245853 | 18.121772 | 18.429903 |

Seed 19 developed a recurrent-state norm roughly one order of magnitude above seeds 1 and 7 and saturated near `19.14` in many long episodes. This is evidence of seed-sensitive learner instability, not evidence of competence or representation progress.

The training logs also show large late-stage policy-gradient and total-loss oscillation, including alternating positive and negative total losses with magnitudes above 30 and a late value above 58. These observations justify selecting a learner-stability factor next. They do not establish that any particular factor will repair competence.

## Official versus matched evaluation

The official continuous stream did not reveal hidden competence absent from fresh matched instances. Per-seed official-stream win rates were `0.05 / 0.00 / 0.00`; fresh-instance win rates were `0.05 / 0.00 / 0.05`. Evaluation semantics therefore remain rejected as the main cause.

## Next single-factor contract

The next screening must change exactly one learner-stability factor while preserving the complete contract above.

Selected factor:

- gradient clipping instrumentation and official-value parity

Required procedure:

1. Record the exact public SILG clipping implementation and default value from the pinned source.
2. Record pre-clip and post-clip gradient norms per learner update without changing optimization behavior.
3. If the current harness already matches the pinned implementation and value, do not claim a clipping mismatch; use the measurements to select the next single factor.
4. If a concrete mismatch is proven, correct only that mismatch and rerun seeds `1 / 7 / 19` at the same frame budget and split.
5. Re-run the unchanged matched controls, recurrent diagnostics, official-evaluation parity, resource audit, and qualification gate.

R0.2 remains blocked until a competent R0.1 external baseline bundle passes the fixed qualification gate.

## Formal status

- R0.1 stateful + unroll-80 reproduction: completed
- unroll shortage as sole cause: rejected
- competent external baseline reproduction: not achieved
- qualified R0.2 Environment-first comparison: not started
- task success / next-state prediction / action accuracy / dynamics transfer: not measured for R0.2
- entity and language-form transfer in RTFM S1: not applicable under the fixed environment contract
- new intelligence principle: not claimed
- capability progress: not claimed
