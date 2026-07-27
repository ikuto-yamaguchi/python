# RESET-E067 — unroll-80 rejection and learner learning-rate screening

## Scope

Canonical branch `research/intelligence-swarm-reconstruction-001`のみを更新した。A〜Dに新規toy仮説、別branch、新規機構族を作らせず、公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。既存stacked draft PRはnegative-results archiveとして扱い、新作業のbaseにしない。

## R0.1 completed evidence

Run `30226976064` / job `89867137085` completed the official-stateful, unroll-80 single-factor screening.

- artifact: `8640762353`
- digest: `sha256:4e7fbacc077121d3fd09db1f6b7ec19a00942f8dc4cbf29b6cb9fd6eb18c9f4c`
- artifact size: `91,615,226 bytes`
- execution commit: `344002bc8e5130cbb9a302fda1a2115baa8edb1c`
- training, factor-routing proof, matched controls, recurrent diagnostics, official/fresh parity, freeze/checksums, artifact upload: passed
- unchanged qualification gate: rejected

Matched aggregate:

- Correct `2/60`, mean return `-1.8059994`
- Random `4/60`, mean return `-1.1513333`
- Language-blind `2/60`
- State-only `0/60`
- Language-shuffle `2/60`

Resources:

- parameters `6,200,115`
- actual frames `131,200` per seed
- model-state bytes `24,827,943 / 24,827,943 / 24,828,026`
- peak RSS `1,699,780 / 1,467,976 / 2,498,024 KiB`
- wall `1479.48 / 1479.02 / 1560.07 s`
- CPU forward approximately `7.86–8.00 ms/step`
- answer leakage: false
- same-instance controls: passed

## Decision

`unroll_length=20`不足を単独主因として棄却する。`unroll_length=80`は全seedの実commandへ到達し、stateful LSTMとrecurrent stateも有効だったが、CorrectはRandomを下回り、language-blind/language-shuffleと同率だった。

このnegative resultだけでiterationを閉じない。learner logsでは終盤までpolicy-gradient lossとtotal lossが大きく正負反転しており、次の単一要因としてlearning rateを選択した。

## Next single-factor run

追加した実装:

- `research/intelligence_swarm/benchmarks/grounded_causal/patch_silg_learning_rate_screening.py`
- `.github/workflows/r01_silg_learning_rate_screening.yml`

変更要因:

- explicit `learning_rate=0.0001`

固定:

- official SILG `multi`
- `stateful=true`
- `unroll_length=80`
- entropy cost `0.05`
- actors `2`, threads `1`, batch `2`
- frames `131072`
- seeds `1/7/19`
- train/test split、matched instances
- random / language-blind / state-only / language-shuffle

Factor routing is fail-closed: every seed command must contain `--learning_rate 0.0001`, `--stateful`, and `--unroll_length 80`; every checkpoint must contain LSTM `core.*` weights and reach the frame budget.

有効なrunでもCorrectがRandomを上回らなければlearning-rate単独原因を棄却し、gradient clippingまたはoptimizer/checkpoint restoreのうち証拠が強い一件だけへ進む。

## Prior-art audit

CLeaR 2026のBayesian Ablationは、neural network内のtask representation単位の因果寄与を確率的に推定し、distributedness、manifold complexity、polysemanticityを測る。unit-level probabilistic ablationや表現寄与診断だけではRQ-001の新規性を認定しない。一次論文は確認済みだが、author-official code、exact commit、immutable numerical reproductionは未確認であり、SILG/J-CRe3の代替baselineには数えない。

RQ-001:

> **FURTHER NARROWED BEYOND PROBABILISTIC CAUSAL ABLATION OF TASK REPRESENTATIONS — NOT ADOPTED**

## Formal status

- immutable R0.1 artifacts: **6**
- competent learned external baseline: **0**
- J-CRe3 numerical reproduction: **0**
- qualified R0.2: **0**
- R0.3 hidden intervention-target ablation: **rejected and retained**
- novelty matrix: **incomplete**
- central-claim preregistration: **incomplete**
- new mechanism family: **not recognized**
- new intelligence principle: **not discovered**
- capability progress: **not recognized**
- high-school-level intelligence: **not achieved**
- next stage: **not proposed**
