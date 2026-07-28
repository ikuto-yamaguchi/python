# RESET-E082 — R0 Research Reconstruction Integration

Date: 2026-07-28

Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope lock

- A〜Dは新しいtoy仮説、別branch、新規機構族を作らない。
- 公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。
- 既存stacked draft PRはnegative-results archiveであり、新作業のbaseにしない。
- competent external baseline再現前に新規機構族、新規知能原理、能力進歩を認定しない。

## 1. Latest primary-literature and official-code overlap audit

再監査した境界:

- JMLR 2025 Score-based CRL: intervention target対応を事前に知らずにlatent variable/graphを回復する条件を扱う。
- NeurIPS 2024 Linear CRL from Unknown Multi-node Interventions: unknown multi-node interventions下のidentifiabilityとalgorithmを扱い、author-official repository `acarturk-e/umni-crl`が存在する。
- 2026 Beyond Identifiability: Few Environments and Finite Samples: logarithmic numberのunknown multi-node intervention environmentsからlatent graph、mixing/representation、unknown intervention targetsを有限標本で回復する保証を提示する。

結論:

- unknown intervention targetsの回復、unknown multi-node intervention、few-environment finite-sample recoveryだけではRQ-001の新規性を認定しない。
- 今回、一次文献・author-official code・exact commit・dependency・public numerical contractまで固定した新しいimmutable reproductionは0件。
- 文献名だけをnovelty matrixへ追加して水増ししない。

## 2. SILG / J-CRe3 reproduction progress

### SILG

Accepted infrastructure evidence:

- exact one-step resume-equivalence run `30300067389`
- job `90090542489`
- artifact `8666312079`
- artifact SHA-256 `34f02c802f6db15b55336a0547e3914846aad6d74783ebfc371d12ca6ac08115`
- frames `3840 -> 5760`

Official first chunk:

- initial run `30308447687`
- failed before training because pinned SILG does not expose `--seed`
- immutable failure artifact `8669383695`
- SHA-256 `9a5518b1a5e5338886ed2d3f2429d0e0246f0ba9cd919de7627e6f01c74dccd4`

Single-cause correction:

- commit `ce6909baf0e0879d1547c34beb457d59d2027b9e`
- unsupported CLI argument removed
- only RNG seeding patched in pinned `run_exp.py`
- model、loss、optimizer、environment、action schema、sampling defaults、frame budget unchanged

Current execution status:

- replacement run/job/artifact/qualification: unconfirmed
- connector-visible PR-triggered workflows on head `e168d58696eea3356adc971e7d2899f914b06b0d`: 12 runs, all `action_required`, no jobs
- classification: `workflow_execution_approval_or_policy_blocker`
- do not duplicate-dispatch the same chunk

### J-CRe3

- exact commit、dataset checksum、official command、matched controlsを固定したnumerical reproduction: 0件

## 3. Matched controls

新しいofficial-horizon能力artifactがないため、新しいcontrol結果はない。

Latest short-horizon negative archive:

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct return `-1.7679994`
- Random return `-1.1513333`

これは公式100M-frame baseline失敗ではない。

## 4. Model / RSS / runtime / seed / split

Latest short-horizon archive:

- parameters `6,200,115`
- actual frames `131,200` per seed
- seeds `1/7/19`
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`

Official-contract resource anchor:

- peak RSS `9,305,052 KiB`
- throughput `63.83 frames/s`
- projected 100M wall `18.13 runner-days` per entropy/seed run

## 5. Leakage

- latest short-horizon answer leakage: `false`
- replacement official chunk has no ability prediction artifact; leakage result is N/A until evaluation runs
- no capability claim is allowed from infrastructure-only evidence

## 6. RQ-001 decision

Broad RQ-001 remains rejected. Narrow RQ-001 remains not adopted.

> **RQ-001: FURTHER NARROWED — NOT ADOPTED**

Adoption still requires language-specific incremental information after existing baselines, countermodel pairs, a non-jointly-recodable external denotation law, and preregistered claim/counterexample/stopping rules.

## Evaluation contract

- D015〜D035 remain frozen.
- normalized-cell workflow is read-only and fail-closed.
- corrected fixture conforms to explicit holdout identity.
- current `action_required` runs are treated as approval/policy blockers, not evaluation-logic regressions.
- standalone canonical-instance audit remains mandatory until direct integration into `validate_dataset()` and `score()` is complete.

## Formal status

- immutable short-horizon artifacts: **8**
- exact one-step resume-equivalence: **1 accepted**
- official SILG 100M reproduction: **0 completed**
- official first 1M checkpoint: **initial pre-training failure archived; replacement result unconfirmed**
- competent external baseline reproduction: **0**
- official-horizon matched controls: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected/closed**
- novelty matrix: **incomplete**
- central proposition preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **none**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
