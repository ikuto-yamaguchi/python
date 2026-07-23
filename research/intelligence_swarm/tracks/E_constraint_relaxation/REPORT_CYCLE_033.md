# 系列E Cycle 033 研究報告

## 仮説

**Curvature-Gated Multi-Value Attractors from Counterfactual Work Loops**  
（反実仮想work loopの曲率でゲートされる複数値アトラクタ）

Cycle 032の次案はmulti-value scope fiberだったが、系列C Cycle 034がすでに複数値・可逆・非対象不変の介入fiberを直接検証している。中心機構の重複を避け、本Cycleではfiber形成そのものを成果対象から外した。

同一候補supportへcommand内の複数値候補を往復介入したときの、

- outcome距離の平均
- 値間の距離分散（局所energy曲率）
- write→restoreのround-trip成功
- 区間外damage
- 利用可能な値数

を局所work signatureとし、energy landscapeの曲率項として候補競合へ組み込んだ。Final testのafter/futureはcandidate生成・energy rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | Multi-value temporal transition fiber | 時間予測状態・carry・次観測 |
| B | Executable scope program | MDL・program grammar |
| C | Multi-value intervention fiber | 因果state-variable・介入support |
| D | Shared-generator memory cycle | 長期memory・read/write閉路 |
| **E** | **multi-value workによるenergy曲率とattractor basin選択** | 今回の固有対象 |

系列Cと同じ「複数値で置換可能な区間の発見」は候補から棄却し、Eでは同じ候補集合に対するenergy curvature・active-state縮小・固定点選択だけを評価した。

## 先行研究整理

- Equilibrium Propagationはfree phaseとnudged phaseの固定点差から局所学習を行うが、状態nodeとenergy topologyを前提とする。
- 2025年のfinite-nudge理論は任意強度のnudgeでも期待局所energy微分差を使える枠組みを示す。
- 2026年のAugmented Lagrangian Predictive Codingは局所constraint errorをdual variableへ蓄積してcredit伝播を改善する。

今回の未解決点は、それらより上流の、生の日本語から意味候補nodeとconstraint topologyを形成する問題である。

参考:
- https://arxiv.org/abs/1602.05179
- https://arxiv.org/abs/2511.22024
- https://arxiv.org/abs/2605.31022

## 実装

- 固定ontology、手書きslot、分類器、辞書、RAG、外部LLMなし
- 生の`before`全局所spanと`command`固有spanから候補生成
- Candidate上限32
- Induction / independent probe / final testを分離
- No-energy / Single-value work / Multi-value curvature / Shuffled outcomeを比較
- Active集合を各sweepでenergy最小値+0.06以内へ単調縮小
- 最大7 sweep、実測最大2 sweep

## 3 seed平均

| 条件 | No energy 精度/wrong | Single-value 精度/wrong | Curvature 精度/wrong | Curvature active |
|---|---:|---:|---:|---:|
| 既知 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 17.73 |
| 未知語 | 0.0000/0.0000 | 0.0000/0.0333 | 0.0000/0.0333 | 15.77 |
| 曖昧性 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 11.53 |
| 入れ子 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 19.60 |
| 主語省略 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 20.00 |
| 複数段落 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 15.50 |
| 計画変更 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 17.90 |
| 反実仮想 | 0.0000/0.0000 | 0.0000/0.0000 | 0.0000/0.0000 | 19.50 |

追加診断:

- Multi-value work state: 40.33
- Shuffled work state: 42.67
- Probe audit: 384
- モデルサイズ: 8586 bytes
- 学習時間: 0.184081 sec
- 既知推論: 22.092 ms/example
- 複数段落推論: 38.132 ms/example
- Peak RSS: 111676 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Work signatureは形成された

Correct probeから平均40.33件のmulti-value work stateが形成された。候補ごとにround-trip、区間外damage、距離平均・分散を計測でき、単純な候補集合空崩壊は回避した。

### Energy curvatureの能力増分は0

