# 系列B Cycle 028 研究報告

## 仮説

**Counterfactual Test Programs from Competing Binding-Graph Output Disagreements**  
（競合binding graphの出力不一致からの反実仮想test program）

Cycle 027では、positive / wrong / noexec witnessを分離し約393個のnegative cutを形成したが、同じ入力で競合するtriangleが入力surface特徴を共有したため、tieを一件も解消できなかった。

今回は入力surfaceからcutを作らず、各triangleが予測した`after`から次のtest outcomeを生成した。

- 変更位置bucket
- 変更外区間の保存
- 補助状態の保存
- inverse reconstruction可否
- 変更値の出力内再現
- 変更幅・変更shape
- 競合出力間で一意になる予測test

学習時のpositive witnessで再現しwrong witnessで崩れるtestだけをtriangleへ付与し、held-out入力上の競合出力を選択できるか検証した。

## 先行研究整理

- NeurIPS 2025のProgram Synthesis via Test-Time Transductionは、test入力上のprogram出力差を使い有限仮説集合をactiveに絞り込む。ただし外部LLMによるtest output oracleと既定program classを前提とする。  
  https://proceedings.neurips.cc/paper_files/paper/2025/hash/35678513540026a9e3bf0d49d7e6f624-Abstract-Conference.html
- CEGISでは非同値programを区別するcounterexample oracleが中心となるが、仕様・候補program・検証器が定義済みである。  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5597726/
- 2025年のbottom-up memory mutation synthesisはobservational equivalenceを副作用付きprogramへ拡張する必要性を論じるが、対象言語とmemory semanticsは既定である。  
  https://2025.ecoop.org/details/ecoop-2025-technical-papers/11/Bottom-up-Synthesis-of-Memory-Mutations-with-Separation-Logic

今回の課題は、生の日本語からprogram・test・観測可能な差を同時に生成するさらに上流の問題である。

## 最新系列との重複表

| 系列 | 最新中心 | Bで棄却・分離した領域 |
|---|---|---|
| A | 介入応答kernelによるroute identity | 談話予測状態・能動推論 |
| C | Outcome-blind source-only witness transport | 因果state-variable identity |
| D | 時間横断予測必要性によるendpoint birth | 長期memory・再固定化 |
| E | Outcome非参照prospective residual field | Energy・attractor |
| **B** | **競合programの予測出力差からtestを生成し、可逆実行とMDLで選択** | 今回の固有対象 |

## 実験条件

- seed: 1 / 7 / 19
- train size: 48 / 144 / 288
- test: 24例 / split / seed
- endpoint上限: 32
- triangle上限: 64
- triangle当たりtest上限: 6
- ablation:
  1. Graph
  2. Counterfactual test
  3. MDL-gated test
- 自由日本語条件:
  - 既知
  - 未知語順
  - 未知語彙
  - Rename
  - 別状態表現
  - 入れ子
  - 主語省略
  - 複数段落

Hidden object・field・valueラベルは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Graph accuracy / pair recall | Test accuracy / pair recall | MDL accuracy / pair recall |
|---|---:|---:|---:|
| 既知 | 0.0000 / 0.0278 | 0.0000 / 0.0278 | 0.0000 / 0.0278 |
| 未知語順 | 0.0000 / 0.0139 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| 未知語彙 | 0.0000 / 0.0139 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| Rename | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 入れ子 | 0.0000 / 0.0139 | 0.0000 / 0.0139 | 0.0000 / 0.0139 |
| 主語省略 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Triangle: 64
- Test program outcome: 590
- Raw候補: 1,900
- Witness audit: 2,472
- 既知平均競合出力: 9.56
- 既知平均test outcome: 66.89
- 全split commit率: 0
- MDL description: 63,488 bits

## 判定

**中核仮説は強く反証された。**

### 約590個のtest outcomeがtieを一件も解消しない

Graph / Test / MDLは全splitでaccuracy・commit率・pair recallが完全同一だった。

既知入力では平均9.56個の異なるafter候補と66.89個のtest outcomeが生成されたが、program間score差は生じず全面棄権した。

### Test outcomeがendpointの自己記述へ退化

今回のtestは各候補出力から生成される。

しかし競合triangleの多くは、同じstate endpointへ異なるvalue spanを挿入するため、以下を共有する。

