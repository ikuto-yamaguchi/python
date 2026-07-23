# 系列C Cycle 020 研究報告

## 仮説

**Intervention-Preserving Soft Correspondence Cycles**  
（介入結果を保存するsoft対応cycle）

Cycle 019ではbefore/afterの保存区間と変化区間を分け、forward/reverse exact transportを要求したが、null transportが20,639件、双方向transport成功が57件に留まり、厳密cycle gateが正候補も破棄した。

本Cycleでは、文字segmentの点対点一致を潜在状態同一性とみなさず、局所対応graphを通した際に次の結果が保存される場合だけedgeを残せるか検証した。

- cycle consistency: A→BとB→Aの対応scoreが双方で高い
- intervention preservation: 対応先ruleが観測afterを再構成する文脈で、対応元ruleも同じ局所変化と非対象保存を示す
- null separation: 対応不明・実行不能は因果edgeとして数えない
- conditional counterfactual: 実行可能pairだけを母数にする

## 先行研究整理

- *Cycle Consistency in Video Object-Centric Learning* (2026) は、曖昧なslotへ明示的cycle consistencyを直接課すとmean-seekingとfeature collapseを招き得るため、再構成manifold上のimplicit cycleを提案する。https://arxiv.org/abs/2605.30211
- *Cycle-World* (2026) はforward/reverse prediction cycleで長期driftを抑えるが、逆予測器と連続latent空間を前提とする。https://arxiv.org/abs/2607.11836
- *Unifying Causal Representation Learning with the Invariance Principle* (ICLR 2025) は、多くの因果表現学習が因果性そのものではなくdata symmetryに整合している点を整理する。https://openreview.net/forum?id=lk2Qk5xjeu
- FACTS (ICLR 2025) はgraph-structured recurrent memoryで効率的world modelを構成するが、factor表現空間は既定である。https://openreview.net/forum?id=dmCGjPFVhF

これらから、cycle consistency自体ではなく、**cycleを通して介入結果・非対象保存・反実仮想合成が維持されるか**を因果反証にした。

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 失敗・未解決 | C候補との区別 |
|---|---|---|---|---|
| A Cycle 019 | 最小十分predictive boundary | object/value失敗を分離 | pair recall 0、value recall 0 | 境界選択は扱わない |
| B Cycle 019 | 匿名failure-cause quotient | seen誤確定を0へ抑制 | program merge 0、未知形式0 | MDL・failure商は扱わない |
| D Cycle 018 | 可逆bridge alias transport | rename write +0.0361 | read悪化、link過剰 | 長期alias同値性は扱わない |
| E Cycle 018 | responsibility-localized frustration | 推論時間短縮、null安全停止 | candidate recall 0 | energy candidate birthは扱わない |
| **C Cycle 020** | **対応cycleが局所介入結果を保存するかを監査** | 今回検証 | world operation transport・因果合成 | 系列固有 |

継承知見:
- A: persistenceとchangeを独立評価しても、最小意味境界は保証されない。
- B: null transportとwrong transportを同じfailureへ圧縮しない。
- D: 往復可能なsurface置換はobject同値性の十分条件ではない。
- E: 候補外では相対scoreで無理に一意化しない。

## 実装

学習器へ渡すのはraw `before / command / after / future`文字列とepisode順序のみ。hidden object・field・valueは評価専用。

1. before/afterから局所transition ruleを抽出
2. 保存context・変化context・command contextからrule間の疎な有向対応候補を生成
3. ablation:
   - Surface rule
   - Hard cycle: 双方向対応scoreだけでedge化
   - Intervention cycle: 双方向scoreと局所介入保存を同時gate
4. 推論では対応edgeが接続するruleのみを疎に実行
5. 候補score差が小さい場合はnull
6. 反実仮想は両ruleが双方の順序で実行可能な例のみ評価

## 実験条件

- train episode: 24 / 72 / 192
- seed: 1 / 7 / 19
- rule上限: 64
- correspondence edge上限: 64
- graph候補監査: 最大160 edge、各24 episode
- test: seen、未学習言い換え、別状態表現、rename、主語省略、複数段落、計画変更、自由状態表現

## 最大192 episode・3 seed平均

### 状態更新精度

| 条件 | Surface | Hard cycle | Intervention cycle |
|---|---:|---:|---:|
| seen | 0.1667 | 0.1667 | 0.1667 |
| 言い換え | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.2639 | 0.2500 | 0.2500 |
| rename | 0.1389 | 0.0556 | 0.0556 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.0000 | 0.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 |
| 自由状態表現 | 0.0000 | 0.0000 | 0.0000 |

