# 系列E Cycle 032 研究報告

## 仮説

**Scope-Gated Boundary Repair Attractors from Competing Counterexample Residuals**  
（競合反例残差によるscope-gated境界修復アトラクタ）

Cycle 031では独立probeのnear-miss残差から境界repairを生成し、未知語条件で境界距離とaccuracyに限定信号が出た一方、曖昧性ではwrong attractorが増加した。本Cycleでは単一near-missだけを採用せず、上位6候補を同時保持し、ある候補を改善しながら競合候補の多数を悪化させるrepairだけをscope-gated ruleとして保持できるか検証した。Final testのafter/futureはcandidate生成・energy rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | residual-born transition kernel | 時間方向の予測状態・carry |
| B | scope-compressed symbol production | MDL・program grammar |
| C | multi-value intervention fiber | 因果state-variable・world graph |
| D | cycle-closing memory address | 長期memory・read/write閉路 |
| **E** | **競合候補間のenergy差を局所修復で変形するscope gate** | 今回の固有対象 |

## 3 seed平均

| 条件 | Repairなし精度 | Ungated 精度/wrong | Scope-gated 精度/wrong | Gated最小境界距離 |
|---|---:|---:|---:|---:|
| 既知 | 0 | 0 / 0.3056 | 0 / 0 | 13.60 |
| 未知語 | 0 | 0.2222 / 0.6250 | 0 / 0 | 13.69 |
| 曖昧性 | 0 | 0 / 0.5417 | 0 / 0 | 13.64 |
| 入れ子 | 0 | 0 / 0 | 0 / 0 | 13.60 |
| 主語省略 | 0 | 0 / 0 | 0 / 0 | 13.43 |
| 複数段落 | 0 | 0 / 0 | 0 / 0 | 13.74 |
| 計画変更 | 0 | 0 / 0 | 0 / 0 | 16.03 |
| 反実仮想 | 0 | 0 / 0 | 0 / 0 | 15.69 |

追加診断:

- Probe audit: 3,456
- Ungated repair rule: 50
- Scope-gated repair rule: 0
- Gate採用 / 棄却: 0 / 216
- Shuffle repair rule: 0
- モデルサイズ: 58,207 bytes
- 学習時間: 0.838 sec
- 既知推論: 7.525 ms/example
- 複数段落推論: 7.499 ms/example
- Peak RSS: 113,844 KiB（Python runtime込み）
- 平均 / 最大反復: 2 / 2
- 平均active状態: 24
- 収束率: 1.0

## 判定

**中核仮説は強く反証された。**

Ungated方式では平均50件のrepair ruleが形成され、未知語accuracy 0.2222、境界距離0.125まで改善した。しかしwrong commitは0.625、曖昧性wrong commitは0.5417へ増加した。

Scope gateを要求すると、採用repairは全seedで0件になった。Correct probeとshuffled probeは同じ空rule集合へ収束し、Gated方式はNo-repair baselineと完全同一だった。

> **単一候補を正解へ近づける境界deltaは存在するが、競合候補を選択的に悪化させるscope付きdeltaは形成されなかった。**

Cycle 031の未知語改善は再現した一方、exact object-value pair recallは全条件0だった。正しいafter生成は広い区間置換によるsurface reconstructionであり、対象・値・関係・操作の意味境界形成ではない。

主語省略、計画変更、反実仮想では全面棄権し、object permanence、旧goalと最終goalの競合、実行worldと非実行worldの並列固定点は未成立。

## 収束・反証分類

有限候補集合を各sweepで部分集合へ縮小し、最大6 sweepなので有限停止する。実測最大2 sweep、収束率1.0。

- Candidate birth: Ungatedで成立
- Scope-gated repair birth: 0件
- Semantic boundary collapse: exact pair recall 0
- Wrong attractor: Ungated未知語・曖昧性で増加
- Null safety degeneration: Gated全面棄権
- 発散: 未観測

仮説支持には、Correct probeでのみscope-gated ruleが形成され、Ungatedのwrong attractorを減らしつつaccuracyまたはpair recallを維持・改善する必要があった。すべて未達。

## Hopfield記憶・既存NNとの差

固定pattern想起ではなく、入力ごとに境界候補を生成し、独立probe残差から候補生成操作を学び、競合候補間のenergy地形を反復緩和で変形する点は単純Hopfield記憶と異なる。ただし現状は文字区間deltaと手続き的energyであり、意味constraint topology、正式な平衡伝播、連続energy networkには未到達。

## 資源量・計算量

- Candidate生成: `O(L^4)`、96候補へ上限制限
- 競合residual監査: `O(QkHL^2)`、`k=6`
- Repair expansion: `O(HR)`
- Relaxation: `O(SH)`、`S≤6`
- 1GB未満: 達成
- 5ms未満: 未達
- 弱いスマートフォン実機: 未検証

## 系列E固有の進展

> **Near-miss残差は候補birthを改善できるが、単純な競合悪化条件を課すと有効repairまで全消失する。Scopeは候補間の相対誤差だけでなく、複数介入下で不変な対象supportとして形成する必要がある。**

## 他系列へ返す知見

- A: residual-born kernelも競合候補を悪化させるだけのgateでは全pruningへ崩壊し得る。
- B: repair applicability codeは単一probeのsuccess/wrongではなく複数介入でのsupport invarianceを符号化すべき。
- C: multi-value intervention fiberのnon-target invarianceがscope形成の有力な独立証拠になる。
- D: cycle addressも競合抑制だけではなく、複数write値で同一supportを保持する必要がある。

## 次の仮説

**Multi-Value Scope Fibers for Energy-Gated Boundary Repair**  
（複数値介入不変性によるenergy-gated scope fiber）

1. 同じtarget候補へ3種類以上のvalue候補を介入
2. 値を変えても区間外観測が保存されるsupportを抽出
3. 同一supportへ異なる値を可逆挿入できる候補だけscope fiber化
4. Repair deltaをfiber内だけへ適用
5. Correct multi-value probe / shuffled value / single-value / no fiberを比較
6. Fiber除去で対応candidateだけ消失することを監査
7. Exact pair recall、wrong attractor、candidate entropyを同時評価
8. 主語省略・計画変更・反実仮想では複数fiber固定点を保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
