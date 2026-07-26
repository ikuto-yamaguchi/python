# Intelligence Swarm State

## Mission

長期目標は、1GB未満で弱いスマートフォンCPU上でも高速に動作し、日本語コミュニケーション・知識・推論を備える知能モデルである。R0では新規toy仮説や新機構族を作らず、公開baselineを固定資源制約下で再現し、失敗原因を一つずつ除去して性能を最大化する。

## Current stage

- Stage: **R0 Research Reconstruction — constrained performance maximization**
- Canonical branch: `research/intelligence-swarm-reconstruction-001`
- A〜Dの新規toy仮説・別branch・新規機構族: **禁止**
- 既存stacked draft PR: **negative-results archive。新作業のbaseにしない**
- 外部baseline再現前の新規知能原理・能力進歩認定: **禁止**

## A–D responsibilities

- **A**: SILG/RTFM、J-CRe3等の公式再現とimmutable artifact保存。
- **B**: 実装・最適化・表現・探索/信号の失敗診断と、原因だけを変える最小run。
- **C**: 最新一次文献・公式codeとの重複監査とnovelty matrix。
- **D**: D015〜D035、matched controls、resource、leakage、RQ-001判定。

## Non-termination rule

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。さらに、宣言した変更変数が実際のcommand・artifactへ到達したことを確認できないrunは仮説検証として無効とし、配線修復後に同一screeningを再実行する。

## R0 status ledger

- immutable 131,072-frame R0.1 bundle: **2件・いずれも不合格**
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleのevaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## R0.1 immutable baseline run 30203026269

- artifact ID: `8633105142`
- artifact digest: `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- Correct `0/60`、Random `4/60`、Language-blind `1/60`、State-only `0/60`、Language-shuffle `0/60`
- Correct mean return `-2.0749993`、Random mean return `-1.1513333`
- answer leakage: `false`
- same-instance controls: 成立
- classification: `optimization_or_policy_competence_failure`

## Invalid R01-SCREEN-002 execution: run 30208660095

- job `r01-public-reproduction`: qualification failure
- artifact ID: `8634594371`
- artifact digest: `sha256:aa2efd6a30d26074a4ddf39195b93f8dc046f164f87446a384e7d808bd5e5fbf`
- requested hypothesis: `entropy_cost 0.05 -> 0.005`
- **actual command for all seeds: `--entropy_cost 0.05`**
- Correct win rate `3/60 = 0.0500`
- Random win rate `4/60 = 0.0667`
- Correct return `-1.6356662`
- Random return `-1.1513333`
- Language-blind `3/60`、State-only `1/60`、Language-shuffle `3/60`
- same-instance controls: 成立
- answer leakage: `false`
- peak training RSS: seed 1 `1,539,572 KiB`、seed 7 `1,294,524 KiB`、seed 19 `1,687,408 KiB`
- training wall: 約23分35秒〜23分59秒/seed

このrunは0.005仮説の検証ではない。0.05 baselineの追加反復としてのみ保存し、entropy_cost単独原因は**未検証**とする。

## Active correction

`.github/workflows/r01_silg_entropy_screening.yml`へ、学習summaryと各seed commandがすべて`entropy_cost=0.005`であることを評価前にfail-closed検証するstepを追加した。commit `54a1f1f3c09ed0a8d526ae4d877057cfa33cd3d6`から正しい同一budget rerunを発行する。

固定条件:

- SILG `2af07578e1264029a240fcfb78d4ac0aea16f5de`
- RTFM `58f17955595b5a127c96d045d896fcbcc7d4b570`
- official `multi` recurrent
- `131,072` frames × seeds `1/7/19`
- same-instance Random / Language-blind / State-only / Language-shuffle
- model/checkpoint bytes、RSS、runtime、CPU latency、seed、split、raw logs、checksums、leakage

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。

## Prior-art and RQ boundary

2025 C3 Regularization、2026 MCDRL、CmIR、score-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE等の既存境界を維持する。今回の一次文献再監査でも、language-guided target selection、multimodal causal invariance、text-defined confounder intervention、causal sufficiency/necessity regularizationだけでRQ-001を採用できる新しい直接証拠は確認していない。

正式判断:

> **RQ-001: FURTHER NARROWED — NOT ADOPTED**

採用には、既存baseline再現後にも残るcountermodel pair、外部固定でjoint recoding不能なdenotation law、language固有追加情報の直接証拠、事前登録済みclaim/counterexample/stopping ruleが必要。

## Stage transition

次stageは、competent external baseline、immutable matched controls、canonical three-seed qualification、qualified R0.2、R0.3棄却維持、novelty matrix、中心命題の事前登録がすべて完了した場合だけ提案する。

## Current status

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 新規知能原理: **未発見**
- 能力進歩: **未認定**
- 完成: **false**

## Last integration

2026-07-26: **RESET-E057**。run `30208660095`はentropy 0.005 screeningとして無効であり、実際には全seedで0.05が使われたことをartifactとcommandから確認した。仮説を棄却せず、配線をfail-closed化して正しい0.005 rerunへ接続した。外部baseline再現0、能力進歩未認定、高校生級未達を維持する。