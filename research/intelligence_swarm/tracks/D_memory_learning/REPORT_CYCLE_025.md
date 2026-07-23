# 系列D Cycle 025 研究報告

## 仮説

**Factorized Endpoint Evidence with Fast-to-Slow Reconsolidation Ladders**  
（因子別endpoint証拠とfast→slow再固定化ladder）

Cycle 024ではquery→state / state→queryのendpoint全体へ完全一致を要求し、wrong readは0になったがstable endpointも0、read accuracyも0へ退化した。

今回はendpointを一括判定せず、生の日本語から形成したobject・relation・value候補ごとに、

- forward reconstruction credit
- reverse reconstruction credit
- wrong credit
- session support
- fast / slow状態
- local decay
- obsolete value flag

を独立管理した。三因子が揃ったbindingだけをslowへ昇格し、更新時には同じobject×relation候補の旧value bindingだけを選択的に減衰させた。

## 先行研究整理

- Osirisは現在・過去・cross-task consolidationの目的を分離し、共有埋め込みだけで安定性と可塑性を両立させる設計の限界を示す。
  - https://proceedings.mlr.press/v274/zhang25a.html
- task-relevant readout rangeとnull spaceを分離する研究は、すべての表現変化が忘却へ直結するわけではなく、どの経路へ変化を流すかが重要であることを示す。
  - https://proceedings.mlr.press/v274/anthes25a.html
- Regenerative Regularizationは最近の損失に寄与しないparameterを初期状態へ戻し、可塑性を維持する。
  - https://proceedings.mlr.press/v274/kumar25a.html
- 2026年のFAASTはラベル例を一回でclosed-form fast weightsへ変換し、低更新コストの高速適応を示す。ただし入力表現と教師ラベルは与えられる。
  - https://arxiv.org/abs/2605.04651
- Replayが常に忘却を減らすとは限らないことも2026年のCoLLAs proceedingsで明示されており、再生量ではなく統合対象の正しさが重要である。
  - https://proceedings.mlr.press/v330/

これらは既存表現上の安定性・可塑性制御であり、生の自由日本語からendpoint identity自体を作る今回の上流問題とは異なる。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 支配的失敗 | Dとの分離 |
|---|---|---|---|---|
| A | commitment-specific predictive responsibility | 主語省略候補carry | event gateが全面終了へ退化 | active inference・談話予測は扱わない |
| B | executable binding graph | MDL短縮 | 可逆surface交換でも実行accuracy 0 | program帰納・MDLは扱わない |
| C | multi-witness state-variable fiber | Null collapse除去 | success-conditioned identity class 0 | 因果world modelは扱わない |
| E | constraint-edge birth before commutator | 収束・null安全停止 | commutator prototype 0 | energy dynamicsは扱わない |
| **D** | **因子別fast/slow endpoint creditと選択的忘却** | 今回検証 | endpoint credit calibration | 系列固有 |

中心機構がBの三部binding graph、Cのstate-variable fiber、Eのconstraint edgeと重なる案は棄却した。Dでは長期read/write addressの局所可塑性と再固定化だけを扱う。

## 実験条件

- seed: 1 / 7 / 19
- 学習event: 24 / 72 / 144
- test: 最大36例 / split / seed
- object上限: 64
- relation上限: 64
- value上限: 32
- binding上限: 96
- 比較:
  1. Flat endpoint memory
  2. Factorized fast→slow ladder
  3. Slow-binding-only
- 自由日本語:
  - 既知
  - 未学習言い換え
  - Rename
  - 別状態表現
  - 主語省略
  - 複数段落
  - 未知domain
- 追加:
  - 一回提示学習
  - 長期干渉
  - obsolete valueの選択的忘却

Hidden object・field・value labelは評価器だけで使用した。

## 最大144 event・3 seed平均

| 条件 | Flat read / wrong | Ladder read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.3148 / 0.5833 | 0.1759 / 0.7593 | 0.0185 / 0.3148 |
| 未学習言い換え | 0.3148 / 0.5741 | 0.1759 / 0.7593 | 0.0185 / 0.3148 |
| Rename | 0.2685 / 0.6111 | 0.1852 / 0.7407 | 0.0185 / 0.3148 |
| 別状態表現 | 0.2778 / 0.6204 | 0.1852 / 0.8148 | 0.0185 / 0.3148 |
| 主語省略 | 0.3611 / 0.4074 | 0.1852 / 0.7130 | 0.0185 / 0.3148 |
| 複数段落 | 0.2963 / 0.5648 | 0.1759 / 0.7963 | 0.0185 / 0.3148 |
| 未知domain | 0.3426 / 0.5556 | 0.1759 / 0.7593 | 0.0185 / 0.3148 |

Write accuracyは全条件・全方式で0.2593、wrong writeは0.7407だった。

追加診断:

- Slow object: 19
- Slow relation: 15.33
- Slow value: 12
- Slow binding: 2.33
- Obsolete binding: 58
- Update量: 3,954
- Local decay: 305.33
- One-shot read: Flat 1.0 / Ladder 1.0 / Slow 0
- One-shot write: 全方式0.6667
- 干渉後recall: Flat 0.2778 / Ladder 0.1389 / Slow 0.0833
- Selective forgetting後latest recall: Flat 0.6667 / Ladder 0.3333 / Slow 0

## 判定

**中核仮説は強く反証された。**

### 因子単位slow昇格は形成された

完全一致gateだったCycle 024ではstable endpointが0だった。

今回は平均で、

- slow object 19
- slow relation 15.33
- slow value 12
- slow binding 2.33

