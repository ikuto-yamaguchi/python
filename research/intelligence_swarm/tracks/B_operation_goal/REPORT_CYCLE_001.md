# 系列B Operation/Goal Cycle 001

## 判断

**仮説棄却・S1継続・G2未達**

A Cycle 001の`Utterance–Witness Synchrony Binding`はheld paraphraseやrenameで限定的なidentity信号を形成したが、G1は未達である。本Cycleではその信号を操作・目的へ直接拡張せず、発話全体と観測された`before witness → after witness`変換関係を局所結合し、span programや固定operation ontologyなしで実行可能な潜在操作を形成できるか検証した。

## 新仮説

**Witness-Conditioned Operation Equivariance without Span Programs**  
（区間programを先に作らないwitness条件付き操作等変性）

操作を語句境界、grammar、固定ラベルとして定義せず、各episodeの変化前後のtrajectory／不可逆痕跡から生成した関係featureとraw Japanese全体のfeatureを局所外積で結合する。同一作用素をprospective rollout、inverse explanation、goal change、failure repairへ再利用できるならoperation unitの限定証拠とする。

モデルはoperation ID、goal slot、identity label、span境界を受け取らない。候補afterは環境が提示するraw worldであり、モデルは発話と観測変換の対応だけで選択する。

## 開始時統合

- Stage: S1 Semantic Identity Birth
- G1: 未達、G1a: synthetic pilot限定支持、G2: 未達
- HF-001〜HF-004は凍結継続。execution 0のgrammar／MDL最適化は禁止
- C PR349: 因果挙動だけではidentityはworld automorphismまでしか定まらない
- D PR350: trajectory 0.9663、scar 1.0000、joint 1.0000、shuffle 0.0236。ただし観測側synthetic再同定
- E PR351: AF-003 Symmetry-Breaking Witness Groundingを本線化
- A PR352: held 0.2431 vs shuffle 0.1233、rename 0.2240 vs 0.1354等の限定信号。ただしdomain 0.1128 vs 0.1181、inverse domain 0.1441でG1未達

## 重複表

| 系列 | 最新中心 | Bで重複採用しないもの | Bの固有問い |
|---|---|---|---|
| A | 発話–trajectory synchronyによるidentity predicate | identity選択そのもの | identity witnessを条件に操作変換が再利用可能になるか |
| C | world automorphismと識別可能性 | 個体identityの必要十分性 | before→after変換を操作候補として使えるか |
| D | symmetry-breaking memory eligibility | 保存・保持・干渉 | 記憶前の実行可能operation資格 |
| E | AF-003統合・stage管理 | gate判定 | G2へ必要な言語–行為反例 |
| 旧B | span/role/grammar/MDL | HF-001/HF-002として凍結 | 発話全体と観測変換の関係学習 |

## 最小実装

- Raw Japanese: 文字1〜3gramのsigned hashing、256次元
- Observed relation: before/after trajectoryとscar差分のsigned hashing、128次元
- 学習: 発話featureとrelation featureの局所Hebbian外積
- 比較: Correct pairing / episode-level shuffled pairing
- 8候補prospective、8候補inverse、2候補goal change、8候補failure repair
- seed: 1 / 7 / 19
- final test outcomeは学習・ranking設計に不使用

## 3 seed平均

8択chanceは0.125、goal changeの2択chanceは0.5。

| 条件 | Correct | Shuffle | Gap |
|---|---:|---:|---:|
| Held paraphrase | 0.1500 | 0.1437 | +0.0063 |
| Rename | 0.1354 | 0.1271 | +0.0083 |
| 未知語順 | 0.1042 | 0.0979 | +0.0063 |
| 入れ子 | 0.1354 | 0.1333 | +0.0021 |
| 複数段落 | 0.1104 | 0.1083 | +0.0021 |
| 自由日本語 | 0.1417 | 0.1313 | +0.0104 |
| 別領域 | 0.1146 | 0.1146 | +0.0000 |

追加:

- Inverse held: **0.1458**
- Inverse domain: **0.1271**
- Goal change: Correct **0.5125** / Shuffle **0.5083**
- Failure repair: Correct **0.1292** / Shuffle **0.1250**

## 反証

**中核仮説は強く反証された。**

Heldの最高値でも0.1500でshuffleとの差は0.0063にすぎない。Rename、未知語順、入れ子、複数段落、自由日本語もgapが小さく、別領域はCorrectとShuffleが完全同一だった。Inverse held 0.1458、domain 0.1271も8択chance近傍であり、同じ内部作用素をforwardとinverseへ再利用できていない。

Goal changeは0.5125、shuffle 0.5083で2択chanceと同等。Failure repairも0.1292、shuffle 0.1250でchance近傍だった。

> **対象を指せる弱いtrajectory predicate groundingと、何を行うか・何を目的とするかを表すoperation/goal bindingは別の形成問題である。**

単一の発話–relation相関行列では、対象記述、操作記述、目的記述が一つのsurface featureへ混合された。操作には少なくとも、agent/patient/targetの役割、before/afterの非対称性、operationとgoalの分離、複数対象への等変性、失敗結果に対する修正方向が必要である。

## 進歩判定

- 外部能力の進歩: **なし**
- 原理的知見: **あり**
- G1: 未達
- G2: 未達
- 旧grammar/MDL本線再開: **拒否**
- 本仮説: **棄却**
- Stage: **S1継続**

Correct–shuffle差が未知条件で実質的に形成されなかったため進歩認定しない。

## Aへ返す反例設計

1. **同一identity・異なるoperation**: identityだけでは答えられない対照
2. **異なるidentity・同一operation**: 操作等変性を要求
3. **同一operation・異なるgoal**: 操作と目的を分離
4. **同一語彙・逆方向変換**: before/after方向を分離
5. **失敗→訂正**: 誤after後の修正方向を選択
6. **cross-domain relation**: 語彙でなく変換関係を共有

## Cへ返すoperation proposal条件

- 同一operationが複数identityで可換
- goal変更時にはoperation componentを維持
- inverseで元操作を識別
- intervention order変更時の予測を説明
- non-target witnessを保存

## Dへ返す記憶資格

取得時prospective/inverseがchance近傍なので、operation episodeをsemantic memoryへ保存する資格はない。

## 資源量

- Matrix: **131,072 bytes**
- Peak RSS: **160,176 KiB**（Python runtime込み）
- 3 seed total: **37.955 sec**
- Update: **32,768 multiply-add / episode**
- Candidate score: **32,768 multiply-add**
- Prospective candidates: **8**
- Complexity: update `O(TR)`、prospective/inverse `O(KTR)`

1GB未満は達成。弱いスマートフォンCPU実機は未検証で、純Python実行時間から実機高速性は主張しない。

## 次仮説

**Factorized Relational Binding from Four-Way Contrastive Episodes**  
（四方向対照episodeからの因子化関係束縛）

spanや固定slotを先に作らず、以下4種類のepisode集合のcross-covariance差からidentity・operation・goalの独立変化方向を形成する。

1. same identity / different operation
2. different identity / same operation
3. same operation / different goal
4. same words / reversed before-after direction

採用条件は、held・rename・別領域でのprospective Correct–shuffle gap、inverse > chance、goal change > shuffle、failure repair > shuffle、およびidentity/operation/goal lesionの選択性とする。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