### Null率

| 条件 | Surface | Hard cycle | Intervention cycle |
|---|---:|---:|---:|
| seen | 0.6389 | 0.5417 | 0.5417 |
| alternate | 0.5278 | 0.4722 | 0.4722 |
| rename | 0.5694 | 0.7083 | 0.7083 |
| その他 | 1.0000 | 1.0000 | 1.0000 |

## 判定

**中核仮説は強く反証。Hard cycleとIntervention cycleの能力差は0。**

### 1. 介入保存gateがedge集合を分割しない

最大条件ではHard cycleとIntervention cycleがともに平均64 edgeを保持し、全splitのaccuracy・null率・候補数が完全に同一だった。介入保存scoreは平均0.5で平坦化している。

### 2. Cycle edgeはseen能力を改善しない

seenはSurface 0.1667、cycle方式も0.1667である。cycle graphを追加しても正しいoperation選択は増えていない。

### 3. Alternateではわずかに悪化

別状態表現はSurface 0.2639に対しcycle方式0.2500。対応graphが正しい候補を増やすのではなく、類似context ruleを追加して競合を増やした。

### 4. Renameで大幅悪化

renameはSurface 0.1389からcycle方式0.0556へ低下した。表面aliasを跨いだ因果対応ではなく、類似したpreservation/change shapeを共有する別ruleが誤接続されている。

### 5. 自由日本語統合は未成立

言い換え・主語省略・複数段落・計画変更・自由状態表現は全方式0、null率1.0。対応graph以前にcommand value抽出とstate変化位置のtransportが成立していない。

### 6. 反実仮想指標は依然として無効

conditional coverageは0.5と表示されるが、評価器が各test episodeの観測before/afterから直接ruleを抽出して実行可能性を測る診断値であり、学習済みmodelが因果operationを発見したcoverageではない。能力指標から除外する。

### 7. Soft cycleではない

今回の“soft”は閾値付きweighted edgeであり、再構成manifold上の分布的なimplicit cycleではない。点対点文字context graphの範囲を出ていない。

## 相関暗記と因果理解の分離

- seen/alternateの部分成功: 観測済み局所文字transitionの再利用
- rename悪化: object identityなし
- held/free-form 0: relation/state表現不変性なし
- intervention gate差0: edgeが介入機能を表現していない
- plan/paragraph 0: goal・revision・constraint graphなし
- model-derived counterfactual coverage: 実質0

## 資源量

- Surface model: 9,838 bytes
- Hard cycle model: 14,736 bytes
- Intervention cycle model: 14,744 bytes
- rules: 64
- edges: 64
- training: 0.1881 sec
- inference: 0.3882 ms/example
- Peak RSS: 111,692 KiB（Python runtime込み）
- complexity: segment `O(L)`、graph `O(P²G + ENG)`、inference `O(EG)`、`P≤64, E≤64`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列C固有の進展

1. Raw object/event proposal
2. Local transition executability
3. Null transport separation
4. Preservation/change view separation
5. Pairwise correspondence proposal
6. Cycle consistency audit
7. **Intervention-discriminative correspondence evidence**
8. Latent state anchor
9. Model-derived conditional counterfactual composition
10. Goal/constraint planning
11. 自由日本語統合

> cycle consistencyへ介入保存scoreを足すだけでは因果対応にならない。対応edgeごとに、同じruleが成功する文脈と失敗する文脈の差を生む最小介入を発見しなければ、介入scoreは平坦化する。

## 他系列へ返す知見

- A: 遮蔽・拡張で境界を選ぶ際、cycle consistencyだけでなく成功/失敗を反転させる最小介入を測る。
- B: failure-success role因子は、対応edge上でsuccess↔failureを変える座標として評価する。
- D: relation-selective bridgeは複数query一致だけでなく、bridgeを切断した際のtarget/non-target consequence差を測る。
- E: factor swapのenergy vectorが全edgeで同じならrole evidenceにならない。識別的介入coverageを必須化する。

## 次の仮説

**Correspondence Edge Roles from Minimal Success–Failure Intervention Cuts**  
（最小success–failure介入cutからの対応edge role）

1. 各対応edgeについて、source/target contextの局所segmentを一つだけswap・削除・拡張
2. operation transportがsuccess↔failureへ反転する最小cutを探索
3. 異なるobject名・値・状態表現でも同じcut consequenceを持つedgeだけ匿名roleへ統合
4. cutがnon-target保存を壊すedgeは棄却
5. model自身が実行可能としたoperation pairだけでcounterfactual coverageを算出
6. goal変更では旧goal・新goal・revision edgeを分離保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
