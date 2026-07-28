# RESET-E074 — Public Reproduction Contract Correction

Date: 2026-07-27
Canonical branch: `research/intelligence-swarm-reconstruction-001`

## Scope

A〜Dは公開benchmark再現、prior-art audit、evaluation contract、hidden intervention-target ablationだけを累積する。新しいtoy仮説、別branch、新規機構族は作成しない。stacked draft PRはnegative-results archiveのまま新作業のbaseにしない。

## Official SILG contract audit

Pinned official SILG `launch.py --envs rtfm`とparser defaultsを再確認した。

- model `multi`
- stateful `false`
- entropy `0.05 / 0.005`
- train `silg:rtfm_train_s1-v0`
- validation `silg:rtfm_test_s1-v0`
- total frames `100,000,000`
- actors `30`
- batch `24`
- unroll `80`
- threads `4`
- learning rate `0.0005`
- RMSprop alpha `0.99`, momentum `0`, epsilon `0.01`
- gradient clip `40`

既存の`131,072`-frame runsは公式frame horizonの`0.131072%`、推定learner update数でも公式契約の約`1/63.58`である。したがって、これらはすべてshort-horizon screening evidenceであり、official public-baseline reproductionでもofficial baseline failureでもない。

正式分類:

> **public_reproduction_contract_mismatch**

## Learner variance diagnostic

artifact `8644560521`の全seed learner logを再集計し、`R0_SILG_ARTIFACT_8644560521_LEARNER_VARIANCE.json`へ固定した。

- total-loss standard deviation `27.46〜28.76`
- PG-loss standard deviation `23.63〜24.51`
- total-loss sign changes `146〜161`
- PG-loss sign changes `142〜159`
- entropy-loss mean 約`-5.52〜-5.54`

これはshort-horizon learner updateが高分散であるnegative diagnosticにとどまる。official `job.tar`欠落のためoptimizer/restore failureとは認定しない。

## Corrected next action

actors/batchの追加hyperparameter screeningは停止する。次の実行は能力試験ではなく、official-contract infrastructure qualificationとする。

- official model/stateful/sampling defaultsを変更しない。
- 短いqualification segmentでcheckpoint/resume integrityとrunner resource feasibilityを確認する。
- model、optimizer、scheduler、frame counter、bytes、SHA-256を全seedでfail-closed保存する。
- one-step resume equivalenceを確認する。
- RSS、throughput、wall timeから100M-frame実行可能性を見積もる。
- runnerがofficial contractを処理できなければresource-blocker artifactを保存し、縮小contractを再現と呼ばない。
- qualificationを能力進歩として数えない。

resource feasibleかつintegrity合格の場合のみ、entropy `0.05`と`0.005`のofficial 100M-frame reproductionを次に提案する。

## Prior-art boundary

CausalVerse公式benchmark/repositoryを追加した。24 sub-scenesで、静止画、動的物理、ロボット操作、交通場面とground-truth causal mechanisms、variables、interventions、temporal dependenciesを構成可能にする。

設定可能な高忠実度simulation、既知の介入target、時間依存を用いたCRL stress test自体はRQ-001の新規性にならない。exact commit、dataset checksum、公式baseline数値のimmutable reproductionは未完了であり、SILG/J-CRe3の代替証拠にしない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CONFIGURABLE GROUND-TRUTH INTERVENTION BENCHMARKING — NOT ADOPTED**

## Status

- immutable R0.1 screening artifacts: **8件**
- official SILG 100M-frame reproduction: **0件**
- competent external baseline reproduction: **0件**
- J-CRe3 numerical reproduction: **0件**
- CausalVerse numerical reproduction: **0件**
- R0.2 qualified reproduction: **0件**
- R0.3: **棄却維持**
- novelty matrix: **未完了**
- central-claim preregistration: **未完了**
- new mechanism family: **未認定**
- new intelligence principle: **未発見**
- capability progress: **未認定**
- high-school-level intelligence: **未達**
- next stage: **提案なし**
