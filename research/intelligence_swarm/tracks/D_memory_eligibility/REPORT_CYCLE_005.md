# 系列D Memory Eligibility Cycle 005

## 仮説

**Cross-Lexicon Consensus Eligibility from Shared Selective Lesion Signatures**

AF-006に従い、完全語彙非共有の3 domainで、prospective・inverse・自由日本語だけでなく、identity / operation / goal channel lesionの符号まで全seedで一致するunitだけを記憶資格へ通す。

semantic identity未成立のままaddress、replay、assembly、fast/slow memoryを作る旧仮説族は継続凍結した。保存方式は追加していない。

## 実験

- Domain d1 / d2 / d3は関係語、操作語、目的語、anchor語、対象名prefixを非共有化
- raw Japanese全文と介入前worldのみをtest入力に使用
- 64候補 target × move × goal prospective選択
- 同一写像によるinverse query
- Correct alignment / outcome shuffle
- identity / operation / goal response channelを個別lesion
- seed 1 / 7 / 19
- 厳格gate:
  - 各domainで未知語順と自由日本語のCorrect-shuffle差が各+0.10以上
  - inverse差が+0.10以上
  - 3 lesionすべてが能力低下
  - 上記を3 domain × 全seedで満たし、lesion符号がdomain間で同一

## 3 seed平均

Joint chance 0.015625、inverse chance 0.125。

| Domain | Held C/S | 未知語順 C/S | 自由日本語 C/S | Inverse C/S |
|---|---:|---:|---:|---:|
| d1 | 0.1597 / 0.0347 | 0.1076 / 0.0521 | 0.1875 / 0.0312 | 0.2778 / 0.1285 |
| d2 | 0.1597 / 0.0347 | 0.0312 / 0.0104 | 0.0764 / 0.0208 | 0.2674 / 0.1319 |
| d3 | 0.1354 / 0.0347 | 0.1285 / 0.0208 | 0.2431 / 0.0347 | 0.3160 / 0.1181 |

平均lesion drop:

| Domain | Identity | Operation | Goal |
|---|---:|---:|---:|
| d1 | +0.0347 | +0.1042 | +0.0556 |
| d2 | +0.0660 | +0.1007 | +0.1007 |
| d3 | +0.0417 | +0.0660 | 0.0000 |

厳格gate通過: **0 / 3 seed**。

seed別には、d3のidentityまたはgoal lesionが0/逆符号となり、d2の未知語順・自由日本語も+0.10条件を満たさなかった。

## 判断

**中核仮説は反証。能力上の進歩は未認定。G1/G2およびformal memory eligibilityは未達。**

3 domainの平均ではprospectiveとinverseのCorrect-shuffle差が確認できた。しかし、同じ因果成分が全domain・全seedで同じlesion応答として再生成されなかった。

特にoperation lesionだけは比較的安定して正方向だった一方、identityとgoal lesionはseed/domain依存で0または逆符号となった。したがって、現在のunitは一つの再利用可能semantic episodeではなく、domainごとに異なるsurface cueの混合で同じ平均精度を作っている可能性が高い。

取得資格unitが0なので、干渉保持、fast weights、replay、sleep consolidation、selective forgetting、latest/obsolete競合は開始しない。失敗分類は**initial semantics failure**であり、catastrophic forgettingではない。

## 系列D固有の知見

平均Correct-shuffle差やdomain平均だけでなく、**各unitがどの因果channelに依存しているかのlesion符号をdomain × seed単位で一致させる必要がある**。

今回、operation channelは最も安定したが、identity/goalとの共同unitは成立しなかった。次は全channelを一つのmatrixへ混ぜず、発話→結果と結果lesion→発話候補棄却が双方向に対応することを要求すべきである。

## 他系列へ返す知見

- A: d3でidentity/goal lesionが不安定。response orbitの平均一致ではなく、unit単位の双方向因果依存を生成する必要がある。
- B: operation lesionは比較的安定だが、結果channel consensusだけでは発話側primitiveの再生成を保証しない。
- C: 次の介入は総精度ではなく、identity/goal lesion符号がdomain間で反転する候補を優先的に識別すべき。
- E: AF-006は候補信号として継続可能だが、mean lesion consensusをmemory eligibilityへ昇格する下位仮説は不採用。

## 資源量

- Matrix: 98,304 bytes/domain、3 domain合計294,912 bytes
- Peak RSS: 161,940 KiB（Python/NumPy runtime込み）
- 3 seed実行時間: 14.1723 sec
- 更新量: 約24,576 ops/episode
- 推論量: 約24,576 ops/option × 64 options
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Bidirectional Lesion-Transpose Eligibility from Cross-Lexicon Counterfactual Codes**

発話counterfactual→結果channel変化行列と、結果channel lesion→発話候補棄却行列が転置近似となり、その符号patternが3 domain × 3 seedで一致するunitだけを資格候補とする。

G1/G2未達の間は保存最適化を再開しない。

- Semantic Identity Gate G1: 未達
- Operation/Goal Gate G2: 未達
- formal memory eligibility: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
