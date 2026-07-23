# 系列C Cycle 032

## 仮説

**Mechanism-Family Birth from Cross-Input Intervention Equivalence Classes**  
（入力横断介入同値類からのmechanism family創発）

Cycle 031では個別source mechanismのtarget境界投票と約30万件の独立probe監査を行ったが、正しい境界候補がなくdiscriminationは0だった。本Cycleでは個別mechanism多数決を棄却し、inductionで生成した境界近傍operatorを、独立probe上の三値応答（correct / wrong executable / noexec）、inverse restoration、non-target damageで同値類化した。

Final testのafter/futureはcandidate生成・family形成・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | Probe駆動transition-kernel可塑性 | 談話予測状態・時間誤差相殺 |
| B | Probe駆動symbol refinement | MDL・program symbol class |
| D | Variable-boundary read/write operator | 長期memory・再固定化 |
| E | Near-miss residual境界拡張 | Energy固定点・局所力学 |
| **C** | **外部介入結果が等価なoperator familyからtarget transitionを生成** | 今回の固有対象 |

Bのbehavioral symbol classと近いため、class形成数や既存program選択は新規性としない。Cではfamilyが未知target上で正しい状態遷移をoutcome-blind生成し、境界・介入・反実仮想へ接続するかだけを中心評価とした。

## 実験

- seed: 1 / 7 / 19
- induction 48 / independent probe 24 / final test 12件×10条件
- 固定ontology・手書きslot・辞書・RAG・外部LLMなし
- 真の局所差分の周囲±1文字からnear-boundary signatureを生成
- Signatureはold/new shape、左右相対位置bucket、old/new長、長さ差だけを保持
- Independent probe上の応答vectorが同じ2 member以上、correct probe 2件以上のclassだけfamily化
- Surface / Family / Family graph / Shuffled-probeを比較

## 3 seed平均

| 条件 | Surface | Family | Graph | Shuffle | Null率 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| 未知語順 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| 未知語彙 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| Rename | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| 別状態表現 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| 入れ子 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |
| 主語省略 | 0 | **0.5000** | 0.5000 | 0 | 0.5000 |
| 複数段落 | 0 | **0.3889** | 0.3889 | 0 | 0.6111 |
| 計画変更 | 0 | 0 | 0 | 0 | 1.0000 |
| 反実仮想 | 0 | **0.4722** | 0.4722 | 0 | 0.5278 |

追加診断:

- Operator signature: 20.67
- Mechanism family: 1.00
- Family member: 2.00
- Independent probe audit: 6,684.67
- Wrong commit: 0
- Exact old/new target-boundary recall: **0**
- モデルサイズ: 1,243 bytes
- 学習時間: 0.761 sec
- 既知推論: 0.505 ms/example
- 複数段落推論: 0.838 ms/example
- Peak RSS: 111,712 KiB（Python runtime込み）

seed別の既知accuracyは0.5833 / 0.5000 / 0.3333で、全seedでfamily 1件・member 2件が形成された。

## 判定

**一般的な因果world model仮説としては反証。全3 seedで再現した局所transition選択信号として限定支持。**

### 独立probe familyが局所実行を改善

Surfaceとshuffled-probeは全条件0だった一方、Family方式は計画変更以外でwrong commitなしのexact-after生成を示した。Shuffleで完全消失したため、信号は独立観測の正しい方向へ依存している。

### 正しいstate-variable境界は形成されていない

Exact old/new境界とvalueの組の回収率は全条件0だった。Exact afterが生成されたのは、真のvalue区間より広い文字区間を置換して同じ最終文字列へ到達したためである。

> **正しいoutcome生成と正しいstate-variable境界形成は同値ではない。**

したがってobject identity、relation、state variable、operation targetの獲得とは認めない。

### 計画・主語省略・反実仮想

- 計画変更は候補があっても全面0。撤回案と最終goalを分離できない。
- 主語省略0.5は前turn object permanenceではなく、現在turnへ偶然適用できたfamily edit。
- 反実仮想0.4722も実行世界・非実行世界の二重rolloutではなく、最終命令の局所更新。

## 反証条件

因果mechanism familyを支持するには以下が必要。

1. 全3 seedでfamily形成（達成）
2. Exact target-boundary recallの増加（未達）
3. Rename・別状態表現で内部境界も維持（未達）
4. Shuffled probeで信号消失（達成）
5. Plan revisionで旧goalと最終goalを分離（未達）
6. Counterfactualで実行・非実行worldを別rollout（未達）
7. Family除去で対応transitionだけが消える（未検証）

## 先行研究との統合

Causal abstractionでは、lossy表現でも観測・介入・反実仮想queryの整合が必要である。一般変換下のcausal representation learningでは十分な介入被覆が識別に必要であり、複数環境の不変性が因果ではなくデータ対称性を捉える場合もある。本Cycleは外部介入応答を使う点では前進したが、境界変数の識別とcounterfactual consistencyを満たしていない。

## 計算量・資源

- Signature birth `O(NL)`
- Probe response `O(QSVL)`
- Family partition `O(SQ log S)`
- Inference `O(SVL)`
- `S≤24, Q=24`
- 1GB未満・5ms未満: 小規模条件で達成
- 弱いスマートフォンCPU実機: 未検証

## 系列C固有の進展

> **独立介入応答同値類はsurface多数決より強く、全seedでwrong commitなしの局所transitionを選べた。しかし正しいoutcomeを生成してもstate-variable境界は形成されず、goal・counterfactual compositionもない。**

## 他系列へ返す知見

- A: Probe creditがstate selectionへ作用しても、内部operator境界の正しさを別評価すべき。
- B: Behavioral symbol classがexecutionを改善しても、exact variable boundaryと共同MDLが必要。
- D: 正しい最終文字列を返してもaddress境界が誤ればmemory endpointではない。
- E: Probe-nudged attractorにはcorrect outcomeだけでなく正しい境界への距離が必要。

## 次の仮説

**Boundary-Faithful Mechanism Families from Minimal Intervention Supports**  
（最小介入supportによる境界忠実mechanism family）

1. 同じafterを生成する複数境界候補を保持
2. 置換区間を1文字ずつcontract
3. Outcomeを維持する最小区間だけminimal intervention support化
4. Independent probeで同じ最小supportが再現するoperatorをfamily化
5. Family除去で対応transitionだけが失われるか監査
6. Correct probe / shuffled probe / minimizationなしを比較
7. Rename・別状態表現のexact target-boundary recallを主評価化
8. Plan revisionでは旧案と最終案のsupportを別class化
9. Counterfactualでは実行・非実行supportを別rollout化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
