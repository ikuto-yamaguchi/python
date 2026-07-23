# 系列A Cycle 034

## 仮説

**Multi-Value Temporal Transition Fibers with Cross-Turn Reactivation**  
（複数値介入とturn横断再起動による時間遷移fiber）

系列C Cycle 034の「状態supportへの複数値介入」と同じ実験は重複のため棄却した。系列Aでは、同じ局所遷移が複数値で成立するだけでなく、連続turnで再起動し、区間外の次観測予測を保存する場合にのみ時間予測状態へ昇格できるかを検証した。

## 他系列との重複表

| 系列 | 最新中心 | Aで分離した領域 |
|---|---|---|
| B | executable scope program | MDL・program grammar |
| C | command-coupled intervention fiber | 因果state support・world transition |
| D | shared-generator memory cycle | 長期memory・read/write閉路 |
| E | command-state coupled energy fiber | energy固定点・work曲率 |
| **A** | **複数turnで再起動する時間遷移fiber** | 現在状態→次観測の時間方向予測 |

## 実装

- Transformer・attentionなし
- 固定ontology・手書きslot・辞書・RAG・外部LLMなし
- induction / independent probe / final testを分離
- raw kernel、single-value、multi-value temporal fiber、shuffled outcomeを比較
- final testのafter/futureは候補生成・rankingに不使用
- 最大12 active候補、有限tie停止

## 3 seed平均

| 条件 | Raw | Single-value | Multi-value temporal | Null率 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 未知語彙 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| Rename | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 明示切替混在 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

追加診断：

- Raw kernel: 6.00
- Single-value fiber: 0.00
- Multi-value temporal fiber: 0.00
- Reactivation edge: 0.00
- Probe audit: 0.00
- モデルサイズ: 134 bytes
- 学習時間: 0.000057 sec
- 既知推論: 0.0008 ms/example
- 複数段落推論: 0.0008 ms/example
- Peak RSS: 111112 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Multi-value条件でfiberが全消失

Raw inductionでは平均6件のsurface-local kernelが形成されたが、独立probe上で3種類以上の値、正しいforward結果、誤実行より多い支持、turn横断再起動を同時に要求すると、fiberは全seedで0件になった。Single-value条件でも0件だった。

> **複数値・再起動条件は既存kernelを厳密に監査できるが、時間予測状態を新生する原理ではない。**

### 全条件で全面棄権

Raw、Single、Multi、Shuffleのexecution accuracyは全条件0である。Multi方式はnull率1.0で、主語省略、切替、計画変更、反実仮想のいずれにも状態候補を形成できなかった。

### 支配的失敗

- **Command-value binding collapse**: command固有spanが真の値境界にならない
- **Temporal reactivation collapse**: 同じ潜在対象を跨ぐfiber identityがない
- **Object permanence collapse**: 主語省略で前turn stateを再起動できない
- **Goal/world separation collapse**: 撤回案・最終案、実行・非実行worldを分離できない
- **発散**: 未観測。候補有限・tie停止

### 先行研究との差

Temporal predictive codingは局所可塑性、reservoir dynamics、階層的再帰、eligibility traceによって長期依存を学べる可能性を示すが、状態表現と回路は事前に存在する。今回の失敗は、その前段である生の日本語からのoperator引数・状態境界birthが未解決であることを示す。

## 資源量

- Induction `O(NL)`
- Multi-value probe `O(QFVL)`
- Inference `O(FOV)`
- Fiber上限32、value候補8、object候補6

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **複数値介入とturn横断再起動は、時間状態候補の厳密な監査条件にはなる。しかし具体的相対境界kernelからは一件も通過せず、状態birthの前段へ戻る必要がある。**

## 他系列へ返す知見

- B: 実行可能scope programも、値交換後の遷移を別turnで再起動できるか監査すべき。
- C: Multi-value fiber形成だけではcommand bindingと時間永続性を保証しない。
- D: Memory cycleのslow化前に、同じlatent proposalが複数turn・複数値で再起動するか確認すべき。
- E: Work曲率だけでなく、正しいcommand交換が次turn予測を一貫して変える必要がある。

## 次の仮説

**Joint-Born Command–State Transition Cells from Cross-Turn Contrastive Swaps**  
（turn横断contrastive swapによるcommand-state共同創発cell）

1. State境界とcommand値境界を別々に生成せず、一つのlatent proposalから共同生成
2. Command値を別値へswapし、prospective stateも対応値へ変化することを要求
3. 次turnのbefore/future予測が同じproposalで再起動することを要求
4. Object swapではtarget state supportだけが切り替わることを要求
5. Correct swap / shuffled swap / state-only / command-onlyを比較
6. 主語省略では前turn cellを再起動
7. 計画変更では撤回cellを抑制し最終cellを保持
8. 反実仮想では実行・非実行cellを並列保持
9. Exact boundary、execution、reactivation、wrong carryを独立評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
