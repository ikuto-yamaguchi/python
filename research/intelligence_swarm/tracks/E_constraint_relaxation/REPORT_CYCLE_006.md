# 系列E Cycle 006 — Role-Structured Conditional Attractor Graphs

## 結論

Cycle 005では、operationとepisode bindingを分離しても64候補が実質同型で、全splitがmargin 0の全面棄権へ収束した。本サイクルでは、同じoperation候補から **action** と **no-op** の異なる実行branchを生成し、入力文脈との局所整合性energyで競合させた。

最大384例・3 seed平均では、単一action graphのbaselineが通常0.5389、blocked 0.0だったのに対し、role-structured attractorは通常0.9972、action 1.0、blocked 0.9889、rename 0.9944を得た。平均marginは通常0.3523、blocked 0.3334で、Cycle 005のmargin 0から脱出した。

ただし、完全未学習命令構文、入れ子、複数段落、計画変更はすべて0だった。未学習contextも0.1556に留まり、67.2%を棄権した。モデルサイズは約140.6KBで、表面context prototypeを多数保持している。したがって、**非同型branch graphはenergy緩和の必要条件として支持されるが、open-set日本語意味構造の創発仮説は反証**である。

## 他系列との重複表

| 系列 | 最新の中心機構 | 本サイクルとの境界 | 継承した知見 |
|---|---|---|---|
| A | 承認・否定による短期予測状態修復 | 外部質問・feedbackではなく内部候補graphの収束 | 候補entropyを減らすには候補ごとに異なる証拠が必要 |
| B | role-factored multi-view MDL encoder | encoder/圧縮ではなく、生成済みrole/branch候補のenergy選択 | span差ではなくargument roleと実行効果が異なる候補が必要 |
| C | context-conditioned counterfactual event algebra | 因果eventやcondition quotientの誘導ではなく、action/no-op候補間のattractor landscape | contextをscalar罰則ではなく別branchへ内部化する |
| D | predictive retrieval gain grouping | 長期記憶・episode groupingではなく即時推論 | 異なる未来を生成しない仮説は保持する価値がない |

候補として検討した「context表現を介入効果で商空間化する」は系列Cと重複するため棄却した。「未知predicateを実行効果でprimitiveへ統合する」は系列Bと重複するため棄却した。本系列では、候補graphが既に与えられた後に、非同型branch構造がenergy landscapeを形成できるかだけを中心にした。

## 先行研究との位置づけ

Energy-based modelやfactor graph最適化は、複数の局所factorを一つのenergyへ統合して状態を選ぶ枠組みを提供する。Equilibrium系や局所学習系では、収束点・局所更新・反復計算の効率が重要になる。一方、制約ソルバ研究でも、探索戦略や候補表現が弱ければenergy最小化だけでは正解へ到達しない。

本実験は既存手法の再現ではなく、**候補graphの構造多様性がない場合にenergyが平坦化する**という過去反証を、action/no-opの実行branch分離で直接検証する最小probeである。

参考:

- Amizadeh et al., PDP: A General Neural Framework for Learning Constraint Satisfaction Solvers, 2019, https://arxiv.org/abs/1903.01969
- Sodhi et al., LEO: Learning Energy-based Models in Factor Graph Optimization, CoRL/PMLR 2022, https://proceedings.mlr.press/v164/sodhi22a.html
- Høier et al., Dual Propagation, ICML/PMLR 2023, https://proceedings.mlr.press/v202/hoier23a.html
- Scellier, A fast algorithm to simulate nonlinear resistive networks, ICML/PMLR 2024, https://proceedings.mlr.press/v235/scellier24a.html

## 仮説

**Role-Structured Conditional Attractor Graphs**

> episode-local identity/valueをoperationから分離した上で、候補graph自身がaction/no-opという異なる実行結果を持ち、文脈factorが各branchへ個別に接続されれば、同型候補のflat energyを解消し、通常入力とblocked入力を正のmarginで選別できる。

反証条件:

1. 通常・rename・blockedがCycle 005同様に全面棄権する。
2. action/no-op候補を分けてもmarginが0のまま。
3. baselineより能力を改善せず、反復・候補数だけ増える。
4. 未学習構文・文脈・入れ子・複数段落・計画変更が0のまま。
5. 保存量がepisode数にほぼ比例する。

## 実装

`role_structured_attractor_cycle6.py`

学習器へentity/value一覧、意味slot名、mode名、形態素解析器、RAG、外部LLMは与えていない。学習時のbefore/command/after文字列から次を誘導した。

1. 三viewで共有されるepisode identity候補
2. before/after差分によるold/new候補
3. identity/valueを匿名化したcommand operation view
4. 状態文末の残差区間を、名前のないcondition候補として匿名化
5. 同じoperationに対するaction観測とno-op観測

推論時は、各operationについて次の2 graphを生成する。

- action branch: new valueを状態へ適用
- no-op branch: before状態を保持

各branchのenergyは、入力condition残差と、そのbranchを生んだ過去condition群との文字2/3-gram類似度から計算する。最大8 sweepの座標更新を行い、最良・次点marginが0.025未満なら棄権する。

比較:

- `flat`: commandが適用可能なら常にaction branchを実行
- `role_attractor`: action/no-opを別graphとして保持し、branch固有energyで緩和

停止条件:

- 最良candidate indexが前sweepと同一
- 最大8 sweep

## 実験条件

