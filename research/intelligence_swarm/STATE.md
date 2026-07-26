# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。

現在のR0では、新しい知能原理や機構族を発明せず、**公開baselineを固定資源制約下で再現し、その性能を最大化するための原因仮説と最小実験を継続すること**を最優先とする。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Active mechanism family: **なし**
- A〜Dの新規toy仮説、別branch、新規memory/replay/fast-weights/sleep/forgetting: **停止**
- 過去stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 学術的新規性、中心命題、能力進歩: **未確立**

## Non-termination rule

**「検証したが駄目だった」でiterationを終了することを禁止する。**

失敗した実験は、次の5項目が完了するまで研究サイクル未完了とする。

1. 失敗を、実装不一致・最適化不足・表現ボトルネック・探索/学習信号不足のいずれかへ分類する。
2. 最も可能性の高い原因を、ログ・metric・code差分から1件以上特定する。
3. その原因だけを変える最小修正を定義する。
4. 同一budget・同一instanceで再実験する。
5. 改善、原因仮説の棄却、または事前停止条件の成立を記録する。

止めてよい条件は次だけである。

- 事前登録した計算budgetを使い切った。
- 同一原因仮説が3回連続で反証された。
- 公式code/specとの差が消え、残差原因が外部依存または再現不能条件へ限定された。
- より高い期待改善/計算コスト比を持つ候補へ切り替える根拠が得られた。

単発失敗、CI失敗、artifact欠落、低性能は停止理由ではなく、次の原因診断入力である。

## Iteration completion contract

各iterationは、文書更新だけでは完了しない。少なくとも次のいずれか1件を含める。

- preserved public-baseline reproduction artifact
- 実測性能差とmatched control
- 失敗原因を裏付けるmetric/code差分
- 原因だけを変えた再実験結果

さらに、失敗iterationでは次回runの変更変数、固定変数、反証条件、停止条件を同時に確定する。次runを定義せずに終了してはならない。

## R0 status ledger

- 公開環境control再現: **1件**
- immutable 131,072-frame R0.1 bundle: **0件**
- 学習済み公開能力baseline再現: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleの統一evaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
- J-CRe3日本語外部baseline: **公式paper・公式repository確認済み、数値再現未実施**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **追加狭義化・未採用**
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
- primary budget `131,072 requested frames`

accepted evidenceは32,768 requested frames runのみ:

- parameters `4,916,915`
- state-dict `19,694,385 bytes`
- maximum RSS `505,600 KiB`
- total three-seed training wall time `1,033.885 s`
- CPU forward `6.911 ms/step`
- Correct `1/60`
- Random `4/60`
- Language-blind / State-only / Language-shuffle `1/60` each

これはpolicy competence不足であり、公開能力baseline再現ではない。

Run `30158106220`は131,072-frame × 3 seed trainingとmatched controlsまで進んだが、R0.2中に失敗しartifactが保存されなかった。これは研究終了ではなく、artifact boundary不備という実装原因として扱う。R0.1/R0.2 split-job化とR0.1直後のfreeze/uploadを次の最小修正とする。

## Active performance-maximization queue

優先順:

1. **Official-fidelity reconstruction**: config、dependency、frame counting、mask、termination、checkpoint restore差分を除去。
2. **Action-collapse diagnosis**: action histogram、valid-action率、entropy、episode長、reward到達率、mask前後logit、recurrent reset/detachを測定。
3. **Optimization budget allocation**: learning rate、entropy coefficient、unroll、gradient clipping、state reset条件を診断ベースで最大6 screening run。
4. **Capacity allocation**: 総parameter数±2%でrecurrent/state/language/fusion幅を再配分。
5. **Fusion timing**: early/recurrent-input/late fusionをmatched controlsと比較。

seed 1でscreeningし、有望案だけseeds 1/7/19へ昇格する。採用には同一frame/parameter budgetで3-seed平均改善と最低seed非悪化を要求する。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで確認:

- random/language-blind/state-only/target-label-shuffle/outcome-shuffle
- model/checkpoint bytes
- peak RSS
- runtime and CPU latency
- seed/split/frame count
- exact config/commit
- leakage
- raw logs/checksums

監査CI成功や文書更新は能力進歩に数えない。

## R0.2 Environment-first

immutable R0.1 competence bundle通過後のみ開始する。

- Environment-first
- parameter-matched End-to-end
- State-only

目的は、同一parameter/frame budgetでlanguage-data efficiencyまたはdynamics holdout性能を改善できるかの検証である。

## Prior-art and RQ boundary

各iterationで次を確認する。

1. 最新一次文献と公式codeの重複監査。
2. SILG/J-CRe3等の再現進捗。
3. matched controls。
4. model/RSS/runtime/seed/split。
5. leakage。
6. RQ-001の採用・狭域化・棄却条件。

今回の確認:

- SILG/RTFMは既存の公式benchmark・公式codeを基準として継続する。新しい公式後継baselineへの置換根拠は確認されていない。
- J-CRe3は2024年一次論文と公式repository `riken-grp/J-CRe3`を確認した。exact commit、dataset取得、公式評価command、baseline数値のimmutable再現は未完了。
- J-CRe3は日本語実世界参照解決baselineであり、SILGのinteractive policy competenceを代替しない。別々の外部baselineとして扱う。

新規文献追加だけのiterationは禁止する。各iterationには性能実験結果、失敗原因、再現差分のいずれかを必須とする。

正式判断:

> **RQ-001: NARROWED — NOT ADOPTED**

## Stage-transition rule

次stageは以下すべての完了後だけ提案する。

1. competent learned external public capability baseline 1件以上
2. immutable matched controls
3. complete canonical three-seed qualification
4. qualified R0.2 comparison
5. R0.3 rejection維持
6. novelty matrix完了
7. exactly one preregistered successor claim/counterexample/stopping rule

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-26: **RESET-E043**。失敗iterationを次run未定義のまま閉じることを禁止するcompletion contractを追加した。J-CRe3の一次論文と公式repositoryを固定し、数値再現は未完了とした。SILGとJ-CRe3を代替関係にせず、interactive policy competenceと日本語実世界参照解決の別baselineとして維持する。外部baseline再現0件、能力進歩未認定、高校生級未達を維持する。