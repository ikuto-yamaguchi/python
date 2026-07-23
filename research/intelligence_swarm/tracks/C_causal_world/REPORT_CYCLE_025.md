# 系列C Cycle 025 研究報告

## 仮説

**Environment-Paired Mechanism Residual Partitions for Event Identity**  
（環境対mechanism残差分割によるevent identity）

Cycle 024ではforward/reverseの情報条件を揃えて偽の方向信号を減らしたが、残る非対称性はevent identityとstate-variable bindingの欠如に支配されていた。今回は方向推定を後段へ送り、局所eventをobject表記・語順・state表現が異なる複数環境へ再実行し、環境別のsuccess／wrong／null／non-target damage／future整合をmechanism残差signatureとした。

## 先行研究整理

- Ng et al. (AISTATS 2025) はgeneral environmentsから潜在DAGを同定する条件を示すが、十分なmechanism change条件を必要とする。https://proceedings.mlr.press/v258/ng25a.html
- Gamella et al. (ICML 2025) は、単純な実機光学系でも代表的CRL手法が真の因果因子を回収できないことを報告した。https://proceedings.mlr.press/v267/gamella25a.html
- Li et al. (AISTATS 2025) は、未知介入から識別できる因果抽象の粒度が介入集合に制約されることを示す。https://proceedings.mlr.press/v258/li25g.html

環境不変性だけでなく、どのmechanismが変わり、何が保存されたかを正の実行証拠で反証する必要がある。

## 他系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した方向 |
|---|---|---|
| A | Event-gated prospective stateとcommitment終了 | 談話carry・予測gate |
| B | Role-exchange permutationによるbinding seed | 置換検定・MDL |
| D | 双方向query-state再構成によるendpoint identity | 長期memory endpoint |
| E | 独立介入pairの交換子によるfactor role | energy応答・交換子 |
| **C** | **実行可能state transitionの環境別mechanism残差分割** | 今回の固有対象 |

## 実験条件

- seed: 1 / 7 / 19
- 学習episode: 48 / 144 / 288
- 学習環境: 標準、言い換え、Rename、別状態表現
- test: 既知、未学習言い換え、Rename、別状態表現、主語省略、複数段落、計画変更、反実仮想
- event上限: 64
- identity class: signatureを0.25刻みで分割し、平均stability 0.65以上
- graph edge上限: 96
- ablation: Surface / Mechanism identity / Identity graph
- hidden object・field・old/new labelは評価器だけで使用

## 最大288例・3 seed平均

| 条件 | Surface | Identity | Identity graph |
|---|---:|---:|---:|
| 既知 | 0.1667 | 0.1667 | 0.1667 |
| 未学習言い換え | 0.1667 | 0.1667 | 0.1667 |
| Rename | 0.1806 | 0.1806 | 0.1806 |
| 別状態表現 | 0.2014 | 0.2014 | 0.2014 |
| 主語省略 | 0 | 0 | 0 |
| 複数段落 | 0.2153 | 0.2153 | 0.2153 |
| 計画変更 | 0.1736 | 0.1736 | 0.1736 |
| 反実仮想 | 0.1667 | 0.1667 | 0.1667 |

診断値:

- event: 64
- identity class: 1
- identity member: 64
- graph edge: 0
- mean stability: 0.9845
- sequential counterfactual coverage: 0.1277
- conditional accuracy: 0.3286

## 判定

**中核仮説は強く反証された。**

### 64 eventが単一identity classへ崩壊

64 eventすべてが1 classへ統合された。高いstabilityは意味mechanismの安定性ではなく、大半のeventが各環境で似た `success≈小 / wrong≈0 / null≈大` signatureを持ったためである。

> 同じように実行不能であることを、同じevent mechanismであると誤認した。

### 能力増分は全split 0

Surface / Identity / Graphはaccuracy・wrong commit・null率・候補数が完全同一だった。正しいevent選択、未知surface transport、object permanence、planningを一件も改善していない。

### Graph edgeは0

全eventが同一classへ潰れ、class間transition graphは形成されなかった。粗すぎるidentity統合は、因果関係を記述するnode差そのものを消す。

### 主語省略・計画・反実仮想

主語省略は全方式0、null率1.0。計画変更と反実仮想の部分得点はbaselineと同一であり、旧goal・最終goal・未実行worldを分離した能力ではない。

### Counterfactual composition

Coverage 0.1277、conditional accuracy 0.3286でCycle 024から改善なし。identity classによる因果合成能力は0だった。

## 反証条件

因果event identityの支持には最低でも次が必要だった。

1. 異環境で2件以上のsuccess support
2. wrong・damageが低い
3. null率の一致だけでは統合しない
4. object/value/relationの単独変更で対応成分だけ変わる
5. held/Rename/alternate accuracyがbaselineを上回る
6. counterfactual coverageまたはaccuracyが増える

今回は1・4・5・6を満たさない。

## 資源量

- model: 22,328 bytes
- training: 0.010837 sec
- inference: 0.042719 ms/example
- Peak RSS: 160,196 KiB（Python runtime込み）
- graph: event 64 / class 1 / edge 0
- 計算量: event抽出 `O(NL)`、環境replay `O(PNE)`、partition `O(P)`、graph `O(C²)`、推論 `O(PL)`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

> 環境間で残差signatureが安定しても、null transportに支配されていればevent identityではない。identity統合には複数環境での正の実行証拠と、介入対象別に分解された効果が必要である。

## 他系列へ返す知見

- A: 同じfailure/null profileのcommitment候補を同一談話状態へ統合しない。
- B: 同じnoexec patternをrole-exchange可能性とみなさず、正の導出supportを必須化する。
- D: 双方向再構成が双方nullになるendpointをidentityとしてslow固定しない。
- E: 同じ高energy/null attractorへ落ちる因子を交換可能roleとして統合しない。

## 次の仮説

**Success-Conditioned Event Identity from Factorized Intervention Target Signatures**  
（因子別介入target signatureによるsuccess条件付きevent identity）

1. 複数環境で各2回以上successしたeventだけ対象
2. object候補・value候補・state context候補を一つずつ交換
3. target reconstruction、non-target damage、future consistencyを別成分化
4. 交換因子に対応する成分だけ変わるeventをidentity class化
5. wrong/nullは棄却証拠に使うが類似性scoreには使わない
6. identity成立後だけdirectionとgraphを評価
7. held・Rename・alternateでclass precision/recallとoperation accuracyを主評価
8. 実行可能classだけでcounterfactual rollout

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
