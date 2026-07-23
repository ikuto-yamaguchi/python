# 系列B Cycle 034

## 仮説

**Executable Scope Programs from Repair-Induced Probe Consequence Predictions**  
（repair誘発probe結果予測による実行可能scope program）

Cycle 033の静的scope codeは全主要入力でほぼ同じrepairを展開し、候補entropyを抑えられなかった。今回は静的codeを廃止し、repair適用後の局所結果だけからsuccessを予測する深さ2以下のdecision DAGを誘導した。

利用した結果特徴は、command内value再現、object候補のbefore/command内存在、inverse restoration、non-target保存、置換幅差、repair前後の予測差、value長である。Induction 40例、独立probe 20例、final testは別seed。final testのafter/futureはscope生成・repair展開・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | command-state共同創発transition cell | 時間予測状態・turn再起動 |
| C | command-coupled intervention fiber | 因果state support・world transition |
| D | tri-view shared-generator memory cycle | 長期memory・read/write閉路 |
| E | command-state coupled energy fiber | energy固定点・work曲率 |
| **B** | **repair適用可否を予測する最小実行scope DAGと共同MDL** | 今回の固有対象 |

## 3 seed平均

| 条件 | Graph pair/候補 | Global pair/候補 | Executable pair/候補 | Executable精度 |
|---|---:|---:|---:|---:|
| 既知 | 0.0667 / 9.47 | 0.1000 / 21.20 | 0.0667 / 12.20 | 0 |
| 未知語順 | 0.0667 / 9.80 | 0.1667 / 21.33 | 0.0667 / 13.53 | 0 |
| 未知語彙 | 0.0667 / 8.73 | 0.1333 / 19.83 | 0.1000 / 11.90 | 0 |
| Rename | 0 / 9.13 | 0 / 20.43 | 0 / 11.80 | 0 |
| 別状態表現 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| 入れ子 | 0.0667 / 9.80 | 0.0667 / 24.53 | 0.0667 / 13.43 | 0 |
| 主語省略 | 0 / 2.93 | 0 / 5.23 | 0 / 3.53 | 0 |
| 複数段落 | 0 / 9.80 | 0 / 27.27 | 0 / 16.10 | 0 |

追加診断:

- Program: 32
- Repair: 13
- Executable scope DAG: 2
- Predicate: 2
- Scope学習例: 112
- 既知repair展開: 2.0
- モデルサイズ: 4,195 bytes
- 学習時間: 0.1012秒
- 既知推論: 9.35 ms/example
- 複数段落推論: 56.57 ms/example
- Peak RSS: 111,960 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

独立probeから平均2個のscope DAGが形成され、outcomeをshuffleするとrepair・DAGはいずれも0へ消失した。DAG形成自体は正しい独立観測対応に依存している。

既知候補数はGlobal 21.20からExecutable 12.20へ、複数段落は27.27から16.10へ減少した。静的scope codeより、実行結果予測はrepair展開を部分的に抑制できた。

しかし既知pair recallはGlobal 0.1000からExecutable 0.0667へ低下しGraphと同値、未知語順も0.1667から0.0667へ低下した。未知語彙だけ0.0667から0.1000へ極小増加したが、execution accuracyは全条件0である。

> **実行可能性を予測するscope programは候補entropyを削減できるが、repairが意味programでないため正候補も同時に削除する。**

採用predicateは局所結果を使うが、候補object/value境界が不正確なため、object identity、relation、operation、goal、主語省略focusを表していない。Rename、別状態表現、主語省略、長文へのsemantic transferは0で、階層文法・概念再利用も未成立。

## MDL

- Literal baseline: 約58,741 bits
- Executable scope: 8,988 bits

記述長は短いがexecution accuracyが0であり、短い失敗programを保存しただけである。説明長と予測性能の均衡条件は未達。

## 先行研究との差

2025年のdecision-tree policy synthesisは離散化済みpredicateとblack-box環境・仕様のもとでtrace-based pruningを行う。2026年のproperty-guided synthesisやcounterexample-guided specification inferenceも検証可能property、program sketch、oracleを前提とする。本実験は生の日本語から生成された不完全repairについて局所consequenceからscope programを誘導したが、正しいprogram candidate不在のため既存合成法の前提を代替できなかった。

## 計算量

- Program induction: `O(NK_oK_v)`
- Near-miss repair: `O(VHL)`
- Predicate DAG探索: `O(RF²V)`
- 推論: `O(TL² + kTRF)`
- Program上限32、候補上限48、repair上限4、DAG深さ2

1GB未満は達成。既知5ms未満は未達、複数段落は約56.6msで弱いスマートフォンCPU条件も未達。実機未検証。

## 系列B固有の進展

> **静的surface scope codeより、repair後の局所consequenceを実行するscope DAGの方が候補数を抑制できる。しかしcandidate birthがsemanticでない限り、実行scopeは正候補まで削りaccuracyを回復しない。**

## 他系列へ返す知見

- A: transition cellのscopeはswap後のforward/inverse consequenceで監査すべきだが、cell候補birthが先。
- C: command-state fiberも介入可能性だけでなく、現在commandとのbinding consequence予測が必要。
- D: memory cycleの起動scopeに局所結果DAGを使うのは、shared generatorがsemantic addressを形成した後に限定すべき。
- E: energy gateは候補数削減には効くが、正候補不在では誤削除か全面棄権へ退化する。

## 次の仮説

**Joint-Born Variable Productions from Command–State Contrastive Swap Grammars**  
（command-state contrastive swap文法による共同創発variable production）

1. 一つのlatent productionからstate target区間・command value区間・object区間を共同生成
2. Command value swapに応じてstate rolloutも同じ値へ変化することを要求
3. Object swapではtarget区間だけが切り替わることを要求
4. 複数swapで再現するproductionだけ匿名variable化
5. Production grammar・probe grammar・residual errorの共同MDLを最小化
6. Joint-born／factorized／shuffled swap／repair-scopeを比較
7. Pair recall・execution accuracy・candidate entropyを同時評価
8. Rename・別状態表現でvariable productionの転移を監査
9. 主語省略では前turn productionを再起動

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