- train sizes: 48 / 192 / 384
- seeds: 1 / 7 / 19
- 各split: 120件 / seed
- 通常混合、actionのみ、blockedのみ、entity/value全面rename
- 完全未学習命令
- 完全未学習context表現
- 入れ子指示
- 複数段落
- 計画変更・訂正
- model bytes、Peak RSS、学習・推論時間、sweep、active candidates、margin

再現:

```bash
python research/intelligence_swarm/tracks/E_constraint_relaxation/role_structured_attractor_cycle6.py \
  > research/intelligence_swarm/tracks/E_constraint_relaxation/results_cycle_006.json
```

## 384例・3 seed平均

| 指標 | flat action | role attractor |
|---|---:|---:|
| 通常混合 | 0.5389 | **0.9972** |
| actionのみ | 1.0000 | 1.0000 |
| blocked/no-opのみ | 0.0000 | **0.9889** |
| entity/value rename | 0.5333 | **0.9944** |
| 完全未学習命令 | 0.0000 | 0.0000 |
| 未学習context | 0.5167 | **0.1556** |
| 入れ子 | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 |
| 通常margin | 0.0000 | **0.3523** |
| blocked margin | 0.0000 | **0.3334** |
| active candidates | 1 | 2 |
| 平均sweep（通常） | 1.0 | 1.4583 |
| モデルサイズ | **979 B** | 140,641 B |
| 学習時間 | **0.01866 s** | 0.08568 s |
| 推論時間（通常） | **0.1291 ms** | 0.4758 ms |
| operation views | 9 | 9 |

Peak RSSは約304,380 KiB。Python runtime全体を含み、方式固有値でも弱いスマートフォン実機値でもない。

## 限定的に支持された部分

Cycle 005では候補64個が実質同型で、local/branch方式とも全splitがmargin 0・棄権1.0だった。本サイクルでは候補数を2へ減らした一方、各候補が異なる出力を生成するようにした。

その結果:

- 通常: 0 → 0.9972相当の選択能力
- blocked: 0 → 0.9889
- margin: 0 → 約0.35
- 全面棄権: 解消

したがって次の部分原理は支持される。

> **energy緩和の有効性を決めるのは候補数ではなく、候補graphが異なる役割・branch・実行結果を持つことである。**

反復回数も平均1.46程度であり、候補が少数なら動的計算深度は小さい。

## 決定的な反証

### 1. 未学習命令は0

command skeletonが一致しなければ候補graph自体を生成できない。energyは正しい候補を選べても、未知表現から候補を提案できない。

### 2. 未学習contextは悪化

flat baselineの偶然的action正答0.5167に対し、role attractorは0.1556、棄権0.6722だった。`扉が閉じている`と`出入口を通れない`を同じconditionとして理解していない。

### 3. 入れ子・複数段落・計画変更は0

文全体が既知command skeletonと一致しないため、candidate recallが0になる。長距離依存、scope、訂正、目的変更をfactor graph化できていない。

### 4. context prototype保存が大きい

モデルは約140.6KBでflatの約144倍。action/no-op contextをepisode単位に近い形で保存しており、軽量なcondition primitiveを形成していない。

### 5. condition境界の提案が人工的

状態文末の文をcondition候補としている。意味名は与えていないが、任意の自由日本語からcondition scopeを生成したわけではない。

### 6. 自由日本語統合能力は0

自由対話、読解、数学・科学推論、自然な反実仮想、目的形成、長期対話、継続学習は未達である。

## 系列E固有の新知見

候補生成とenergy緩和を明確に分離できた。

1. **非同型候補graphが存在する場合**
   - 少数候補・短い反復で正のmarginを作れる。
   - action/no-opのような下流branch選択は成立し得る。

2. **候補graph proposalが失敗する場合**
   - energyを改善しても未知構文・未知condition・入れ子・計画変更は解けない。
   - 全面棄権または候補なしになる。

したがって、系列Eの次の中心課題は重み学習でも反復回数でもなく、**入力ごとにscope・role・condition・branchが異なる非同型factor graphを生成する提案原理**である。

## 他系列へ返す知見

- A: 質問対象は表面候補ではなく、異なるbranch結果を生成するfactor graph差分にする。
- B: primitive encoderの成功条件へ、生成した候補がaction/no-op等の異なるworld結果を持つことを加える。
- C: condition quotientが成立すれば、E側のbranch energyは少数候補で有効に働く可能性がある。
- D: memory graph候補は、後続想起だけでなく異なる実行branchを生成するものだけ保持する。

## 次の仮説

**Scope-Induced Factor Graph Proposal with Contrastive Attractor Selection**

次は状態文末をconditionと決め打ちしない。入力中の複数区間について、次が異なるfactor graph候補を生成する。

1. entity/value境界
2. predicate primitive
3. condition scope
4. conditionが修飾するoperation
5. action/no-op/blocked branch
6. 訂正前・訂正後の目的状態
7. 段落間の共参照edge

候補は可逆再構成、介入効果、別identity再束縛、逆操作、非対象非干渉、後続予測で緩和する。

必須成功条件:

- 未学習命令を0から改善
- 未学習contextを0.1556より改善
- 入れ子・複数段落・計画変更のいずれかを0から改善
- 通常・rename・blockedの高精度と正marginを維持
- model bytesを140KBから大幅削減
- episode数に近いprototype増加を止める

## 最終判定

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: 未達
