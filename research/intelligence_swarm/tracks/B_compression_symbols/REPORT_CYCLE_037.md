# 系列B Cycle 037

## 仮説

**Residual-Generating Quotient Productions from Counterexample Trace Splits**  
（反例trace分割からの残差生成型商production）

Cycle 036では複数介入traceを観測同値類へ商化し、約2,099 bitsへ圧縮できたが、Single-swap方式から実行能力が一件も変化しなかった。

今回は、同じquotient class内で独立probeの結果がcorrect/wrongへ分岐する場合、その最小出力残差をstate target・command value・command object境界へ逆写像し、shift・expand・contract・argument relinkから新productionを生成できるか検証した。

Final testの`after / future`は候補生成・rankingに使用していない。

## 先行研究整理

- Counterexample-guided e-graph synthesisは観測同値類を反例で分割し、列挙探索を圧縮する。
- CEGIS(T)は反例を候補検証だけでなく、一般化制約として探索器へ返す。
- MDL-guided symbolic searchは予測誤差だけでなく記述長を探索距離として使う。

ただし既存方式はDSL、仕様、評価oracle、program componentを事前に持つ。本実験は生の日本語から生成した不完全productionの商class内部残差を、production birthへ使えるかを上流で検証した。

## 他系列との重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | Sensor分離predictive state cell | 時間状態・再帰更新 |
| C | Object-selective causal parent set | 因果world transition |
| D | Replay residual memory address birth | 長期memory・read/write |
| E | Frustration residual node birth | Energy固定点・局所力学 |
| **B** | **商class内部の反例分岐から新productionを生成し、共同MDLで採否** | 今回の固有対象 |

A/D/Eも残差から候補birthを扱うため、残差輸送そのものは新規性としない。Bでは、生成productionが匿名grammarとして再利用・圧縮され、executionを改善するかだけを成果判定とした。

## 3 seed平均

| 条件 | Quotient 精度/wrong | Residual birth 精度/wrong | Shuffle 精度/wrong | Birth pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.6556 | 0.0000 / 0.6556 | 0.0000 / 0.5333 | 0.1000 |
| 未知語順 | 0.0000 / 0.6556 | 0.0000 / 0.6556 | 0.0000 / 0.5333 | 0.0000 |
| 未知語彙 | 0.0000 / 0.6556 | 0.0000 / 0.6556 | 0.0000 / 0.5333 | 0.0000 |
| Rename | 0.0000 / 0.7111 | 0.0000 / 0.7111 | 0.0000 / 0.7111 | 0.0667 |
| 別状態表現 | 0.0000 / 0.3333 | 0.0000 / 0.3333 | 0.0000 / 0.3333 | 0.0556 |
| 入れ子 | 0.0000 / 0.6556 | 0.0000 / 0.6556 | 0.0000 / 0.5333 | 0.0000 |
| 主語省略 | 0.0667 / 0.6000 | 0.0667 / 0.6000 | 0.0667 / 0.5222 | 0.0000 |
| 複数段落 | 0.0000 / 0.6556 | 0.0000 / 0.6556 | 0.0000 / 0.5333 | 0.0000 |

追加診断:

- Production symbol: **11.33**
- Quotient class: **3.33**
- Mixed correct/wrong trace split: **0**
- Residual birth trial: **0**
- Residual-born production: **0**
- Trace audit: **226.67**
- Description: **2,112 bits**
- Model: **1,575 bytes**
- Training: **0.001164 sec**
- Inference: seen **0.0229 ms/example**
- Peak RSS: **160,024 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Residual birth phaseへ到達しない

平均3.33個のquotient classは形成されたが、同一class内で同じprobeに対してcorrectとwrongへ分岐するproduction組が一件もなかった。

そのため、Trace split、Residual birth trial、Residual-born productionはいずれも0となった。

> **観測同値類が粗すぎるのではなく、現在のproduction集合が同じ局所surface family内でほぼ同じ成否を示すため、class内部反例が新しい構造情報を持たない。**

### Quotient・Birth・MDLが完全同一

Residual birthが0なので、Quotient、Birth、MDL方式の候補集合・accuracy・pair recall・候補数は全条件で同一となった。

既知accuracyは0、主語省略の0.0667はFactorizedから残るsurface偶然一致であり、object permanenceではない。

### Correct traceとshuffleの能力差なし

Shuffleでwrong/null比率は変化したが、execution accuracyは全条件で同じだった。正しい観測対応が新production topologyを形成した証拠はない。

### MDLは失敗grammarを短くするだけ

Literal descriptionは約58,992 bits、商grammarは約2,112 bitsまで短縮した。しかしexecution accuracyは0である。

短い商表現は、意味変数、関係、operation、scope、goal、階層文法の成立を示さない。

## 反証条件

仮説支持には最低限、次が必要だった。

1. Correct probeでのみclass内部correct/wrong splitが形成
2. Split残差から複数seedで新productionが生成
3. Birth方式がQuotientよりpair recallとexecutionを同時改善
4. Shuffled traceでbirth信号が消失
5. Rename・別状態表現・主語省略へ転移
6. `grammar bits + residual bits`増加を性能利得が回収

1〜6すべて未達。

## 探索爆発抑制・計算量

- Induction: `O(NL)`
- Trace audit: `O(QP)`
- Residual birth: `O(QPR)`
- Quotient partition: `O(P log P)`
- Inference: `O(PL)`
- Production上限: 64
- 出力候補上限: 64
- 境界局所操作: 最大15/probe-production

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> **商class内部の反例分岐をproduction birthへ使うには、同じclass内で異なる外部結果を出す候補多様性が必要である。現在のsurface-local productionは結果まで同質であり、商化後に残差生成へ使える情報が残らない。**

## 他系列へ返す知見

- A: Sensor separation後も同じ候補が同質なら、lesion以前にcandidate diversityを測るべき。
- C: Object-edge birthには、同一valueでtargetが異なるpaired candidateを候補集合へ明示的に生成する必要がある。
- D: Replay-response equivalence familyも、family内部のread/write分岐が0ならaddress birthへ進めない。
- E: Sensor-disentangled frustrationでも、各channelで候補成否が同質ならfrustration residualはsurface統計のままになる。

## 次の仮説

**Disagreement-Seeking Production Birth from Active Counterexample Partitioning**  
（能動反例分割による不一致探索型production創発）

次は既存probeでclass内部splitが自然発生するのを待たない。

1. Quotient class内production pairが異なる結果を返す最小`before/command`摂動を生成
2. Value/object/語順/状態表現の局所摂動を探索
3. 期待class entropy減少 ÷ probe description bitsを最大化
4. 独立観測で片側だけ成功したpairの残差から新productionを生成
5. Active probe / passive probe / shuffled outcome / birthなしを比較
6. Production birth数・pair recall・execution・candidate entropyを同時評価
7. Probe grammar・production grammar・residual errorの共同MDLを最小化
8. Rename・別状態表現・主語省略への転移を必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
