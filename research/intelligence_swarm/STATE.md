# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。

現在のR0では、新しい知能原理や機構族を発明せず、公開baselineを固定資源制約下で再現し、失敗原因を特定して性能を最大化する反復を継続する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- Active mechanism family: **なし**
- A〜Dの新規toy仮説、別branch、新規memory/replay/fast-weights/sleep/forgetting: **禁止**
- 過去stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 学術的新規性、中心命題、能力進歩: **未確立**

## A–D execution allocation

A〜Dは同一canonical branchと同一実験台帳を共有し、次だけを担当する。

- **A — Public reproduction executor**: SILG/RTFMとJ-CRe3/J-ORAの公式code・dataset・command・dependencyを固定し、無改変再現とartifact保存を実行する。
- **B — Failure diagnosis and constrained optimization**: 実装不一致、最適化不足、表現ボトルネック、探索/学習信号不足を切り分け、原因だけを変える最小runを設計する。
- **C — Prior-art and novelty boundary**: 最新一次文献と公式codeを監査し、既存研究で達成済みの主張をnovelty候補から除外する。文献追加だけでiterationを閉じない。
- **D — Evaluation and falsification**: frozen D015〜D035 gate、matched controls、leakage、resource provenance、RQ-001の採用・狭域化・棄却条件を適用する。

A〜Dは別branch、別機構族、独立toy benchmarkを作成しない。

## Non-termination rule

**「検証したが駄目だった」でiterationを終了してはならない。**

失敗runは次が完了するまで未完了である。

1. 失敗分類。
2. metric・log・code差分に基づく原因候補。
3. 原因だけを変える最小修正。
4. 同一budget・同一instanceの再run。
5. 改善、原因仮説棄却、または事前停止条件。

停止可能条件は、事前budget消化、同一原因仮説の3回連続反証、公式との差が消えて外部依存だけが残る場合、または期待改善/計算コスト比が明確に高い候補への切替だけである。

## R0 status ledger

- 公開環境control再現: **1件**
- immutable 131,072-frame R0.1 bundle: **0件**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- J-ORA numerical reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleの統一evaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却**
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

Run `30158106220`は131,072-frame × 3 seed trainingとmatched controlsまで進んだが、R0.2中に失敗しartifactが保存されなかった。原因分類はartifact boundary不備であり、R0.1/R0.2 split-job化とR0.1直後のfreeze/uploadを次の最小修正として維持する。

## Active execution queue

1. R0.1 split-jobを実行し、R0.1終了直後にcheckpoint、prediction、resource、raw log、checksumをfreeze/uploadする。
2. preserved bundleへD015〜D035を適用する。
3. CorrectがRandomを下回る原因をaction histogram、valid-action率、entropy、episode長、reward到達率、mask前後logit、recurrent reset/detachで分類する。
4. 診断結果に基づき、official family内で最大6 screening runを実行する。
5. 有望案のみseeds 1/7/19へ昇格し、同一frame・parameter budgetで確認する。
6. SILG competence成立後にR0.2を開始する。
7. J-CRe3はexact commit、dataset checksum、公式評価command、dependency lockを固定し、無改変baseline再現を開始する。
8. J-ORAはJ-CRe3を置換せず、object identification・reference resolution・next-action predictionを含む隣接benchmarkとして公式project/code/datasetの再現可能性を監査する。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

毎runで保存・確認する:

- random/language-blind/state-only/applicable shuffle controls
- identical initial instances
- model/checkpoint bytes
- peak RSS
- training runtime and CPU latency
- seed/split/actual frame count
- exact config/commit/dependency
- leakage
- raw logs/checksums

監査CI成功、文書更新、queued/cancelled runは能力進歩に数えない。

## Prior-art and RQ boundary

2025年までのgeneral-environment、causal abstraction、score-based CRL境界に加え、2026年の有限標本CRLは、少数の未知multi-node interventionからlatent graph、mixing、representation、unknown targetsを有限標本で回復できる領域を示す。unknown targetや少数environment自体は言語固有の新規性根拠にしない。

J-ORAは日本語ロボット知覚におけるobject identification、reference resolution、next-action predictionと属性情報の効果を扱う。J-CRe3のreference-resolution範囲を越える隣接prior artとして監査するが、SILGのinteractive policy competenceを代替しない。

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

2026-07-26: **RESET-E044**。A〜Dを再現実行、原因診断と制約内最適化、prior-art境界、評価反証へ固定した。2026年有限標本CRLと2025年J-ORAを重複監査へ追加した。新しい実験artifactやbaseline数値は確認できないため、外部baseline再現0件、能力進歩未認定、高校生級未達を維持する。