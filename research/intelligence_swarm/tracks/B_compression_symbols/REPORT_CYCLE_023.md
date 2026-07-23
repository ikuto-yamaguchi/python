# 系列B Cycle 023 研究報告

## 仮説

**MDL-Gated Reversible Edit-Skeleton Grammars by Raw Derivation Anti-Unification**  
（raw導出の反単一化によるMDLゲート付き可逆edit-skeleton文法）

Cycle 022の次案だったedit graph反単一化は系列Cのtransport-map案と重複していたが、系列C Cycle 023が時間方向auditへ移行したため、本Cycleでは因果world transportではなく、**導出記述の反単一化・可逆再構成・総符号長**に限定して検証した。

raw `before / command / after` から局所edit scriptを抽出し、異なるscriptの左右contextを最小反単一化した。生成grammarは、複数episode再現、odd held-out再現、wrong抑制、正の絶対MDL利得、未知surfaceでの新candidate生成を採用条件とした。

## 先行研究整理

- Anti-unificationは複数項の最小一般化を求める基礎操作だが、通常は項・binding・演算構造が既に与えられる。
- 2026年のcommutative function付きleast general generalization研究は、代数的自由度による探索複雑性を扱う。
- Nominal anti-unification modulo equational theoriesはbindingとfreshnessを扱うが、有限atom集合などの構造制約を置く。
- Usage-based grammar inductionは短いsequence memoryとchunk再利用の有効性を示すが、人工言語上の頻度構造を利用する。
- MADILはMDLによる効率的program inductionをARCで検証するが、構造化されたpattern decompositionを前提とする。

今回の実験は、固定語彙・slot・DSLなしにraw日本語文字列からこれらの構造自体を形成できるかを反証対象とした。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な未解決 | Bとの分離 |
|---|---|---|---|---|
| A | 残差逆投影と談話carry | 主語省略pair recallを0→0.2917 | 事後観測依存・5ms未達 | active predictionは扱わない |
| C | 対称情報付きevent direction | 局所event再実行 | 因果方向が情報非対称性 | world causal graphは扱わない |
| D | write-only class / read address分離 | endpoint分離で誤読抑制 | slow class誤統合 | 長期memoryは扱わない |
| E | 環境分離energy応答 | null安全停止 | factor birth・binding崩壊 | energy dynamicsは扱わない |
| **B** | **導出edit skeletonの反単一化と絶対MDL** | 今回検証 | open-form grammar | 系列固有 |

## 実験条件

- seed: 1 / 7 / 19
- train size: 48 / 144 / 288
- test: 48例 / split / seed
- script上限: 64
- grammar上限: 32
- ablation: Exact script / Anti-unification / MDL-gated grammar
- split: 既知、未知語順、未知語彙、Rename、入れ子、主語省略、別状態表現、複数文
- Hidden object・field・valueは評価器だけで使用

## 最大288例・3 seed平均

| 条件 | Exact | Anti-unification | MDL-gated |
|---|---:|---:|---:|
| 既知 | 0.1181 | 0.1181 | 0.1181 |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知語彙 | 0.0000 | 0.0000 | 0.0000 |
| Rename | 0.2639 | 0.2639 | 0.2639 |
| 入れ子 | 0.1181 | 0.1181 | 0.1181 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0625 | 0.0625 | 0.0625 |
| 複数文 | 0.1181 | 0.1181 | 0.1181 |

追加診断:

- raw candidate: 288
- exact script: 64
- anti-unification grammar: **0**
- MDL採用grammar: **0**
- baseline description length: 19,656 bits
- MDL total description length: 19,656 bits
- unknown order / lexeme / omission candidate recall: 0

## 判定

**中核仮説は強く反証された。**

### Grammar候補が0件

全seed・最大288例で、held-out再現とwrong抑制を通過する反単一化grammarは一件も形成されなかった。異なるsurface scriptの左右contextをprefix/suffix反単一化しても、同じ局所導出を共有するsupportが不足した。固定slotを持たないraw文字列では、何を定数・変数・relation contextとして一般化すべきか決まらない。

### 能力増分が完全に0

Exact / Anti-unification / MDL-gatedは全splitで完全に同じだった。候補生成、accuracy、wrong commit、未知形式への転移のいずれにも増分がない。

### MDL gate以前に可逆導出が成立しない

総符号長は19,656 bitsから一切短くならなかった。MDL gateなしのAnti方式でもgrammarが0件であり、penaltyが厳しすぎたことが原因ではない。

> **圧縮候補を評価する前に、複数surfaceを跨いで同じ導出を再現する可逆な変数束縛が必要。単純な文字context反単一化は、その束縛を生成しない。**

### 見かけ上の得点

Rename 0.2639は学習mixtureにrename表現を含むため、同じalias surfaceの再出現である。入れ子・複数文の0.1181も学習済みcommand substringの局所再実行で、scope・目的・制約・談話構造の証拠ではない。

## 反証条件

仮説支持には、複数seedでgrammar形成、未知形式candidate recall増加、wrongを増やさないaccuracy改善、metadata込み絶対MDL利得、held-out surfaceでの新規導出が必要だった。今回は全条件を満たさない。

## 探索爆発抑制・計算量

- script上限64、pair最大2,016組
- prefix/suffix最小反単一化のみ
- reversible support 2以上、odd held-out support 1以上
- grammar上限32、MDL方式は正の絶対gainのみ採用
- proposal `O(NL²)`
- anti-unification `O(P²L)`
- audit `O(GN)`
- inference `O((P+G)L)`、`P≤64, G≤32`

## 資源量

- モデルサイズ: **48,524 bytes**
- 学習時間: **0.005833 sec**
- 推論時間: **0.025370 ms/example**
- Peak RSS: **111,608 KiB**（Python runtime込み）

1GB未満・5ms未満は制御条件で達成した。弱いスマートフォン実機では未検証。

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
10. Filler nonterminal
11. Context bisimulation――反証
12. Partial derivation homomorphism――反証
13. **Raw edit-skeleton anti-unification――今回反証**
14. Binding-before-compression induction
15. Hierarchical MDL consolidation

核心的知見:

> **文字contextの反単一化は、表面差をワイルドカードへ置換するだけで、object・value・relationの可逆bindingを作らない。MDLは成立済みの導出候補を選べても、導出意味そのものを生成しない。**

## 他系列へ返す知見

- A: 残差windowの共通部分をcell変数化しても、双方向bindingがなければ意味状態にならない。
- C: forward/reverse replayの前に、old/new valueを同一eventへ束縛する可逆表現が必要。
- D: write consequence classを圧縮する前に、query-conditioned inverse bindingを独立に成立させる。
- E: 環境不変energy responseだけでなく、candidate factorを入出力へ可逆に束縛できるかを監査する。

## 次の仮説

**Reversible Binding Seeds from Three-Way Derivation Intersections before MDL Compression**  
（MDL圧縮前の三者導出交差からの可逆binding seed）

1. command差分、before→after差分、future再出現を独立view化
2. 3 viewすべてに同じ局所文字区間が現れる場合だけbinding seed候補化
3. object側とvalue側のseedを独立保持
4. seedをswapして導出が壊れる最小反例を測定
5. source→targetとtarget→sourceの双方で再構成できるseedだけ匿名変数へ昇格
6. binding成立後に初めてanti-unificationとMDL library圧縮を適用
7. object recall・value recall・pair recall・絶対MDLを独立gate化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
