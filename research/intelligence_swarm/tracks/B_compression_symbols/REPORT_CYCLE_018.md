# 系列B Cycle 018 研究報告

## 仮説

**Counterexample-Coded Program Symbols by Minimum Exception Cover**  
（最小反例被覆による反例符号化program symbol）

Cycle 017の次案だった「可逆boundary–program共同帰納」は、系列A Cycle 018のboundary–action split/merge共同探索と中心機構・反証条件が実質的に重なるため棄却した。

本Cycleでは文字境界の生成そのものを中心にせず、raw before / command / afterから既に提案された局所programについて、成功episodeだけでなく誤適用episodeの最小反例集合を明示的に符号化したとき、個別episode保存より総記述長を短縮できるprogramだけを匿名symbolとして採用できるか検証した。

- program構造code: command左右context + state左右context
- positive witness: 正しくbefore→afterを再構成するepisode index
- negative witness: 実行はできるが誤ったafterを生成するepisode index
- greedy minimum-exception cover: 未被覆episodeのliteral code節約がprogram + witness + exception codeを上回る場合だけ採用
- inference: empirical precisionとraw command-context similarityで候補を順位付け
- 同点時は一意化せずnull

## 先行研究整理

- Zhu & Srebro, COLT 2025, *Quantifying Overfitting along the Regularization Path for Two-Part-Code MDL in Supervised Classification*: two-part-code MDLが正則化強度とnoise条件により過適合し得ることを定量化しており、「短いcodeなら自動的に一般化する」とは限らない。https://proceedings.mlr.press/v291/zhu25a.html
- Egolf & Tripakis, 2026, *Recursive Program Synthesis from Sketches and Mixed-Quantifier Properties*: counterexample-guided synthesisで反例から構文制約を学び、探索枝を事前に除外する。ただしDSL・sketch・論理仕様は既定。https://arxiv.org/abs/2601.04045
- Xu et al., EMNLP 2025, *MC²*: compositional generalizationにprimitive coverageが必要で、最低被覆条件でも汎用化は自動的に成立しない。https://aclanthology.org/2025.findings-emnlp.406/
- Chen et al., ICML 2025, *Non-Asymptotic Length Generalization*: minimum-complexity interpolationのlength generalizationを理論化する一方、一般的文法族では必要長の計算可能上界が存在しない場合がある。https://proceedings.mlr.press/v267/chen25ar.html
- Opper & N, ICML 2025, *Banyan*: 明示的階層構造が低資源表現学習に有効だが、構造の型はモデル側に与えられる。https://proceedings.mlr.press/v267/opper25a.html

本Cycleは、既定DSLの反例誘導ではなく、生日本語由来のraw局所program候補を「反例まで含む絶対code length」でsymbolへ昇格できるかを対象とする。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との区別 |
|---|---|---|---|---|
| A | boundary–action共同提案 | 境界探索の誤確定条件を特定 | 全split pair recall 0、28–34ms | boundary split/mergeを中心にしない |
| C | executable operation fiber | conditional-CF評価漏れを除去 | transport coverage 0 | world operation/因果代数を扱わない |
| D | provenance-gated alias reconsolidation | provenance保持 | slow link 0、interference 0 | 長期memory同値性を扱わない |
| E | frustration-driven candidate birth | nullで誤確定0 | candidate recall 0、birthはjunk化 | energy relaxation/candidate birthを扱わない |
| **B** | **正例と最小反例集合を共同符号化するprogram symbol** | 今回検証 | absolute MDL・open-form transfer | 系列固有 |

継承知見:
- A: after/futureへの表面適合だけで境界を増やすとjunk候補が増える。
- C: 実行不能と誤実行を同じoutcomeに混ぜない。
- D: 共起やview復号だけでは同一trajectoryを証明しない。
- E: candidate外で相対scoreを一意化しないnullが必要。

## 実験条件

- 学習episode: 48 / 144 / 432
- seed: 1 / 7 / 19
- test: 120例 / split / seed
- split: seen / 未知語順 / 未知語彙表現 / 入れ子 / 主語省略 / 別state表現 / 複数文自由形式
- raw proposal上限: 96 / episode
- candidate program上限: 64
- 保存program上限: 32
- 比較:
  1. executable個別保持
  2. success-only MDL grouping
  3. counterexample-coded minimum-exception cover
- learner入力: raw before / command / afterのみ
- hidden object / field / value: 評価器専用

## 最大432 episode・3 seed平均

| 条件 | Executable acc/recall | Success-MDL acc/recall | Exception-MDL acc/recall |
|---|---:|---:|---:|
| seen | 0.6889/0.6889 | 0.6889/0.6889 | 0.6861/0.6861 |
| 未知語順 | 0/0 | 0/0 | 0/0 |
| 未知語彙 | 0/0 | 0/0 | 0/0 |
| 入れ子 | 0.6889/0.6889 | 0.6889/0.6889 | 0.6861/0.6861 |
| 主語省略 | 0/0 | 0/0 | 0/0 |
| 別state表現 | 0/0 | 0/0 | 0/0 |
| 複数文 | 0.6889/0.6889 | 0.6889/0.6889 | 0.6861/0.6861 |

