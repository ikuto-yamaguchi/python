# 系列B Cycle 035 研究報告

## 仮説

**Joint-Born Variable Productions from Command–State Contrastive Swap Grammars**  
（command-state contrastive swap文法による共同創発variable production）

Cycle 034ではrepair適用後のconsequenceを予測するscope DAGが候補数を減らした一方、正候補も同時に削除し、execution accuracyは0だった。本Cycleではrepairを先に作らず、一つのlatent productionからstate変更区間、command value区間、command object区間を共同生成し、独立probe上のvalue swapに共変するproductionを匿名variable classへまとめた。

Final testのafter/futureは候補生成・rankingに使用していない。

## 重複表

| 系列 | 最新中心 | Bで棄却・分離した領域 |
|---|---|---|
| A | turn横断command-state transition cell | 時間予測状態・再起動 |
| C | command-coupled intervention fiber | 因果state support・world transition |
| D | tri-view shared-generator memory cycle | 長期memory・read/write閉路 |
| E | command-state coupled energy fiber | Energy固定点・work loop |
| **B** | **swap共変productionの匿名variable化と共同MDL** | 今回の固有対象 |

共同生成やswap自体は他系列と重なるため新規性としない。系列Bでは、複数productionを再利用可能な匿名記号へ統合し、追加記述長に見合う実行性能を得られるかだけを中心評価にした。

## 設計

- Stateの変更区間、command value区間、command object区間を一つの相対境界productionで共同表現
- Independent probeでvalue swapを行い、prospective stateも同じ値へ変化するか監査
- old/new/object文字shapeとswap応答が同じ複数productionを匿名class化
- Factorized / Joint swap / Joint+MDL / Shuffled outcomeを比較
- 固定ontology、手書きslot、辞書、RAG、外部LLMなし

## 3 seed平均

| 条件 | Factorized 精度/wrong | Joint 精度/wrong | Shuffle 精度/wrong | Joint pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.0000/0.7444 | 0.0000/0.4556 | 0.0000/0.6222 | 0.1556 |
| 未知語順 | 0.0000/0.7444 | 0.0000/0.4556 | 0.0000/0.6222 | 0.0000 |
| 未知語彙 | 0.0000/0.7444 | 0.0000/0.4556 | 0.0000/0.6222 | 0.0000 |
| Rename | 0.0000/0.5333 | 0.0000/0.3778 | 0.0000/0.4333 | 0.0667 |
| 別状態表現 | 0.0000/0.3333 | 0.0000/0.3333 | 0.0000/0.2111 | 0.0556 |
| 入れ子 | 0.0000/0.7444 | 0.0000/0.4556 | 0.0000/0.6222 | 0.0000 |
| 主語省略 | 0.0667/0.4667 | 0.0000/0.3333 | 0.0667/0.4667 | 0.0000 |
| 複数段落 | 0.0000/0.7444 | 0.0000/0.4556 | 0.0000/0.6222 | 0.0000 |

追加診断:

- Production symbol: 15.00
- Anonymous swap class: 6.67
- 既知候補数: 2.63
- Joint description: 2053 bits
- Factorized literal description: 106285 bits
- モデルサイズ: 1603 bytes
- 学習時間: 0.001855 sec
- 既知推論: 0.0262 ms/example
- 複数段落推論: 0.0264 ms/example
- Peak RSS: 111188 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

平均6.67個の匿名classが形成され、Joint descriptionはliteral保存より大幅に短くなった。しかし既知・未知語順・未知語彙・Rename・別状態表現・入れ子・複数段落でaccuracyは0だった。主語省略ではFactorizedとShuffleが0.0667を出したがJointは0へ低下した。

Joint方式は一部条件でwrong commitを減らしたが、正答を増やさずnullへ移しただけである。

> **Swap共変性と圧縮可能性は、semantic variable productionの十分条件ではない。**

既知pair recallは0.1556だが、正しいafterは生成できない。object/value文字列が候補集合に含まれても、state target、operation、relation、scopeが正しく束縛されていない。

Correct probeとshuffleでwrong/null比率は変わったが、accuracyはどちらも0である。正しい観測がproduction topologyへ意味のある能力差を作ったとは認めない。

Joint grammarは約2053 bitsで、literal約106285 bitsより短い。しかし予測性能0であり、説明長と予測性能の均衡条件を満たさない。短い失敗programを得ただけで、概念再利用・階層文法・変数束縛の証拠ではない。

## 反証条件

1. Joint-bornがFactorizedよりexecution accuracyを改善
2. Correct swapがshuffleよりaccuracyを改善
3. Pair recallとexecutionが同時に増加
4. Rename・別状態表現・入れ子へ転移
5. 追加symbol bitsを予測性能で回収

すべて未達。

## 探索爆発抑制・資源量

- Production induction `O(NL)`
- Probe swap監査 `O(QPV)`
- Equivalence class形成 `O(P log P)`
- 推論 `O(PL)`
- Production上限48
- Candidate上限64

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> **State・command value・object境界を共同生成してswap応答で匿名class化しても、surface-relative boundaryの共有に留まり、semantic variableにはならない。MDLは短いclassを選べても、正しいprogram birthを保証しない。**

## 他系列へ返す知見

- A: command-state共同cellでも、swap共変だけでは時間状態identityにならない。
- C: command-coupled fiberはexact target boundaryとoperation bindingを別途監査すべき。
- D: tri-view共同generatorも、三視点を共同生成した事実だけでsemantic addressとは判定できない。
- E: command-state work closureはshuffleとaccuracy差がなければsurface constraintである。

## 次の仮説

**Intervention-Quotient Grammar from Minimal Swap-Commuting Diagrams**  
（最小swap可換図式による介入商文法）

1. Value swap、object swap、語順swapの3介入を生成
2. 介入順序を変えても同じprospective stateへ到達する可換図式を監査
3. 可換しないproductionを別classへ分割
4. 最小可換diagramだけを匿名variable／operation候補化
5. Diagram bits＋production bits＋residual errorの共同MDLを最小化
6. Correct diagram／shuffled edge／single-swap／factorizedを比較
7. Exact boundary、execution、candidate entropyを同時評価
8. Rename・別状態表現・主語省略で商classの転移を監査

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
