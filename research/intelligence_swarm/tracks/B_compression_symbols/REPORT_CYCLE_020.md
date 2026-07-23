# 系列B Cycle 020 研究報告

## 仮説

**Substitution-Closed Program Nonterminals by Exact Derivation Compression**  
（正確な導出圧縮による置換閉包program非終端記号）

Cycle 019の次案だったsuccess/failure因子swapは、系列E Cycle 019のfactor swapと系列C Cycle 020の介入cutに中心機構・反証条件が重なるため棄却した。

本Cycleでは、raw before/command/afterから得た局所program候補について、同じcommand contextとstate transition contextへ複数のfillerを相互置換し、全success contextで正確な局所導出を再現する場合だけ匿名非終端記号へ昇格した。

- command context
- state transition context
- filler集合
- substitution closure
- exact local derivation
- absolute description length

を一つの可逆文法codeとして保持し、既知programを圧縮しつつ未知形式へ生成的に転移できるかを検証した。

## 先行研究整理

- LILOはprogram corpusを圧縮して再利用可能なlibrary abstractionを形成するが、LLM-guided synthesisと既定program表現を前提とする。
- LIBRARIAN/MINICODEはMDLが人間の良いrefactoring判断と整合し、複数programのlibrary化で有効と報告するが、入力programと実行意味は既に与えられている。
- MDLによるtransduction grammar inductionは文法圧縮の根拠を与えるが、生の自由日本語からoperation semanticsを形成する問題は残る。
- 2025年のcompact grammar induction研究は、分布collapseにより大きく弱いgrammarへ陥る問題を報告している。

## 他4系列との重複表

| 系列 | 最新中心 | 限定信号 | 主な失敗 | B候補との判定 |
|---|---|---|---|---|
| A | surprisal位相同期による予測role候補 | candidate recall部分回復 | 選択精度低、長距離崩壊 | 予測境界探索は棄却 |
| C | intervention-preserving correspondence cycle | alternateに表面信号 | gate増分0、rename悪化 | 介入cut / transportは棄却 |
| D | cross-query bridge consequence | rename write改善 | read悪化、endpoint混線 | 長期memory aliasは棄却 |
| E | counterfactual factor swap | object recall信号 | value recall 0、能力増分0 | factor swap案を棄却 |
| **B** | **置換閉包で匿名非終端記号を形成し導出を圧縮** | 今回検証 | open-form grammar生成 | 系列固有 |

継承知見:
- A: candidate recallとcandidate selectionを別評価する。
- C: execution failureとwrong executionを分離する。
- D: write transportとread identityを混同しない。
- E: factor swap以前に候補境界が成立している必要がある。

## 実験条件

- 学習episode: 48 / 144 / 432
- seed: 1 / 7 / 19
- test: 120例 / split / seed
- split: seen、unseen word order、unseen lexeme、rename、nested、subject omission、alternate state、free paragraph
- 比較: Executable program、Surface filler group、Substitution-closed grammar
- program上限: 32
- nonterminal上限: 32
- candidate上限: 96 / episode

学習器が使用するのはraw before/command/afterのみ。hidden object・field・valueは評価器専用。

## 最大432 episode・3 seed平均

| 条件 | Executable | Surface group | Substitution grammar |
|---|---:|---:|---:|
| seen | 0.6833 | 0.6944 | **0.7889** |
| unseen order | 0 | 0 | 0 |
| unseen lexeme | 0 | 0 | 0 |
| rename | 0 | 0 | 0 |
| nested | 0.6833 | 0.6944 | **0.7833** |
| subject omission | 0 | 0 | 0 |
| alternate state | 0 | 0 | 0 |
| free paragraph | 0.6833 | 0.6944 | **0.7444** |

### Seen詳細

- candidate execution recall: 0.6833 → **0.8306**
- wrong commit: 0.0611 → **0.0028**
- exact program: 32 → **8**
- nonterminal: **32**
- merge: **8**

## 判定