全条件でNo-energy、Single-value、Multi-value curvatureのexecution accuracyは0だった。Exact boundary recallとobject-value pair recallも全条件0である。

Curvature項はactive状態数を既知条件で20から17.73へ縮小したが、正しい候補を残した証拠はなく、全面tie/nullへ収束した。

> **局所energy曲率は候補集合の形を変えられるが、候補のsemantic identityを生成しない。**

### Correctとshuffleを識別できない

Shuffled outcomeでもwork state数は42.67件となり、Correct probeよりむしろ多い。Final能力・active数・null率もほぼ同一だった。

距離分散やround-tripは、正しい外部対応ではなくsurface長・shape・置換幅からも容易に形成されるため、正しいconstraint topologyの根拠にならなかった。

### 未知語で誤固定点

未知語条件ではSingle-value、Curvature、Shuffleのすべてでwrong commitが0.0333発生した。Curvature固有の改善ではなく、work項が平坦地形を一部のsurface候補へ傾けた誤アトラクタである。

### 計画変更・反実仮想

計画変更と反実仮想はaccuracy 0、null率1.0で、旧案・最終案、実行world・非実行worldを別固定点として保持できなかった。

## 収束保証と失敗分類

Active集合は各sweepで単調に部分集合へ縮小し、最大7 sweepで停止するため有限停止する。実測最大は2 sweep。

- Candidate birth: 32候補を維持
- Curvature-state birth: 成立
- Semantic boundary collapse: exact recall 0
- Constraint-grounding collapse: Correctとshuffle能力差0
- Flat landscape: ほぼ全面tie/null
- Wrong attractor: 未知語で0.0333
- 発散: 未観測

## Hopfield・既存NNとの差

固定patternの保存・想起ではなく、入力ごとに局所境界候補を生成し、複数反実仮想writeのworkと曲率からenergyを構成し、疎な反復緩和で固定点を探索した点は単純Hopfield記憶と異なる。

ただし現状は文字区間置換に基づく手続き的energyであり、学習された意味constraint graph、正式な平衡伝播、連続energy networkには未到達。

## 資源量・計算量

- Candidate生成: `O(L^4)`、32候補へ上限制限
- Multi-value work: `O(QHVL^2)`
- Relaxation: `O(SH)`
- `H<=32, S<=7`

1GB未満は達成。既知でも約22.1ms、複数段落約38.1msのため5ms未満は未達。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **複数値介入の可逆性・非対象保存・距離曲率をenergy項へ変換しても、Correct probeとshuffleを分離できなければattractor selectionはsurface work統計へ退化する。Energy topologyには値介入だけでなく、命令側と状態側が同時に変化する結合constraintが必要である。**

## 他系列へ返す知見

- A: Multi-value fiberでもcommand-state結合がなければ時間遷移identityにならない。
- B: Scope programは静的featureでなく、command変更に応じてstate consequenceが変わる相互予測を必要とする。
- C: Multi-value fiber形成だけではcommand bindingを解けず、Cycle 034の次案であるcross-value action contrastが妥当。
- D: Read/write cycleも、query・command・stateを同一生成constraintで結ばなければsurface nodeの閉路に留まる。

## 次の仮説

**Command–State Coupled Energy Fibers from Cross-Value Contrastive Work**  
（値横断contrastive workによるcommand-state結合energy fiber）

1. 同一state supportへ複数値を介入
2. Command側の候補値区間も同じ値へ交換
3. Command交換とstate rollout交換が一致するときだけ結合edgeを生成
4. State-only fiberとcommand-state coupled fiberを比較
5. Correct exchange / shuffled exchange / single-value / no-couplingを比較
6. Coupling edge除去で対応attractorだけが消えることを監査
7. 曖昧性では複数object候補を並行active stateとして保持
8. 計画変更では撤回edgeへ抑制constraintを付与
9. 反実仮想では実行edgeと非実行edgeを別固定点へ分離
10. Exact boundary、execution、wrong attractor、energy gapを同時評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
