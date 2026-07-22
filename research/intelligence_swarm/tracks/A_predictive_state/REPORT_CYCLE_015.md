# 系列A Cycle 015 研究報告

## 仮説

**Self-Generated Probe Programs from Prediction-Error Gradients**  
（予測誤差勾配からの自己生成probe program）

Cycle 014では、`execute / preserve / reverse / recall / next` の5観測channelを実験側が与えた状態で、marked候補集合をworld outcomeで分割するとseen精度1.0を得た。しかしprobe空間は手書きであり、引用なし日本語のcandidate recallは0だった。

本Cycleでは固定観測channelを廃止し、各候補に対する局所surgery、すなわちtarget/valueの削除、role交換、別候補への再束縛、候補回転からprobe program候補を生成した。probeの返答は、surgery実行後のraw state差分signatureのみであり、正答target/value文字列は返さない。

学習時にはcross-episodeで、

- 正候補が観測partition内に生存するか
- 候補classをどれだけ縮小するか
- 同じsurgeryが複数episodeで再利用できるか

を測り、上位probeだけをlibraryへ昇格した。

## 先行研究整理

- Bayesian active learningでは、単なる不確実性最小化より、最終意思決定を共有するhypothesis regionを高速に特定するquery設計が重要とされる。
- Active Learning with Simple Questionsは、query回数とquery languageの複雑さに本質的なtrade-offがあることを示す。
- 2026年のactive query synthesis研究は、固定poolから選ぶだけでなくquery自体を生成する方向を扱うが、連続表現空間と目的関数は既に与えられている。
- 2026年のschema-based active inferenceは階層生成modelとgrounding likelihoodを前提に抽象schema再利用を示すが、生の日本語からprobeや状態変数を創発する上流問題は残る。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B | outcome rankを増やす介入basis | executable seen 0.6222 | quotient 0.1778、未知形式0 | program quotient形成は棄却 |
| C | rank増加outcomeによるidentity basis | seen 1.0 | unknown・省略・段落0 | object identity形成は棄却 |
| D | factorized object/relation address trace | 軽量address探索 | write 0.0201、read 0 | 長期memory addressは棄却 |
| E | raw outcome圧縮から残差basis | 既知basis routing回復 | basis自体は手書き、unmarked 0 | 内部残差cause形成は棄却 |
| **A** | **外部観測用probe programの自己生成・選択** | 今回検証 | candidate proposalとprobe意味 | 系列固有 |

継承した知見:
- B: 固定破壊vectorはroleを識別しない。
- C: target/non-target保存が候補classを分割しない場合は増分情報0。
- D: write側改善とread側address形成は別能力。
- E: 既知basis間対応の学習とbasis自体の生成を分ける必要がある。

## 実験条件

- 学習量: 30 / 90 / 180 episode
- seed: 1 / 7 / 19
- candidate上限: 32
- surgery probe候補: 最大24
- learned library上限: 12
- 最大probe: 6
- 比較:
  1. 全surgeryを毎回探索
  2. cross-episode utilityから学習したprobe library
- 統合テスト:
  - 既知marked
  - 多候補曖昧性
  - 入れ子
  - 引用なし言い換え
  - 主語省略
  - 複数段落
  - 候補外

学習器に固定ontology、形態素解析、意味slot、RAG、外部LLMは与えていない。

## 最大180例・3 seed平均

| 条件 | recall | 全surgery精度 / probe | Learned精度 / probe | Learned推論 |
|---|---:|---:|---:|---:|
| 既知 | 1.0000 | 1.0000 / 2.00 | **1.0000 / 2.00** | 1.3901 ms |
| 曖昧性 | 1.0000 | 1.0000 / 2.00 | **1.0000 / 2.00** | 1.3824 ms |
| 入れ子 | 1.0000 | 1.0000 / 2.00 | **1.0000 / 2.00** | 1.3777 ms |
| 言い換え | 0.0000 | 0 / 1.00 | 0 / 1.00 | 1.1661 ms |
| 主語省略 | 0.0000 | 0 / 1.00 | 0 / 1.00 | 0.9083 ms |
| 複数段落 | 0.0000 | 0 / 1.00 | 0 / 1.00 | 0.9760 ms |
| 候補外 | 0 | wrong 0 / null 1.0 | wrong 0 / null 1.0 | 0.8365 ms |

