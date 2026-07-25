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
- 公開学習経路実行: **131,072 requested frames × seeds 1/7/19のtraining/matched-control step成功。ただしartifact喪失のため再現完了とは認定しない**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleの統一evaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- J-CRe3日本語外部baseline: **未再現**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

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

従来のaccepted evidenceは32,768-requested-frame runのみ:

- parameters `4,916,915`
- state-dict audit `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total three-seed training wall time `1,033.885 s`
- CPU forward audit `6.911 ms/step`
- Correct `1/60`、Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60` each

これはpolicy competence不足であり、公開能力baseline再現ではない。

### Run 30158106220

install、generator-signature test、random/schema probe、official recurrent 131,072-frame × 3 seed training、Correct/Random/Language-blind/State-only/Language-shuffle matched evaluationまで成功した。

しかしR0.2 typed trajectory/baseline工程中に`failure`で終了し、holdout audit、dependency freeze、artifact uploadは実行されず、workflow artifactは0件だった。checkpoint、能力値、model bytes、RSS、runtime、CPU latency、raw logs、checksumsはaccepted evidenceへ昇格しない。

正式分類:

- execution progress: **training/matched-control step成功**
- reproducible R0.1 bundle: **なし**
- public capability reproduction: **未成立**
- classification: **`initial_reproduction_failure_due_to_unpreserved_bundle_after_downstream_failure`**

canonical workflowはR0.1とR0.2を別jobへ分離し、R0.1終了直後にfreeze/uploadしてからR0.2がimmutable artifactをdownloadする。この境界を次回実行の必須条件とする。

## R0.2 Environment-first

固定参照はGaddy & Klein 2019および著者公開codeである。

公開code参照は次へimmutable固定した。

- repository `kristyelee/environment-learning`
- historical reference `dgaddy/environment-learning`
- commit `98c0dc68926ee9535f15019922d2ca871b0ac0b5`
- README、pretraining、evaluation、model、baseline、message-space、discrete-message utilityのGit blob SHAを `GADDY_KLEIN_PUBLIC_REFERENCE_MANIFEST.json` に保存

実装済み:

- language-free state transition pretraining後のinstruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed trajectory export
- generator-side entity/dynamics/language-form signature export
- immutable signature-to-trajectory join
- same-initial-instance online evaluator
- model/checkpoint bytes、RSS、training time、CPU latency、raw logs、checksums

RTFM S1で正式に測定可能なtransferは**dynamicsのみ**。entity ontologyと言語生成familyはtrain/testで分離されないため、entity/language-form holdoutはformal inapplicabilityとする。

現portは高水準のtwo-stage method transferには対応するが、次のため再現主張は不可である。

- RTFM移植はACL 2019 SHRDLURN/regex数値のnumerical reproductionではない
- author component-to-SILG component mappingのfail-closed validatorがない
- paper中心のlanguage-data-efficiency curveを未再現
- 著者codeをnative taskで未実行
- immutable R0.1 source artifactと3-seed dynamics-holdout結果がない

accepted task success、next-state prediction、action accuracy、dynamics holdout transferの3-seed resultは0件である。

## Evaluation contract

D015〜D031を統合する。

監査範囲:

- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed-trajectory/post-treatment leakage
- semantic alias leakage
- exact global and per-cell seeds `1,7,19`
- domain/split/condition presence
- prediction coverage
- sparse observed cell topology
- mean gap、minimum cell gap、paired randomization、McNemar、episode-cluster CI
- model bytes、RSS、training wall time、CPU latency、raw logs、commit、checksums
- exact six-method prediction/artifact topology
- one immutable code commit per bundle and one data path/hash per cell
- strict prediction payload schema and leakage rejection
- D031: prediction JSONLとderived statistics artifact自体を必須checksummed evidenceにし、method/seed整合、有限JSON値、coverage/cell statistics/summaries/paired gapsを検査する

D031専用CI run `30171670131`はsuccess。これは監査コードの回帰証拠に限定し、実benchmark成功には数えない。

## Prior-art and RQ boundary

C023〜C025、C029、C030までの境界を維持する。

- state-dependent local dynamicsから言語なしで同定可能なparameterを命名するだけではjoint identificationではない
- isolated language effectを同定してもraw utterance equivalenceとlatent target partitionは同定されない
- mechanistic independenceで識別可能なcomponentを命名しても内部partitionは同定されない
- general-environment nonparametric CRLは既知targetなしでも十分なenvironment variationからlatent DAG・variablesを識別し得る
- lossy projected causal abstractionは複数low-level interventionを一つのhigh-level interventionへ潰しても、許容されたobservational/interventional/counterfactual queryを識別できる
- high-level queryの完全回復は、abstraction fibre内部のfine target partitionやraw-language equivalenceの回復を意味しない

残る候補は、最強の非言語CRLとprojected abstractionを適用した後にも同一fibre内に残るexplicit countermodel pairを、外部固定かつ共同再符号化不能なlanguage contrastがstrictly分離できるか、である。

必要条件は `I(P_fiber ; L | A_proj, X, A, Y, H) > 0`。ただし十分条件ではなく、fibre-preserving joint automorphism groupが自明になることを事前登録された外部anchorで証明する必要がある。

正式判断:

> **NARROWED BEYOND LOSSY PROJECTED CAUSAL ABSTRACTIONS — NOT ADOPTED**

## Stage-transition rule

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上
2. immutable matched controls
3. complete canonical three-seed prediction/artifact/leakage qualification
4. qualified R0.2 online comparison with real dynamics holdoutとentity/language-form boundary
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

2026-07-26: **RESET-E037**。D031 prediction/statistics evidence-chain監査、Gaddy–Klein公開code commit/blob固定、C030 lossy projected causal abstraction境界を統合した。CI成功は監査コードの証拠に限定する。immutable R0.1 bundle、公開baseline値、R0.2結果、実contract通過は0件であり、`initial_reproduction_failure`、RQ-001未採用、能力進歩未認定、高校生級未達を維持する。
