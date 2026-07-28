# RESET-E070 — Gradient-clipping run observability and R0 integration

Date: 2026-07-27

Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 公開benchmark再現、prior-art audit、D015〜D035 evaluation contract、R0.3 rejectionだけを累積する。
- stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。
- competent external baseline再現前に新規知能原理・能力進歩を認定しない。
- 高校生級知能は未達を維持する。

## Reproduction progress

Latest immutable accepted-as-evidence negative bundle remains learning-rate screening run `30235108376`:

- artifact `8642403437`
- execution commit `67556f067028edac502380c6d3de15575c996ffc`
- Correct `0/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `1/60`
- Language-shuffle `0/60`
- Correct return `-2.1523326`
- Random return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,470,976 / 1,269,884 / 2,414,924 KiB`
- wall `1441.30 / 1404.99 / 1483.19 s`
- leakage `false`
- qualification rejected

Learning-rate shortage remains rejected as a sole cause.

## Active gradient-clipping screening

The next single changed factor remains:

- pinned official source `clip_grad_norm_(..., 40.0)` → `10.0`

All model family, stateful, unroll, learning-rate default, entropy, actors, batch, frames, seeds, split, instances and controls remain fixed.

The workflow and source patch already existed, but the push-run locator did not query `r01_silg_gradient_clip_screening.yml`. This made run/job/artifact status unobservable and risked either duplicate expensive dispatch or false claims that the experiment had not started.

RESET-E070 updates `.github/workflows/r0_silg_rtfm_run_locator.yml` to add:

- label `gradient-clip-10`
- workflow `r01_silg_gradient_clip_screening.yml`
- latest push-run summary
- latest jobs JSON
- latest artifacts JSON

Locator integration commit: `2cc76a969e5b596ea5026960984b614608c39f23`.

At integration time, the locator had been updated but the resulting gradient-clipping run/job/artifact evidence was not yet available. Therefore no start, completion, artifact or performance result is recognized.

## Non-termination contract

1. Do not redispatch the same gradient-clip condition while a run is pending, queued or in progress.
2. If no push run exists, classify trigger routing failure and repair only trigger/path wiring.
3. If a run exists with no job, inspect Actions policy, concurrency and capacity without changing the model factor.
4. If the job completes, inspect source-routing proof, all seed commands, LSTM checkpoints, actual frames, matched controls, model bytes, RSS, runtime, CPU latency, raw logs, dependency lock, checksums, leakage, parity and qualification.
5. If valid clip `10.0` remains at/below Random, reject gradient clipping as the sole cause and continue immediately to optimizer/checkpoint restore integrity.
6. A negative result or execution failure alone does not close the iteration.

## Prior-art update

CodeBind, Findings of ACL 2026, decomposes multimodal representations using a modality-shared codebook and modality-specific codebooks, with compositional vector quantization and bridging-modality incremental alignment across up to nine modalities. Therefore the following are not sufficient novelty for RQ-001:

- shared/specific multimodal representation decomposition
- compositional codebook alignment
- bridging-modality incremental alignment without fully paired data
- prevention of modality dominance through modality-specific codebooks

The paper and project page are confirmed. An author-official repository exact commit, dependencies, dataset commands and immutable numerical reproduction are not fixed, so it is not counted as a reproduced baseline or capability evidence.

RQ-001 decision:

> **FURTHER NARROWED BEYOND SHARED/SPECIFIC COMPOSITIONAL MULTIMODAL ALIGNMENT — NOT ADOPTED**

## Formal status

- immutable R0.1 artifacts: 7
- competent external baseline reproduction: 0
- gradient-clipping screening: locator integrated; run result not yet recognized
- J-CRe3 numerical reproduction: 0
- qualified R0.2: 0
- R0.3: rejected and retained
- novelty matrix: incomplete
- central claim preregistration: incomplete
- new mechanism family: not recognized
- new intelligence principle: none
- capability progress: not recognized
- high-school-level intelligence: not achieved
- next-stage proposal: none
