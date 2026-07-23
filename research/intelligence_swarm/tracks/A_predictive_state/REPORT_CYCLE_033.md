# 系列A Cycle 033 研究報告

## 仮説

**Residual-Born Transition Kernels from Probe-Localized Error Transport**  
（probe局所誤差輸送からのresidual-born遷移kernel創発）

Cycle 032ではprobeをtransition-kernelの保持・削除・topology生成へ作用させたが、Correct probeでも全kernelが削除され空topologyへ崩壊した。本Cycleでは、失敗したprospective stateと独立probe outcomeの局所残差を、state境界bucket・width・command引数bucketへ逆輸送し、新しいtransition kernelを生成できるか検証した。

Final testのafter/futureは候補生成・rankingに使用していない。固定ontology、手書きslot、分類器、RAG、外部LLM、Transformer attentionは使用していない。

## 他系列との重複排除

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B | Scope-compressed symbol production | MDL・program grammar・repair圧縮 |
| C | Multi-value intervention fiber | 因果state-variable・world graph |
| D | Cycle-closing memory address | 長期memory・read/write閉路 |
| E | Multi-value scope fiber | Energy固定点・境界repair attractor |
| **A** | **局所予測誤差を時間遷移kernelのbirthへ輸送** | 今回の固有対象 |

Eのnear-miss repairは境界候補集合とenergy地形を対象とする。Aでは現在状態→次観測の時間方向operator、複数turnでの継続・終了・切替を担うtransition kernelだけを対象とした。

## 実装

- Induction: before→after差分から相対位置kernelを生成
- Independent probe: prospective afterと観測afterの編集距離を計測
- Residual transport: state bucket shift、width shift、command bucket shiftを局所生成
- Birth条件: 元kernelよりprobe残差を減らし、複数probeで2回以上再現
- Topology: 近接kernel間に局所edge
- Ablation: Base / Carry / Pruning-only / Correct residual birth / Shuffled residual birth
- Relaxation: active集合不変または最大6 sweep

## 3 seed平均

| 条件 | Base 精度/wrong | Prune 精度/wrong | Residual-birth 精度/wrong | Shuffle精度 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 未知語彙 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 明示切替混在 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |

追加診断:

- Induction kernel: 3.33
- Residual-born kernel: 3.00
- Birth後kernel総数: 6.33
- Topology edge: 20.67
- Probe audit: 296.00
- モデルサイズ: 530 bytes
- 学習時間: 0.0577 sec
- 既知推論: 1.757 ms/example
- 複数段落推論: 2.054 ms/example
- Peak RSS: 111492 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Kernel birth自体は成立

Correct probe残差から平均3個の新kernelが形成された。Cycle 032の全削除・birth 0から、prediction errorが新しい局所遷移候補を生成する段階には進んだ。

### 能力増分は0

しかしBase、Pruning、Residual-birth、Shuffled-birthのexecution accuracyは全条件0だった。新kernelはfinal testで正しいprospective stateを一件も生成しなかった。

> **局所残差を境界shiftへ逆輸送するとkernel候補は生まれるが、残差位置だけでは対象・値・関係・操作・scopeを束縛するtransition identityにならない。**

### 正しいprobe固有の因果効果がない

Correct residualでkernel birthは発生したが、Shuffled residualとの能力差は0だった。Topology差が状態選択・主語省略継続・計画変更へ作用していない。

### 主語省略・計画変更・反実仮想

- 主語省略: object permanence・前turn state再起動は未成立
- 明示切替: old state終了とnew state開始は未成立
- 計画変更: 撤回案と最終案を別kernelへ分離できない
- 反実仮想: 実行worldと非実行worldを並行保持できない

## 反証分類

- Kernel birth: 成立（平均3）
- Semantic argument binding: 崩壊
- Execution: 全条件0
- Probe-specific topology effect: 0
- Candidate/tie degeneration: 支配的
- 発散: 最大6 sweepで未観測
- 高校生級: 未達

## 既存方式との差

単なる一方向分類や文字列検索ではなく、prospective stateの誤差を局所遷移構造へ逆輸送し、kernel birth・topology・反復緩和を行う。ただし現状は相対文字位置の離散edit kernelであり、世界状態・言語状態・active inferenceには未到達。

## 資源・計算量

- Induction `O(NL)`
- Probe residual transport `O(QKVL²)`
- Topology `O(K²)`
- Inference `O(KOV + SH)`
- `K≤64, S≤6, H≤16`

1GB未満・小規模5ms未満は達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **Prediction errorへbirth作用を持たせると空topologyから脱出できる。しかし位置残差だけを輸送したkernelは、時間的な状態identityや引数bindingを獲得しない。次は単一after差分ではなく、複数値・複数turnで同じ非対象予測を保存する遷移fiberを形成する必要がある。**

## 他系列へ返す知見

- B: repair ruleのcandidate birthだけではselection entropyを解けない。適用scopeと外部実行差が必要。
- C: 単一outcomeの境界残差はstate-variable同定にならず、複数値介入不変性が必要。
- D: read/write cycleも位置残差だけではsemantic addressにならない。
- E: near-miss repairのbirth信号はAでも再現したが、scopeなしでは能力へ接続しない。

## 次の仮説

**Multi-Value Temporal Transition Fibers from Non-Target Predictive Invariance**  
（非対象予測不変性による複数値時間遷移fiber）

1. 同じtarget境界候補へ3種類以上のvalueを介入
2. 各介入で区間外のnext-observation予測が不変か監査
3. Forward・inverse・再適用が同じ境界で成立するkernelだけfiber化
4. 複数turnで同じfiberが再起動することを要求
5. Correct multi-value probe／single-value／shuffled value／no-fiberを比較
6. 主語省略では前turn fiberを再起動
7. 明示切替では新fiberが旧fiberのprediction errorを説明した時だけ終了
8. 計画変更では撤回・最終goalを別fiberへ分離
9. 反実仮想では実行・非実行fiberを並行保持
10. Exact boundary、execution、non-target invariance、wrong carryを独立評価

**高校生級知能：未達**  
**ネイティブ日本語コミュニケーション：未達**  
**弱いスマートフォン実機検証：未達**  
**完成：未達**
