# 系列B Cycle 012 研究報告

## 仮説

**Relation-Preservation Anti-Unification with Contrastive Multi-Field States**  
（対照的複数field状態によるrelation保存反統一）

Cycle 011では文字span境界を拡張・縮小してもrole境界にならず、candidate recall 0.9037に対してprecision 0.2600、全統合テスト0だった。そこで本Cycleでは、一対象一値の状態を廃止し、同一objectに複数field、別objectにも同型fieldを持たせた。候補programが観測された変更だけでなく、同一objectの非対象fieldと別objectの全fieldを保存する場合のみMDL libraryへ昇格できるか検証した。

## 先行研究整理

- Relational Program Synthesisは、単独入出力ではなく複数program間のrelational specificationを満たす合成を扱い、CEGISとrelational version space learningで探索する。単一episode整合より、複数実行間の関係制約が重要である。https://doi.org/10.1145/3276525
- ExeDecは、最終入出力だけでなくexecution subgoalへ分解して合成することでcompositional generalizationを改善した。実行分解は有効だが、分解変数自体を生の日本語から作る問題は残る。https://openreview.net/forum?id=oTRwljRgiv
- CEGISは反例でversion spaceを縮小するが、反例が候補を意味的に区別できる仕様を持つことが前提である。
- MDLとcompositionalityの関係は、短い記述と構成性を結び付けるが、最短表現が正しいrelation structureであることを保証しない。https://arxiv.org/abs/cs/0001002

## 他系列との重複表

| 系列 | 最新の中心機構 | 成功・失敗 | 未解決点 | B候補との重複判定 |
|---|---|---|---|---|
| A | raw区間候補を未来予測class化し共有probeで分割 | 16候補でprobeを約半減。paraphrase/nested recall 0 | 候補生成・probe program生成 | 外部観測policyは棄却 |
| C | context/state probeでmechanism edgeを分離 | raw fingerprintへ過分裂、seen 0.1444 | relation-selective state variable | 世界モデルとしてのrelation発見はCへ委ねる |
| D | retrieval Jacobianでevent boundaryへcredit | seen F1改善、topic/held precision悪化 | signed interference credit | 長期記憶境界は棄却 |
| E | 残差classだけへadaptive factor取得 | factor評価削減、候補外でも誤収束0.7617 | null hypothesis attractor | energy選択は棄却 |
| B | relation保存制約を満たす可逆programだけを圧縮 | 本Cycleで検証 | open-form encoder | 系列固有 |

他系列から継承した知見:
- A: 候補集合外の正解は候補選択で救えない。
- C: raw context/state fingerprintをrelationとみなすと過分裂する。
- D: 単一targetの改善だけでなく非対象への干渉を負例にする。
- E: 追加probeは候補classを実際に分割する場合だけ取得する。

## 実装

学習器が受け取るのはrawのbefore / command / after文字列のみ。field ID、object ID、value辞書、意味slot、形態素解析、固定ontology、RAG、外部LLMは与えない。評価器だけがhidden field/objectを用いる。

状態には2〜3 objectを含め、各objectは3つの値を同時に持つ。before/afterの句読点区間差から変更区間候補を生成し、commandとの共通spanからentity候補を形成する。

比較方式:
1. `single_change`: 観測afterを再現できれば昇格。
2. `contrastive_no_preservation`: 保存clauseにold/newが現れる曖昧候補を除外。
3. `relation_preservation`: さらに全非対象clauseがbyte単位で保存された候補のみ昇格。

MDLは昇格後のprogram保存長にのみ使用した。

## 実験条件

- train sizes: 32 / 96 / 192
- seeds: 1 / 7 / 19
- 各split: 24例 / seed
- 既知、未知語順、未知述語、入れ子、主語省略、状態表現2種、3 object

## 最大192例・3 seed平均

### 候補品質

| 指標 | 単一変更候補 | 対照候補 |
|---|---:|---:|
| recall | 0.1910 | 0.0903 |
| precision | 0.1495 | 0.1448 |
| 平均候補数 | 1.2760 | 0.6267 |

### 統合テスト

