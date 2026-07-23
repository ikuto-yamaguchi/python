# 系列C Cycle 027 研究報告

## 仮説

**Multi-Witness State-Variable Fibers from Positive Intervention Alignment**  
（正の介入witness整列からの多証拠state-variable fiber）

Cycle 026では、複数環境で正のsuccessを持つeventだけへ絞ったものの、surface span swapのtarget signatureが一致するevent pairは0、identity classも0だった。

今回はevent間のsignature一致をやめ、同じ局所eventを正しく再構成できた複数episodeをwitness setとして扱った。各witnessについて、生の `command / before / after / future` から次の局所対応edgeを生成した。

- command内の変更値
- before内の旧状態区間
- after内の新状態区間
- future内の新状態再出現
- object候補のbefore/after/future持続
- non-target文字列の保存

各edgeを除去したとき、witness setの80%以上かつ3環境以上が同時に再構成不能になる場合だけ「共同必要edge」とした。同じ必要edge集合とold/new shapeを持つeventをstate-variable fiberへ統合し、fiber成立後だけgraphを形成した。

## 先行研究整理

- Causal Information Bottleneckは、統計的予測だけでなく介入対象へのcausal controlを保持する変数圧縮を提案する。ただし低水準変数と介入targetは定義済み。
  - https://proceedings.mlr.press/v286/simoes25a.html
- Causal Abstraction Inference under Lossy Representationsは、複数の低水準介入が同一高水準介入へ写る場合を扱う projected abstraction を定式化する。ただし低水準causal modelが前提。
  - https://proceedings.mlr.press/v267/xia25a.html
- Causal Representation Learning from General Environmentsは、一般環境下で潜在変数を同定するには十分なmechanism change条件が必要と示す。
  - https://proceedings.mlr.press/v258/ng25a.html
- Intervening to learn and compose causally disentangled representationsは、介入contextを用いた表現分離を示すが、encoderとcontext moduleを持つ。
  - https://proceedings.mlr.press/v323/markham26a.html

今回の対象は、それらより上流にある、生の日本語文字列からstate-variable候補と対応edge自体を形成する問題である。

## 最新PR・他系列との重複表

| 系列 | 最新中心 | 限定成功 | 支配的失敗 | Cで棄却・分離した方向 |
|---|---|---|---|---|
| A | 局所残差routingによるcommitment責任 | 事後逆投影で主語省略候補を部分回復 | prefix除去責任が負、carry 0 | 予測責任routingは扱わない |
| B | role交換consequenceからの実行binding graph | MDL符号長を約79%短縮 | 実行accuracy 0 | 三部binding graph・MDLは扱わない |
| D | memory要素除去によるcredit分離 | 少数slow binding形成 | 誤factorをslow固定 | 長期memory creditは扱わない |
| E | 残差媒介triadic hyperedge | 有限収束・安全停止 | pair edge 0、候補崩壊 | energy synergyは扱わない |
| **C** | **複数success witnessを共同で必要とするtransition対応集合** | 今回検証 | state-variable fiber | 系列固有 |

Bの三部graph、Eのresidual hyperedgeと「第三nodeを介したgraph形成」が重なるため、Cではgraph構造自体を新規性とせず、**正の実行witness集合を同時に壊す必要対応の環境再現性**だけを中心機構とした。

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- 環境: 標準、言い換え、Rename、別状態表現
- test:
  - 既知
  - 未学習言い換え
  - Rename
  - 別状態表現
  - 主語省略
  - 複数段落
  - 計画変更
  - 反実仮想
- event上限: 64
- edge channel: 6
- fiber条件:
  - success witness 3件以上
  - edge除去で80%以上のwitnessが壊れる
  - 3環境以上で再現
  - 同じ必要edge集合を持つevent 2件以上
- ablation:
  1. Surface event
  2. Multi-witness fiber
  3. Fiber graph

学習器はraw日本語と時間順序だけを使用し、hidden object・field・old/new labelは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Surface | Fiber | Fiber graph |
|---|---:|---:|---:|
| 既知 | 0.2917 | 0.2917 | 0.2917 |
| 未学習言い換え | 0.1667 | 0.1667 | 0.1667 |
| Rename | 0.1806 | 0.1806 | 0.1806 |
| 別状態表現 | 0.2014 | 0.2014 | 0.2014 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.2153 | 0.2153 | 0.2153 |
| 計画変更 | 0.1736 | 0.1736 | 0.1736 |
| 反実仮想 | 0.1667 | 0.1667 | 0.1667 |

追加診断:

- Event: 64
- Fiber: 0
- Fiber member: 0
- Graph edge: 0
- Eventあたり平均positive witness: 1.2135
- Sequential coverage: 0.1277
- Sequential conditional accuracy: 0.3286

## 判定

**中核仮説は強く反証された。**

