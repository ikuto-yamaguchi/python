# 系列E Cycle 019 研究報告

## 仮説

**Role-Separated Residual Transport with Counterfactual Factor Swaps**  
（反実仮想factor swapによるrole分離残差transport）

Cycle 018ではfree/nullとnudged candidateの残差を文字位置へ局所化し、探索時間と一部の誤確定を削減したが、全splitでcandidate recallは0だった。本Cycleではpair候補を直接birthせず、raw観測挙動から得た3つの独立候補集合を保持し、一因子だけを別episode候補へswapした際の after / future / non-target / execution 残差変化vectorが、surfaceを跨いで再発するかを検証した。

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 主失敗 | E候補との区別 |
|---|---|---|---|---|
| A | 遮蔽・拡張対比による最小予測境界 | object/value失敗を分解 | value・pair recall 0 | 境界最小化は扱わない |
| B | 双方向failure-success role因子 | 既知誤確定抑制 | open-set program生成0 | MDL・program商は扱わない |
| C | 最小success-failure介入cut | 対応graph評価を厳密化 | intervention score平坦 | world operation roleは扱わない |
| D | query-object-relation endpoint分離 | Rename writeに限定信号 | read誤伝播 | 長期memory addressは扱わない |
| **E** | **factor swap後の局所energy変化vectorから匿名roleを形成** | 今回検証 | candidate/role創発 | 系列固有 |

継承知見:
- A: 位置や持続性だけでは最小意味境界を選べない。
- B: failure圧縮は棄却器になってもrole生成器ではない。
- C: intervention scoreが全edgeで同じなら因果role evidenceではない。
- D: write transportとquery endpointを同一edgeへ混ぜるとreadが悪化する。

## 先行研究との位置づけ

Equilibrium Propagationの近年研究では、散逸・時間依存系や局所収束、保存則が解析され、局所更新の安定条件が明確化されつつある。一方、それらは状態変数と結合候補が定義済みである。本実験は正式なEP勾配ではなく、生の日本語から形成した匿名factor候補の一因子swapが局所energyをどのように変えるかを測る最小反証実装である。

2026年のAttractor Modelsは固定点による反復深度の適応化を示すが、backboneが既に意味表現を提案する。本Cycleはその前段、候補factor自体のopen-set形成を扱う。

## 実験条件

- 学習例: 12
- seed: 1 / 7 / 19
- test: 3例 / split / seed
- split: seen / unseen paraphrase / nested / subject omission / paragraph / plan change / counterfactual
- factor候補: 各最大6
- candidate tuple: 最大48
- 最大sweep: 4
- ablation:
  1. Joint residual
  2. Role-separated residual without swap credit
  3. Counterfactual factor-swap prototypes
  4. Factor-swap + null

学習器はraw command / before / after / futureと順序だけを使用し、hidden target/valueは評価器だけが使用した。

## 3 seed平均

| 条件 | Object recall | Value recall | Pair recall | Swap精度/誤確定 | Swap+Null精度/null |
|---|---:|---:|---:|---:|---:|
| seen | 1.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| unseen | 0.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| nested | 0.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| omission | 0.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| paragraph | 0.1111 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| plan | 0.7778 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| counterfactual | 0.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |

## 判定

**中核仮説は強く反証。Null安全停止だけが再確認された。**

### 1. Value recallが全条件0

seenではobject recall 1.0、planでは0.7778まで上がったが、value recallは全splitで0だった。そのためpair recallとaccuracyも全条件0である。

変化残差を独立factorへ分けても、command内の最小value spanではなく、それを包含する長いsurface spanが上位へ残った。

### 2. Factor swap prototypeの能力増分0

Joint / Separated / Swapは全splitでaccuracy 0、wrong commit 1.0、active候補8、sweep 2で完全に同じだった。

41個の匿名swap prototypeを形成したが、候補classを一件も意味的に分割しなかった。

### 3. Swap vectorはroleではなくfailure geometry