が形成された。fast→slow ladderは全面棄権を避け、局所factorへsupportを蓄積できた。

ただし、形成数は能力の証拠ではない。

### Ladder readはFlatより悪化

既知readは、

**0.3148 → 0.1759**

へ低下し、wrong readは、

**0.5833 → 0.7593**

へ増えた。

forward/reverse creditを因子別に分けても、object・relation候補が同じsemantic endpointを表していないため、誤ったfactor supportがread scoreを増幅した。

### Slow-onlyは安全側だが能力崩壊

Slow-onlyでは既知wrong readが0.3148へ減った一方、read accuracyは0.0185まで低下した。

2.33件のslow bindingは形成されたが、正しいlatest-value addressを十分に含まない。厳しいgateによる全面棄権から、少数の誤った固定memoryへ失敗形態が変わっただけである。

### 干渉耐性は悪化

干渉後latest-value recallは、

- Flat: 0.2778
- Ladder: 0.1389
- Slow: 0.0833

だった。

slow factorを形成しても、干渉耐性は増えず、誤ったcreditが固定化された。

### 選択的忘却も逆効果

obsolete bindingは平均17件識別されたが、latest recallは、

- Flat: 0.6667
- Ladder: 0.3333
- Slow: 0

へ悪化した。

同じobject×relation候補としてまとめたaddress自体が誤っており、旧valueだけでなく正しい経路も減衰している。

### One-shotはfast/slow分離を示すが一般化ではない

Flat / Ladderはone-shot read 1.0、Slowは0だった。fast endpointの即時形成とslow gateの違いは実装できた。

しかし同一episode直後の再読であり、未知表現転移やsemantic memoryの証拠から除外する。

### 支配的失敗は破滅的忘却ではない

支配的失敗は、良い記憶が後で消えることではない。

- Flatの初期wrong readが高い
- factor ladderでwrong readがさらに増える
- write wrongが0.7407
- obsolete判定がlatest recallを悪化させる

したがって主問題は、

> **object・relation・value因子の初期identityとcredit assignmentが誤っていること**

である。

## RAG・検索との差

保存文書や近傍vectorを返すのではない。

1. 生のquery/stateからobject・relation・value候補を形成
2. 因子別fast weightを局所更新
3. object×relation×value bindingを推論状態へ注入
4. session supportによりslow化
5. obsolete valueだけ局所減衰

を行う。

ただし現状は文字gramとsubstring由来の疎transducerであり、semantic associative memoryには未到達。

## 資源量

- Ladder model: 20,235 bytes
- 学習時間: 0.054390 sec
- 推論時間: 1.360679 ms / read-or-write
- Peak RSS: 160,092 KiB（Python runtime込み）
- 記憶容量:
  - object 64
  - relation 64
  - value 12
  - binding 96
  - slow binding 2.33
- 更新量: 3,954
- local decay: 305.33
- 推定計算量:
  - Candidate生成 `O(NL²)`
  - Factor更新 `O(NF)`
  - Sparse binding `O(N)`
  - Read `O(BL)`
  - Write `O(VL)`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 破滅的忘却と表面暗記の反証条件

破滅的忘却の支持条件:

1. 干渉前に高いread/write accuracy
2. 同一endpointの干渉前後比較
3. slow化がFlatよりlatest recallを維持
4. obsolete valueだけ低下し、最新valueは維持
5. Alias・別状態表現でも同じendpointへ戻る

今回は1〜5を満たさないため、破滅的忘却克服の証拠なし。

表面暗記の証拠:

- substring/gram candidate
- one-shot同一episode再読
- 全splitで同じwrite accuracy
- factor support増加でも未知表現能力増分なし
- selective forgettingで正しい経路も消える

## 系列D固有の進展

Memory形成段階を更新する。

1. Episodic raw trace
2. Write/read経路分離
3. Bidirectional endpoint gate
4. **Factorized fast→slow ladder――形成可能だが能力仮説は反証**
5. Credit isolation by counterfactual memory removal
6. Calibrated selective forgetting
7. Sleep consolidation
8. Episodic-to-semantic integration

核心的知見:

> **完全一致gateを因子別ladderへ緩和すればslow factorは形成できる。しかし、因子identityが誤ったままsupportを蓄積すると、fast memoryの誤りをslow memoryへ固定し、干渉耐性と選択的忘却を同時に悪化させる。**

## 他系列へ返す知見

- A: commitment responsibilityを蓄積する前に、cellを除去したときの実際の予測損失増分を測る必要がある。
- B: binding graph edgeのsupport回数だけでlibrary化せず、edge除去でexecutionが壊れるかを監査する。
- C: multi-witness fiberも共通supportだけでは誤identityを固定する。witness除去による因果必要性が必要。
- E: constraint edge weightを再発回数だけで強化すると誤attractorを固定する。edge除去energy差が必要。

## 次の仮説

**Counterfactual Credit Isolation by Memory-Element Removal before Reconsolidation**  
（再固定化前のmemory要素除去による反実仮想credit分離）

次はsupport回数をslow creditにしない。

1. Object・relation・value factorを一つずつmemoryから除去
2. Held-out read/write損失が増えるfactorだけpositive credit
3. Loss不変factorはsurface redundancyとして減衰
4. Wrong readを増やすfactorはnegative credit
5. 三因子の除去効果が独立に正の場合だけbinding化
6. Fast endpointはone-shotで即時利用
7. 複数sessionでcounterfactual creditが再現した場合だけslow化
8. Obsolete value除去でlatest recallが維持されるかを主評価
9. Top-k indexで全binding走査を削減

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