## 限定的に支持された部分

marked制御条件では、learned libraryは全surgery探索と同じ精度1.0を維持しながら、推論時間を削減した。

- seen: 2.4013 → 1.3901 ms
- ambiguous: 1.6157 → 1.3824 ms
- nested: 1.5843 → 1.3777 ms

したがって、**surgery候補を毎回総当たりせず、cross-episodeで正答生存とpartition gainを再現したprobeだけをlibrary化する**下流部品には効率上の信号がある。

## 決定的な反証

**中核仮説は反証。**

### 1. Probe libraryが退化

3 seedすべてで上位libraryはほぼ同一になり、`drop_target` 4件、`drop_value` 4件が上位を占めた。これは経験から意味的なprobeを創発したのではなく、現在の文字状態実行器で最も大きな差分を作る破壊操作が機械的に選ばれただけである。

### 2. 学習probeの能力増分は0

全surgery方式とlearned方式は、全marked条件でaccuracy 1.0、平均probe 2.0と完全に同一だった。改善したのは候補probeの列挙時間だけで、候補classの意味的分離能力ではない。

### 3. 引用なしcandidate recallは0

言い換え、主語省略、複数段落では正答候補を一件も生成できなかった。probe生成・能動観測・再帰更新は、存在しないtarget/value候補を救えない。

### 4. Raw outcome signatureはworld semanticsではない

観測は実行後文字列の短いhashと変更文字数である。object、relation、operation、goal、constraint、causal edge、future consequenceを表していない。

### 5. marked 1.0は正答候補供給条件

引用区間からtarget/valueが候補集合に入り、environmentがtrue actionのraw outcomeを返す制御条件である。自由日本語理解や自律的世界状態形成の証拠ではない。

### 6. Query languageの複雑性を解決していない

probe候補は6種類のsurgery familyと最大4 indexの直積である。自由日本語のgraph edgeが増えれば候補probe数は `O(HK)` で増加する。現在の上限切断は探索爆発の原理解決ではない。

## 資源量

- probe library model: **2123 bytes**
- Peak RSS: **111496 KiB**（Python runtime込み）
- candidate上限: 32
- learned probe上限: 12
- 推論: 約0.84～1.39 ms/example
- 推定計算量:
  - candidate proposal `O(L²)`
  - surgery proposal `O(HK)`
  - probe learning `O(NHK)`
  - inference `O(PH)`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列A固有の進展

予測状態・能動推論を次の9段階へ更新した。

1. Raw candidate proposal
2. Candidate precision / null
3. Executable predictive outcome
4. Outcome-equivalence partition
5. Shared active probe scheduling
6. Recursive reversible update
7. Probe surgery proposal
8. **Probe semantics / cross-world invariance**
9. Open-set semantic abstraction

今回は第7段階の表面版とprobe library圧縮を実装した。しかし第8段階がなく、破壊量の大きい文字操作へ退化した。

> probeを自動生成できることと、意味のある問いを生成できることは別である。probeが異なる世界仮説に対して再利用可能な因果結果を生成する必要がある。

## 他系列へ返す新知見

- **Bへ:** outcome matrixのrank増加だけでは、drop系の大破壊操作が常に優先される。role保存とabsolute execution fitを別制約にする。
- **Cへ:** identity basisはcandidate分割量でなく、target objectだけを変えnon-target trajectoryを保存するかで校正する。
- **Dへ:** address traceを分割するprobeは、write/read双方の局所結果を変えなければ意味addressにならない。
- **Eへ:** raw residual basisも変更量が大きいpatternへ偏る。cause node昇格にはcross-world局所性が必要。

## 次の仮説

**Invariant Counterfactual Probe Graphs from Cross-World Locality**  
（世界横断局所性からの不変反実仮想probe graph）

次はprobe utilityをpartition gainだけで更新しない。

各surgeryについて、

- 異なるobject名・値・表現でも同じ局所edgeだけを変える
- non-target stateを保存する
- query後のfuture stateを同じ方法で分割する
- raw文字変更量ではなく局所因果outcomeを再現する
- cross-episodeで同じ候補商を作る

場合だけprobe graphへ昇格する。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
