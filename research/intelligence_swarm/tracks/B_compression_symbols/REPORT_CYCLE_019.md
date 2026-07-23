# 系列B Cycle 019 研究報告

## 仮説

**Anonymous Failure-Cause Quotients from Minimal Counterexample Hitting Sets**  
（最小反例hitting setからの匿名failure-cause商）

Cycle 018では、誤適用episodeの番号を例外として保存した結果、既知精度は改善せず、総記述長は12,244 bitsから81,578 bitsへ悪化した。今回はepisode indexを保存せず、raw execution outcomeから得る匿名failure vectorを用い、多数の誤適用を少数predicateで被覆できる場合だけprogram symbolへ原因商を付与した。

## 先行研究整理

- CEGISは反例を用いて候補空間を反復的に絞るが、通常はDSL・仕様・検証器が既に定義されている。
- Counterexample-guided Cartesian abstraction refinementは、失敗点を使って抽象状態を洗練するが、抽象変数候補は計画モデル側から与えられる。
- MDL学習は形式言語一般化で有効な場合があるが、短い記述だけで意味的役割やopen-form候補生成が保証されるわけではない。
- Executable Functional Abstractionsは実行テストで抽象programをfilterするが、LLM生成候補と数学問題構造を前提とする。

本Cycleは、固定のfailure名を与えず、raw実行差分の匿名座標から反例商を形成する点を検証対象とした。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との区別 |
|---|---|---|---|---|
| A | persistence/change二視点境界生成 | 境界候補の観測 | pair recall 0、junk境界、30ms級 | 境界birthは棄却 |
| C | cycle-consistent transport対応写像 | 保存区間anchorに限定信号 | 双方向transport崩壊、自由形式0 | world operationは棄却 |
| D | relation-selective bridge link | rename writeに限定信号 | read悪化、alias過生成 | 長期memoryは棄却 |
| E | role-separated residual transport | 局所責任で探索高速化 | candidate recall 0、全面null | energy relaxationは棄却 |
| **B** | **複数反例を匿名raw failure causeで圧縮しprogram symbolへ商形成** | 今回検証 | open-form program生成 | 系列固有 |

継承知見:
- A: candidate recall成立前に誤差creditを与えるとjunkを強化する。
- C: execution failureとcorrespondence absenceを分離する。
- D: episode provenanceをそのまま保存すると圧縮にならない。
- E: candidate外ではnullを維持し、相対scoreだけで一意化しない。

## 実装

各programを全episodeへ再実行し、hidden role名を使わず次のraw failure vectorを生成した。

- 実行可否
- state match多重度
- command/state context出現数
- before→predictedの局所差分長
- predicted→afterの長さ差
- unchanged bit
- observed changeとの一致bit
- raw文字類似bit

各座標値を匿名predicateとし、成功episodeをhitせず、誤適用episodeを被覆するpredicateをgreedy hitting setで最大8個選択した。全誤適用を被覆できないprogramにはcause quotientを形成しない。

比較:
1. Executable baseline
2. Episode-index exception code
3. Anonymous failure-cause quotient

## 最大432 episode・3 seed平均

| 条件 | Executable精度/誤確定 | Episode例外 精度/誤確定 | Anonymous商 精度/誤確定 |
|---|---:|---:|---:|
| 既知 | 0.6889 / 0.0278 | 0.6889 / 0.0278 | **0.6889 / 0.0000** |
| 未知語順 | 0 / 0 | 0 / 0 | 0 / 0 |
| 未知語彙 | 0 / 0 | 0 / 0 | 0 / 0 |
| 入れ子 | 0.6889 / 0.0278 | 0.6889 / 0.0278 | **0.6889 / 0.0000** |
| 主語省略 | 0 / 0 | 0 / 0 | 0 / 0 |
| 別状態表現 | 0 / 0 | 0 / 0 | 0 / 0 |
| 複数文 | 0.6889 / 0.0278 | 0.6889 / 0.0278 | **0.6889 / 0.0000** |

## 判定

**中核仮説は反証。既知surface内の誤確定抑制と例外code圧縮だけ限定支持。**

