# 系列A Cycle 038 研究報告

## 仮説

**Sensor-Causal State Cells from Selective Channel Lesions and Object-Target Birth**  
（選択的channel lesionとobject-target新生によるsensor因果状態cell）

Cycle 037ではvalue swap・object swap・future・non-target保存・inverseの3-of-5多数決により既知surface精度が上がったが、channelをepisode間でshuffleしても能力が同一で、object sensor supportは0だった。

本Cycleではsensor数の追加を棄却し、系列A固有の因果要件へ進んだ。

1. 各cellからsensorを一つずつlesionし、対応するprobe成功だけが低下することを要求
2. Object-swap失敗時の正target位置残差をstate supportへ輸送し、object→target edge候補を新生
3. Object sensorが必要で、かつ2種類以上のsensor lesionがcell採用数を低下させる場合だけsensor-causal cell化
4. Correct object residualとshuffled object residualを比較
5. Final testのafter/futureはcandidate生成・rankingに不使用

## 他系列との重複排除

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B Cycle 037 | Counterexample trace splitによるproduction birth | MDL・記号grammar |
| C Cycle 037 | Paired-world object→support edge birth | 因果world graph・causal parent |
| D Cycle 037 | Replay-response equivalence address family | 長期memory・read/write閉路 |
| E Cycle 037 | Selective sensor lesion synergy hyperedge | Energy fixed point・非加法constraint |
| **A Cycle 038** | **sensor lesion profileを持ち、次観測へ再起動する時間状態cell** | 今回の固有対象 |

Cもobject→support edgeを扱うため、edge形成そのものは系列Aの成果としない。Aではobject edgeがfuture継続・inverse・non-target予測と共に時間状態cellを形成し、lesionで対応能力が選択的に落ちるかを中心評価にした。

## 先行研究整理

- *Learning Long-Range Dependencies with Temporal Predictive Coding* (2026) はtPCと近似RTRLを組み合わせ、局所・並列的credit assignmentで長距離依存を扱うが、15M parameter RNNのstateと結合は既定である。https://arxiv.org/abs/2602.18131
- *Object-Centric World Model for Language-Guided Manipulation* (2025) はlanguage-conditioned object slot上で将来状態を予測し、diffusion型より計算効率を高めるが、slot attentionでobject表現を先に与える。https://openreview.net/forum?id=CMItmXqrue
- *Does Representation Intervention Really Identify Desired Concepts and Elicit Alignment?* (2025) は、介入で期待挙動が得られてもfaithful concept位置を同定したとは限らないことを示す。今回も出力一致とsensor-causal state identityを分離して監査した。https://openreview.net/forum?id=htUGMDzk2A

既存研究との差は、network state・object slot・concept locationを与えず、生の自由日本語からcell候補とobject-target edgeを生成し、選択的lesionで内部状態の因果必要性を監査する点にある。

## 3 seed平均

| 条件 | Separated 精度/wrong | Object-birth 精度/wrong | Lesion-causal 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0.5926 / 0.4074 | 0 / 0 | 0 / 0 | 0 / 0 |
| 未知語順 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 未知語彙 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 入れ子 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 主語省略 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 複数段落 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 計画変更 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |
| 反実仮想 | 0 / 1.0000 | 0 / 0 | 0 / 0 | 0 / 0 |

追加診断:

- Separated rule: 3.67
- Correct object birth: 1.00
- Object edge candidate: 3.33
- Lesion profileを持つcell: 2.00
- Lesion-causal採用rule: 0
- Shuffled lesion profile cell: 5.00
- Probe audit: 160
- Object birth trial: 136
- Model: 627 bytes
- Training: 0.01475 sec
- Seen inference: 0.00558 ms/example
- Paragraph inference: 0.00593 ms/example
- Peak RSS: 111,136 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Object residualから境界候補は形成

Correct paired object residualから平均1件のobject-target境界候補が生成された。Cycle 037のobject sensor support 0から、object変更先の残差をcandidate birthへ戻す段階には進んだ。

### Object sensorを要求すると全ruleが消失

