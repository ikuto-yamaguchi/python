# 系列D Cycle 007 — Counterfactual Retrieval-Graph Proposal with Self-Supervised Coreference

## 結論

中核仮説は反証された。入力ごとにentity境界・value境界・照応先・更新先が異なる複数のmemory graphを生成し、各候補をfast memoryへ仮書込みして後続想起と負の質問で比較したが、代名詞・長い未学習質問・干渉後の最新値保持は改善しなかった。

一方、明示的に二つの引用区間を持つ新規identityの一回提示では、表面全件検索0.2000に対しgraph方式0.6611となった。したがって、**正しいepisode-local境界候補が候補集合へ含まれる場合に限り、仮書込み→想起probeによる候補監査はone-shot bindingを改善できる**。しかしこれは自由日本語からの照応・episode構造創発ではない。

## 先行研究と位置付け

近年のPredictive Attractor Modelsは、局所更新・一回提示・複数可能性保持・破滅的忘却回避を同時に狙う逐次記憶を報告している。また、疎なmemory slotだけを更新するcontinual learning、fast/slow結合を持つ多時間尺度記憶、hippocampal pattern separationも、干渉回避と迅速学習の有力な設計原理を示している。

ただし、これらは今回の最大ボトルネックである「生の日本語から、どの発話が同じepisode・entity・relationを指すかをopen-setに提案する」問題を直接解決しない。そこで本サイクルは、記憶更新則ではなく**memory graph proposal recall**を反証対象にした。

## 他4系列との重複表

| 系列 | 現在の仮説・実装 | 成功 | 失敗・未解決点 | D候補との重複判定 |
|---|---|---|---|---|
| A | entropy-matched multi-turn predictive repair | 既知yes/noなら2〜8候補を理論bit数付近で分離 | 未知feedbackで誤確信、候補世界は外部付与 | 外部質問policyは採用せず、記憶graphの仮書込み結果だけを比較 |
| B | effect-conditioned primitive MDL + one-shot lexeme bridge | 効果付き一回観測で未知述語0.4917、約3.3KB | role/scope/state relation共同誘導に失敗 | predicate primitive誘導は行わず、episode/coreference graphの形成に限定 |
| C | intervention-equivalence condition quotient | 効果付き一回bridge後に未知context 1.0、486B | action/no-op node固定、zero-shot意味転移0.2833 | 因果conditionを扱わず、事実記憶の照応・更新先を扱う |
| E | role-structured conditional attractor graphs | 非同型action/no-op候補で正marginとblocked選択 | 未知命令・入れ子・複数段落・訂正0 | energy緩和ではなく、候補graphを実際にmemoryへ書いて想起差を測る |
| D候補 | counterfactual retrieval-graph proposal | 正しい候補が含まれるone-shot明示文で改善見込み | 代名詞・省略・表記揺れ・更新先の候補recallが主要反証 | 固有方向として採用 |

中心機構・反証条件・期待能力が実質的に重なる「MDLでrole候補を生成」「因果branchを誘導」「energyでgraphを選択」「外部質問で候補を絞る」は棄却した。

## 仮説

**Counterfactual Retrieval-Graph Proposal with Self-Supervised Coreference**

単一のepisode groupingを早期確定せず、入力ごとに次が異なる少数の候補graphを生成する。

- entity/valueの方向
- 直近entityのどれを代名詞・主語省略のantecedentとするか
- 既存episodeの更新か新episodeか
- relation surface skeleton

各候補を一時的にfast memoryへ書込み、以下の結果を比較する。

1. 直後の質問に正しい値を返すか
2. 別episode質問へ誤干渉しないか
3. 更新後に最新値を返すか
4. 同じ未来想起しか生まない候補は同一視できるか
5. marginがない候補は統合せず撤回できるか

単なる検索/RAGとの差は、文書を返すのではなく、候補graphごとに内部のwrite/read状態を変化させ、その差を後続推論状態へ統合する点にある。

## 実装

- 生文字列中の引用区間から双方向entity/value候補を生成
- 引用区間が一つだけの発話では、直近entityごとに異なるantecedent graphを生成
- 各候補を仮書込みし、後続質問と負の質問を実行
- 同じ正規化entity・relation・valueを生む候補は同一視
- 最良候補が同率なら統合せず可逆撤回
- 確定edgeは `(匿名化entity, relation skeleton) -> latest value` として保持
- query時は全episodeではなく低速schema集合とfast edgeを読む

固定entity/value辞書、意味slot、形態素解析、埋込みモデル、ベクトルDB、RAG、外部LLM、正解クラス分類器は使用していない。

## 実験条件

- 更新数: 48 / 180 / 540
- seed: 1 / 7 / 19
- split:
  - 直接質問
  - 代名詞質問
  - 表記揺れ
  - 長い未学習質問
  - distractor入り質問
  - 新規identity一回提示
  - 15件の無関係発話を挟んだ最新値更新
- baseline: 全表面観測の文字n-gram走査
- 測定: 精度、棄権率、候補生成数、撤回数、edge/schema数、モデルbytes、学習・推論時間、Peak RSS

## 540更新・3 seed平均

| 指標 | 表面全件検索 | counterfactual graph |
|---|---:|---:|
| 直接質問 | 0.4583 | 0.4583 |
| 代名詞 | **0.2361** | 0.0139 |
| 表記揺れ | **0.4444** | 0.3333 |
| 長い未学習質問 | **0.3889** | 0.0000 |
| distractor付き | 0.4028 | 0.3889 |
| 新規identity一回提示 | 0.2000 | **0.6611** |
| 干渉後の最新値 | **0.2833** | 0.0750 |
| モデルサイズ | 36,459 B | **31,009 B** |
| 読み出し | 675観測 | **19 schema** |
| 推論時間（direct） | **4.504 ms** | 4.957 ms |
| 学習時間 | — | 0.1099秒 |