- 同じ変更位置
- 同じnon-target保存
- 同じinverse可否
- 同じ変更幅・shape
- 変更値が出力に存在するという自明な再現

> **Program出力からtestを作っても、競合programが同じ出力構造を共有する場合、そのtestはprogram identityを識別しない。**

### 観測可能な外部差ではない

CEGISやtest-time transductionで有効なのは、候補programが異なる観測可能結果を予測し、その結果をoracleまたは実環境で確認できる場合である。

今回のtestは候補自身の局所構造から計算できる内部整合性であり、future observation、別入力、介入結果といった独立観測ではない。そのため全候補が自己整合的に通過した。

### Candidate recallも低下

既知pair recallは0.0278、未知語順・未知語彙・入れ子は0.0139、Rename・別状態表現・主語省略・複数段落は0だった。

正しいprogram選択以前に、object/value binding候補が安定していない。

### MDLは短縮するが能力0

MDL descriptionは63,488 bitsまで短縮したが、execution accuracyは0のままだった。

今回もMDLは、意味を持つtest grammarではなく、短く保存可能な自己整合test libraryを選択した。

## 反証条件

仮説支持には最低限次が必要だった。

1. Test方式がGraph方式よりcommit coverageを増やす
2. Wrong commitを増やさずexecution accuracyを改善する
3. 競合triangle間でtest outcomeが異なる
4. Held-out観測で正triangleのtestだけが再現する
5. Rename・別状態表現・主語省略でpair recallまたはexecution coverageが増える
6. Test metadata込みMDLが短く、同時に能力が向上する

今回はすべて未達。

## 探索爆発抑制

- Endpoint上限32
- Triangle上限64
- Object候補3 / value候補6
- Triangle当たりtest 6
- 競合出力を同一文字列で集約
- Test comparisonはheld-out入力ごとの候補集合内だけ

推定計算量:

- 候補生成 `O(NL²)`
- Witness監査 `O(NKₒKᵥ)`
- Test誘導 `O(TF)`
- Disagreement選択 `O(C²F)`
- 推論 `O(TL²)`

## 資源量

- Model: 8,877 bytes
- Training: 0.087309 sec
- Inference:
  - 既知: 4.470 ms/example
  - 入れ子: 8.486 ms/example
  - 複数段落: 17.965 ms/example
- Peak RSS: 112,224 KiB（Python runtime込み）

1GB未満は達成した。既知条件は5ms未満だが、入れ子・複数段落と弱いスマートフォン実機検証は未達。

## 系列B固有の進展

研究段階を更新する。

1. Surface candidate
2. Reversible anchor
3. Role-exchange seed
4. Executable binding triangle
5. Surface negative witness――反証
6. **Output-internal counterfactual test――今回反証**
7. Cross-input discriminating experiment
8. Relation・scope-conditioned executable grammar
9. MDL consolidation

核心的知見:

> **競合programの出力差からtestを生成するだけでは不十分である。Testは候補自身から自動的に成立する内部整合性ではなく、別入力・将来観測・介入によってprogramごとに異なる外部予測を生じさせる必要がある。**

## 他系列へ返す知見

- A: Commitment routeの自己応答ではなく、次turnの独立観測差を生む介入をtest化する必要がある。
- C: Source-only transport候補は、別target入力で異なるcounterfactual transitionを予測する場合にのみ識別可能。
- D: Memory endpointの自己再構成ではなく、別session queryへの異なる予測をcoalition testにする必要がある。
- E: Candidate自身のenergy低下は自己整合的なので、別rolloutで異なる不一致を生むexperimentが必要。

## 次の仮説

**Cross-Input Discriminating Experiments from Program-Composed Probe States**  
（program合成probe stateによる入力横断識別実験）

次は同一入力内の候補出力をtest化しない。

1. 競合triangle pairを抽出
2. 両triangleが異なる結果を返す最小probe beforeを合成
3. Probe commandを各triangleの保存contextから生成
4. Trainingの別episodeをoracleとしてprobeに近い観測を探索
5. 一方だけがforward / inverse / non-targetを満たす場合にtest採用
6. Testが存在しないtriangle pairはobservationally equivalentとして統合またはunknown保持
7. Test集合とtriangle libraryの共同MDLを評価
8. Execution accuracy・commit coverage・wrong binding・probe数を主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
