# 系列E Cycle 014 研究報告

## 仮説

**Residual-Cause Bipartite Attractors with Edge-Wise Contradiction Routing**  
（残差原因二部アトラクタとedge別矛盾routing）

Cycle 013では、言語再構成・介入結果・非対象保存・future recallの残差を分けても、それぞれがどの候補edgeを反証するか識別できず、誤候補の一意化か全面平坦化になった。

本Cycleでは、候補graphの局所edge nodeと残差cause nodeからなる二部graphを作り、矛盾を反証可能なedgeにだけ配送する。

- reconstruction residual → value edge
- non-target preservation residual → target / address edge
- inverse residual → direction edge
- revision residual → scope edge
- future-recall residual → address / target edge

同じedge値を共有する候補へ矛盾を局所集約することで、欠落・誤検出を含む疎なgeneric feedbackをdenoiseし、候補全体へ残差を加える方式より正しいattractorへ収束する、という検証可能仮説を立てた。

## 先行研究整理

- Equilibrium Propagationはfree phaseとnudged phaseの局所energy derivative差からcreditを伝える。有限nudgeへの拡張も提案されているが、局所状態が反証原因を表現できることが前提である。  
  https://arxiv.org/abs/1602.05179  
  https://arxiv.org/abs/2511.22024
- least-control principleは、解状態へ到達するために必要なcontrolを減らす局所学習原理を示す。ただしcontrolがどの状態変数へ作用すべきかは表現構造に依存する。  
  https://openreview.net/forum?id=ttQ_3CiZqd3
- 2025年のcontext-factorized online credit assignment研究は、plasticityを関連contextへ局所gateすることがcompositional generalizationに有効と報告している。  
  https://openreview.net/forum?id=S9Y89poypx
- bipartite attractor networkは曖昧・欠損証拠から整合状態を形成する構造を持つが、今回の課題は画像復元ではなく、生の日本語候補graphにおける矛盾原因routingである。  
  https://arxiv.org/abs/1906.03504

## 他系列との重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決点 | E候補との判定 |
|---|---|---|---|---|
| A | causal-survival active probes | 外部probeによる候補修復を探索 | candidate recallが低く、surface probeの生存率が飽和 | 外部観測policyは重複のため棄却 |
| B | destruction-vector e-graph | clause-local実誤適用が既知精度を改善 | relation quotientがsurface圧縮で能力破壊 | program生成・MDL統合は棄却 |
| C | identity-selective intervention partitions | object nodeをrelationより先に形成する方向 | temporal persistence clusterは全条件0 | object/world node形成は棄却 |
| D | bidirectional query-write address nodes | cross-query非干渉でwriteを局所改善 | relation-specific readとaddress形成は未成立 | 長期memory address形成は棄却 |
| **E** | **残差causeと候補edgeの二部graph** | 今回検証 | edge候補自体のopen-set生成 | 系列固有 |

継承した知見:

- A: 情報利得や候補生存だけでは現実適合性を保証しない。
- B: 誤適用結果をprogram全体でなく壊れた局所bindingへ帰属する必要がある。
- C: object nodeがない状態でobject residualを与えてもsurface fingerprintになる。
- D: future-recall差はmemory-address edgeへ帰属できなければ過剰統合する。

## 実装

比較方式:

1. `global`
   - 各残差を全edgeへ配送する。
2. `wrong`
   - reconstructionをtargetへ、inverseをscopeへ送るなど、誤ったcause-edge対応を与える。
3. `bipartite`
   - 上記の局所cause-edge対応で矛盾を配送する。

各causeでは、同じ局所edge値を共有する候補間で矛盾率を集約する。候補単体のnoisy residualではなく、edge-value単位の局所統計でenergyを更新する。

### 停止条件

- active candidate集合が前sweepと同じなら固定点として停止
- 最大4 sweep
- 一意候補がなく同率ならflat attractor
- 正答候補が候補集合外で複数cause残差が残る場合はnull causeへ収束
- 最大反復でも集合が変化する場合を発散と定義

## 実験

- 学習・評価量: 60 / 180 / 360例
- seed: 1 / 7 / 19
- 候補上限: 16
- edge: target / value / direction / scope / address
- residual cause: reconstruct / preserve / inverse / revision / recall
- 観測noise:
  - 真の矛盾を一部欠落
  - 一部候補へ偽陽性矛盾を注入
- split:
  - 既知表現
  - 未知語proxy
  - 入れ子
  - 反実仮想proxy
  - 計画変更
  - 長距離distractor
  - 引用なし自由日本語candidate-collapse

hidden target/value/edge正解は評価器だけが使用する。learnerはraw文字列から作られたspan候補、generic binary residual、候補graphだけを利用する。

## 最大360例・3 seed平均