### 限定支持1: 既知条件のwrong commitを0へ抑制

既知・入れ子・複数文で、accuracy 0.6889を維持しつつwrong commitを0.0278から0へ低下させた。

ただし、これはprogramが実行後に生成するraw failure vectorが既知の誤適用patternへ一致した場合に棄却した効果であり、意味role形成ではない。

### 限定支持2: Episode例外codeより短い

- Episode-index exception: 12637 bits
- Anonymous quotient: 12309.3 bits
- cause predicate: 平均 4.67 個、65.3 bits

episode番号を個別保存するより約2.6%短縮した。

### 反証1: Executable baselineより総記述長が長い

- Executable: 9208 bits
- Anonymous quotient: 12309.3 bits

反例表現を改善しても、baselineより約33.7%大きい。絶対MDL利得は負であり、program symbol圧縮として採用できない。

### 反証2: Program統合は0

- 保存program: 32
- merge: 0
- 匿名cause: 4.67

同じsuccess集合とcause quotientを共有するprogramがなく、failure cause商はprogram libraryを圧縮しなかった。

### 反証3: 未知形式candidate recallは全て0

未知語順・未知語彙・主語省略・別状態表現のcandidate execution recallは全方式0。匿名failure causeは既存候補の誤適用を抑えるだけで、候補外programを生成しない。

### 反証4: 匿名causeは意味causeではない

形成されたpredicateはraw match数・差分長・一致bitであり、object/relation/value/scope/goalを表現しない。異なる意味原因が同じ数値vectorへ潰れる可能性が残る。

### 見かけ上の自由日本語得点

入れ子・複数文は学習済みcommand substringをそのまま含む。0.6889はscope理解や構成的一般化の証拠ではない。

## 資源量

- Anonymous model: 38939 bytes
- Executable model: 38905 bytes
- programs: 32
- raw candidates: 432
- cause predicates: 4.67
- training: 0.01939 sec
- inference: 0.05315 ms/example
- Peak RSS: 112064 KiB（Python runtime込み）
- complexity:
  - proposal `O(NC²)`
  - behavior matrix `O(PN)`
  - predicate induction `O(PND)`
  - greedy hitting set `O(PKW)`
  - inference `O(PL)`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列B固有の進展

Program symbol形成を次の11段階へ更新する。

1. Clause候補生成
2. 局所実行可能性
3. 誤適用反証
4. Intervention outcome
5. Numerical rank basis
6. Multi-view separation
7. Held-out reversible reconstruction
8. Positive/negative witness joint coding
9. **Anonymous reusable failure-cause quotient**
10. Open-form role proposal
11. Hierarchical MDL library consolidation

今回、第9段階はepisode-index例外より短い反例codeとwrong commit抑制として限定成立した。しかしprogram統合・絶対MDL・未知形式生成は成立しなかった。

最大の新知見:

> 匿名failure quotientは既知programの安全な棄却器にはなり得るが、意味symbolやprogram生成器ではない。反例圧縮と役割創発を同一視してはいけない。

## 他系列へ返す知見

- A: object/value候補の誤束縛を匿名failure vectorで抑制できても、boundary recallは増えない。
- C: null transportの原因商は誤operationの棄却には使えるが、対応写像を生成しない。
- D: bridge linkの誤伝播を少数failure predicateで抑制できても、alias同値性証明にはならない。
- E: factor swapの残差vectorをcause quotientへ圧縮しても、role候補生成と絶対energy改善を別gateにする必要がある。

## 次の仮説

**Bidirectional Failure–Success Role Factors from Contrastive Program Transport**  
（contrastive program transportからの双方向failure–success role因子）

次はfailureだけを圧縮しない。

1. 同一programを異なるepisodeへtransport
2. 成功episodeと失敗episodeのraw差分を対で保持
3. 一因子だけswapしたとき、success↔failureが反転する最小座標集合を抽出
4. cross-surfaceで同じ反転を示す因子だけ匿名role候補へ昇格
5. role候補から新しいprogram boundary/bindingを再生成
6. candidate recall、wrong commit、absolute MDLを独立gate化
7. baselineより短く、未知形式recallを増やす場合だけ採用

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
