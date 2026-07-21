# 系列D Cycle 006 — Predictive Retrieval Gain Grouping with Negative Evidence

## 結論

中核仮説は反証された。後続応答の予測利得と他episode質問への負の証拠をgrouping採択条件へ加えても、生の時系列日本語から対象・関係・値・episode identityを安定して形成できなかった。

最大540更新・3 seed平均で、予測利得方式は直接質問0.03125、代名詞・表記揺れ・長い未学習質問・distractor質問・新規identity一回提示がすべて0だった。学習量増加に伴い直接質問も48更新0.1996から540更新0.03125へ悪化した。

一方、表面観測を全件走査するbaselineに対し、低速schema数5、モデル約5.45KB、推論0.170ms/query、読み出し5まで圧縮できた。しかしこれは能力を保持した圧縮ではないため採用しない。

## 他系列との重複表

| 系列 | 最新の中心機構 | 重複回避・継承 |
|---|---|---|
| A | 承認・否定による短期予測状態修復 | 対話feedbackではなく、長期記憶へ入る前のepisode groupingを検証。候補entropy不足の知見を、grouping候補の識別不足として継承。 |
| B | role-factored multi-view MDL encoder | role/primitive誘導そのものは行わず、候補groupingが後続想起を改善するかで監査。未知predicate 0の反証を継承。 |
| C | context-conditioned event branch | 因果branchではなく事実記憶のepisode identity。surface context prototypeがopen-set転移しない知見を継承。 |
| E | 非同型role/world候補が必要 | 異なる未来想起を生成しないgrouping候補は別仮説でない、という選別条件を採用。 |

## 仮説

`Predictive Retrieval Gain Grouping with Negative Evidence`

時間近接・文字重なりだけでgroupingせず、候補groupingが次を満たす場合だけ低速write/read schemaへ統合する。

1. 後続の自然言語応答を再現できる。
2. 別対象への質問では同じ値を誤想起しない。
3. 新しい観測を一回でfast bindingへ書き込める。
4. 更新後は古い値ではなく最新値を返す。
5. marginが小さい候補は可逆的に棄権する。

学習時の応答は正解クラスではなく、時系列中に実際に現れる次発話として扱った。モデルへentity/value一覧、意味slot名、形態素解析器、外部LLM、RAG、ベクトルDBは渡していない。

## 実装

- 観測文・質問文・後続応答の文字列対応から匿名key/value候補を生成。
- 複数応答から共通suffixを誘導し、応答内のepisode固有残差を候補値とする。
- 観測／質問の共有substringを候補keyとする。
- 観測schemaと質問schemaを可逆な `<K>` / `<V>` 骨格として保持。
- 正例の後続応答予測利得からsupportを加算。
- 他対象質問へ同じkeyが混入する場合にharmを加算。
- `support - 2*harm >= 2` の候補だけ低速schemaへ統合。
- 新規観測は、統合schemaでparseが一意な場合だけfast bindingへ書き込む。

## 実験条件

- 学習更新数: 48 / 180 / 540
- seed: 1 / 7 / 19
- 評価: 直接質問、代名詞、表記揺れ、distractorを含む長い質問、完全未学習質問、新規identity一回提示
- baseline: 全表面観測に対する文字2-gram最近傍
- 測定: 正答率、棄権・解除数、schema/binding数、モデルbytes、読み出し量、学習・推論時間、Peak RSS

## 最大540更新・3 seed平均

| 指標 | 表面全件検索 | 予測利得grouping |
|---|---:|---:|
| 直接質問 | 0.0000 | 0.03125 |
| 代名詞 | 0.0000 | 0.0000 |
| 表記揺れ | 0.0000 | 0.0000 |
| distractor付き長文 | 0.0000 | 0.0000 |
| 完全未学習質問 | 0.0000 | 0.0000 |
| 新規identity一回提示 | 0.0000 | 0.0000 |
| モデルサイズ | 29,693 B | 5,454 B |
| 読み出し | 794.3観測 | 5 schema |
| 推論時間 | 6.724 ms | 0.170 ms |
| 学習時間 | 0.00011秒 | 0.05484秒 |
| schema数 | — | 5 |
| binding数 | — | 50 |
| 可逆棄権・解除 | 0 | 628.3 |

Peak RSSは279,508 KiB。Pythonランタイム全体を含み、方式固有値でも弱いスマートフォン実機値でもない。

## 反証

### 1. 後続想起利得は、正しい候補が存在する場合の選別器にすぎない

未来応答を使って候補を採点しても、入力側でentity/value境界が誤っていれば正しいgrouping候補を生成できない。未来予測を追加しただけでは上流のcandidate recallは改善しなかった。

### 2. 学習量増加で性能が悪化

直接質問は48更新で0.1996、180更新で0.0450、540更新で0.03125へ低下した。経験が増えるほど表面骨格の競合が増え、一意parse条件による棄権が増加した。

### 3. 可逆棄権は選択的な不確実性ではない

540更新で平均628.3回の解除・棄権が発生したが、誤groupingだけを拒否したのではなく、正しい新規観測も大量に拒否した。margin collapseによる能力消失である。

### 4. 代名詞・表記揺れ・未知質問は未成立

完全な表面共参照がない場合、episode identityを復元できなかった。時間的なlast-entity fallbackも、雑音発話や複数episodeの切替に耐えなかった。

### 5. 後続応答は自己教師あり信号だが、自由日本語意味理解ではない

自然な次発話を利用しているものの、制御された一関係世界であり、対象・関係・値・目的を自律形成した証拠ではない。自由対話、読解、推論、計画、因果、反実仮想、自由生成、一般継続学習は0のまま。

## 系列D固有の新知見

記憶形成を次の二層へ明確に分離する必要がある。

1. **episode hypothesis proposal**: 生の入力から、entity/value/relation/coreferenceが異なる複数のgrouping候補を生成する。
2. **predictive consolidation**: その候補が将来想起を改善し、負の質問へ誤干渉しない場合だけ低速記憶へ統合する。

今回検証した第2層は、第1層のcandidate recallが不足すると機能しない。したがって予測利得は主原理ではなく、候補生成後の監査・統合条件として位置付けるべきである。

## 他系列へ返す知見

- A: 外部feedbackで状態を修復する前に、どの発話群を同一episode状態として扱うかの候補生成が必要。
- B: role-factored parseを圧縮率だけでなく、one-shot write/readと負の質問干渉で評価するべき。
- C: event identityとepisodic identityを分け、同じeventでも異なるepisodeへ誤伝播しないことを監査するべき。
- E: grouping候補は境界差だけでなく、将来の想起・更新・棄権結果が異なる非同型memory graphでなければならない。

## 次の仮説

**Counterfactual Retrieval-Graph Proposal with Self-Supervised Coreference**

次は、時間・文字類似から単一groupingを作らない。各入力から以下が異なる複数のmemory graphを生成する。

- entity境界
- value境界
- relation edge
- 代名詞・省略のantecedent
- episode開始／終了
- 更新か別episodeか

各graphを実際にfast memoryへ書き込み、後続質問に対する想起、別episode質問への非干渉、更新後の最新性、後続反例による解除を比較する。異なる未来想起を生成しない候補は統合前に同一視する。

必須成功条件は、直接質問だけでなく代名詞・表記揺れ・未学習質問を0から改善し、新規identity一回提示を成立させ、棄権率増加だけで見かけの精度を作らないこと。

## 状態

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
