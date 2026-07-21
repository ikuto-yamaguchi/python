# 系列B Cycle 011 研究報告

## 仮説

**Counterexample-Guided Role Boundary Refinement with Cross-Form Execution**  
（反例誘導role境界精密化と表現横断実行）

Cycle 010では、複数entity/valueへの置換監査によって既知性能を維持しながらprogram数・モデル・読み出しを約半減できた。一方、proposal recall 0.6102、precision 0.5679で、未知語順・未知述語・入れ子・主語省略・別状態表現は全て0だった。

本Cycleでは、部分span・助詞込みspan・全spanを同時保持し、次の反例で境界を拡張・縮小できるか検証した。

1. 観測afterの再実行
2. inverseによるbefore復元
3. 非対象文字列の保存
4. 複数episodeでの同一境界support
5. 境界を1文字縮小した候補とのsupport比較
6. 状態文templateを保存せず、old→new編集として別状態表現へ再実行

MDLは実行監査後のsurface alias統合にのみ用いた。

## 先行研究整理

- program synthesisでは、関数libraryと探索戦略の双方が一般化・探索効率を左右する。LAPS/DreamCoder系列は自然言語やwake-sleepを使ってlibrary/searchを学習するが、本研究は外部LLM・大規模NNを使わず、raw日本語境界を局所実行反例だけで誘導できるかを問う。  
  https://proceedings.mlr.press/v139/wong21a.html  
  https://proceedings.mlr.press/v235/palmarini24a.html
- CEGISは候補と反例検証を反復するが、verifierが候補の意味構造を識別できる仕様を持つことが前提である。  
  https://proceedings.mlr.press/v288/debauche25a.html
- nominal anti-unificationではbindingを含む一般化の存在・一意性が許容atomや変数条件に依存する。raw文字列だけでは、その条件自体を誘導する必要が残る。  
  https://arxiv.org/abs/2504.21097
- 少数の代表例でsynthesis constraintを強める研究は探索削減を示すが、正しいcandidate languageが先に存在することを仮定する。  
  https://proceedings.mlr.press/v80/pu18b.html

## 他系列との重複表

| 系列 | 最新中心機構 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | scope候補の実行後generic feedbackによる可逆修復 | 正答候補があればheld scopeを修復 | delimiterなしcandidate recall 0、逐次probe | 外部観測policyは重複のため棄却 |
| C | 匿名effect-state間の順序transition automaton | order counterfactual 0.6333、2.3KB | command cluster崩壊、context gatingなし | 因果transition形成は重複のため棄却 |
| D | boundary surprise fast stateとreplay圧縮 | 干渉後最新値0→0.3333 | event F1 0.0216、過分割 | episode境界・記憶統合は重複のため棄却 |
| E | edge介入Jacobianと局所credit | whole outcomeで引用付き候補を分離 | Jacobian追加情報0、無標識candidate recall 0 | energy/factor取得は重複のため棄却 |
| B | role境界候補をcross-episode反例で精密化 | 本Cycleで検証 | raw境界から実行programを生成できるか | 系列固有 |

継承した知見:

- A: 正答候補が無ければ修復・質問policyは救えない。
- C: whole outcomeの一致だけでoperation/roleを同定できない。
- D: surface圧縮をsemantic consolidationと混同しない。
- E: 追加probeは既存候補classを実際に分割する増分情報が必要。

## 実装と探索爆発対策

最初の実装は全共通substring×境界拡張×old/new spanを無制限に組み合わせ、300秒を超えて完了しなかった。これは探索爆発の実測反証として棄却した。

最終実装では:

- 共通span seed: 上位24
- 境界拡張: 左右各1文字
- value候補: 上位8
- old span候補: 上位8
- cross-episode bucket内監査: 最大96候補
- 推論program: 約26.7

へ疎化した。正しい候補を事前に注入してはいない。

## 実験条件

- train sizes: 30 / 90 / 180
- seeds: 1 / 7 / 19
- split: 既知、未知語順、完全未知述語、入れ子、主語省略、別状態表現2種
- ablation:
  1. cross-episodeのみ
  2. 境界拡張のみ
  3. 境界拡張＋counterexample score
- hidden entity/old/newはcandidate recall/precision評価専用で、model fit/predictの正答選択には使用しない。

## 最大180例・3 seed平均

### Proposal品質

