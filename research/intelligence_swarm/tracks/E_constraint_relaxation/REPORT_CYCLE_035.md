# 系列E Cycle 035

## 仮説

**Frustration-Localized Constraint Hyperedges from Basin-Specific Counterexample Residuals**  
（競合盆地固有の反例残差からのfrustration局在制約hyperedge）

Cycle 034ではcommand-state同時swap閉路がenergy landscapeを変えたが、correct probeとshuffleを区別できなかった。次案のobject/value二重swapは、系列B Cycle 035のswap grammar、系列C Cycle 035のintervention commutator、系列A Cycle 035のjoint contrastive swapと中心機構が重なるため棄却した。

今回は値・対象交換そのものを新規性にせず、同一入力上の複数候補が異なるprospective stateを作る**競合盆地**を検出し、独立probe outcomeが局所的に選ぶtarget境界・command値境界・文脈・frustration位置の4者を高次hyperedgeとして局所学習した。Final testのafter/futureはcandidate生成・energy rankingに使用していない。

## 他4系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A Cycle 035 | joint-born command-state transition cell | 時間方向再起動・carry |
| B Cycle 035 | joint-born variable production / swap grammar | MDL・匿名variable・圧縮 |
| C Cycle 035 | intervention commutatorによる因果方向 | 因果diagram・方向性 |
| D Cycle 035 | deletion-causal consolidation | memory read/write必要性 |
| **E Cycle 035** | **競合候補盆地に局在する高次energy hyperedge** | 今回の固有対象 |

## 実装

- `before`内target候補と`command`固有value候補から最大32 prospective stateを生成
- 候補間で予測文字が分岐する位置を8 bucketのfrustration basinとして抽出
- Independent probe上で最小残差+2以内の局所候補だけを監査
- target signature・value signature・context・frustration basinを4項hyperedge化
- Correct / shuffled outcome / no-energyを比較
- 最大8 sweep、active集合単調縮小、energy gap不足時はnull

固定ontology、手書きslot、分類器、辞書、テンプレート、RAG、外部LLMは使っていない。

## 3 seed平均

| 条件 | No energy 精度/wrong | Hyperedge 精度/wrong | Shuffle 精度/wrong | Hyperedge active |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 未知語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 18.77 |
| 曖昧性 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 19.27 |
| 入れ子 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |
| 反実仮想 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 20.00 |

追加診断:

- Correct hyperedge: 37.00
- Shuffled hyperedge: 36.67
- Probe audit: 195.67
- 候補数: 32.00
- 平均/最大反復: 2.00 / 2
- 収束率: 1.0000
- Exact boundary / pair recall: 全条件0
- モデルサイズ: 16398 bytes
- 学習時間: 0.224020 sec
- 既知推論: 11.177 ms/example
- 複数段落推論: 11.309 ms/example
- Peak RSS: 159944 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Hyperedge birth自体は成立

Correct probeでは平均37.00件のfrustration hyperedgeが形成された。単純pairwise edgeではなく、target境界・value境界・文脈・競合位置を同時に結ぶ高次制約である。

### Correct probeとshuffleを分離できない

Shuffled outcomeでも平均36.67件が形成され、Correctとほぼ同数だった。未知語ではshuffleの方がactive状態を強く削減し、正しいprobe固有の固定点変化はない。

候補間の分岐位置と局所残差は、正しい意味制約がなくても文字列長・shape・相対位置・置換幅から形成できる。

> **競合盆地に局在した高次hyperedgeであっても、node候補がsurface-localならfrustrationは意味矛盾ではなく文字列矛盾を表す。**

### 能力増分は0

全条件でaccuracy 0、exact boundary recall 0、object-value pair recall 0、null率1.0だった。Hyperedgeは一部条件でactive集合を変えたが、正しい固定点を一件も作らなかった。

主語省略、曖昧性、長距離依存、計画変更、反実仮想の状態分離も未成立。

## 収束保証・失敗分類

各sweepで`最小energy + 0.05`以内の候補へactive集合を単調縮小し、最大8 sweepで停止する。有限候補集合なので有限停止し、実測最大は2 sweepだった。

- Candidate birth: 32候補
- Hyperedge birth: 成立
- Constraint grounding collapse: Correct/shuffle差なし
- Semantic boundary collapse: exact/pair recall 0
- Flat landscape: 全面tie/null
- Wrong attractor: 今回は安全閾値で未確定
- 発散: 未観測

## Hopfield・既存NNとの差

固定pattern想起ではなく、入力ごとに複数prospective stateを生成し、候補間frustrationから高次hyperedgeを形成し、局所energyで反復緩和する点は単純Hopfield記憶と異なる。

2025年のhypergraph学習は高次相互作用を扱い、Energy-Guided Hypergraphも高次整合性をenergy化する。しかし既存研究ではnode・特徴・対応候補が事前に与えられる。今回の失敗は、生の日本語からnode identity自体を形成する前段である。

Equilibrium Propagationや2026年のAugmented Lagrangian Predictive Codingは局所constraint errorの伝播を提供するが、状態nodeとconstraint topologyを前提とする。今回、topologyをfrustrationから新生しても、surface nodeではsemantic constraintにならなかった。

## 資源量・計算量

- Candidate生成: `O(L^4)`、32候補へ上限
- Frustration監査: `O(QHL^2)`
- Hyperedge energy: `O(SHE)`
- Relaxation: `O(SH)`
- `H≤32, S≤8, E≈37`

1GB未満は達成した。既知約11.2ms、複数段落約11.3msであり、5ms未満・弱いスマートフォンCPU実機条件は未達。

## 系列E固有の進展

> **Pairwise couplingより強い、競合盆地固有の高次hyperedgeをenergyへ導入できた。しかしCorrect/shuffleを分離できず、frustrationはsemantic contradictionではなくsurface disagreementへ接地した。**

## 他系列へ返す知見

- A: 複数viewのprediction errorを結ぶだけでは、境界nodeがsurface-localなら時間状態cellにならない。
- B: 可換diagramや匿名class形成時、Correct/shuffleで同数の高次関係が生まれる場合は意味記号と認めない。
- C: 介入交換子はdiagram形成数だけでなくexact boundaryとoutcome固有性を必須にすべき。
- D: deletion necessity以前に、address hyperedgeがshuffleで再現しないことを監査すべき。

## 次の仮説

**Residual-Transported Node Birth from Hyperedge Frustration Gradients**  
（hyperedge frustration勾配からの残差輸送型node創発）

次は既存surface node間にhyperedgeを張るだけにしない。

1. 高frustration hyperedgeの残差位置をtarget/value境界へ逆輸送
2. Target shift・width split・value relinkを新node生成操作化
3. 一つの操作で複数hyperedge frustrationが同時低下する場合だけ保持
4. Correct probeでのみnode topologyが新生することを必須化
5. Shuffled residual / edge-only / node-birth / no-energyを比較
6. Node生成後にfree/nudged二相の局所weight差を計測
7. Exact boundary・pair recall・accuracy・wrong attractorを同時評価
8. 曖昧性では複数object nodeを並行保持
9. 計画変更・反実仮想ではgoal/world nodeを別固定点化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
