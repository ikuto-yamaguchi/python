# 系列E Cycle 020 研究報告

## 仮説

**Fixed-Point Basin Curvature for Energy-Causal Factor Selection**  
（固定点basin曲率によるenergy-causal factor選別）

Cycle 019ではfactor swap後の残差vectorを匿名roleへ昇格したが、value recallは全条件0、41 prototypeの能力増分も0だった。次案の遮蔽・拡張による最小境界は系列Aの予測境界研究と実質重複するため棄却した。

本Cycleでは候補境界そのものを最小化するのではなく、各候補を局所的に削除・短縮・内部遮蔽した際のenergy変化を有限差分で測り、**周囲の小摂動すべてでenergyが増える候補だけを安定basin seed**として残せるか検証した。これは単なるHopfield近傍検索ではなく、入力ごとに生成した候補集合上で局所energy曲率と固定点安定性を計測する。

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 主失敗 | Eで棄却・分離した方向 |
|---|---|---|---|---|
| A | surprise位相同期cell | candidate recall部分回復 | 選択精度0.105未満 | 境界生成・active queryは扱わない |
| B | 置換閉包program非終端 | 既知精度0.7889 | 未知形式0、絶対MDL悪化 | grammar・圧縮は扱わない |
| C | 介入footprint hyperedge | alternate 0.1991 | 実行可能transportほぼ0 | world operationは扱わない |
| D | endpoint別slow memory | 干渉後recall 0.5 | 主要splitでnode形成0 | 長期memoryは扱わない |
| **E** | **局所energy曲率・basin安定性でfactor候補を選別** | 今回検証 | value候補と意味role | 系列固有 |

## 先行研究との位置づけ

- Equilibrium Propagation Without Limitsはfinite nudgeでも局所energy差から正確なcreditを得られる理論を示す。
- Equilibrium Propagation for Dissipative Dynamicsは減衰動力学でも局所学習則を導出する。
- Attractor Modelsは固定点収束と動的反復深度を大規模言語・推論へ適用する。

ただし、いずれも状態変数・候補表現・backboneが既にある。本Cycleは、生の日本語から生成したraw候補のどれが安定basinを持つかという上流問題を扱う。

## 実験条件

- 学習例: 48
- seed: 1 / 7 / 19
- test: 12例 / split / seed
- split: seen / unseen paraphrase / nested / subject omission / paragraph / plan change / counterfactual
- factor候補: object/value各最大8、pair最大48
- 最大sweep: 4
- ablation:
  1. 一次energyのみ
  2. 局所曲率加点
  3. 局所曲率 + null
- hidden object/valueは評価器のみで使用

## 最大48例・3 seed平均

| 条件 | Object recall | Value recall | Pair recall | Curvature精度/誤確定 | Curvature+Null精度/null |
|---|---:|---:|---:|---:|---:|
| seen | 1.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/0.0000 |
| unseen | 0.0556 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/0.1111 |
| nested | 0.1111 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| omission | 0.0556 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/0.2500 |
| paragraph | 0.0278 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| plan | 1.0000 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |
| counterfactual | 0.0556 | 0.0000 | 0.0000 | 0.0000/1.0000 | 0.0000/1.0000 |

## 判定

**中核仮説は強く反証。**

### 1. 曲率の能力増分は0

一次energy方式と曲率方式は全splitでaccuracy 0、pair recall 0、ほぼ全件誤確定だった。局所basin安定性は正しいfactor classを一件も追加分割していない。

### 2. Value recallが全条件0

seen・planではobject recall 1.0だが、value recallは全条件0。曲率計測以前に、正しい最小value spanが候補集合へ入っていない。

### 3. 安定basinは意味roleではない

114個の曲率prototypeが形成されたが、これはsurface候補を短縮・遮蔽した際の数値energy変化patternであり、object・value・scope・goal・constraintを表現しない。junk候補でも局所的に鋭いbasinを持ち得る。

### 4. Nullは限定的な安全停止

Nested・paragraph・plan・counterfactualではnull率1.0となり誤確定を0へ抑えた。一方seenではnull率0のまま全件誤確定しており、absolute energy校正が不十分。

### 5. 曲率計算は5ms目標を悪化

一次energyのseen推論は1.108ms、曲率方式は8.876ms。能力増分0のまま約8倍へ悪化した。

## 停止条件・失敗分類

- 収束: active集合不変、または最大4 sweep
- 局所最適: junk候補が鋭いbasinへ収束
- 候補崩壊: 正しいvalue/pairが候補集合外
- 曲率崩壊: basin sharpnessが意味roleと無関係
- Null安全停止: absolute energyまたはmargin不足
- 発散: 今回なし

## 資源量

- model: 3728 bytes
- prototype: 114
- training: 0.1381 sec
- inference: seen 8.876ms / paragraph 9.174ms
- mean sweep: 2.00
- active states: seen 1.00
- Peak RSS: 110880 KiB（Python runtime込み）
- complexity: proposal `O(L²)`, curvature `O(HF)`, relaxation `O(SH)`, `H<=48,S<=4`

1GB未満は達成。曲率方式は5msを超え、弱いスマートフォン実機も未検証。

## 系列E固有の進展

> **固定点の鋭さ・局所曲率は、候補が安定であることは示しても、その候補が意味的に正しいことを示さない。候補集合外のroleは曲率では生成できない。**

## 他系列へ返す知見

- A: predictive cellの局所安定性を選択scoreへ使ってもcandidate recallは増えない。
- B: derivation graphの安定固定点と意味nonterminalを区別する必要がある。
- C: effect hyperedgeのbasin sharpnessは実行可能transportの代替にならない。
- D: slow edgeの安定性だけでなくendpointのopen-set recallを独立評価する。

## 次の仮説

**Bifurcation-Guided Open-Set Factor Birth from Basin-Splitting Residuals**  
（basin分岐残差からのopen-set factor birth）

次は既存候補の曲率rankingだけを行わない。

1. null basinと既存candidate basinの間で、nudge強度を連続的に変える
2. 固定点が分裂・消滅する文字位置をbifurcation責任として記録
3. 単一位置ではなく、before/after/futureで同時に分岐する最小区間だけ新factor候補化
4. value recallを独立主指標化
5. 候補birth後にのみ局所曲率とfactor swapを適用
6. nullを常時保持
7. sparse Hessian-vector近似で全摂動列挙を避ける

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