追加測定:

- fast edge: 234.3
- 生成候補: 1,926.7
- 可逆撤回: 331.0
- 代名詞棄権率: 0.9167
- 長文棄権率: 0.9861
- Peak RSS: 実行JSONに記録。Python runtime込みであり方式固有値ではない。
- 更新計算量上限: `O(H*(Q+N)*G)`, `H<=12`
- 想起計算量: `O(S*G)`, 最大規模で `S≈19`

モデル本体は1GBを大幅に下回る。候補数とschema数は弱いCPUでも扱える規模だが、スマートフォン実機検証は未実施である。

## 支持された部分

### 明示的な候補境界があるone-shot binding

新規identity一回提示は0.2000から0.6611へ改善した。二つの引用区間によって正しいentity/value候補が候補集合へ入り、仮書込み後の質問再現が方向選択に使えた。

この結果から、次の限定原理は残せる。

> 正しいepisode-local候補が少数集合へ含まれる場合、候補をfast memoryへ実際に書き込み、将来想起と非干渉を比較することで、一回提示bindingの選択を改善できる。

### 容量と読み出しの分離

全675観測を読むbaselineに対し、graph方式は19 schemaを読む。モデルサイズも約31KBで1GB未満である。

## 決定的な反証

### 1. 自己教師ありcoreferenceは成立していない

代名詞精度は0.0139、棄権率0.9167だった。直近entityを複数候補として列挙しても、質問がどのantecedentを支持するかを文字列だけで識別できない。

### 2. 長い自由質問では全面的に崩壊

長い未学習質問は精度0、棄権率0.9861だった。relation skeletonを表面文字列として保持しているため、同じ意味の異なる質問表現へ転移しない。

### 3. 最新値更新と干渉回避に失敗

15件のdistractor後に代名詞形式で更新すると、正しい更新先を選べず最新値精度0.075となった。これは破滅的忘却ではなく、**新しい経験をどの既存episodeへ結合するかの誤り**である。

### 4. 表記揺れ正規化は意味同一性ではない

句読点・全角数字の一般的正規化を行ったが、表記揺れはbaselineを下回った。同義語、略称、代名詞、暗示的照応は扱えない。

### 5. 可逆撤回も選択的ではない

平均331候補を撤回したが、誤候補だけを除いたのではなく、正しい代名詞・長文候補もほぼすべて捨てた。Cycle 006と同様、候補margin不足による能力消失が残る。

### 6. 自由日本語統合ゲートは0

対象・変数・関係・操作・目的の自律形成、読解、推論、計画、因果、反実仮想、自由生成、長期対話は成立していない。

## 破滅的忘却と表面暗記の反証条件

- **破滅的忘却**: 正しいedgeを形成できた後、新規無関係episodeで既存edgeが上書きされ精度が低下すること。
- **grouping failure**: edge形成前または更新時に誤antecedentへ結合すること。
- **表面暗記**: identity rename、質問言い換え、代名詞で性能が消え、既知skeletonだけで成功すること。

今回の主失敗は破滅的忘却より上流のgrouping failureと表面暗記である。

## 系列D固有の進展

記憶形成を三段へ整理できた。

1. **Memory graph proposal**: entity/value/relation/coreference/update先が異なる候補を生成
2. **Counterfactual fast write/read**: 各候補を一時記憶へ書き、異なる未来想起を生成
3. **Predictive consolidation**: 正例想起と負の非干渉を満たす候補だけ低速schemaへ統合

Cycle 006は第3段だけを検証し失敗した。今回は第1・第2段を追加し、明示的二区間one-shotでは改善した。しかし代名詞・長文・更新で候補recallと識別が崩壊した。

したがって、次のボトルネックは「memoryをどう検索するか」ではなく、**照応・relation・episode更新をまたぐ候補を、表面文字一致なしで生成する局所学習信号**である。

## 他系列へ返す新知見

- **Aへ**: 情報利得質問を行う前に、候補memory graphが代名詞や更新先について異なる未来想起を生成できる必要がある。候補recallが0なら質問policyは救えない。
- **Bへ**: effect/role lattice候補は、圧縮長だけでなくone-shot write/read、代名詞更新、負のepisode非干渉を通す必要がある。
- **Cへ**: event conditionとepisodic antecedentは別潜在変数である。action/no-op効果が同じでも更新対象episodeを誤れば記憶は壊れる。
- **Eへ**: 非同型graphは異なる実行結果だけでなく、異なる将来想起・更新先を生成する必要がある。表面境界差だけでは不十分。

## 次の仮説

**Bidirectional Discourse-State Memory with Effect-Grounded Coreference**

次は質問側の表面一致を主証拠にしない。発話ごとに、

- 候補entity
- 候補relation
- discourse focus
- 更新対象episode
- 予測される次発話
- 操作がある場合のbefore/after effect

を双方向に保持する。

代名詞・主語省略候補は、単なるrecencyではなく、候補を選んだときに次の複数ターン予測、更新後の質問、別episode非干渉が改善するかで局所更新する。新しい照応edgeは一回で確定せず、fast weightとして保持し、異なる表現・episodeで再現した場合だけ睡眠統合する。

必須成功条件:

1. 代名詞0.0139を大幅改善
2. 干渉後最新値0.075を改善
3. one-shot 0.6611を維持
4. 長い未学習質問を0から改善
5. 棄権増加だけで見かけの精度を作らない
6. 保存量をepisode数へ線形増加させない
7. 後続反例でcoreference edgeを撤回可能

## 状態

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