形成されたvectorは after類似、future包含、target不在、value不一致、非対象保存、実行不能、scope類似の差分である。object / value / scopeの意味roleではなく、現在のsurface候補が作るfailure patternを分類している。

### 4. Nullは安全だが全面棄権

Swap+Nullは全splitでwrong commit 0、null rate 1.0、accuracy 0だった。候補外でjunk attractorへ収束しない安全機構としてのみ支持される。

### 5. Swap計算は効率悪化

seen推論はSeparated約1.81msに対しSwap約10.46ms、paragraphでは12.57msだった。候補能力が増えないまま5ms目標を超えた。

## 停止条件・失敗分類

- 収束: active集合が不変、または最大4 sweep
- 局所最適: nullなしで一意junkへ収束
- 候補崩壊: 正しいvalue/pairが候補集合外
- factor崩壊: swap vectorが意味roleを分離しない
- null安全停止: absolute energyまたはmargin不足
- 発散: 今回なし（上限停止）

支配的失敗はvalue candidate collapseとfactor collapse。

## 資源量

- model: 3006 bytes
- prototype: 41
- training: 0.0484 sec
- inference:
  - seen 10.4573 ms/example
  - nested 11.4274 ms/example
  - paragraph 12.5750 ms/example
- mean sweep: 2.00
- active states: 8.00
- Peak RSS: 111244 KiB（Python runtime込み）
- complexity:
  - proposal `O(L²)`
  - swap fit `O(NWHF)`
  - relaxation `O(SHF)`
  - `H<=48`, `S<=4`

1GB未満は達成したが、Swap推論は10ms超で弱いスマートフォン5ms目標を未達。実機検証も未実施。

## Hopfield・既存NNとの差

固定patternを保存して近傍へ引き込むHopfield記憶ではなく、入力ごとにraw factor候補を生成し、一因子swapによる制約残差の変化を局所energyへ反映した。ただし、匿名roleが形成されず、結果としてsurface候補上の小規模energy rankingに留まった。

## 系列E固有の進展

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Absolute residual calibration
7. Residual identifiability
8. Cause-to-edge routing
9. Cause basis self-generation
10. Candidate/cause co-generation
11. Frustration-triggered birth
12. Position-local responsibility flow
13. **Counterfactual factor-swap residual transport**
14. Minimal sufficient factor boundary
15. Attractor relaxation・局所学習

最大の新知見:

> 一因子swapで残差energyが変わることはrole evidenceではない。包含spanの最小十分性を先に確立しなければ、swap prototypeはsurface failure geometryを再分類するだけである。

## 他系列へ返す知見

- A: occlusion/expansionで最小境界を確立する前のfactor swapは包含junkを強化する。
- B: success/failure反転vectorも、最小boundaryが未成立ならrole商ではなくfailure codeになる。
- C: minimal intervention cutは対応segmentの最小十分性を先に監査する必要がある。
- D: endpoint分離後も各endpoint spanの最小十分性を独立評価する必要がある。

## 次の仮説

**Energy-Causal Minimal Factors by Occlusion–Expansion Equilibrium Tests**  
（遮蔽・拡張平衡検定によるenergy-causal最小factor）

次はfactor swapより先に各候補境界を反証する。

- 候補内部を1文字遮蔽したfree/nudged energy増加
- 左右へ1文字拡張したenergy利得
- 別episode transportでの同じ局所energy consequence
- non-target factor energyの保存
- 遮蔽で悪化し、拡張で改善しない最小区間だけfactorへ昇格
- 最小factor成立後だけswap matrixを形成
- nullを常時保持
- role別active setと動的sweepを維持

最低成功条件:
- seen value recall > 0
- unseen / nestedのいずれかでfactor recall > 0
- swapがSeparatedよりaccuracyまたはwrong commitを改善
- null rate < 1かつwrong commitを増やさない
- model < 32KB
- inference < 5ms/example

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
