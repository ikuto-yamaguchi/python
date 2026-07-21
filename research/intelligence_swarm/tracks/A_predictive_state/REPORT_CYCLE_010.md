# 系列A Cycle 010 研究報告

## 仮説

**Scope-Fork Predictive Programs with Counterfactual Evidence Scheduling**  
（scope分岐予測プログラムと反実仮想証拠スケジューリング）

Cycle 009ではglobal / speaker / episode / fastへsurface prototypeを複製しても、引用・否定・訂正scopeを構造化できず、全条件でstatic方式を下回った。

本Cycleでは保存箱を増やす方向を棄却し、生の発話から複数のscope候補を同時生成し、各候補を実行した際の汎用成功・失敗だけで状態を再帰更新する最小probeを検証した。候補値そのものは後続証拠へ含めない。

## 先行研究整理

- Prediction-Oriented Bayesian Active Learningは、parameter不確実性ではなく将来予測空間の情報利得を取得基準にする。候補仮説空間が正しいことは前提であり、本Cycleではcandidate recallを別指標にした。  
  https://proceedings.mlr.press/v206/bickfordsmith23a.html
- MacKayのactive data selectionは、期待情報量に基づく観測選択を定式化する一方、仮説空間が正しいという仮定を主要弱点として明記している。  
  https://authors.library.caltech.edu/records/efefp-2j353
- discrete-state active inferenceは知覚・行動・計画・学習を生成モデル上で統合するが、生の日本語から状態候補を作る原理は別途必要である。  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7732703/
- predictive informationの制約から言語的systematicityが形成され得るという2025年研究は、未来予測可能性が構造形成の信号になり得ることを示す。  
  https://www.nature.com/articles/s41562-025-02336-w

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B Cycle 010 | cross-episode置換監査 | 既知性能維持でprogram数・サイズを約半減 | 未知語順・述語・scopeは0 | program誘導は重複のため棄却 |
| C Cycle 010 | 順序依存mechanism edge automaton | order counterfactual 0.6333、2.3KB | command/context意味分離が弱い | world transition生成は重複のため棄却 |
| D Cycle 010 | boundary-surprise fast stateとreplay | 干渉後最新値0→0.3333 | event F1 0.0216、長gap 0 | 長期memory境界は重複のため棄却 |
| E Cycle 010 | edge-intervention Jacobian | whole outcomeで引用付き候補を分離 | Jacobian増分0、無標識candidate recall 0 | edge credit学習は重複のため棄却 |
| A Cycle 010 | raw scope候補と能動実行証拠による再帰修復 | 本Cycleで検証 | open-set candidate generation | 系列固有 |

継承知見:

- B: 内部で短い・実行可能でも、別形式へのcandidate recallがなければ一般化しない。
- C: 状態遷移は順序で異なる未来を生成する必要がある。
- D: retrieval改善と正しいevent構造を分離評価する。
- E: 追加factorは候補classを新たに分割する増分情報を持つ場合だけ有効。

## 実装

学習器が受け取るのは、生の日本語文字列、句点・改行・日本語括弧の位置、候補を実行した後のgeneric success/failureのみである。

使用していないもの:

- 肯定/否定辞書
- entity/value辞書
- 形態素解析
- semantic slot
- 固定ontology
- Transformer / RNN
- RAG / 外部LLM
- 正答値を含む後続証拠

候補は括弧delimiterから再帰的に抽出し、位置、深さ、長さ、反復回数だけを局所featureとする。pairwise prediction errorで6重みを更新する。

比較方式:

1. **Immediate structural ranking**: 現在の重みでscope候補を即時確定。
2. **Active executable repair**: 上位候補を順に実行し、generic success/failureで候補集合を更新。最大4 probe。

## 実験条件

- train sizes: 64 / 256 / 1024
- seeds: 1 / 7 / 19
- splitあたり160件
- literal / quote / negation / correction
- nested / multi-paragraph / plan change
- ambiguous two-candidate
- 未学習scope reversal 2種
- 引用符なし自由日本語proxy 240件

## 最大1024例・3 seed平均

