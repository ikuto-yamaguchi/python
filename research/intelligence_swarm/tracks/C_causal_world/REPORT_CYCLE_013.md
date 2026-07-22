# 系列C Cycle 013 研究報告

## 仮説

**Identity-Conservation Causal Edge Discovery by Object-Swap Surgery**  
（オブジェクト交換surgeryによる同一性保存因果edge発見）

前Cycleの `Relation-Selective State Variable Discovery from Preservation Contrasts` では、changed-chunk方式が全文prototypeより軽量・高速だった一方、preservationあり/なしの差が完全に0で、9 bucketはrelationではなく句読点・prefixの表面classだった。

当初予定していた clause-lattice misapplication は、系列B Cycle 013の次仮説 `Clause-Lattice Misapplication Execution with Relation Quotient Induction` と中心機構・反証条件・期待能力が重なるため棄却した。本Cycleではprogram inductionではなく、**world state上の対象同一性が、relation edgeの誤束縛時に保存されるか**へ焦点を移した。

## 先行研究整理

- Li et al. (AISTATS 2025) は、任意subset interventionから識別可能なcausal abstractionの粒度が介入集合に依存することを示す。単一のchanged/preserved観測だけで真のlatent variableまで識別できる保証はない。https://proceedings.mlr.press/v258/li25g.html
- Ng et al. (AISTATS 2025) は、一般environmentで潜在DAGを識別するにはcausal mechanismの十分な変化条件が必要とする。表面fingerprintの多様性だけではmechanism variationにならない。https://proceedings.mlr.press/v258/ng25a.html
- Causal-JEPA (2026) はobject-level maskingをcounterfactual-like latent interventionとして用い、interaction reasoningのshortcutを抑える。ただし強いobject representationを前提とし、生の日本語からobject/relationを形成する問題は未解決。https://arxiv.org/abs/2602.11389
- AAAI 2026のSTICAはobject token単位のworld dynamicsとcause-effect relationを扱うが、Transformer tokenizationとobject slotが既に存在する。https://doi.org/10.1609/aaai.v40i29.39642

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との判断 |
|---|---|---|---|---|
| A | learned probe program + null state | out-set誤確定を拒否 | 既知も98.3%拒否、paraphrase/nested recall 0 | 外部観測policyなので棄却 |
| B | adversarial misapplication risk | raw候補を削減 | accuracy不変、実際のmisapplication未実行 | clause/program帰納は重複のため棄却 |
| D | signed retrieval-interference credit | event F1、干渉後latest改善 | 長gap過分割、semantic write/read未形成 | memory境界なので棄却 |
| E | null attractor + absolute residual | out-set誤確定を約半減 | 依然50.6%誤確定、候補空間供給 | energy校正なので棄却 |
| **C** | **object clauseの交換・逆操作・再適用でidentity-local edgeを監査** | 今回検証 | raw object/relation proposal | 系列固有 |

継承知見:

- A: 候補削減量と意味的生存率を分離する。
- B: surface risk proxyではなく実際のworld破壊差を測る。
- D: target gainだけでなく非対象への干渉を負例にする。
- E: 追加factorが候補classを本当に分割したかablationする。

## 実装

学習入力はraw `before / command / after` 日本語文字列だけ。hidden object ID、field ID、value辞書、形態素解析、固定ontology、RAG、外部LLMは学習器へ渡していない。

1. 状態を句点・改行でobject clause候補へ分割する。
2. before/afterで変化したclauseを抽出する。
3. prefix / changed span / suffix の局所edge候補を生成する。
4. 各edgeをtarget clauseと別object clauseの位置交換、forward後のinverse復元、同一edgeの二回適用へ実際にcounterfactual適用する。
5. object交換後に別clauseへ誤適用されず、inverseで元clauseを復元し、再適用がidempotentなedgeだけを保持する。

比較方式:

- `SurfaceChunk`: command類似のchanged clauseを全文置換
- `EdgeNoSurgery`: 局所edge化のみ
- `EdgeSurgery`: object-swap / inverse / idempotence監査あり

## 実験条件

- train size: 48 / 192 / 512
- seed: 1 / 7 / 19
- 2〜3 objects × 3 fields
- 各split 120例 / seed
- seen、rename / word order、alternate state representation、held command、subject omission、multi paragraph、plan change、order counterfactual

## 最大512例・3 seed平均

