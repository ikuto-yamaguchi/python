# 系列E Cycle 021 研究報告

## 仮説
**Bifurcation-Guided Open-Set Factor Birth from Basin-Splitting Residuals**  
（basin分岐残差からのopen-set factor birth）

Cycle 020では既存候補の固定点basin曲率を測ったが、value recallは全条件0であった。今回は候補rankingではなく、null basinからcandidate basinへnudge強度を連続変化させた際に、最良固定点の文字位置が切り替わる分岐点周辺から新しいfactor候補をbirthさせた。

## 他系列との重複表
| 系列 | 最新中心 | 限定信号 | 未解決 | E候補との重複判定 |
|---|---|---|---|---|
| A | 候補不一致からの予測test自己生成 | 候補集合内のactive識別 | open-set候補生成 | query policyは棄却 |
| B | 部分導出準同型 | 既知contextの局所再利用 | context抽象化0 | grammar/MDLは棄却 |
| C | edit対応programによるtransport map | success/wrong/null分離 | transport map未生成 | world operationは棄却 |
| D | value-change同値類memory | endpoint分離で誤読低下 | value class形成 | 長期memoryは棄却 |
| **E** | **null↔candidate固定点分岐からfactor node birth** | 今回検証 | value/open-set factor | 系列固有 |

## 先行研究との位置づけ
Equilibrium Propagationの近年研究は散逸・時間発展系への局所学習拡張を示し、Attractor Modelsは固定点収束と動的計算深度の有効性を示す。ただし、いずれも候補状態や表現器が存在する。本Cycleは、生の日本語で候補node自体を固定点分岐から生成できるかを検証した。

## 実験
- 学習例: 48
- seed: 1 / 7 / 19
- test: 12例 / split / seed
- 条件: seen, unseen paraphrase, nested, subject omission, paragraph, plan revision, counterfactual
- 比較: Base energy / Bifurcation birth / Bifurcation birth + Null
- nudge: 0, 0.1, 0.2, 0.35, 0.5, 0.7, 1.0
- 最大candidate: 48
- 最大反復: 4
- 学習器はraw command/before/after/futureのみを使用。hidden object/valueは評価専用。

## 3 seed平均
| 条件 | Base object/value/pair recall | Bifurcation object/value/pair recall | Base精度 | Bifurcation精度 |
|---|---:|---:|---:|---:|
| 既知 | 1.0000/0.1944/0.1944 | 1.0000/0/0 | 0.1944 | 0 |
| 言い換え | 0.4722/0.1944/0.0833 | 0/0/0 | 0.0833 | 0 |
| 入れ子 | 0.1111/0/0 | 0/0/0 | 0 | 0 |
| 主語省略 | 0.0556/0/0 | 0/0/0 | 0 | 0 |
| 複数段落 | 0.0556/0/0 | 0/0/0 | 0 | 0 |
| 計画変更 | 1.0000/0/0 | 1.0000/0/0 | 0 | 0 |
| 反実仮想 | 0.0556/0/0 | 0/0/0 | 0 | 0 |

## 判定
**中核仮説は強く反証。**

### 分岐birthがvalue recallを消失させた
Base方式はseen/unseenでvalue recall 0.1944を持ったが、Bifurcation方式は全splitで0。Null→candidateの最良固定点が切り替わる位置は、意味的value境界ではなかった。

### Open-set factor birthではなく候補削減
平均candidate数はseenで37.11から23.25に減少したが、正答pair recallも0.1944から0へ低下した。探索効率化ではなく正候補の切り捨てである。

### 分岐prototypeはsurface failure pattern
平均15.67個のprototypeを形成したが、能力増分は0。Nudgeに対するargmin位置の切替は、object/value/scope/goal roleではなく表面energy landscapeの不連続を記録しただけである。

### Nullは安全停止のみ
Bifurcation+Nullは全splitでwrong commit 0、null率1.0。junk attractor防止には有効だが、全面棄権である。

## 単なるHopfield/既存NNとの差
固定pattern recallではなく、null basinからcandidate basinへのnudge homotopyを使い、分岐位置からnode候補を新生する点が異なる。しかし今回の実装は文字列上の有限候補energyであり、正式な連続力学・平衡伝播・学習された意味energyではない。

## 資源量
- Bifurcation model: 1,047 bytes
- Prototype: 15.67
- Training: 0.0644 sec
- Inference: seen 1.356 ms / unseen 1.714 ms / paragraph 2.490 ms
- 平均sweep: 2.00
- Peak RSS: 111,628 KiB（Python runtime込み）
- 推定計算量: proposal O(L²), homotopy O(JH), local birth O(JR²), relaxation O(SH), J=7, H≤48, S≤4

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列E固有の進展
> 固定点分岐はenergy landscapeの候補切替を検出するが、その切替位置が意味roleである保証はない。Null basinとの分岐だけではopen-set factor birthの方向を決められず、観測制約ごとの独立な分岐を一致させる必要がある。

## 他系列へ返す知見
- A: candidate disagreementやquery outcomeの切替点だけでは意味境界にならない。
- B: unknown transportが解消される分岐と、単なるargmin切替を分離する。
- C: transport map生成では、map候補の固定点分岐が実行可能transitionと一致するか監査する。
- D: value classをslow固定する前に、複数の独立制約で同じfactor境界が再現するか確認する。

## 次の仮説
**Constraint-Wise Bifurcation Intersection for Open-Set Factor Birth**
（制約別分岐交差によるopen-set factor birth）

1. after再構成、future整合、non-target保存、execution可否を別energy landscapeとして保持
2. 各制約でnull→candidate分岐位置を独立計測
3. 2つ以上の制約で同じ最小区間が分岐する場合だけfactor birth
4. Object/value/scope候補を独立集合化
5. Candidate birth後のみfactor swapと反復緩和
6. Nullを常時保持
7. Value recallとopen-set pair recallを主指標化

## 最終状態
- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
