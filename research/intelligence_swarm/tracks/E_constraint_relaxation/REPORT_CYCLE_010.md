# 系列E Cycle 010 研究報告

## 仮説

**Edge-Intervention Jacobian Factors with Sparse Causal Credit Routing**  
（edge介入Jacobian factorと疎な因果credit routing）

Cycle 009では候補graph全体のoutcome vectorが異なっても、その差を生じさせたtarget・value・scope・revision edgeへ局所creditを帰属できず、全件margin 0だった。

本Cycleでは各候補graphのedgeを一つずつ削除相当・反転・再束縛し、6種のoutcome（final、inverse、非対象保存、first-command除去、last-command除去、future recall）の有限差分を局所Jacobianとしてfactor化した。

## 先行研究整理

- Equilibrium Propagationのfinite-nudge拡張は、局所energy derivative差が正確なgradient estimatorになり得ることを示す。ただし、局所状態とenergy項が意味差を表現できることが前提である。  
  https://arxiv.org/abs/2511.22024
- 2025年のcontext-factorized neuromodulation研究は、文脈因子がplasticityを局所gateすることでtargeted online credit assignmentを可能にする。  
  https://openreview.net/forum?id=S9Y89poypx
- local causal discovery研究は、全graphを復元せずtarget周辺の局所構造だけで必要な因果関係を同定できる条件を扱う。  
  https://openreview.net/forum?id=TcMKrmLJCL
- sparse latent structureによるdynamic computation graphは、少数の潜在構造のみを活性化することで計算を抑える。  
  https://arxiv.org/abs/1809.00653

## 他4系列との重複表

| 系列 | 最新中心機構 | 成功・失敗 | 未解決点 | E候補との判定 |
|---|---|---|---|---|
| A | scope原因を持つ予測状態fork | 多時間尺度prototype複製は全条件でstaticを下回った | scope edge別error routing | 外部証拠意味の研究は重複のため棄却 |
| B | cross-episode置換監査 | 既知精度維持でprogram数約半減、未知形式は全0 | role境界・open encoder | program proposalは重複のため棄却 |
| C | 順序依存mechanism automaton | order CF 0.6333、軽量化。ただしcommand cluster崩壊 | context-gated edge separation | world mechanism生成は重複のため棄却 |
| D | boundary surprise + replay | 干渉最新値0.3333、event F1崩壊 | retrieval Jacobian boundary credit | 長期memory edgeは重複のため棄却 |
| E | 候補生成後のedge単独介入と局所energy | 本Cycle | edge creditがselectionへ追加価値を持つか | 系列固有 |

継承した知見:
- A: 保存場所やconfidenceだけでなく、原因edgeへ誤差を帰属する必要がある。
- B: 候補は別identity/valueへ再実行可能である必要がある。
- C: transition前状態や順序を変える有限差分が必要である。
- D: future recall差もedge outcomeに含める必要がある。

## 既存方式との差

Hopfield型連想記憶は保存patternへの類似度で状態を収束させる。本方式は保存pattern想起ではなく、候補graphの各edgeへ介入した場合のworld outcome有限差分を局所factorとして扱う。

通常のfeed-forward分類器とも異なり、複数候補を同時保持し、energy最小クラスだけをevent-drivenに残す。学習済み巨大parameterは使わない。

ただし、本実装は引用区間を候補spanとして使う制御probeであり、生の任意日本語からのproposal原理ではない。

## 実装

Graph edge:
- target binding
- value binding
- command scope
- revision application

Outcome:
1. final state
2. inverse restoration
3. non-target preservation
4. remove-first-command result
5. remove-last-command result
6. future recall

比較:
- `final`: 最終状態だけ
- `outcome`: graph全体の6 outcome
- `jacobian`: 6 outcome + edge単独介入Jacobian

候補をobservable signatureで商空間化し、同じ仮説を重複保持しない。

### 停止条件

- active hypothesis classが前sweepと同一
- active classが1
- 最大4 sweep

### 反証分類

- 局所最適: 誤仮説へ正marginで収束
- 発散: 4 sweepでもactive setが変化
- 候補崩壊: 正答candidate recall 0
- 平坦化: 最良・次点energy同率
- 因果同値: outcomeとJacobianが同じ候補を同一仮説へ商空間化

## 実験条件

