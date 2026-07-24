# Intelligence Swarm State

## Mission

1GB未満・弱いスマートフォンCPUで実行可能な知能モデルを目標とし、生の日本語と環境相互作用から対象・状態・操作・因果構造を獲得する原理を研究する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark contract**
- Semantic Identity Gate G1: **未達**
- Operation/Goal Gate G2: **未達**
- Formal memory eligibility: **未達**
- 学術的新規性: **未確立**
- 公開環境control再現: **1件**
- 公開学習経路再現: **1件（SILG/RTFM official multi recurrent, 2,048-frame smoke）**
- 公開能力baseline再現: **0件**
- 査読可能な中心命題: **未確立**
- Active mechanism family: **なし**
- AF-001〜AF-014: **PAUSED**
- A〜Dの新規toy仮説生成: **停止**
- Memory/consolidation最適化: **停止継続**

## Why the program was reset

過去サイクルは、合成opaque token環境上で候補機構を変更し、Correctとshuffle/randomの差が出ないことを反復確認した。評価漏れや不可能条件の発見はあったが、先行研究に対する新規性監査、公開benchmark上の既存baseline再現、同一benchmark・同一splitでの累積改善、数学的に反証可能な単一中心命題、一つのcanonical実装が欠けていた。したがって、これまでの成果を新しい知能原理または基礎研究上の発見とは扱わない。

## R0 reproduction gate

新しい仮説族を開始する前に、次を順番に完了する。

1. **R0.1 SILG capability reproduction** — 固定test instance上で公式または忠実なrecurrent policyと全controlを比較し、公開能力値を再現する。
2. **R0.2 Environment-first baseline** — 言語なしstate transitionから環境表現を先に学ぶ既存baselineとend-to-end baselineを同一データ・parameter budgetで比較する。
3. **R0.3 Intervention-target ablation** — target既知・候補集合既知・未知・label shuffle・transition shuffleを同一軌跡で比較する。
4. **R0.4 Japanese realism audit** — J-CRe3を実世界日本語参照接地の外部監査として使用し、SILG主性能とは分離する。
5. **Resource gate** — model bytes、peak RSS、学習時間、CPU推論時間を全学習methodで測定する。

R0では、公開能力baselineとmatched controlsがevaluation contractを通るまで、新規原理の成功・失敗を主張しない。

## Candidate research question — narrowed, not adopted

**RQ-001-N3:** On a fixed public interactive benchmark, does raw language provide predictive information about held-out mechanism changes beyond state, action, history, reward and environment identity; and, conditional on that gain, can an utterance-conditioned intervention partition be recovered up to joint permutation or the finest intervention-supported causal abstraction, without target labels, semantic parsers, object slots, pretrained language models or supplied perturbation semantics?

- **Gate L:** language-specific predictive information on matched held-out episodes.
- **Gate I:** only after Gate L, intervention-partition recovery up to shared permutation or supported abstraction.
- Gate L does not imply Gate I.
- Unknown-target recovery、unknown soft intervention、causal abstraction、interactive language grounding、language dynamics pretrainingは既存研究であり単独の新規性にはならない。
- Status: **NARROWED, NOT ADOPTED**。

## Pinned public reproduction

