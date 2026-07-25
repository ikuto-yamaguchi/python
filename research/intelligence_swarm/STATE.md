# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。現在は新しい知能原理や機構族の発明を停止し、公開benchmark再現、評価資格、既存研究との境界、反証可能な中心命題の確立を優先する。

## Current stage

- Stage: **R0 Research Reconstruction — public capability reproduction and benchmark qualification**
- Active mechanism family: **なし**
- A〜Dの新規toy仮説、別branch、新規memory/replay/fast-weights/sleep/forgetting: **停止**
- 過去stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 学術的新規性、中心命題、能力進歩: **未確立**

## R0 status ledger

- 公開環境control再現: **1件**
- 公開学習経路再現: **1件（SILG/RTFM、32,768 requested frames、seed 1/7/19）**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- J-CRe3日本語外部baseline: **未再現**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**

## R0.1 SILG / RTFM

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- train `silg:rtfm_train_s1-v0`
- test `silg:rtfm_test_s1-v0`
- official `multi` recurrent
- pretrained language modelなし
- seeds `1,7,19`
- observation: 6×6 grid、wiki 80 token、task 40 token、inventory 8 token、valid-action mask 5、relative position 6×6×2
- action space 5、maximum episode length 80

Accepted evidence remains the 32,768-requested-frame run:

- parameters `4,916,915`
- state-dict audit `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total three-seed training wall time `1,033.885 s`
- CPU forward audit `6.911 ms/step`
- Correct `1/60`、Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60` each

これはpolicy competence不足であり、公開能力baseline再現ではない。

### Active 131,072-frame run

GitHub Actions run `30158106220` は、install、generator-signature test、random/schema probeを完了し、official recurrent 131,072-frame × 3 seed学習stepを実行中として確認済み。checkpoint、matched controls、artifact、能力値は未取得であり、完了までは進歩に数えない。

PR累積diffにbenchmark workflowが含まれるため無関係なgovernance commitでも長時間runがqueueされる問題を確認した。workflowをbenchmark-code/run-requestの**pushまたはmanual dispatchだけ**で起動する構成へ変更し、今後の統合commitによる重複queueを停止した。既にpendingのrunは成果に数えない。

## R0.2 Environment-first

固定参照はGaddy & Klein 2019および著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`。

実装済み:

- language-free state transition pretraining後のinstruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed trajectory export
- generator-side entity/dynamics/language-form signature export
- immutable signature-to-trajectory join
- same-initial-instance online evaluator
- model/checkpoint bytes、RSS、training time、CPU latency、raw logs、checksums

RTFM S1で正式に測定可能なtransferは**dynamicsのみ**。entity ontologyと言語生成familyはtrain/testで分離されないため、entity/language-form holdoutはS1ではformal inapplicabilityとする。

未完了:

- qualified 3-seed join artifact
- real dynamics holdout audit pass
- online task success、next-state prediction、action accuracyの3-seed結果
- competent R0.1 source-policy trajectory

## Evaluation contract

D015〜D025に加え、D026としてdataset全体と各`domain × split × condition` cellについてcanonical seed `1,7,19`、train/evaluation presence、domain/split/condition非欠落をfail-closed監査する。

監査範囲:

- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed trajectory/post-treatment leakage
- semantic alias leakage
- prediction coverage
- random/language-blind/state-only/target-label shuffle/outcome shuffleの同一instance coverage
- sparse observed cell topology
- mean gap、minimum cell gap、paired/randomization/McNemar、episode-cluster CI
- model bytes、RSS、training wall time、CPU latency、raw logs、commit、checksums

実R0 bundleは未通過。分類は **`initial_reproduction_failure`**。

## Prior-art and RQ boundary

C023はstate-dependent local dynamics identifiabilityを追加した。trajectoryとlocal sparsityから言語なしで同定できるsystem parameterを言語で命名するだけではjoint identificationにならない。

C024はisolated causal effects of natural languageを追加した。既知の言語介入属性の外部結果への因果効果が識別できても、raw utterance equivalenceとlatent intervention-target partitionは識別されない。

残るRQ候補は、最強のnon-language estimator、完全なinteraction history、isolated-language-effect adjustmentを条件付けた後にも残るequivalence classに対し、environment identity、incidence、observation、action、outcome、completed trajectoryから復元不能で、latent representationと共同再符号化できない外部固定language contrastがstrict reductionを与えるか、である。

この候補は**未採用**。採用にはexplicit countermodel、anti-recoding anchor、strict joint-identification theorem、anchor除去時のimpossibility theorem、finite-sample/consistency保証、公開baseline再現、exactly one preregistered claimが必要。

## Stage-transition rule

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdoutとentity/language-formの別公開splitまたはformal inapplicability boundary
5. R0.3 rejection維持
6. relevant 2026 primary workまで閉じたnovelty matrix
7. exactly one preregistered successor claim/theorem/counterexample/stopping rule

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-25: **RESET-E031**。R0.1 run `30158106220`の学習中状態を記録したが、能力証拠は増加なし。PR統合commitによる重複長時間run queueを停止。D026 seed/domain/cell topology監査、C023 local-dynamics境界、C024 isolated-language-effect境界を統合。R0.1未再現、R0.2未完了、RQ-001未採用、`initial_reproduction_failure`、高校生級未達を維持する。