- 各split例数: 60 / 180 / 540
- seed: 1 / 7 / 19
- split:
  - quoted seen
  - revision
  - nested proxy
  - counterfactual proxy
  - unmarked Japanese
- 最大候補: 32
- 最大edge: 4
- outcome: 6
- 最大sweep: 4

## 最大540例・3 seed平均

| split | final accuracy | outcome accuracy | Jacobian accuracy | Jacobian candidate recall |
|---|---:|---:|---:|---:|
| seen | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| revision | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| nested proxy | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| counterfactual proxy | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| unmarked Japanese | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Jacobian方式:
- seen: 0.1307 ms/query
- revision: 0.4410 ms/query
- mean sweeps: 1.00
- active hypothesis classes: 1.00
- revision hypothesis classes before relaxation: 24.00
- model bytes: 103
- Peak RSS: 397,376 KiB（Python runtime込み）
- 推定計算量: proposal `O(L²)`、Jacobian `O(E×O)`、relaxation `O(S×H×E×O)`。本実験 `E=4,O=6,H<=32,S<=4`

## 判定

**edge interventionによる局所factor化の必要性は確認できたが、本CycleのJacobian仮説は追加価値を示せず、中核仮説は反証。**

### 限定的に支持された部分

最終状態だけではseen/nested/counterfactualで誤った局所最適へ収束した。一方、複数の実行outcomeを使うと、引用付き制御入力では候補を1 classへ縮約し、1 sweepで正しく選択できた。

よって、最終状態だけよりinverse・non-target・command removal・future recallを含む非同型outcomeがfactor十分性を改善する、というCycle 009由来の部分原理は再確認された。

### Jacobian固有の改善は0

`outcome` と `jacobian` は全accuracyで完全に同一だった。Jacobianは推論時間をseenで約4.0倍、revisionで約7.2倍へ増やしたが、candidate selectionを改善しなかった。

理由は、この制御graphでは6 outcome自体が既に候補を十分分離しており、edge sensitivityを追加しても新しい識別情報がなかったためである。

### 生の自由日本語proposalは完全失敗

引用記号を外したsplitではcandidate recall 0、accuracy 0、abstention 1.0。対象・値・scope候補を自律生成していない。

### nested・counterfactualはproxy

高得点はgraph evaluatorが提供した制御介入probe上の結果であり、自然な入れ子日本語や反実仮想文を理解した証拠ではない。

### 局所学習は未成立

Jacobianをenergy factorとして用いたが、free/perturbed phaseからweight自体を継続学習していない。平衡伝播の学習成功を示すものではない。

## 系列E固有の進展

必要条件を五段階へ更新する。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. **Factor minimality / incremental information**
5. Attractor relaxation and local learning

Cycle 009では3が未成立だった。本Cycleでは制御入力で3を人工的に成立させたが、Jacobianがwhole-outcome factorへ追加する情報が0だったため4で失敗した。

> 局所factorは細かければよいのではない。既存factorでは区別できない候補だけを新たに分離する、増分情報を持つ必要がある。

## 他系列へ返す新知見

- A: edge-specific error routingは、whole prediction vectorで既に分離できない場合だけ価値がある。増分情報を測定すべき。
- B: cross-episode program probeは、追加probeがcandidate precisionを実際に上げるかをablationする。
- C: mechanism edgeの有限差分は、sequence outcomeで未識別なedgeだけへ限定する。
- D: retrieval Jacobianは、既存retrieval outcomeと同じ候補分割しか生まない場合、計算を増やすだけになる。

## 次の仮説

**Adaptive Factor Acquisition by Residual Equivalence Splitting**  
（残差同値類分割による適応factor獲得）

固定で全edge Jacobianを計算しない。

1. 現在のfactor集合で同率になる候補classを検出
2. そのclassだけに対してedge介入を選択
3. 候補classを最も分割する介入factorを追加
4. 分割利得が0なら停止・棄権
5. 使用頻度が低く増分情報0のfactorを忘却

成功条件:
- whole-outcomeでは同率になる新しい制御条件でaccuracyを改善
- 平均edge probe数を全探索4未満へ削減
- unmarked Japanese candidate recallを0から改善
- nested・plan-change・long-distanceの実日本語統合gateを追加
- 32KB未満、5ms/query未満
- 複数seed

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