**中核仮説は反証。既知surface内の導出再利用には明確な限定信号がある。**

### 既知精度と誤確定は改善

Seen accuracyは0.6833から0.7889へ改善し、wrong commitは0.0611から0.0028へ低下した。置換閉包を通過した非終端記号は、既知context内でfillerを再利用する局所導出器として機能した。

### Nested / paragraphの改善は構造理解ではない

Nestedは0.7833、free paragraphは0.7444となった。しかし両条件には学習済みcommand substringがそのまま含まれる。これは入れ子scope、談話構造、目的、制約を理解した証拠ではなく、既知局所導出を長い文字列内で再発見した結果である。

### 未知形式は全面0

- unseen order: 0
- unseen lexeme: 0
- rename: 0
- subject omission: 0
- alternate state: 0

非終端記号はfiller集合を抽象化したが、command contextとstate transition contextは固定surfaceのままである。置換閉包は値集合の変数化にはなっても、語順・語彙・object alias・state表現を跨ぐ文法規則にはなっていない。

### 絶対MDLは悪化

- Executable description: 9,120 bits
- Surface group: 9,042.67 bits
- Substitution grammar: **14,876 bits**

Program数は32から8へ減ったが、32個の非終端記号・filler辞書・derivation indexにより総記述長は約1.63倍へ増えた。圧縮研究として絶対MDL利得が負なので、現形は採用できない。

### 形成された記号は意味roleではない

非終端記号は、同じ文字contextへ挿入可能なfiller集合である。Object、relation、value、scope、goal、constraintを表す匿名roleではなく、surface transduction contextの置換classに留まる。

## 探索爆発抑制

- episode当たりproposal上限96
- program上限64、保存上限32
- filler上限12
- success context監査上限24
- nonterminal上限32

推定計算量:
- proposal `O(NC²)`
- substitution closure `O(P·S·F)`
- quotient `O(P)`
- inference `O((P+G)L)`

## 資源量

- Grammar model: **15,512 bytes**
- Executable model: 40,144 bytes
- training: **0.02549 sec**
- inference: **0.03475 ms/example**
- Peak RSS: 112,124 KiB（Python runtime込み）

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列B固有の進展

1. Clause候補生成
2. 局所実行可能性
3. 誤適用反証
4. Intervention outcome
5. Numerical rank basis
6. Multi-view separation
7. Held-out可逆復号
8. Positive/negative witness共同符号化
9. Anonymous failure quotient
10. **Substitution-closed nonterminal induction**
11. Cross-context derivation grammar
12. Hierarchical MDL library consolidation

最大の新知見:

> filler置換閉包は既知context内の局所導出精度を改善できる。しかしcontext自体を抽象化しなければ未知語順・語彙・状態表現へ転移せず、非終端記号metadataにより絶対MDLも悪化する。

## 他系列へ返す知見

- A: candidate cellのfiller置換可能性は選択signalになり得るが、context abstractionを別に形成する必要がある。
- C: correspondence edgeは値置換閉包だけでなく、command/state contextを跨ぐ導出閉包を監査する。
- D: relation/value endpointのfiller classとobject/query endpoint contextを別圧縮する。
- E: factor roleはswap energyだけでなく、複数contextでのexact derivation closureと絶対code lengthを測る。

## 次の仮説

**Second-Order Context Nonterminals from Derivation-Graph Bisimulation**  
（導出graph双模倣からの二階context非終端記号）

1. 各programを `command context → filler → state transition` の導出graphへ変換
2. 異なるsurface contextでも同じsuccess/wrong/noexec遷移を持つnodeをbisimulation候補化
3. Held-out episodeで双方向に同じ導出を再現する場合だけcontext nonterminalへ統合
4. filler nonterminalとcontext nonterminalを階層結合
5. unseen order / lexeme / rename / alternateのcandidate recallを独立gate化
6. Executable baselineより絶対description lengthが短い場合だけ採用
7. 説明不能形式はunknown productionとして保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