| 条件 | Global精度 | Wrong-routing精度 | Bipartite精度 | Bipartite誤確定 | Bipartite flat |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.9019 | 0.0000 | **0.9898** | 0.0056 | 0.0046 |
| 入れ子proxy | 0.7824 | 0.1185 | **0.9685** | 0.0269 | 0.0046 |
| 計画変更proxy | 0.8898 | 0.0000 | **0.9944** | 0.0056 | 0.0000 |
| 長距離distractor | 0.9074 | 0.0000 | **0.9963** | 0.0009 | 0.0028 |
| 引用なし | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0574 |

引用なし条件:

| 方式 | candidate recall | wrong commit | null rate |
|---|---:|---:|---:|
| Global | 0.0000 | 0.9537 | 0.0000 |
| Wrong routing | 0.0000 | 0.0000 | 1.0000 |
| Bipartite | 0.0000 | 0.0000 | 1.0000 |

## 資源測定

- Bipartite model: 384 bytes
- Global model: 651 bytes
- Bipartite latency: 0.3145 ms/example
- 平均sweep: 2.00
- 平均active state: 1.005
- 収束率: 1.0000
- Peak RSS: 112188 KiB（Python runtime込み）
- 計算量:
  - proposal `O(L²)`
  - relaxation `O(S(H+R))`
  - local update `O(R × degree)`
  - `H≤16`, `S≤4`

モデル本体は1GB未満で、局所状態・短い反復という弱CPU向け条件を満たす。ただしスマートフォン実機では未検証。

## 判定

### 限定的に支持された部分

制御された候補graphとcause-edge対応が存在する条件では、edge別routingがnoisy residualを候補単体ではなくedge-value単位で集約し、Global方式を改善した。

- 既知: 0.9019 → **0.9898**
- 入れ子proxy: 0.7824 → **0.9685**
- 計画変更proxy: 0.8898 → **0.9944**
- 長距離: 0.9074 → **0.9963**

誤routingでは既知精度0.0000、flat率1.0000となった。したがって単に残差channelを増やしたのではなく、**どのcauseをどのedgeへ送るか**に増分情報がある。

### 中核仮説は反証

1. **cause-edge対応を手で与えている**
   - reconstruction→value、inverse→direction等のrouting mapは実験側が定義した。
   - 生の日本語からresidual cause nodeとedge typeを創発したわけではない。

2. **正答候補recallは引用付き制御入力で1.0**
   - target/value span候補は引用記号から作られる。
   - 引用なしcandidate recallは0であり、自由日本語構造創発は失敗。

3. **入れ子・反実仮想・計画変更はproxy**
   - graph上のscope/direction bitを評価している。
   - 自然な日本語の入れ子、反実仮想、撤回・目的変更を理解した証拠ではない。

4. **局所学習は限定的な重み更新のみ**
   - cause-edge pairの局所support更新を行ったが、free/nudged phaseの相関差による平衡伝播ではない。

5. **候補崩壊を解決していない**
   - 引用なしではBipartiteはnullへ棄権し誤確定を防ぐが、正しい候補を生成できない。

よって、**局所矛盾routingという下流部品は限定支持、中核のopen-set日本語attractor知能原理は反証**と判定する。

## 局所最適・発散・候補崩壊の分離

- 局所最適: 一意候補へ収束したがhidden truthと不一致
- 発散: 最大4 sweepまでactive集合が変化
- 平坦化: 複数候補が同energyで停止
- 候補崩壊: 正答候補が集合外
- null cause: 原因不明残差を保持し既存候補へ強制収束しない

今回の制御条件では収束率1.0で、主問題は発散ではない。引用なしでは候補崩壊が支配的である。

## 系列E固有の進展

必要条件を9段階へ更新した。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Adaptive factor中の絶対残差校正
7. Residual identifiability
8. **Residual-cause-to-edge routing**
9. Attractor relaxation・局所学習

Cycle 013では第7段階で失敗した。本Cycleは、routing mapが既知の制御条件では第8段階に強い信号があることを示した。しかしrouting自体の創発は未成立。

## 他系列へ返す新知見

- A: probe outcomeを候補全体へ与えず、どのscope/object/value edgeを反証したかへroutingする必要がある。
- B: destruction vectorはprogram全体のscoreでなく、壊したtarget/value/binding edgeへ局所帰属する。
- C: identity-selective residualはobject node全体でなくidentity-binding edgeへ配送する。
- D: cross-query failureはschema全体でなくmemory-address / relation-binding edgeへ分離する。

## 次の仮説

**Self-Induced Residual Cause Nodes by Minimal Edge Surgery**  
（最小edge surgeryによる残差原因node自己誘導）

次はcause-edge routing mapを手で与えない。

各候補edgeを一つずつ削除・反転・再束縛し、観測残差vectorのどの成分が変化したかを測る。反復して同じ有限差分signatureを持つ残差をcause nodeへ統合し、そのcause nodeと感度を持つedgeの間だけ二部接続を形成する。

最低成功条件:

- 手書きroutingなしで既知精度0.9898の80%以上を維持
- wrong-routing ablationを明確に上回る
- 引用なしcandidate recallを0から改善
- cause node 3～12
- candidate 16以下
- sweep 4以下
- 32KB以下
- 5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