| split | candidate recall | immediate | active | wrong commit | probes |
|---|---:|---:|---:|---:|---:|
| literal | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| quote | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| nested | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| ambiguous | 1.0000 | 0.5375 | 1.0000 | 0.4625 | 1.4625 |
| held scope | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 2.0000 |
| held retraction | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 2.0000 |
| unmarked Japanese | 0.0000 | 0.0000 | - | - | - |

## 資源

- model: 139 bytes
- training: 0.013861 sec
- marked推論: 約0.02–0.04 ms/example
- 平均候補: 2–4
- active probe: 1–2
- Peak RSS: 390,788 KiB（Python runtime込み）
- complexity: proposal `O(L)`, rank `O(HF)`, active `O(min(H,4))`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**能動実行による下流修復は限定支持。中核の自由日本語構造創発仮説は反証。**

### 支持された部分

候補集合へ正答scopeが含まれる場合、未学習scope reversalではimmediate accuracy 0、wrong commit 1.0だったが、generic action success/failureを用いるactive repairは平均2 probeで1.0へ修復した。

曖昧二候補でもimmediate約0.54からactive 1.0へ改善した。

> 正しいscope候補が既に存在する場合、候補を実行して得る予測誤差は、表面順位の誤りを可逆修復する有効な観測になる。

### 反証1: 即時理解は完全失敗

held scope/retractionのimmediateは0。学習した構造重みは末尾・短いspanを好むだけで、引用・否定・撤回・報告の意味を理解していない。

active 1.0は最初に誤実行し、失敗を見て別候補へ切り替えた結果であり、言語理解ではない。

### 反証2: 無標識日本語candidate recall 0

引用符を除くと候補生成自体が0。対象、変数、関係、操作、目的、制約、因果候補を生の任意日本語から作れていない。

### 反証3: probeが候補単位で非効率

候補ごとの逐次実行なので、一般には最悪`H`回必要。候補が大きい自由日本語では探索爆発する。予測空間を半分に分ける観測生成や、候補classの共有probeは未成立。

### 反証4: 制御データ依存

nested、paragraph、planの1.0は正答が最終quoted spanである生成規則に依存する。自然な入れ子・計画変更・談話理解の証拠ではない。

### 反証5: 世界候補はscope値だけ

形成した候補はquoted stringのどれを現在値にするかだけ。object identity、relation、operation、goal、constraint、causal edgeは創発していない。

## 系列A固有の進展

予測状態研究を以下へ分離できた。

1. **Raw candidate proposal**
2. **Structural prior ranking**
3. **Counterfactual executable observation**
4. **Recursive reversible repair**
5. **Semantic abstraction / open-set transfer**

本Cycleでは、delimiter付き制御入力に限って1、3、4が成立した。2は未学習scopeで破綻し、5は未成立。

重要な結論:

> 予測誤差は、候補生成後の修復信号にはなる。しかし、正しい候補が生成されない入力を救えず、候補を逐次試すだけでは知能原理にならない。

## 他系列へ返す新知見

- B: program proposal recallがある場合、cross-episode実行失敗をactive repair signalに使える。ただし候補逐次probeは探索爆発する。
- C: mechanism edge候補を実行して分ける際、既知sequence結果ではなく候補classを最大分割する観測を選ぶべき。
- D: event-boundary候補はfuture retrievalを一件ずつ試すのではなく、複数候補を共有して分けるprobeが必要。
- E: residual equivalence classだけへ追加factorを取得する案は、系列Aのactive observation schedulingと接続可能。ただしEは内部factor、Aは外部観測選択として分離する。

## 次の仮説

**Predictive-Equivalence Scope Classes with Shared Active Probes**  
（予測同値scope classと共有能動probe）

次は候補を一つずつ試さない。

- 候補が生成する次発話
- action outcome
- correction発生
- speaker transfer
- future recall

の予測vectorが同じ候補を同一classへまとめ、classを最大分割する観測だけを取得する。

同時にdelimiter依存を外すため、文字区間境界を局所surprisal・再現性・別発話への置換可能性で生成する。

必須成功条件:

- held immediate 0を改善
- unmarked candidate recall 0を改善
- active probe回数を`O(log H)`へ近づける
- 誤実行を伴わない観測を優先
- model 32KB未満
- 5ms/query未満
- 複数seed
- 自由日本語統合ゲートを別評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