| split | Surface | Edge no surgery | Edge surgery |
|---|---:|---:|---:|
| seen | 0.0222 | 0.0083 | **0.0111** |
| rename/order | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.0167 | 0.0056 | 0.0056 |
| held command | 0.0056 | 0.0083 | 0.0056 |
| subject omission | 0.0000 | 0.0056 | 0.0056 |
| multi paragraph | 0.0167 | 0.0083 | **0.0222** |
| plan change | 0.0056 | 0.0083 | 0.0056 |
| order counterfactual | 0.0111 | 0.0111 | **0.0167** |

### 資源

- Edge surgery model: **32,582 bytes**
- Edge no surgery model: 32,540 bytes
- Surface model: 267,433 bytes
- retained edges: **64**
- raw edge candidates: **512**
- surgery rejected: **175.7**
- seen inference: **0.2356 ms/query**
- order inference: **0.2500 ms/query**
- Peak RSS: **116,080 KiB**（Python runtime込み）
- estimated complexity: train `O(N C²)`, infer `O(E C G)`, `E<=64`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**中核仮説は強く反証。**

### object-swap surgeryの増分能力はほぼ0

surgeryは平均175.7候補を追加棄却したが、seen accuracyは0.0083から0.0111で、実用的改善にならない。全条件が0〜0.0222の範囲に留まる。

### clause位置交換はobject identity介入ではない

句点単位のclauseを交換しても、内部にはobject identity nodeがない。prefix/suffixとchanged spanが一致するかを検査しただけで、別objectへのrelation edge再束縛を表現していない。

### inverse/idempotenceもrelationを識別しない

old→new文字置換は多くの誤候補でもinverse復元・二回適用不変を満たす。これらは編集演算の代数的性質であり、どのworld relationを変更したかの証拠ではない。

### 表面edgeへ過圧縮

512 raw候補を64 edgeへ制限したが、relation quotientではなく似たprefix/suffix edit familyである。alternate representation、held command、rename/orderに転移しない。

### object permanence・計画・照応は未成立

subject omission、plan change、multi paragraph、order counterfactualはほぼ0。対象永続性、段落間event、goal撤回、因果順序を内部状態として形成していない。

## 相関暗記と因果理解の反証

- seen: 0.0111
- rename/order: 0.0000
- alternate state: 0.0056
- order counterfactual: 0.0167

既知表面すら低性能で、未知表現・順序変更へ一貫した転移がない。因果方向・object-local relation edgeの形成証拠はない。

## 系列C固有の進展

relation surgeryを以下へ分解できた。

1. **Text-clause surgery**: clause位置交換・文字置換。今回実装、意味増分ほぼ0。
2. **Object identity proposal**: 発話横断で同じ対象を表すnode形成。未成立。
3. **Relation-bearing edge proposal**: object nodeに接続する状態変数edge形成。未成立。
4. **Cross-object counterfactual rebinding**: edgeだけを別objectへ再束縛し非対象を保存。未成立。
5. **Event/order/goal dynamics**: 操作順序・撤回・計画を再帰実行。未成立。

> **文字clauseを交換してもobject surgeryにはならない。object identityとrelation-bearing edgeを先に形成しない限り、counterfactual misapplicationは表面編集監査に退化する。**

## 他系列へ返す新知見

- A: probe候補が文字spanである限り、実行失敗はobject/relationの意味誤差へ帰属できない。
- B: clause-lattice misapplicationは、clause位置交換だけではrelation quotientを作らない。identity nodeの形成を独立ゲートにすべき。
- D: replayやwrite/read schemaでobject identityをsurface clauseと同一視すると、言い換え・主語省略で更新先が消える。
- E: object-swap factorはidentity-bearing edgeが存在しない候補classを分割しないため、取得前に増分情報を監査すべき。

## 次の仮説

**Temporal Co-Reference Object Nodes from Intervention Persistence Signatures**  
（介入持続signatureからの時系列照応object node形成）

次はrelation edgeより先にobject nodeを形成する。生の複数文で、同じ候補spanが、複数時点で状態を保持し、操作後も非対象属性を保存し、主語省略後の更新で一貫した最新状態を持ち、identity名のrename後も同じ介入trajectoryを生成し、別objectへの操作で変化しない場合だけ同一object nodeへ統合する。

最低成功条件:

- seen 0.0111を改善
- subject omission 0.0056を実質改善
- rename/order 0を改善
- object node数を実object数に近づける
- identity rename ablationとの差を明確化
- 32KB未満、5ms/query未満、複数seed

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
