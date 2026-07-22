# 系列C Cycle 012 研究報告

## 仮説

**Relation-Selective State Variable Discovery from Preservation Contrasts**  
（保存対照からのrelation選択的状態変数発見）

Cycle 011ではcontext/state全文fingerprintでmechanism edgeを分離しようとして、本来3 operationに対して16 command edge・約153 gated edgeへ過分裂した。本Cycleでは全文keyを廃止し、同一objectの複数field状態について、介入で変化した文字区間と同時に保存された区間の対照から再利用可能な状態変数候補を形成できるかを検証した。

## 先行研究整理

- CausalTripletはactionable counterfactualとOOD interventionで、distributed表現よりobject-centric/disentangled表現が有利だが、latent構造同定自体は依然困難と報告する。
- 部分観測CRLではinstance-dependentな観測欠落下でも、疎性制約がlatent回復の識別条件になり得る。
- multi-node interventionの識別結果は、介入のcoverage/diversityと、介入traceに対する疎性が重要であることを示す。
- 2025年のgeneral-environment CRLも、環境変化が十分に多様であることを識別条件に置く。

参照:
- https://proceedings.mlr.press/v213/liu23a.html
- https://proceedings.mlr.press/v235/xu24ac.html
- https://proceedings.mlr.press/v236/bing24a.html
- https://proceedings.mlr.press/v258/ng25a.html

## 他系列との重複表

| 系列 | 現在の中心 | 成功・失敗 | 未解決点 | C候補との判定 |
|---|---|---|---|---|
| A | shared active probeでpredictive classを分割 | 大候補でprobe半減、paraphrase/nested recall 0 | null校正、probe自律生成 | 外部観測policyは重複のため棄却 |
| B | multi-field relation-preservation anti-unification | 既知0.375、保存制約の増分情報0 | adversarial misapplication | program library/MDLは重複のため棄却 |
| D | retrieval-Jacobian boundary credit | seen F1改善、held/topic precision悪化 | signed interference credit | episodic境界・記憶統合は重複のため棄却 |
| E | adaptive residual factor acquisition | factor評価半減、候補外で誤収束0.7617 | null attractor | energy/factor取得は重複のため棄却 |
| C | changed/preserved区間から状態変数を形成 | 本Cycleで検証 | relation-level因果変数 | 系列固有 |

継承知見:
- A: 候補を分けるだけでなく候補集合外を検知する必要がある。
- B: 観測済み保存はexact reconstructionに包含される可能性がある。
- D: 単一目的のgainは誤統合を生むため負の干渉costが必要。
- E: 追加factorは残差classを実際に分割する増分情報を持つ必要がある。

## 実装

比較方式:

1. `Whole`: command文字類似でbefore/after全文episodeを選び、その編集を適用。
2. `RelationContrast`: before/afterを句読点・改行で区切り、変化chunk、保存chunk、commandとの共通spanを複数episodeで束ねる。多様なchanged chunkと保存chunkを持つbucketだけをprogramとして残す。
3. `NoPreservation`: 保存条件を外すablation。

学習器へfield ID、object ID、value辞書、形態素解析、固定ontology、RAG、外部LLMは与えていない。

## 実験

- 学習量: 48 / 192 / 512
- seed: 1 / 7 / 19
- 3 field: 場所・状態・担当（名称はgenerator評価用でlearner非公開）
- split: 既知、rename/語順、別状態表現、未知command、主語省略、複数段落、計画変更

## 最大512例・3 seed平均

| 条件 | Whole | Relation contrast | No preservation |
|---|---:|---:|---:|
| 既知 | 0.2028 | **0.5500** | 0.5500 |
| rename/語順 | 0.2306 | **0.4750** | 0.4750 |
| 別状態表現 | 0.2500 | **0.4556** | 0.4556 |
| 未知command | 0.2500 | **0.4389** | 0.4389 |
| 主語省略 | 0.1639 | **0.4667** | 0.4667 |
| 複数段落 | 0.2444 | **0.4389** | 0.4389 |
| 計画変更 | 0.1444 | **0.4889** | 0.4889 |

## 資源量

- contrast model: 97,524 bytes
- whole model: 265,853 bytes
- program bucket: 9
- raw proposal: 1,049
- seen inference: 0.9697 ms/query
- multi-paragraph inference: 1.5097 ms/query
- Peak RSS: 314,544 KiB（Python runtime込み）
- 推定計算量: train `O(NL²)`、infer `O(PG+PL)`、span/program上限あり
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**変化chunkのepisode横断束ねには限定的な信号があったが、中核仮説は反証。**

### 限定的結果

whole episode prototypeより、contrast方式は全splitで精度と速度を改善し、モデルも約63%削減した。状態全文ではなく少数のchanged-chunk programへ縮約する方向は、軽量な編集再利用部品としては有効。

### 決定的反証1: 保存対照の増分情報が0

`RelationContrast` と `NoPreservation` の全精度・program数・モデルサイズが完全に同一だった。保存chunk条件は、今回もchanged-chunkのcross-episode多様性に包含され、relation classを追加分割しなかった。

### 決定的反証2: 状態変数ではなく表面chunk

既知精度は0.55、別状態表現0.4556、未知command0.4389に留まる。形成した9 bucketは場所・状態・担当の3 relationへ対応せず、句読点位置とprefix断片の組合せである。

### 決定的反証3: 計画・談話得点は理解の証拠でない

主語省略0.4667、複数段落0.4389、計画変更0.4889は、command内に学習済み表面断片が残るため得られる。照応先、撤回scope、goal stateを内部graphへ形成していない。

### 決定的反証4: 反実仮想・因果方向未成立

異なるfieldへ誤適用した結果、inverse、非対象object保存、operation順序相互作用をprogram selectionへ直接使っていない。相関的な文字編集をrelation-level mechanismと区別できない。

## 系列C固有の進展

状態変数発見を次へ分解した。

1. changed-region proposal — 限定成立
2. observational preservation — 増分情報0
3. interventional relation contrast — 未成立
4. representational invariance — 未成立
5. object/relation binding・order interaction — 未成立
6. goal/constraint planning — 未成立

重要な結論:

> 変化区間と保存区間を同時に観測するだけではrelationは創発しない。誤ったrelation候補を別field・別object・別表現へ意図的に介入し、候補ごとに異なる破壊patternを作る必要がある。

## 他系列へ返す新知見

- A: 保存確認を共有probeにしても候補classを分割しない。誤適用で異なる未来を生むprobeが必要。
- B: relation-preservationの増分情報0というCycle 012結果をCでも再現。次はobservationalでなくinterventional preservationを共同検証すべき。
- D: replay schemaをchanged/preserved byte chunkで統合すると表現別surface memoryになる。
- E: preservation factorは残差classを分割せず、factor取得候補から除外すべき。

## 次の仮説

**Adversarial Relation Surgery with Object-Persistent Counterfactuals**  
（オブジェクト永続反実仮想を用いる敵対的relation surgery）

候補relation edgeを意図的に、同一objectの別field、別objectの同型field、逆操作、順序交換、別状態表現へ再束縛する。正しいedgeだけがtarget relationを変え、非対象relation・object identityを保存し、inverseで復元する場合に昇格する。

最低成功条件:
- 既知0.55、別状態0.4556、未知command0.4389を同時改善
- preservation ablationとの差を明確化
- relation nodeを3〜8へ抑制
- order counterfactualとplan changeを漏洩なしで改善
- 32KB未満、5ms/query未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
