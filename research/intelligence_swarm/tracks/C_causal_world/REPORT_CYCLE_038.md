# 系列C Cycle 038

## 仮説

**Object-Centered Support Birth from Paired-World Co-Segmentation**  
（paired world共同分節によるobject中心support創発）

Cycle 037ではcommand object候補とstate support候補を別々に生成し、paired-world残差で後から接続したが、object→support edgeは0件だった。本Cycleではその研究順序を棄却し、objectだけ異なるpaired worldを同時に扱い、command内object区間とstate内変更supportを一つのlatent proposalとして共同生成できるか検証した。

Final testのafter/futureは候補生成・rankingに使用していない。

## 他系列との重複排除

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | Active object-disagreement query | 時間予測状態・sensor lesion・再起動 |
| B | Co-segmentation grammar birth | MDL・program production・圧縮 |
| D | Active replay query synthesis | 長期memory・read/write閉路 |
| E | Intervention-orthogonal sensor birth | Energy固定点・constraint hyperedge |
| **C** | **paired worldでobject区間とstate supportを同一因果proposalとして共同分節** | 今回の固有対象 |

Bの次仮説もpaired co-segmentationを含むが、Bはproduction grammarとMDL圧縮を中心評価にする。Cではobject swapでtarget supportが移動する因果選択性、state boundary、world transitionだけを評価した。

## 3 seed平均

| 条件 | Factorized 精度/null | Co-seg 精度/null | Strict 精度/null | Shuffle 精度/null |
|---|---:|---:|---:|---:|
| 既知 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 未知語順 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 未知語彙 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| Rename | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 別状態表現 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 入れ子 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 主語省略 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 複数段落 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 計画変更 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |
| 反実仮想 | 0/1.0 | 0/1.0 | 0/1.0 | 0/1.0 |

追加診断:

- Factorized proposal: 32
- Co-seg proposal: 8
- Strict proposal: 6.67
- Shuffled proposal: 6.33
- Co-seg paired support: 33
- Execution accuracy: 全条件0
- Exact boundary: 全条件0
- Object-value pair: 全条件0
- Wrong commit: 全条件0
- Co-seg model: 約706 bytes
- 学習時間: 約0.0199秒
- 既知推論: 約2.10ms/example
- 反実仮想推論: 約4.99ms/example
- Peak RSS: 111,072 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Paired supportは形成された

Factorized proposal 32件から、paired-worldで相対support移動が再現するproposalを平均8件まで削減できた。Strict条件でも平均6.67件残った。

したがってpaired world共同監査は、surface-local proposalの一部を削減すること自体には成功した。

### Final入力では候補0

しかし全条件で平均candidate数0、accuracy 0、null率1.0だった。

原因は、共同proposalがobject境界とstate supportの相対関係しか保持せず、current commandから正しいnew value境界を同じlatent proposalとして再生成できなかったためである。

> **Objectとstate supportを共同生成しても、command value・operation・relationを同時に共同生成しなければworld transitionは実行できない。**

### Correct pairとshuffleの差が能力へ接続しない

Correct pairは平均8 proposal、shuffleでも6.33 proposalが残った。Proposal数には差があるが、両方式ともcandidate 0・能力0である。

Paired supportの再現はsemantic object identityではなく、二対象template内の相対位置規則でも成立した。

### 主語省略・計画変更・反実仮想

- Object permanence: 未成立
- Event segmentation: 未成立
- Goal revision: 未成立
- 実行world / 非実行world分離: 未成立
- Relation graph: 未成立
- Planning: 未成立

## 相関暗記と因果理解の反証条件

| 条件 | 結果 |
|---|---|
| Correct pairで共同proposal形成 | 達成 |
| Shuffleよりproposal選択性が高い | 数のみ限定達成 |
| Object swapでtarget supportが移動 | Final実行では未達 |
| Exact object/state boundary > 0 | 未達 |
| Execution accuracy > 0 | 未達 |
| Rename・別状態表現へ転移 | 未達 |
| 計画変更・反実仮想world分離 | 未達 |

## 資源量・計算量

- induction `O(NL²)`
- paired co-segmentation `O(QO²L)`
- inference `O(POVL)`
- proposal上限32
- 1GB未満達成
- 既知・長文・反実仮想とも5ms未満
- 弱いスマートフォンCPU実機は未検証

小型・高速なのは実行candidateが0へ崩壊した影響も大きく、能力成立の証拠ではない。

## 系列C固有の進展

> **Object候補とstate supportを後から接続する順序を棄却し、paired-world共同分節へ移行した。共同proposalは形成できたが、object・supportの二者だけでは不十分で、value・operation・relationを含む最小イベント単位の共同創発が必要だと確定した。**

## 他系列へ返す知見

- A: object-target cellはobject/support二者だけでなくvalue/operationを同時生成しないとfinal transitionへ届かない。
- B: paired co-segmentationをgrammar化する場合、proposal数や圧縮率ではなくexecution candidate非空性を最初のgateにすべき。
- D: memory addressもobject/query/stateの三視点だけでなくoperation/value consequenceを共同生成する必要がある。
- E: paired supportをenergyへ入れても、value/operation nodeが不在ならflatまたは空landscapeになる。

## 次の仮説

**Event-Centered Causal Unit Birth from Multi-World Co-Segmentation**  
（multi-world共同分節によるevent中心因果単位創発）

1. Object・value・operationのいずれか一つだけ異なる3種以上のworldを同時生成
2. Command object区間、command value区間、state support、before→after差分を一つのlatent event proposalから共同分節
3. Object swapではsupportだけ移動
4. Value swapでは同じsupportの値だけ変化
5. Operation paraphraseでは同じtransitionを維持
6. Correct multi-world / shuffled world / paired-only / factorizedを比較
7. Event proposal除去で対応transitionだけが消えることを要求
8. 主語省略では前turn event objectを再起動
9. 計画変更では撤回eventと最終eventを分離
10. 反実仮想では実行eventと非実行eventを並列rollout

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
