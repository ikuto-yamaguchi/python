# 系列B Cycle 021 研究報告

## 仮説

**Second-Order Context Nonterminals from Derivation-Graph Bisimulation**  
（導出graph双模倣からの二階context非終端記号）

Cycle 020ではfiller置換閉包により既知surface内精度が改善した一方、command/state contextは固定のままで、未知語順・未知語彙・rename・主語省略・別状態表現へ転移せず、絶対MDLも悪化した。

本Cycleではprogramを `command context → filler → state transition` の導出graphとして扱い、各programの全episodeに対する success / wrong / noexec partition、state transition shape、filler数を匿名状態とした。odd/even held-out viewで同じ遷移partitionを再現するcontextだけをbisimulation候補として二階非終端記号へ統合できるか検証した。

## 先行研究整理

- CAV 2025のBranching Bisimulation Learningは、非決定的遷移系からbisimulation quotientを学習する方向を示す。ただし状態・遷移系は既に定義済みである。
- 2025年のprogram synthesis研究はDSLやobject-centric abstractionを前提としており、生の日本語からgrammar state自体を形成する問題は残る。
- 2026年のcompositionality議論では、library全体を含む総符号長が短くなるrefactoringを本質とする。program数だけの削減は圧縮ではない。

参考:
- https://link.springer.com/chapter/10.1007/978-3-031-98685-7_8
- https://journals.sagepub.com/doi/10.1177/17248035251363178
- https://iclr-blogposts.github.io/2026/blog/2026/compositionality/

## 他4系列との重複表

| 系列 | 最新中心 | 限定成功 | 主失敗 | Bとの分離 |
|---|---|---|---|---|
| A | surprise同期cellへのactive query | 候補集合内の選択改善 | open-set候補生成なし | 予測query policyは扱わない |
| C | 実行可能effect hypergraph | 別状態表現に表面信号 | operation transportほぼ0 | 因果world operationは扱わない |
| D | endpoint別slow memory | 干渉後recall 0.5 | 主要splitでnode形成0 | 長期memoryは扱わない |
| E | basin曲率factor選別 | null安全停止 | value recall 0 | energy basinは扱わない |
| **B** | **導出graphのcontext双模倣とgrammar quotient** | 今回検証 | open-form context abstraction | 系列固有 |

## 実験条件

- 学習例数: 48 / 144 / 288
- seed: 1 / 7 / 19
- test: 60例 / split / seed
- 条件: seen, unknown order, unknown lexeme, rename, nested, omitted subject, alternate state, free paragraph
- 比較: Executable / Filler substitution / Context bisimulation
- program上限: 32
- learner入力: raw before / command / afterのみ
- hidden object / field / value: 評価器のみ

## 最大288例・3 seed平均

| 条件 | Executable | Filler group | Context bisimulation |
|---|---:|---:|---:|
| 既知 | 0.6667 | 0.6111 | 0.6667 |
| 未知語順 | 0 | 0 | 0 |
| 未知語彙 | 0 | 0 | 0 |
| Rename | 0 | 0 | 0 |
| 入れ子 | 0.6667 | 0.6111 | 0.6667 |
| 主語省略 | 0 | 0 | 0 |
| 別状態表現 | 0 | 0 | 0 |
| 複数文 | 0.6667 | 0.6111 | 0.6667 |

## 判定

**中核仮説は強く反証。**

### 二階context非終端が1件も形成されない

最大288例でもcontext nonterminalは全seedで0件だった。success/wrong/noexec partitionとtransition shapeを同時に一致させると、異なるsurface contextは同じbisimulation classへ入らない。

これは「厳しい双模倣が誤統合を防いだ」のではなく、抽象化が完全に個別program保持へ退化したことを意味する。

### 能力増分が完全に0

Context bisimulationはExecutable baselineと全splitで同一精度だった。既知0.6667、入れ子0.6667、複数文0.6667で、未知語順・語彙・rename・省略・別状態表現は0のままである。

### Filler groupingも今回条件では悪化

Filler groupingは既知0.6111でExecutable 0.6667を下回った。Cycle 020で見えた改善は、実装した置換閉包と上限選択の組合せに依存し、単純な同一filler/state groupingでは再現しない。

### Bisimulation対象が意味遷移系ではない

今回の状態はepisode index上のsuccess/wrong/noexec partitionであり、object・relation・operation・goal・constraintではない。異なる表現で同じ意味を持つprogramは、そもそも同じepisode上で実行不能になるため、意味同値性を評価する前に別classへ分裂する。

### 絶対MDL利得なし

- Executable description: 9,128 bits
- Context bisimulation: 9,128 bits
- Context nonterminal: 0
- Merge: 0

総符号長は一切短くならない。

## 資源量

- model: 24,936 bytes
- programs: 32
- context nonterminals: 0
- raw candidates: 288
- training: 0.01079 sec
- inference: 0.02946 ms/example
- Peak RSS: 111,876 KiB（Python runtime込み）
- 推定計算量: proposal `O(NC²)`, behavior `O(PN)`, quotient `O(P)`, inference `O((P+G)L)`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列B固有の進展

> **既知episode上の完全なbehavioral bisimulationは、surface contextを跨ぐ意味抽象化には厳しすぎる。実行不能を意味差と扱うと、未知表現候補は同値性検査の前に分裂する。**

## 他系列へ返す知見

- A: 候補を同じ観測queryで完全分離することと、未知表現を同一状態へ結ぶことは別。
- C: null transportを通常遷移としてbisimulation signatureへ入れると、意味同値operationが分裂する。
- D: endpointの未形成をidentity差としてslow memoryへ固定しない。
- E: 実行不能basinの一致・不一致は意味role evidenceではない。

## 次の仮説

**Open-Transport Context Relations from Partial Derivation Homomorphisms**  
（部分導出準同型からのopen-transport context関係）

次は完全bisimulationを要求しない。

1. Context間で共通する成功導出だけを部分写像化
2. Noexecを意味差ではなくunknown transportとして分離
3. Filler・state transition・preservationのうち2 view以上が対応する場合だけrelation候補化
4. Held-out surfaceで新たな導出を生成できた場合にのみcontext abstractionへ昇格
5. Wrong transportを増やす写像は反例で局所切断
6. 未知語順・語彙・rename・別状態表現のcandidate recallを主指標化
7. Executable baselineより絶対description lengthが短い場合だけlibrary採用

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
