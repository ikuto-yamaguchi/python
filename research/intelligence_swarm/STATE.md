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

「検証したが駄目だった」で終了しない。失敗runは、失敗分類、metric/log/code差分に基づく原因、最小修正、同一budget・instance再run、採用・棄却・停止判定まで未完了とする。宣言した変更変数が実command・artifactへ到達しないrunは仮説検証として無効とし、配線修復後に同一screeningを再実行する。高コスト学習が成功済みなら、監査・qualification障害のために再学習せず、immutable artifactから回復する。

## R0 status ledger

- immutable 131,072-frame R0.1 bundle: **3件**（baseline不合格2件、有効entropy=0.005 bundle 1件・qualification回復中）
- 学習済み公開能力baseline再現: **0件**
- J-CRe3 numerical reproduction: **0件**
- R0.2正式再現: **0件**
- 実R0 bundleのevaluation contract通過: **0件**
- R0.3 hidden intervention-target ablation: **棄却維持**
- 広義RQ-001: **棄却**
- 狭義RQ-001: **未採用**
- 評価分類: **`initial_reproduction_failure`**

## Baseline immutable failure: run 30203026269

- artifact ID `8633105142`、digest `sha256:43ab7f1df82e9eba98c132b2e84a9ec55dbfdd726795fb43f7608fe288e00eef`
- Correct `0/60`、Random `4/60`、Language-blind `1/60`、State-only `0/60`、Language-shuffle `0/60`
- Correct return `-2.0749993`、Random return `-1.1513333`
- same-instance成立、answer leakage `false`
- classification: `optimization_or_policy_competence_failure`

## Invalid factor-routing run: 30208660095

要求は`entropy_cost=0.005`だったが、全seedの実commandは`0.05`だった。artifact `8634594371`は0.05条件の追加negative resultとしてのみ保存し、entropy仮説の採否には使わない。

## Valid entropy=0.005 screening: run 30215555334

- job `89830932884`、execution commit `cbd4af3d89718df76cc481f7c730ed80334ef223`
- artifact ID `8636643017`
- artifact size `72,690,803 bytes`
- artifact digest `sha256:094ba8d6fba428c15e1dfa43298f3af9943d9fae840a072a691d3f420c5bcec2`
- `entropy_cost=0.005`はtraining summary、seed `1/7/19` record、全seed commandで到達確認済み
- actual frames: 全seed `131,080`
- model parameters `4,916,915`、state dict約`19.69 MB`
- training wall: seed 1 `1447.61 s`、seed 7 `1519.27 s`、seed 19 `1436.77 s`
- peak RSS: seed 1 `1,370,676 KiB`、seed 7 `1,337,440 KiB`、seed 19 `1,247,468 KiB`
- CPU forward audit `7.564 ms/step`
- Correct `0/60`、Random `4/60`、Language-blind `2/60`、State-only `0/60`、Language-shuffle `0/60`
- Correct mean return `-2.1523326`、Random mean return `-1.1513333`
- same-instance controls: 成立
- policy diagnostics: chosen-action valid fraction `1.0`、masked entropy平均はseed 1/7/19で`1.273/1.216/1.133`

数値上、`entropy_cost=0.005`はCorrectをRandom以上へ引き上げず、entropy単独原因は**棄却候補**である。ただしrunのqualification stepはofficial-eval parity監査の実装不具合によりskipされたため、正式な採否は保存artifactからのrequalification完了後に確定する。

## Evaluation parity failure and repair

`audit_silg_official_eval_parity.py`のfresh-instance経路が`Environment.initial()`の境界`done=True`を終了済みと誤解し、一度もstepせず`empty evaluation stream`で失敗した。matched evaluatorは正しく`done=False`から開始していた。監査を同じ意味論へ修正し、expensive training workflowから監査修正triggerを外した。

既存artifact `8636643017`を`actions/download-artifact`で取得し、pinned SILG/RTFMを再導入してparity監査とunchanged qualificationだけを再実行する`.github/workflows/r01_silg_entropy_requalify.yml`を追加した。再学習は行わない。

## Evaluation contract

D015〜D035を凍結する。実bundleが具体的なfalse pass/failureを示すまで新規auditorを追加しない。今回の修正は新規監査追加ではなく、既存監査の実行意味論修復である。

## Prior-art and RQ boundary

既存のscore-based CRL、finite-sample CRL、Multi-View CRL、LeGIT、GPI、ReCITE、C3、MCDRL、CmIR等の境界を維持する。

C038としてACL 2026 **Learning Invariant Modality Representation for Robust Multimodal Learning from a Causal Inference Perspective**を明示する。同研究は各modalityをcausal-invariant representationとenvironment-specific spurious representationへ分離し、invariance・mutual-information・reconstruction制約でOOD/noise robustnessを高める。したがって、multimodal invariant/spurious decomposition、環境横断安定表現、情報保持付き因果不変表現だけではRQ-001の新規性を認定しない。ACL Anthology一次論文は確認済みだが、掲載ページからauthor-official codeは確認できず、再現済みbaselineには数えない。

正式判断:

> **RQ-001: FURTHER NARROWED BEYOND CAUSAL MODALITY-INVARIANT REPRESENTATION — NOT ADOPTED**

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

2026-07-26: **RESET-E060**。有効なentropy=0.005 runのimmutable artifactと数値を回収した。性能はRandom未満でentropy単独原因は棄却候補だが、official-eval parity監査の`initial done`誤解でqualificationがskipされたため、監査を修正し既存artifactから再qualificationする回復workflowを追加した。高コスト再学習は行わない。C038 CmIR境界を明示し、外部baseline再現0、能力進歩未認定、高校生級未達を維持する。