全方式のseen wrong commitは0.0278。未知形式ではcommit自体が0で、誤確定も0だった。

## 判定

**中核仮説は強く反証。**

### 1. 反例符号化は能力を改善しない

seen accuracyはExecutable 0.6889に対しException-MDL 0.6861で、0.0028悪化した。入れ子・複数文でも同じ差が出た。反例情報はprogram選択を意味的に改善せず、正しい候補を一部取り落とした。

### 2. 未知形式candidate recallは全て0

- 未知語順: 0
- 未知語彙: 0
- 主語省略: 0
- 別state表現: 0

反例集合を精密に符号化してもcandidate外programは生成されない。これはCycle 017のmulti-view復号と同じ上流限界である。

### 3. 絶対MDL利得が負

最大条件の平均description length:

- Executable: 12,244 bits
- Success-only MDL: 12,244 bits
- Exception-MDL: **81,578 bits**

Exception-MDLは反例index 369 bitsに加え、未被覆episodeのliteral residualを大量に残し、baselineの約6.66倍となった。

### 4. Program数を削減できない

全方式でprogram数は32。Success-only groupingのmergeは0、Exception-MDLもcapまで32 programを選んだ。反例signatureがsurface contextごとに細分化し、symbol統合ではなく個別program保持へ戻った。

### 5. 「反例」は意味的反例ではない

negative witnessは「このraw context programが別episodeで誤った文字stateを生成した」というindexである。object role、relation role、scope、goal、causal constraintを表現しない。反例を符号化したこと自体は意味symbol創発の証拠ではない。

### 6. 入れ子・複数文は既知substring

入れ子・複数文の0.6861は学習済みcommand断片を含むため、scope理解・談話理解・構成的一般化ではない。

## 系列B固有の進展

program symbol形成を10段階へ更新する。

1. clause-lattice proposal
2. local executable reconstruction
3. misapplication precision
4. intervention outcome
5. numerical rank basis
6. multi-view separation
7. held-out reversible view reconstruction
8. **positive/negative witness joint coding**
9. open-form role proposal
10. hierarchical MDL library consolidation

今回、第8段階の制御版を実装した。重要な否定結果:

> **反例をcodeへ含めるだけでは意味symbolにならない。反例indexがsurface episode単位なら、説明長を増やして個別性を記録するだけである。圧縮に効く反例は、複数episodeを横断して再利用できる匿名のfailure causeでなければならない。**

## 資源量

- Exception-MDL model: 38,936 bytes
- Executable model: 38,917 bytes
- programs: 32
- raw candidates: 432
- covered train: 337.33 / 432
- training: 0.01680 sec
- inference seen: 0.02894 ms/example
- inference freeform: 0.03794 ms/example
- Peak RSS: 159,992 KiB（Python runtime込み）
- 推定計算量:
  - proposal `O(NC²)`
  - behavior matrix `O(PN)`
  - greedy exception cover `O(KPN)`
  - inference `O(PL)`
  - `P<=64`, `K<=32`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 他系列へ返す知見

- A: object/value独立viewの反例をepisode indexで保持すると圧縮せず、failure causeを再利用可能な形へ商形成する必要がある。
- C: null transport・wrong transportを個別episodeとして数えるだけではlatent state anchorにならない。
- D: bridge episodeを全件provenance保存するとsemantic consolidationでなく記録量増加になる。反例causeの匿名圧縮が必要。
- E: responsibility-localized residualがepisode固有ならcause basisにならない。異なる文字表現でも再利用できるfailure quotientを測るべき。

## 次の仮説

**Anonymous Failure-Cause Quotients from Minimal Counterexample Hitting Sets**  
（最小反例hitting setからの匿名failure-cause商）

次はepisode indexをそのまま例外codeにしない。

- wrong executionごとに、command側context欠落・state側anchor不一致・非対象破壊・多重適用などのraw outcome差分を匿名featureとして生成
- program × failure-featureの二部graphを作る
- 多数episodeの反例を少数failure featureでhitできる場合だけcause quotientへ統合
- quotient導入後に総description lengthがExecutable baselineより短くなることを必須gate化
- 未知語順・未知語彙・主語省略でcandidate execution recallを独立測定
- candidate外はunknownとして保持
- failure quotientがobject/relation/value roleを本当に分離するか、role-swap反例で検証

## 再現性

`py_compile`を通過し、同じseedで再実行した際、accuracy・recall・wrong commit・program数・description bits・exception bitsが完全一致した。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