| 条件 | Single change | Contrastive | Relation preservation |
|---|---:|---:|---:|
| 既知 | 0.3750 | 0.3750 | **0.3750** |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知述語 | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.3333 | 0.3333 | 0.3333 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 状態表現1 | 0.0000 | 0.0000 | 0.0000 |
| 状態表現2 | 0.0000 | 0.0000 | 0.0000 |
| 3 object | 0.2917 | 0.2917 | 0.2917 |

## 資源量

- Relation-preservation model: 5469 bytes
- Program数: 9.33
- Raw candidates: 120.33
- Program reads/query: 9.33
- Execution candidates/query: 0.4722
- Seen inference: 0.5469 ms/query
- Peak RSS: 309776 KiB（Python runtime込み）
- 推定計算量: train `O(NL²+C)`、infer `O(PCL³)`、span候補は5/6に制限
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**中核仮説は反証。保存対照は候補数とモデルを減らすが、relation programを形成しなかった。**

### 1. 保存制約の増分情報がゼロ

`contrastive_no_preservation` と `relation_preservation` の全accuracy、program数、モデルサイズが完全に同一だった。観測before/after自体が非対象clauseを保存しているため、単一episode内のexact reconstructionだけで保存条件が自動的に満たされ、追加反例にならなかった。

### 2. 対照化でcandidate recallが悪化

対照候補はprecisionをほぼ改善せず、recallを0.1910から0.0903へ落とした。old/new文字列が別fieldにも現れる場合を機械的に捨てると、正しいrelation候補も失う。

### 3. 既知入力も0.375止まり

複数fieldにしたことで、どのclauseを変更するかというrelation identityは必要になった。しかしcommand templateとclause prefix/suffixの表面一致だけでは、全既知入力を束縛できなかった。

### 4. 未知語順・未知述語・状態表現・主語省略は0

未知語順、未知述語、主語省略、2種の状態言い換えは全て0。入れ子0.3333も学習済み命令文字列を内部に含む場合だけである。

### 5. Relation preservationは意味保存ではない

測定したのはbyte単位の非対象clause保存である。状態表現が変わると同じ意味を保存していても一致しないため、relationの意味的同一性ではない。

## 探索爆発

初版は全substringを再列挙し120秒で完走しなかった。最終版では、学習サイズ・評価数を縮小し、推論時bindingをprefix/suffix直接照合へ変更して完走させた。探索を抑えられたのは原理的なversion-space圧縮ではなく、表面template照合への強い制限による。

## 系列B固有の進展

program inductionに必要な対照を三つへ分離した。

1. **Observational preservation**: 観測afterで非対象文字列が保存される。
2. **Interventional preservation**: programを別field・別objectへ誤適用したとき非対象が壊れる。
3. **Representational preservation**: 状態表現が変わっても同じrelationを保存する。

今回実装したのは1のみで、単一episode exact executionに包含されていた。必要なのは2と3である。

## 他系列へ返す新知見

- A: active probeは観測済み保存の再確認ではなく、候補ごとに異なる誤適用結果を作る必要がある。
- C: relation候補はchanged/preserved文字列ではなく、別fieldへの誤介入で異なる結果を生む必要がある。
- D: replay schemaの保存性はbyte一致ではなく、表現変更後のwrite/read不変性で監査する。
- E: residual splittingには、既存exact reconstructionに包含されないintervention factorだけを追加する。

## 次の仮説

**Adversarial Misapplication Programs with Relation-Contrastive MDL**  
（relation対照MDLを持つ敵対的誤適用program）

次は正しいafterだけを検証しない。各候補programを意図的に、

- 同一objectの別field
- 別objectの同名field
- role反転command
- 別状態表現
- entityを省略した談話更新

へ誤適用し、候補ごとに異なる破壊patternを生成する。正しい候補だけがtarget fieldを変え、他fieldを保存する場合に昇格させる。

最低成功条件:
- seen 0.375を改善
- candidate recall 0.191とprecision 0.150を同時改善
- 未知語順または状態表現を0から改善
- subject omission候補recallを0から改善
- execution candidates 50/query未満
- 32KB未満、5ms/query未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
