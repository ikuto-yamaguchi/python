# 系列B Cycle 039

## 仮説
**Co-Segmentation Grammar Birth from Paired Disagreement Worlds**

能動queryで作ったpaired worldを同時分節し、command変化区間とstate変化区間を一つのlatent productionとして共同生成する。共同生成された対応写像を匿名grammarへ商化し、factorized productionより候補entropyと実行性能を改善できるか検証した。

## 重複表
| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | 遅延予測誤差ヒステリシス | 時間状態・再起動 |
| C | paired-world object-support共同分節 | 因果world・object support |
| D | paired replay world共同分節 | 長期memory・read/write閉路 |
| E | paired query world constraint node | energy固定点・局所力学 |
| **B** | **共同分節対応の匿名grammar化とMDL採否** | 今回の固有対象 |

## 結果
3 seed（1/7/19）でFactorized、Co-segmentation、Strict co-segmentation、Shuffled pairを比較した。

- 全8条件でexecution accuracy 0、null率1.0
- Factorized grammar 5.67、Co-seg grammar 5.67、Strict grammar 5.33、Shuffle 0
- 既知候補数: Factorized 11061.8、Co-seg 11061.8、Strict 10412.7
- 複数段落候補数: Factorized 23248.5、Co-seg 23248.5、Strict 21880.5
- Co-seg model: 117 bytes
- Training: 0.3395 sec
- Inference: seen 3.034ms、paragraph 6.154ms
- Peak RSS: 111132 KiB（Python runtime込み）

## 判定
**中核仮説は強く反証。**

Paired-world共同分節はshuffle時にgrammarを消失させたため、正しいpaired対応に依存する構造は形成された。しかしFactorizedとCo-segはgrammar数・候補数・能力が完全同一で、Strictでも候補を約6%減らしただけだった。全条件で候補が数千〜数万へ爆発し、同点のため全面棄権した。

> Paired worldの変化区間を共同分節しても、対応写像を文字shape・幅・相対位置で商化する限り、semantic variable productionにはならない。

不足しているのは、単なる区間対応ではなく、一つのproductionが異なるobject/value/worldで同じ役割置換関係を保つことの証明である。

## 反証条件
1. Correct pairでのみgrammar形成: 部分達成
2. Co-segがfactorizedより候補entropy削減: 未達
3. execution accuracy改善: 未達
4. Rename・別状態表現・主語省略転移: 未達
5. 追加grammar bitsを予測利得で回収: 未達

## 計算量
- paired segmentation O(NL²)
- quotient O(P log P)
- inference O(GL²V)
- 1GB未満は達成
- 長文5ms未満は未達
- 弱いスマートフォンCPU実機未検証

## 系列B固有の進展
Correct paired worldに依存する共同grammarを形成できたが、factorized方式から候補topologyを変えず、共同分節だけでは記号創発にならないことを確定した。

## 他系列へ返す知見
- C: object-supportだけでなくvalue/operation roleを共同生成しないとpaired supportは相対位置規則に留まる。
- D: command/state/query三視点共同分節でも、役割交換不変性を要求しないとaddress候補爆発になる。
- E: paired constraint nodeのenergy化前に、correct pairが候補entropyを実際に下げるか監査すべき。
- A: microstate寿命を測る前に、初回候補の役割同値性が必要。

## 次の仮説
**Role-Permutation Quotient Grammar from Multi-World Co-Segmentation**

1. object/value/語順が別々に変わる3世界以上を共同分節
2. latent production内の区間を匿名role node化
3. object swapとvalue swapでrole permutationが可換することを要求
4. 文字shape・絶対位置をgrammar identityから除外
5. Correct multi-world / shuffled alignment / pair-only / factorizedを比較
6. grammar bits + residual errors + candidate entropyの共同MDL
7. Rename・別状態表現・主語省略でrole class転移を必須化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
