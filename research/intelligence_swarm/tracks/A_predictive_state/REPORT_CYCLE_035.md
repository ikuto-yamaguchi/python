# 系列A Cycle 035 研究報告

## 仮説

**Joint-Born Command–State Transition Cells from Cross-Turn Contrastive Swaps**  
（turn横断contrastive swapによるcommand-state共同創発cell）

Cycle 034では、state側で複数値介入とturn横断再起動を同時に要求すると、surface-local kernelを厳密に棄却できた一方、時間遷移fiberは0件になった。

今回はstate境界とcommand境界を別々に生成せず、一つのlatent proposalから以下を共同生成した。

- before内の更新対象区間
- command内のvalue区間
- command内のobject区間
- prospective next-state
- 次turnで再起動する時間状態identity

独立probe上でcommand valueを別probeのvalueへswapし、prospective stateも対応値へ共変するproposalだけをtransition cellへ昇格させた。Final testのafter/futureは候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B | Joint-born variable productionと共同MDL | 記号・program圧縮 |
| C | Command-coupled intervention fiber | 因果state support・world graph |
| D | Tri-view shared-generator memory cycle | 長期memory・read/write閉路 |
| E | Double-contrast work network | Energy固定点・局所曲率 |
| **A** | **command-state共同cellの時間方向再起動・終了・切替** | 今回の固有対象 |

共同生成・value swap自体は他系列と重なるため、新規性には数えない。Aでは、同一cellが次turnの観測予測へ再起動し、主語省略・明示切替・計画変更で時間状態として機能するかだけを中心評価にした。

## 3 seed平均

| 条件 | Factorized 精度/wrong | State-only 精度/wrong | Joint 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0.0139 / 0.4167 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語順 | 0.0000 / 0.5000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語彙 | 0.0000 / 0.5000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.0139 / 0.4167 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 入れ子 | 0.0000 / 0.3611 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.6528 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 明示切替混在 | 0.0000 / 0.3472 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.5278 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 計画変更 | 0.0000 / 0.2083 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 反実仮想 | 0.0000 / 0.3333 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Factorized cell: 5.67
- State-only cell: 0.00
- Joint cell: 0.00
- Joint swap-supported cell: 0.00
- Reactivation edge: 0.00
- Probe audit: 185.33
- Joint model: 598 bytes
- Joint training: 0.001198 sec
- Joint seen inference: 0.003961 ms/example
- Joint paragraph inference: 0.003885 ms/example
- Peak RSS: 159844 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 共同cellは一件もprobeを通過しない

Factorized方式では平均5.67件のsurface-local cellが形成された。

しかし独立probeで、command value区間の抽出、command object区間の抽出、state更新、cross-value swap共変性、正実行が誤実行を上回ることを要求すると、State-only・Joint・Shuffleの全方式でcellは0件になった。

### Joint条件以前にState-only条件で崩壊

Joint方式だけでなく、cross-value swapを要求しないState-only方式も0件だった。

したがって支配的失敗は、swap条件が厳しすぎることではない。相対位置・幅・文字shapeから形成したlatent proposalが、独立probe上でcommand境界とstate境界を再現できないことにある。

> **境界を同じproposalへ格納するだけでは共同創発にならない。複数視点の予測誤差が、境界生成過程そのものを相互拘束する必要がある。**

### Factorized方式は誤commitを大量発生

Factorized方式は一部条件で候補を実行したが、正答は全条件0だった。

- 主語省略 wrong: 0.6528
- 明示切替混在 wrong: 0.3472
- 複数段落 wrong: 0.5278
- 計画変更 wrong: 0.2083
- 反実仮想 wrong: 0.3333

主語省略でreactivationに見える活性化も、正しいobject permanenceではなくsurface-local cellの誤再適用だった。

### Correct probeとshuffleの能力差は0

Correct probe・shuffled outcomeとも空cell集合へ収束した。正しい独立観測だけが生むcell topology、reactivation edge、execution能力は確認できなかった。

## 反証条件

仮説支持には最低限、Joint cellの複数seed形成、Correct probe固有のswap-supported cell、Factorizedより高いexecution accuracy、主語省略での正しい再起動、明示切替でのwrong carry低下、計画変更での撤回案と最終案の分離、反実仮想での実行・非実行state並列保持が必要だった。すべて未達。

## 既存方式との差

Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは使用していない。一方向変換ではなく、一つのlatent proposalからcommand/state/object境界を共同生成し、cross-value interventionとturn横断再起動で時間状態を監査した。

ただし現在は離散的な相対位置cellであり、予測符号化回路、active inference、world state、意味的operatorには未到達。

## 資源量

- Model: 約598 bytes
- Peak RSS: 159844 KiB
- Training: 約0.001198 sec
- Inference: 0.003〜0.02 ms/example
- 計算量: Induction `O(NL)`、Contrastive probe `O(QC)`、Inference `O(C)`、`C≤48`

1GB未満・5ms未満は小規模条件で達成した。ただし小ささと速度は、有効cellが消失した結果であり、知能効率の証拠ではない。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **State・command・object境界を一つのrecordへまとめるだけではjoint birthにならない。独立probe上で三境界が同時に再現せず、時間状態cellは形成されなかった。次は境界候補を先に固定せず、cross-view prediction errorを相互輸送しながら共同探索する必要がある。**

## 他系列へ返す知見

- B: Joint productionも、境界を一つのtupleへ格納するだけではsemantic variableにならない。共同MDL以前にcross-view再現が必要。
- C: Command-coupled fiberはstate/command境界の独立抽出に依存するとprobe転送前に崩壊する。
- D: Tri-view memory generatorも共同record化と共同生成を区別し、write/read/query誤差を境界探索へ戻す必要がある。
- E: Command-state coupling edgeを既存候補間へ張るだけでなく、coupling errorから新候補をbirthさせる必要がある。

## 次の仮説

**Reciprocal Boundary Birth from Cross-View Predictive Error Transport**  
（cross-view予測誤差の相互輸送による境界共同創発）

1. before・command・次観測を独立境界候補populationとして初期化
2. command value候補の誤差をstate境界へ逆輸送
3. state rollout誤差をcommand value/object境界へ逆輸送
4. 双方の予測誤差を減らすsplit・merge・shiftだけ保持
5. 境界確定前から複数候補を疎に並行保持
6. Correct probe／shuffled error transport／one-way transport／fixed boundaryを比較
7. 次turnで同じcross-view cellが再起動した場合だけ時間状態化
8. 主語省略では前turn cellを再起動
9. 明示切替では新cellが旧cellの誤差を説明した場合だけ終了
10. 計画変更・反実仮想では複数cellを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
