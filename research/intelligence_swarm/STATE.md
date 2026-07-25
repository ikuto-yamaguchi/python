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

固定参照はGaddy & Klein 2019および著者code commit `ac1e7cb62ae94c76f545bf942f0c8febce43891f`。

実装済み:

- language-free state transition pretraining後のinstruction following
- Environment-first / parameter-matched End-to-end / State-only
- typed trajectory export
- generator-side entity/dynamics/language-form signature export
- immutable signature-to-trajectory join
- same-initial-instance online evaluator
- model/checkpoint bytes、RSS、training time、CPU latency、raw logs、checksums

RTFM S1で正式に測定可能なtransferは**dynamicsのみ**。entity ontologyと言語生成familyはtrain/testで分離されないため、entity/language-form holdoutはformal inapplicabilityとする。

accepted task success、next-state prediction、action accuracy、dynamics holdout transferの3-seed resultは0件である。

## Evaluation contract

D015〜D029を統合する。

監査範囲:

- train/test utterance overlap
- entity/dynamics split leakage
- gold action/after-state/completed trajectory/post-treatment leakage
- semantic alias leakage
- exact global and per-cell seeds `1,7,19`
- domain/split/condition presence
- prediction coverage
- sparse observed cell topology
- mean gap、minimum cell gap、paired/randomization/McNemar、episode-cluster CI
- model bytes、RSS、training wall time、CPU latency、raw logs、commit、checksums
- D027: 各cellで全6手法が同一data path/hashを使い、bundle全体が単一code commitに固定されること
- D028: 各instance・各cellのprediction methodを `correct/random/language_blind/state_only/target_label_shuffle/outcome_shuffle` の厳密な6種へ固定し、余分・欠落・評価外predictionを拒否すること
- D029: core `evaluation_contract.py`単独でも未登録method、mixed full code commit、同一cell内の異なる`data_path + data_sha256`を拒否し、companion auditorを迂回できないこと

D028専用CI run `30165709843`は成功した。D029のfocused local regressionも成功記録がある。ただし現headのpublished combined statusは空であり、いずれも実R0 bundle通過や能力進歩ではない。

## Prior-art and RQ boundary

C023〜C025までの境界を維持する。

- state-dependent local dynamicsから言語なしで同定可能なparameterを命名するだけではjoint identificationではない
- isolated language effectを同定してもraw utterance equivalenceとlatent target partitionは同定されない
- mechanistic independenceで識別可能なcomponentを命名しても内部partitionは同定されない

残る候補は、最強のnon-language estimator、mechanistic-independence criterion、完全なinteraction history、isolated-language-effect adjustmentを条件付けた後にも残るexplicit countermodel pairを、外部固定かつ共同再符号化不能なlanguage contrastがstrictly分離できるか、である。

この候補は**未採用**。採用にはexplicit countermodel、anti-recoding anchor、strict joint-identification theorem、anchor除去時のimpossibility theorem、finite-sample/consistency保証、公開baseline再現、exactly one preregistered claimが必要。

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

2026-07-26: **RESET-E035**。D029のcore-contract内method registry・single-code-commit・cell内dataset identity監査を統合した。実R0 bundle、公開baseline値、checkpoint/resource/log/checksumは増えていない。run `30158106220`のartifact未保存failure、R0.2未完了、RQ-001未採用、`initial_reproduction_failure`、能力進歩未認定、高校生級未達を維持する。