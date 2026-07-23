# 系列C Cycle 039

## 仮説

**Event-Centered Causal Units from Multi-World Intervention-Closure Co-Segmentation**  
（multi-world介入閉包共同分節によるevent中心因果単位創発）

Cycle 038ではobject境界とstate supportをpaired worldから共同形成できたが、value・operation・relationを同じlatent proposalへ統合できず、final入力の実行候補は0だった。

今回はobjectだけ、valueだけ、operation表現だけが変化する複数worldを横断し、command区間・state変更区間・before→after差分を同一event signatureへ統合した。2対象以上で再現し、正しいrolloutが誤rolloutより多いfamilyだけを保持した。Final testのafter/futureは候補生成・rankingに不使用。

## 重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | 遅延言い換え再入場によるprediction-error hysteresis | 時間状態の寿命・終了 |
| B | paired disagreement world共同分節grammar | MDL・production grammar |
| D | paired replay world共同分節address | 長期memory・read/write閉路 |
| E | paired query world共同分節constraint node | energy固定点・constraint field |
| **C** | **object/value/operation介入閉包を満たす最小event因果単位** | 今回の固有対象 |

Bの共同分節grammarと中心機構が近いため、単なる共同分節・匿名grammar形成はCの進展としない。Cでは同一eventがobject swapでsupportを移し、value swapで同support内だけを変更し、operation言い換えで同transitionを維持する介入閉包を中心反証条件とした。

## 3 seed平均

全10条件（既知・未知語順・未知語彙・Rename・別状態表現・入れ子・主語省略・複数段落・計画変更・反実仮想）でaccuracy 0、wrong 0、null 1.0、exact event recall 0だった。

追加診断:

- Event family: **0**
- モデルサイズ: **5 bytes**
- 学習時間: **0.3804 sec**
- Peak RSS: **125300 KiB**（Python runtime込み）
- Seed: 1 / 7 / 19

## 判定

**中核仮説は強く反証された。**

Object・value・operationの複数介入worldを横断し、2対象以上で正しいrolloutが誤rolloutを上回るevent familyは全seedで0件だった。

> Object・support・value・operationを一つのtupleへ共同格納するだけでは、再利用可能なevent identityにならない。

候補生成器は相対位置、区間幅、文字shapeを用いている。Object swap・value swap・operation言い換えで同じ潜在eventを追跡するのではなく、各worldで別々のsurface置換候補を生成している。このため介入閉包を要求すると全候補が消失した。

Object permanence、event segmentation、state transition、relation graph、causal direction、goal revision、planning、counterfactual world separationはいずれも未成立。Wrong commit 0は安全な因果推論ではなく、event familyが空で全面棄権した結果である。

## 反証条件

1. Correct multi-worldでのみevent family形成: 未達
2. Object swapでtarget supportのみ移動: 未達
3. Value swapで同support内の値のみ変化: 未達
4. Operation言い換えで同transition維持: 未達
5. Exact object/value/support境界 > 0: 未達
6. Family除去で対応transitionのみ崩壊: family 0のため未検証
7. 計画変更・反実仮想で複数world分離: 未達

## 資源量

- Candidate audit: `O(NL^4)`、各episode最大96候補へ疎制限
- Inference: `O(FL^4)`
- モデルは1GB未満、ただし空familyによる小型化
- 弱いスマートフォンCPU実機: 未検証

## 系列C固有の進展

> Object-support二者共同分節の不足を受け、value・operationを含むevent単位へ拡張した。しかし複数介入閉包を要求するとfamilyは0となり、共同格納と因果event identityを切り分けた。

## 他系列へ返す知見

- A: 時間寿命を評価する前に、介入閉包を持つevent cellのbirthが必要。
- B: paired-world共同分節grammarは、object/value/operation role permutationを満たさない限りsurface grammarに留まる。
- D: read/write addressへevent tupleを保存する前に、複数介入で同じevent identityが再現する必要がある。
- E: constraint node共同分節だけでなく、介入閉包をenergy constraintとして独立監査すべき。

## 次の仮説

**Relation-Bearing Event Birth from Cross-Object State-Difference Tensors**  
（対象横断状態差tensorによる関係保持event創発）

複数対象worldのbefore→after局所差を疎tensor化し、object swapで移動する差分axis、value swapで変化するpayload axis、operation言い換えで不変なtransition axisを分離する。三axisの低rank分解からevent candidateを生成し、Correct multi-world／shuffle／pair-only／文字shape-onlyを比較する。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
