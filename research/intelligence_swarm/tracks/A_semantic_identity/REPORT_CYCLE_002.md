# 系列A Semantic Identity Cycle 002

## 仮説

**Pre-Treatment Relational Change Binding by Joint Target-Transition Prediction**  
（対象と変化の同時予測による介入前関係接地）

PR #356 の統合判断に従い、完成trajectory・行為後scar・after差分を候補featureへ入れる方式を凍結した。今回は、生の日本語発話全体と、介入前の複数対象配置から構成されるraw sensor状態、および候補targetへ仮定した局所変化だけを局所Hebbian外積で結合した。

文字区間、位置、幅をsemantic unitとして先に候補化していない。identity label、operation ID、手書きslot、固定ontology、文字列retrieval、RAG、外部LLMは使っていない。

## 現在段階と重複回避

- Stage: `S1 Semantic Identity Birth`
- G1: 未達
- Active family: `AF-004 Pre-Treatment Relational Change Grounding`
- 凍結済みHF-001〜HF-006の再試行は行っていない
- Dの保存最適化、旧Eのattractor、旧BのMDLを利用していない

## 最小実装

- raw Japanese全文を文字1〜4-gramの符号付きhashへ写像
- 介入前の全対象位置、基準との相対配置をraw sensor featureへhash
- 各候補target × 4候補移動についてhypothetical local transition featureを生成
- 発話featureと正しいtarget-transition featureの外積だけを更新
- 推論時は`before + command`のみから32候補をrank
- テスト時に完成trajectory、scar、正解afterは使用しない

## 3 seed平均

8対象 × 4移動なのでjoint chanceは **0.03125**、target chanceは0.125、move chanceは0.25。

| 条件 | Correct joint | Shuffle joint | 差 | Target | Move |
|---|---:|---:|---:|---:|---:|
| Held paraphrase | 0.0708 | 0.0458 | +0.0250 | 0.1875 | 0.2792 |
| Rename | 0.0500 | 0.0333 | +0.0167 | 0.1750 | 0.2875 |
| 未知語順 | 0.0458 | 0.0417 | +0.0042 | 0.1708 | 0.2708 |
| 主語省略 | 0.0542 | 0.0125 | +0.0417 | 0.1375 | 0.3875 |
| 複数段落 | 0.0792 | 0.0417 | +0.0375 | 0.1500 | 0.3875 |
| 自由日本語 | 0.0375 | 0.0292 | +0.0083 | 0.1417 | 0.2500 |
| 別domain | 0.0625 | 0.0625 | 0.0000 | 0.1458 | 0.2875 |

## Lesion

- Relation lesion: joint 0.0000 / target 0.0000 / move 0.3125
- Operation lesion: joint 0.0375 / target 0.1667 / move 0.2333

介入前の関係配置を消すとtarget選択は完全に崩壊した。一方、操作語は主語省略・複数段落の表層共有に偏っており、別domainではCorrectがshuffleを上回らなかった。

## 判定

**中核仮説は反証。能力上の進歩は未認定。AF-004は継続するが、現在実装は採用しない。**

Held条件ではjoint chanceを上回り、relation lesionも選択的だったため、介入前関係が候補target選択へ利用される弱い信号は存在する。しかし、進歩基準に必要な別domain、自由日本語、unknown word orderでのCorrect-shuffle差が実質的に形成されていない。さらにtargetとmoveのjoint bindingは低く、対象同一性と操作を一つのunitとして再利用できていない。

今回の失敗はpost-treatment leakageではない。最大の問題は、raw relation sensorと日本語の関係表現を絶対hash相関で結合しており、座標変換・対象入替・関係変換を跨ぐ**equivariance**がないことである。

## 他系列へ返す知見

- B: operation語だけは一部条件で学習できるが、target relationとjoint化されない。same identity/different operationとdifferent identity/same operationの直交対照を強化する。
- C: relation lesionはtarget選択に必須だが、絶対座標依存でdomain transferしない。座標回転・平行移動・対象入替を含む対称性監査が必要。
- D: prospective acquisitionは0ではないが、domain差0のためmemory eligibility unitは0件のまま。保存最適化は再開しない。
- E: AF-004は継続。ただし`absolute relational hash binding`を進歩とは認めず、次cycleで変換可換性を必須化する。

## 資源量

- Matrix: **32,768 bytes**
- Peak RSS: **112,632 KiB**（Python runtime込み）
- 3 seed総実行時間: **20.539 sec**
- Update: **8,192 ops/episode**
- Candidate score: **8,192 ops/option**
- 32 options/query: 約262,144 ops/query
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 次の仮説

**Transformation-Equivariant Relational Unit Birth from Paired Coordinate Worlds**

同一episodeを平行移動・回転・対象index置換したpaired worldとして提示し、発話変換とsensor変換が可換になる最小latent unitだけを形成する。

次回の必須条件:

1. test worldのabsolute座標と対象indexをtrainingから分離
2. rotation / translation / object permutationで同じunitを再生成
3. held、自由日本語、別domainすべてでjoint Correct-shuffle `>= 0.05`
4. targetとmoveの双方でchanceを上回る
5. inverse queryとselective lesionでも同一unitを使用

- Semantic Identity Gate G1: 未達
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