### Positive witnessがeventごとに平均1.21件しかない

Fiber候補には最低3件のpositive witnessを要求したが、64 eventの平均は1.2135件だった。

大半の局所eventは同一surface contextで一度だけ成功し、複数環境へtransportできていない。必要edge集合を比較する前提となるmulti-witness supportが形成されなかった。

### Fiberは全seedで0件

共同必要edge条件を通過し、かつ同じ必要集合を共有するevent pairは一件もなかった。

Cycle 026のidentity class 0という結果を、event間signature比較からwitness集合の共同必要性へ変更しても突破できなかった。

> **複数witnessを共同説明するという評価原理は妥当でも、既存surface eventが複数witnessへ到達できないためfiber形成以前で停止する。**

### 能力増分は全条件0

Surface / Fiber / Fiber graphは全splitでaccuracy・wrong commit・null率・候補数が完全同一だった。

- 主語省略: 0
- 計画変更: 0.1736
- 反実仮想: 0.1667
- sequential coverage: 0.1277

部分得点は既知substring eventの局所再実行であり、fiber・graphの増分ではない。

### 必要edgeは存在論を創発しない

今回のedge channel名は評価・実装上の観測viewであり、object / value / state-variable ontologyを正解として与えてはいない。しかし、各edgeの有無は依然として文字列再出現へ依存する。

共同必要性を課しても、surface eventが複数環境で成功しない限り、潜在state-variable identityへ進めない。

### Counterfactual compositionは未成立

Fiber 0・edge 0のため、counterfactual rolloutはSurface baselineのまま。coverageとconditional accuracyはCycle 026から変化しない。

## 相関暗記と因果理解の反証条件

因果state-variable fiberを支持する最低条件:

1. 3環境以上で各eventに3件以上のpositive witness
2. edge除去が複数witnessのtarget reconstructionだけを同時に壊す
3. non-target damageを増やさない
4. Rename・別状態表現で同一fiberへ再結合
5. Fiber利用によりSurfaceよりexecution accuracyまたはcounterfactual coverageが改善
6. 主語省略・計画変更でobject/goal stateを持続・更新

今回は1から未達で、2〜6もすべて未達。

## 資源量

- Fiber graph model: 9,757 bytes
- Training: 0.011132 sec
- Inference: 0.054753 ms/example
- Peak RSS: 160,140 KiB（Python runtime込み）
- Graph規模:
  - event 64
  - fiber 0
  - edge 0
- 推定計算量:
  - event抽出 `O(NL)`
  - witness audit `O(PN)`
  - edge necessity `O(PNF)`
  - fiber partition `O(P)`
  - graph `O(C²)`
  - inference `O(PL)`
  - `P≤64、F=6`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列C固有の進展

因果world model形成段階:

1. Raw event proposal
2. Local transition extraction
3. success / wrong / null分離
4. symmetric-information replay
5. environment residual identity
6. success-conditioned target identity
7. **multi-witness necessary alignment――今回反証**
8. open-form witness transport
9. state-variable fiber
10. counterfactual composition
11. goal・constraint planning

核心的知見:

> **複数の正の実行witnessを同時に壊す対応集合はstate-variable候補の強い反証原理になり得る。しかし、surface eventが環境を跨いで複数witnessへtransportできない段階では、必要性監査は空になる。次に必要なのはidentity groupingではなく、未知surfaceに対するpositive witness生成そのもの。**

## 他系列へ返す知見

- A: commitment責任は同じ局所残差を複数turnで正に説明できる場合だけstate候補とする。
- B: binding graph triangleには、複数held-out execution witnessを共同で必要とすることを要求する。
- D: memory要素除去creditは単一episodeではなく複数sessionの正答を同時に壊すか測る。
- E: triadic hyperedgeは単一候補energyではなく複数環境の正の実行witnessを共同説明する必要がある。

## 次の仮説

**Positive Witness Birth from Bidirectional Local Alignment Search**  
（双方向局所整列探索によるpositive witness創発）

次は既存eventをwitness集合へtransportするだけにしない。

1. Source episodeのcommand-change-state対応を局所alignment候補化
2. Target episode側でforward alignmentを探索
3. Target→sourceのinverse alignmentも同じ局所区間を復元する場合だけ保持
4. Exact surface context一致を要求せず、保存区間・変化shape・future再現を共同score化
5. Wrong/nullはalignment pruningに使用
6. 新たに生成したpositive witnessが3環境以上で再現した場合だけfiber necessity監査へ進む
7. Held・Rename・別状態表現のpositive witness coverageを主指標化
8. Fiber成立後にのみdirection・counterfactual rolloutを評価

Bの実行binding graphとは異なり、Cは**世界状態遷移を再現するsource-target局所alignmentとpositive intervention witness coverage**を中心にする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
