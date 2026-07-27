# RESET-E073 — R0 Research Reconstruction Integration

Date: 2026-07-27
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope guard

- A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。
- 新しいtoy仮説、別branch、新規機構族は作成しない。
- stacked draft PRはnegative-results archiveとして保持し、新作業のbaseにしない。
- 外部baseline再現前に新しい知能原理、能力進歩、高校生級到達を認定しない。

## SILG/RTFM evidence audit

直近の有効negative bundleはrun `30240410850`、artifact `8644560521`である。

- Correct `3/60`
- Random `4/60`
- Language-blind `0/60`
- State-only `0/60`
- Language-shuffle `3/60`
- Correct mean return `-1.7679994`
- Random mean return `-1.1513333`
- parameters `6,200,115`
- actual frames `131,200` per seed
- peak RSS `1,299,228 / 1,180,104 / 1,856,556 KiB`
- wall `1528.08 / 1559.30 / 1591.64 s`
- CPU forward `8.565 ms/step`
- leakage `false`
- qualification rejected

Gradient clip `10.0`は全seedへ到達したが、CorrectはRandomを超えずlanguage-shuffleと同率だった。gradient clip norm `40.0`不足は単独主因として棄却済みである。

## Learner variance reconstruction

artifact内の全seed learner logを再集計し、次へ固定した。

`benchmarks/grounded_causal/results_audits/R0_SILG_ARTIFACT_8644560521_LEARNER_VARIANCE.json`

結果:

- total-loss standard deviation: `27.46〜28.76`
- policy-gradient-loss standard deviation: `23.63〜24.51`
- total-loss sign changes: `146〜161`
- policy-gradient-loss sign changes: `142〜159`
- entropy-loss mean: 約`-5.52〜-5.54`

これはlearner updateが高分散であることを示すdiagnosticであり、optimizer/checkpoint restore failureの証明ではない。official `job.tar`がartifactに保存されていないため、optimizer state、parameter groups、frame counter、model tensor equality、resume-equivalenceは未判定のまま維持する。

## Next single-cause rule

古いartifactのcheckpoint欠落だけを直すための重複3-seed trainingは禁止する。次の独立に正当化されたperformance runでcheckpoint保存とoptimizer integrityを同時に回収する。

残る最大のofficial-default差はsampling scaleである。

- current actors `2` vs official default `30`
- current batch `2` vs official default `24`

actorsとbatchを同時に変更しない。既存RSSからresource feasibilityを確認した後、`actors 2→4`または`batch 2→8`の一方だけを事前登録する。CorrectがRandom以下、またはlanguage-shuffleと同等なら、その要因を単独主因として棄却する。

## Evaluation contract

D015〜D035は凍結を維持する。次runでも必須項目は以下である。

- random / language-blind / state-only / language-shuffle
- same-instance matched evaluation
- model/checkpoint bytes
- peak RSS / runtime / CPU latency
- seed / split / actual frames
- raw logs / dependency lock / SHA-256
- leakage
- official/fresh evaluation parity
- checkpoint/optimizer integrity
- qualification JSON

## Prior-art audit

CausalVerse公式benchmark/repositoryを境界へ追加した。CausalVerseは24 sub-scenesにわたり、静止画、動的物理、ロボット操作、交通場面と、ground-truth causal mechanisms、variables、interventions、temporal dependenciesを構成可能にする。

したがって、設定可能な高忠実度simulation、既知の介入target、時間依存を用いたCRL stress test自体はRQ-001の新規性にならない。exact commit、dataset checksum、公式baseline数値のimmutable再現は未完了であり、SILG/J-CRe3を代替しない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CONFIGURABLE GROUND-TRUTH INTERVENTION BENCHMARKING — NOT ADOPTED**

## Status

- immutable R0.1 artifacts: **8件**
- competent external baseline reproduction: **0件**
- J-CRe3 numerical reproduction: **0件**
- CausalVerse numerical reproduction: **0件**
- R0.2 qualified reproduction: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- novelty matrix: **未完了**
- central-claim preregistration: **未完了**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- high-school-level intelligence: **未達**
- next stage: **提案なし**