| 指標 | Cycle 010報告値 | 本Cycle baseline | 境界refinement |
|---|---:|---:|---:|
| candidate recall | 0.6102 | 0.9037 | 0.9037 |
| candidate precision | 0.5679 | 0.2600 | 0.2600 |
| 平均候補数 | 1.0750 | 3.4833 | 3.4833 |

本Cycleのgenerator/全substring proposalはCycle 010と同一実装ではないため、Cycle間の絶対値は直接比較しない。重要なのは同一Cycle内で境界refinementがbaselineと完全同一だった点である。

### 能力

| split | cross-episode | 境界拡張 | counterexample refinement |
|---|---:|---:|---:|
| 既知 | 0.0000 | 0.0000 | 0.0000 |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知述語 | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現1 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現2 | 0.0000 | 0.0000 | 0.0000 |

### 資源

- model: 7612 bytes
- programs: 26.67
- raw candidates: 627
- counterexample rejected items: 119.67
- seen inference: 1.7488 ms/query
- seen generated execution candidates: 478.93/query
- held-order candidates: 419.20/query
- Peak RSS: 309496 KiB（Python runtime込み）
- complexity: train `O(NL² + C²)`、infer `O(PL³)`、value/old spans各8にcap
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**中核仮説は強く反証。**

### 1. 境界refinementがproposal classを分割しない

baselineとrefinedのrecall・precision・候補数が完全同一だった。共通substringを左右へ1文字拡張・縮小しても、実行制約から見れば同じold→new編集を生成するため、反例にならなかった。

### 2. 約120候補をrejectしても能力0

counterexample scoreは平均約119.7 candidate itemをrejectしたが、全splitのaccuracyは0だった。誤候補だけでなく、実行時に必要なrole情報を持たない候補classをまとめて順位付けしただけである。

### 3. 実行候補が約400〜480/queryへ再膨張

program読出しは約26.7でも、各programからentity/new/old spanを再列挙すると、既知で約478.9、未知語順で約419.2候補となった。探索爆発は学習時から推論時へ移っただけである。

### 4. 既知入力まで0へ回帰

Cycle 010の既知1.0を維持できなかった。状態templateを捨ててgeneric old→new置換へ一般化した結果、どのsubstringが状態変数の値かを決めるrelation boundaryが失われた。

### 5. 主語省略はcandidate 0

entityがcommandに現れないため、before-command共通substringからは候補生成できない。照応・談話状態なしで境界だけを精密化しても救えない。

## 系列B固有の新知見

program inductionを次の五段階へ更新する。

1. surface span proposal
2. role/relation boundary proposal
3. cross-episode execution precision
4. inference-time binding without combinatorial re-enumeration
5. MDL consolidation

Cycle 010は3と5を限定改善した。本Cycleは1の境界変形を試したが、2が存在しないため、同じ編集結果を持つ候補同値類を分割できず、4で探索が再爆発した。

> **文字境界の反例精密化だけではrole境界にならない。反例は「どのsubstringを変えたか」ではなく、「どのrelation edgeを変更し、どの非対象relationを保存したか」を区別しなければならない。**

## 他系列へ返す新知見

- A: active probe対象はsurface spanではなく、異なるrelation updateを生成する候補classに限定する。
- C: effect stateだけでなく、変更relationと非対象relation保存を独立edgeにする必要がある。
- D: replay圧縮前に、同じsurface updateが異なるrelationへ書かれていないか監査する。
- E: residual-equivalence splittingは文字境界Jacobianではなく、relation-preservation outcomeで候補を分割すべき。

## 次の仮説

**Relation-Preservation Anti-Unification with Contrastive Multi-Field States**  
（対照的複数field状態によるrelation保存反統一）

次は一対象一値の状態文をやめ、同一objectに複数の同時fieldを持たせる。

- before/afterで変わるfield
- 保存されるfield
- 別objectの同名field
- role反転したcommand
- 語順・状態表現の変更

を同時に提示し、候補programが正しい一つのrelationだけを更新し、他fieldを保存する場合のみ昇格させる。

最低成功条件:

- 既知accuracyを0から回復
- proposal precision 0.2600を改善しrecall 0.9037を維持
- 実行候補を100/query未満へ削減
- 未知語順または別状態表現を0から改善
- 主語省略は別系列D/Aの談話状態を使わず、達成不能なら明示的に分離
- 32KB未満、5ms/query未満、複数seed

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
