# 系列A Cycle 036 研究報告

## 仮説

**Reciprocal Boundary Birth from Cross-View Predictive Error Transport**  
（cross-view予測誤差の相互輸送による境界共同創発）

Cycle 035ではstate・command value・command object境界を一つのtupleへまとめても、独立probeで全cellが消失した。今回は境界固定後に監査する順序を棄却し、probe上のstate rollout誤差とcommand-value整合誤差を相互輸送して、shift・contract・expand操作から境界を生成した。

Fixed boundary、state誤差だけのone-way transport、state／command双方を改善するreciprocal transport、shuffled outcomeを比較した。Final testのafter/futureは候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B | 介入商grammar・可換diagram | MDL・記号圧縮 |
| C | 介入交換子による因果方向 | 因果world graph |
| D | 削除必要性によるmemory統合 | 長期memory・再固定化 |
| E | Frustration局在hyperedge | Energy固定点・constraint topology |
| **A** | **時間予測誤差をcommand/state境界birthへ相互輸送** | 今回の固有対象 |

## 先行研究との位置づけ

2025年のpredictive alignmentは局所可塑性でrecurrent trajectoryを整えるが、network stateと結合は既定である。PCN-TAは時間相関を利用しpredictive-coding inference反復を削減するが、latent stateは既定である。2026年のTemporal Predictive Coding + approximate RTRLも、既定RNN上の時空間credit assignmentであり、生の日本語から状態境界を生成する今回の上流課題とは異なる。

## 3 seed平均

| 条件 | Fixed 精度/wrong | One-way 精度/wrong | Reciprocal 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0/0 | 0/0 | 0/0 | 0/0 |
| 未知語順 | 0/0 | 0/0 | 0/0 | 0/0 |
| 未知語彙 | 0/0 | 0/0 | 0/0 | 0/0 |
| 入れ子 | 0/0 | 0/0 | 0/0 | 0/0 |
| 主語省略 | 0/0 | 0/0 | 0/0 | 0/0 |
| 複数段落 | 0/0 | 0/0 | 0/0 | 0/0 |
| 計画変更 | 0/0 | 0/0 | 0/0 | 0/0 |
| 反実仮想 | 0/0 | 0/0 | 0/0 | 0/0 |

追加診断:

- Fixed rule: 13.00
- Reciprocal rule: 0.00
- One-way transport step: 80.67
- Reciprocal transport step: 80.67
- Shuffled transport step: 64.67
- Probe audit: 511.33
- Reciprocal model: 136 bytes
- Training: 0.007508 sec
- Seen inference: 0.004664 ms/example
- Paragraph inference: 0.004659 ms/example
- Peak RSS: 168052 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 誤差輸送操作は生成された

One-way・Reciprocalとも平均80.67件の局所境界操作を生成した。Fixed方式と異なり、probe誤差がcandidate birthへ作用した。

### 再利用可能ruleは0

独立probe上で正しいafterを再構成し、2例以上で再現するboundary ruleはOne-way・Reciprocalとも0件だった。

> **Cross-view error transportはboundary searchを動かせるが、文字位置残差だけでは対象・値・操作・scopeを共同同定できない。**

### One-wayとReciprocalが同じ

両方式のtransport stepは同一だった。command誤差が「command候補値がtarget文字列に含まれるか」という粗い信号で、state rollout誤差から独立した拘束にならなかった。二つのviewが実質同じsurface outcomeへ従属していた。

### 全面棄権

全条件でaccuracy 0、wrong 0、null 1.0。主語省略のobject permanence、明示切替の旧state終了、計画変更の撤回案／最終案分離、反実仮想の実行／非実行state並列保持、長距離時間抽象化は未成立。

## 反証分類

- Transport birth: 成立
- Reusable boundary rule collapse: 支配的失敗
- Cross-view independence collapse: One-wayとReciprocal同一
- Predictive state collapse: execution 0
- Null degeneration: 全面棄権
- 発散: 候補上限と2 sweepで未観測

## 資源量

- Candidate生成 `O(L²)`、24候補へ疎制限
- Error transport `O(QSHM)`
- Inference `O(R)`
- `S=2`、rule上限32
- Model 136 bytes
- Training 0.007508 sec
- Inference 約0.005 ms/example

1GB未満・5ms未満は小規模条件で達成。ただし有効rule 0のため効率的知能の証拠ではない。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **境界固定後の監査から誤差駆動boundary birthへ進めた。しかしstate viewとcommand viewが同じ正解文字列へ依存すると、reciprocal transportはone-way transportと区別できず、意味状態を形成しない。**

## 他系列へ返す知見

- B: 可換diagramも各viewが同じsurface outcomeへ従属すると独立制約にならない。
- C: 介入交換子を異なる観測channelからboundary birthへ作用させる必要がある。
- D: Read/write residual transportには独立witnessが必要。
- E: Hyperedge frustrationをboundary birthへ戻す際、constraint channelの独立性を反証すべき。

## 次の仮説

**Counterfactual Sensor Separation for Multi-Channel Predictive State Birth**  
（反実仮想sensor分離による多channel予測状態創発）

1. State-after文字列だけを共通oracleにしない
2. Command-value swap、object swap、future継続、non-target保存を独立sensor channel化
3. 各channelが別々に支持・反証できるboundary populationを維持
4. 一つのchannelだけ改善する操作は保留
5. 3 channel以上を同時改善する操作だけstate cell化
6. Correct channel／channel shuffle／single-channel／shared-outcomeを比較
7. 次turnで同じcellが再起動した場合だけ時間状態化
8. 主語省略・明示切替・計画変更・反実仮想を独立固定点として評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
