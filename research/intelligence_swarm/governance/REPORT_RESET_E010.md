# RESET-E010 — Public recurrent smoke integration and matched-evaluation lock

## Decision

**Continue R0 Research Reconstruction. Do not transition stages. Do not activate a new mechanism family.**

The official SILG/RTFM recurrent training path is now reproduced as an engineering smoke test for canonical seeds 1, 7 and 19, but no learned public capability baseline has passed the evaluation contract.

## 1. Primary-literature and official-code overlap audit

This cycle rechecked the closest primary research lines and found no basis for broadening RQ-001-N3.

Already covered by prior art:

- unknown intervention-target recovery from heterogeneous environments;
- latent causal representation recovery under unknown interventions;
- causal abstraction as the identifiable object under subset interventions;
- causal representation recovery from general environments under nonparametric mixing;
- interactive language grounding on SILG;
- environment-first and language-dynamics pretraining.

The current gap, if any, remains narrower: whether raw language provides information about held-out mechanism changes beyond state/action/history/reward/environment identity on a matched public benchmark, and only then whether a language-conditioned intervention abstraction can be recovered up to shared permutation or supported abstraction.

No new primary source found in this cycle establishes that exact joint claim under equal or weaker assumptions. This is not evidence of novelty; the question remains **narrowed and unadopted**.

## 2. SILG / RTFM reproduction status

Verified repository result:

- workflow run: `30104299406`;
- SILG SHA: `2af07578e1264029a240fcfb78d4ac0aea16f5de`;
- RTFM SHA: `58f17955595b5a127c96d045d896fcbcc7d4b570`;
- model: official SILG `multi` recurrent;
- pretrained LM: none;
- environment: `silg:rtfm_train_s1-v0`;
- validation target: `silg:rtfm_test_s1-v0`;
- seeds: `1,7,19`;
- training budget: 2,048 frames per seed;
- all three training runs completed.

Engineering measurements:

| Seed | Wall time | Peak RSS |
|---:|---:|---:|
| 1 | 26.547 s | 462,752 KiB |
| 7 | 26.531 s | 516,792 KiB |
| 19 | 31.536 s | 481,432 KiB |

- parameters: 4,916,915;
- state dict: 19,694,385 bytes;
- CPU forward: 7.49024244 ms/environment step;
- maximum RSS: 516,792 KiB;
- top-level artifact digest: `sha256:51d8bfb3fe31f4a00d9b5f86f1bc2761da5f91c70067d222e8f376f334418070`.

Classification: `official_recurrent_training_smoke_not_full_baseline_reproduction`.

## 3. Matched controls

Current status:

- random: public control exists, but not on the same replayed test instances;
- language-blind: absent;
- state-only: absent;
- environment-ID-only: absent;
- language shuffle: absent;
- target-label shuffle: absent;
- outcome/transition shuffle: absent;
- recurrent checkpoint test predictions: absent.

Therefore there is no valid Correct-control capability comparison.

## 4. Resource and artifact audit

Available:

- model parameter count and state-dict bytes;
- state-dict SHA-256;
- peak RSS and training time for three seeds;
- CPU forward latency;
- source pins and top-level workflow artifact digest.

Still missing for a completed capability reproduction:

- frozen test dataset checksum;
- per-instance fingerprints;
- full per-run raw-log SHA-256 rather than truncated summaries;
- per-run code commit;
- complete method × seed × split artifact coverage;
- checkpoint test inference logs.

Formal classification remains `initial_reproduction_failure` for public capability reproduction. This does not invalidate the training-path smoke.

## 5. Leakage and statistics

`evaluation_contract.py` now checks:

- utterance, entity and dynamics train/test overlap;
- gold action, after-state and completed-trajectory leakage;
- immutable instance-snapshot equality across methods;
- seed/domain/split/method coverage;
- prediction coverage;
- domain × seed × condition cells;
- paired gaps, minimum cell gap, approximate 95% CI and paired randomization p-value;
- model/data/log checksums and resource metadata.

Six regression tests pass. No current public capability result passes the contract because predictions and matched controls are absent.

## 6. RQ-001 status

RQ-001-N3 remains **NARROWED, NOT ADOPTED**.

- Gate L is not operational because matched Full/state-only/language-shuffle results do not exist.
- Gate I is not authorized because Gate L is untested and the benchmark's intervention diversity has not yet been shown to define a nontrivial partition without a hand-written ontology.
- No novelty, intelligence principle or capability progress is recognized.

## Maximum bottleneck

Capture a deterministic `rtfm_test_s1-v0` instance set for seeds 1, 7 and 19 once, preserve the immutable fingerprint of every input snapshot, and replay it through the learned recurrent checkpoint and all required controls with complete artifact coverage.

## Track assignment

- A/R0.1: deterministic test-instance capture, checkpoint save/load and official recurrent test evaluation.
- B/R0.2: wait for R0.1 replay; then run public environment-first and matched end-to-end baselines.
- C/R0.3: continue prior-art and identifiability audit; do not implement Gate I.
- D: enforce evaluation contract, full hashes and coverage; reject unmatched scores.
- E: keep one canonical branch, prevent toy branches and update stage only after a learned public capability baseline passes.

## Stage-transition decision

**No transition.** R0.1–R0.3, novelty matrix and central-claim preregistration are incomplete.

## Status

- learned public capability baseline: 0;
- public recurrent training-path smoke: 1;
- new intelligence principle: none;
- novelty: not established;
- high-school-level intelligence: not achieved;
- completion: false.