Object-birth方式・Lesion-causal方式とも、最終採用ruleは0件だった。新生境界は単一probe上ではobject-swap targetを再構成したが、複数probeでvalue swap・future・inverse・non-target保存と共同再現しなかった。

> **正しいtarget位置残差をstate境界へ輸送しても、object identity・value binding・時間継続を共同生成するcellにはならない。**

### Lesion profileは存在するが能力cellではない

平均2件のcandidateにsensor lesion profileが記録された。しかしobject sensorを必須にし、2 sensor以上が選択的必要であることを要求すると採用ruleは0になった。

Shuffleでは平均5件のlesion profile candidateが生じた。したがってlesion変化だけでも正しいsensor対応の証拠にはならず、surface候補数や偶然の閾値変化で作れる。

### Cycle 037の局所陽性を降格

Separated baselineは既知で0.5926を再現したが、wrongも0.4074で、自由日本語条件はaccuracy 0・wrong 1.0だった。Object選択性を要求すると、この既知surface信号は全面消失した。

Cycle 037の陽性は、objectを持つ予測状態ではなく、value位置・inverse・non-target文字列保存によるsurface editとして降格する。

### 時間能力

- 主語省略のobject permanence: 未成立
- 次turn再起動: 未成立
- 明示的な状態終了・切替: 未成立
- 計画変更の撤回goal抑制: 未成立
- 反実仮想worldの並列保持: 未成立
- 長距離・複数段落の時間抽象化: 未成立

## 反証条件

仮説支持には以下が必要だった。

1. Correct object residualでのみobject-target edgeが形成される
2. Object sensor lesionでobject-swap能力だけが選択的に低下する
3. Future lesionで継続予測だけが低下する
4. Object-birth／Lesion-causalがSeparatedよりwrongを減らしつつaccuracyを維持または向上する
5. 未知語順・未知語彙・主語省略でobject targetが転移する
6. Shuffleでは上記profileが消える

1は候補birthとしてのみ部分達成、2〜6は未達。

## 資源量・必要計算量

- Candidate生成: `O(L²)`、最大64候補
- Object residual transport: `O(QC)`
- Selective lesion audit: `O(QCK)`、`K=5`
- 推論: `O(R)`
- Model: 627 bytes
- Training: 0.01475 sec
- Inference: 約0.006 ms/example

1GB未満・5ms未満は小規模条件で達成した。ただし採用rule 0による小型化であり、弱いスマートフォン上の知能成立を示さない。実機検証は未実施。

## 系列A固有の進展

> **Sensor多数決の局所陽性を、object選択性と選択的lesionで厳密に降格した。Object残差は境界候補を生めるが、後付けedgeでは時間状態cellを形成しない。**

## 他系列へ返す知見

- B: Productionの出力一致だけでなく、構成要素をlesionした際に対応能力だけが崩れるかをMDL採用条件へ加えるべき。
- C: Paired-world residualからobject edge候補が生まれても、複数sensorとの共同再現がなければcausal parentではない。
- D: Memory address familyもread/write node lesionで対応閉路だけが崩れるunique witnessを必要とする。
- E: Lesion profileやsynergy countはshuffleでも形成され得るため、固定点変化だけでなく独立能力channelの選択的崩壊を要求すべき。

## 次の仮説

**Active Object-Disagreement Queries for Predictive State Birth**  
（object disagreementを最大化する能動queryによる予測状態創発）

既存paired probesからobject edgeが自然に再現するのを待つ方式を棄却する。

1. 候補cell対が異なるtargetを予測する最小object/value commandを生成
2. 期待cell entropy減少／query記述bitを最大化
3. Objectだけ変更、valueだけ変更、futureだけ変更する直交queryを生成
4. 同じsurface outcomeに従属しない独立sensor集合を構成
5. Query応答からobject-target boundary populationをsplit／merge
6. Correct active query／random query／shuffled response／passive probeを比較
7. 次turnで再起動し、object lesionで選択的に崩れるcellだけ時間状態化
8. 主語省略・切替・計画変更・反実仮想で評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