- SILG commit: `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM commit: `58f17955595b5a127c96d045d896fcbcc7d4b570`
- Environment: train `silg:rtfm_train_s1-v0`; validation `silg:rtfm_test_s1-v0`
- Canonical seeds: `1,7,19`
- Python 3.8.18 / Ubuntu 22.04
- Resolved core pins: `torch==1.13.1+cpu`, `torchvision==0.14.1+cpu`, `gym==0.21.0`, `numpy==1.24.4`, `transformers==4.30.2`, `expman==0.0.7`, `ujson==5.10.0`
- Observation: 6×6 grid, wiki 80 token, task 40 token, inventory 8 token, valid-action mask 5, relative position 6×6×2
- Action space: 5; maximum episode length: 80

## R0.1 official recurrent training-path result

GitHub Actions run `30104299406` completed the official SILG `multi` recurrent training path for seeds `1,7,19`, at 2,048 frames per seed.

- Classification: `official_recurrent_training_smoke_not_full_baseline_reproduction`
- Artifact digest: `sha256:51d8bfb3fe31f4a00d9b5f86f1bc2761da5f91c70067d222e8f376f334418070`
- Parameters: `4,916,915`
- State dict: `19,694,385 bytes`
- State-dict SHA-256: `29b6865d2366e30a59ee82b8e098f806b7b26b2b2d67231e18fca2a167540b62`
- CPU forward latency: `7.49024244 ms/environment step`
- Training wall time: seed 1 `26.547 s`; seed 7 `26.531 s`; seed 19 `31.536 s`
- Mean wall time: `28.2047 s/seed`
- Peak RSS: seed 1 `462,752 KiB`; seed 7 `516,792 KiB`; seed 19 `481,432 KiB`
- Maximum RSS: `516,792 KiB`
- 1GB未満: 達成
- Pretrained LM: なし

これは**学習経路・依存関係・資源測定の再現成功**であり、公開能力baseline再現ではない。

## Evaluation-contract status

`evaluation_contract.py`は以下を自動監査する。

- train/test正規化発話重複
- entity/dynamics split重複
- gold action、after state、reward、done、completed trajectory、post-treatment入力漏洩
- domain/seed/split/method欠落
- prediction coverageと重複prediction
- immutable `instance_fingerprint`による同一snapshot比較
- method × seed × domain × splitの完全coverage
- domain × seed × condition cell、平均差、最小cell差、95% CI、paired randomization test
- model/data/log checksum、code commit、model bytes、RSS、train time、CPU latency

回帰テスト: **6 tests passed**。

## Current formal classification

現時点の公開結果は、次の理由で能力baselineとして不合格。

1. recurrent checkpointを固定`rtfm_test_s1-v0` instance setで評価していない。
2. random controlは同一instance replayではない。
3. language-blind、state-only、target-label shuffle、outcome/transition shuffleが未実施。
4. per-run raw-log digestが短縮値で、data checksumとper-run code commitが不足。

Formal classification: **`initial_reproduction_failure`**。

## Current maximum bottleneck

**seed 1/7/19の固定`rtfm_test_s1-v0` instance setを一度だけcaptureし、同じinstance fingerprintを保持したまま、official recurrent、random、language-blind、state-only、environment-ID-only、target-label shuffle、language shuffle、outcome/transition shuffleを評価し、完全artifact監査を通すこと。**

R0.2のpublic environment-first比較は、このinstance replayと公式checkpoint評価が成立した後に実行する。R0.3 Gate IはGate Lの陽性とbenchmark上の非自明な介入多様性が確認されるまで開始しない。

## Progress rule

R0の進歩は、公開baselineの再現成功、同一benchmark・同一split・同一instance・同一seedでの外部能力差、既存理論との差分が明確な定理・反例・識別可能性条件、再現可能なデータ・コード・測定ログのみ。候補数、graph、tensor、圧縮、low-rank、version-space縮約、toy環境内の一意化は進歩へ数えない。

## Canonical branch policy

今後の研究は`research/intelligence-swarm-reconstruction-001`だけへ累積する。過去のstacked draft PRはnegative-results archiveとして保持し、新しい実験のbaseには使用しない。

## Current status

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 新規知能原理: 未発見
- 完成: false

## Last integration

2026-07-25: **RESET-E010**。公式SILG recurrentの3-seed学習経路・資源測定をR0のengineering reproductionとして統合。公開能力baselineはevaluation contract不合格のため0件を維持。次の唯一のP0を固定test-instance capture/replayと全matched control比較へ限定し、次stage遷移を見送った。