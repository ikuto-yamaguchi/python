# 系列B Cycle 038

## 仮説

**Disagreement-Seeking Production Birth from Active Counterexample Partitioning**  
（能動反例分割による不一致探索型production創発）

Cycle 037ではquotient class内部のcorrect/wrong分岐が0件で、残差birth phaseを開始できなかった。今回は既存probeで自然分岐を待たず、production pairが異なる結果を返す最小入力摂動を能動合成した。

各候補pairに対してvalue交換、object交換、prefix/suffix/wrapper摂動を生成し、`期待class分割 / probe記述bit`を最大化するprobeだけを選択した。独立probe outcomeで片側だけ成功した場合、そのwinner/loser差を境界mutationへ返した。Final testのafter/futureはcandidate生成・rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Bで成果対象にしない領域 |
|---|---|---|
| A | Object disagreement queryによるpredictive state birth | 時間状態・再帰更新 |
| C | Paired-world co-segmentation | 因果world・object support |
| D | Active replay queryによるmemory address birth | 長期memory・read/write閉路 |
| E | 直交constraint queryによるsensor birth | Energy固定点・局所力学 |
| **B** | **候補programの分割情報量/bitを最大化するquery grammarとproduction共同MDL** | 今回の固有対象 |

## 3 seed平均

| 条件 | Accuracy | Wrong commit | Pair recall | 候補数 |
|---|---:|---:|---:|---:|
| 既知 | 0 | 0.9444 | 0.2889 | 3.53 |
| 未知語順 | 0 | 0.9444 | 0 | 3.53 |
| 未知語彙 | 0 | 0.9444 | 0 | 3.53 |
| Rename | 0 | 0.7889 | 0.1111 | 3.60 |
| 別状態表現 | 0 | 0.3333 | 0.0889 | 1.12 |
| 入れ子 | 0 | 0.9444 | 0 | 3.53 |
| 主語省略 | 0 | 1.0000 | 0 | 2.58 |
| 複数段落 | 0 | 0.9444 | 0 | 3.53 |

追加診断:

- Production symbol: 18.33
- Active query: 53.00
- Correct disagreement: 1.67
- Shuffled disagreement: 0.33
- Residual-born production: 0
- Active grammar: 4,771 bits
- Factorized literal: 177,077 bits
- Model: 1,715 bytes
- Training: 0.2483 sec
- Inference: 0.0337 ms/example
- Peak RSS: 112,008 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### 能動probe自体は不一致を生成した

各seedで平均53件のqueryを選択し、正しいoutcomeでは平均1.67件の片側成功disagreementが得られた。Shuffleでは0.33件へ低下したため、極小ながら正しい独立観測に依存する分割信号は存在する。

### Production birthは0

Winner/loserが分かれた局所probeから、state/value/object境界を±1 bucket変異させたが、複数probeで再利用できる新productionは一件も形成されなかった。

> **不一致を生むqueryは作れても、その不一致残差を再利用可能なvariable productionへ変換する原理は得られなかった。**

### 能力増分は完全に0

Factorized、Active、Birth、MDLは全条件でaccuracy・wrong・pair recall・候補数が同一だった。Active creditも候補順位を変えず、Birth方式は候補集合自体を変えなかった。

既知条件ではpair recall 0.2889まで候補内にobject/value文字列が存在するが、execution accuracyは0、wrong commitは0.9444である。state target、relation、operation、scope、goalが束縛されていない。

### MDL

Active grammarは約4,771 bitsで、literal 177,077 bitsより短い。しかしaccuracy 0であり、短い失敗grammarを得ただけである。説明長短縮をsemantic symbol、概念再利用、階層文法の成立とは認めない。

## 反証条件

1. Active probeがpassiveよりclass splitを増やす: 極小達成
2. Correct probeがshuffleよりdisagreementを増やす: 達成
3. Split残差から複数seedで新productionが生まれる: 未達
4. Birth方式がpair recallとexecutionを同時改善する: 未達
5. Rename・別状態表現・主語省略へ転移する: 未達
6. Production追加bitを予測利得で回収する: 未達

## 資源量・探索爆発抑制

- Induction: `O(NL)`
- Pair query synthesis: `O(QP²UL)`
- Boundary mutation: `O(DR)`
- Inference: `O(PL)`
- Production上限64、pair監査160/input、query pool 24/pair、出力候補64

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> **商class内部に自然な分岐がなくても、能動query合成で候補pairの外部不一致を極小ながら作れる。しかしsurface-local候補間の不一致は、再利用可能な記号・変数・program境界を与えない。**

## 他系列へ返す知見

- A: disagreement queryを作るだけではobject-state cellにならず、query後の共同境界birthが必要。
- C: paired-world queryはobject/supportを別候補から選ぶのではなく共同分節へ直結させるべき。
- D: active replayでaddress pairを分けても、read/write共通生成器がなければ新addressは生まれない。
- E: 直交queryの応答差はsensor候補の必要条件だが、surface bucket差をsensorと誤認しないlesion反証が必要。

## 次の仮説

**Co-Segmentation Grammar Birth from Paired Disagreement Worlds**  
（不一致paired worldの共同分節によるgrammar創発）

次は既存production pairを分けた後に境界を局所mutationしない。

1. Active queryと元probeをpaired worldとして同時整列
2. 変化したcommand区間とstate区間を共同分節
3. Object/value/targetを別々に候補化せず、一つのlatent productionとして生成
4. 複数paired worldで同じ対応写像を再現するproductionだけ保持
5. Active／passive／shuffle／factorized co-segmentationを比較
6. Production grammar・query grammar・residual errorの共同MDLを評価
7. Exact boundary、pair recall、execution、candidate entropyを同時評価
8. Rename・別状態表現・主語省略への転移を必須化

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
