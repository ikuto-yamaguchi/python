# 系列D Memory Eligibility Cycle 001

## 現在段階

- Active stage: **S1 Semantic Identity Birth**
- Semantic Identity Gate G1: **未達**
- Dのmemory/consolidation mainline: **G1待ち**
- HF-003 `memory before re-identifiable semantics`: 凍結継続

A/Bの新制度後proposalはまだ未提出であり、C Cycle 001は、因果挙動のみでは対象identityがworld automorphismまでしか決まらず、trajectory continuityや不可逆介入痕跡などのsymmetry-breaking witnessが必要だと報告した。

したがって本Cycleではaddress、trace、replay、assembly、fast/slow memoryを構築せず、**どのepisodeに記憶資格を与えてよいか**を監査した。

## 新仮説

**Symmetry-Breaking Witness Eligibility**

> 行動応答が同じで置換可能な対象について、同じ対象を未知表現・別観測座標系でも再同定できるsymmetry-breaking witnessを持たないepisodeは、semantic memoryとして保存する資格を持たない。Trajectory continuityまたは不可逆痕跡がCorrect対応で再同定を支え、identity対応shuffleを上回る場合に限りmemory-eligibleとする。

HF-003は先にmemory unitを作りreplayで意味化した。本仮説は保存前の資格gateを定義し、identity証拠がないepisodeを保存対象から除外するため、根本前提が異なる。

## 最小実験

- 完全に同じ4-action behavioral signatureを持つ双子対象を24組、合計48対象生成
- 表面日本語は5形式から毎回変更し、対象名も毎回rename
- Retrievalは日本語文字列をkeyに使用しない
- 未知domainではsensor frameを90/180/270度回転
- Behavior only / trajectory / irreversible scar / joint / shuffled jointを比較
- 取得後に同じbehaviorを持つidentity-distinct episodeを96件追加しretentionを再測定
- seed: 1 / 7 / 19
- Final identityは評価以外に使用しない

## 3 seed平均

| 条件 | 取得直後 accuracy | 棄権率 | 干渉後 accuracy | 干渉後棄権率 |
|---|---:|---:|---:|---:|
| Behavior only | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| Trajectory | 0.9663 | 0.0306 | 0.8333 | 0.1458 |
| Irreversible scar | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Joint witness | **1.0000** | **0.0000** | **1.0000** | **0.0000** |
| Shuffled joint | 0.0236 | 0.0000 | - | - |

## 判定

### 能力上の進歩候補あり

Joint witnessは未知日本語surface・対象rename・別sensor座標系でaccuracy 1.0を達成し、identity対応shuffle 0.0236を大幅に上回った。3 seedすべて同方向であり、候補数削減や内部graph形成ではなく、外部の対象再同定能力差である。

同じretrieval結果をforward selectionとinverse identity queryの双方へ利用できる。ただし、この実験は日本語意味解析の成功ではない。日本語surfaceは意図的にkeyから除外しており、観測channel側でsemantic identityが識別可能になる条件を監査したpilotである。G1達成には、生の日本語から同じwitness-bearing unitを自律生成する必要がある。

### 取得失敗と保持失敗を分離

Behavioral equivalenceのみでは全queryがtieとなり、取得直後からaccuracy 0だった。これはretention failureではなく**acquisition failure**である。

Trajectory continuityは取得直後0.9663から干渉後0.8333へ低下したため、初めて保持劣化を測定可能になった。ただし低下の一部はtrajectory noiseによるtie増加であり、catastrophic forgettingとは断定しない。

不可逆scarとjoint witnessは96件のbehavior-equivalent干渉後も1.0を維持した。

## 記憶資格条件

1. 未知surfaceと別contextで同じ個体を再同定できる
2. Correct witness alignmentがshuffle/randomを上回る
3. forward selectionとinverse queryの双方で同じidentityを使える
4. 同じ因果的役割を持つ別個体を区別できる
5. witness対応をlesion/shuffleすると能力が選択的に崩れる

## 旧memory仮説との差

文章、embedding、近傍文、保存回答は検索していない。旧Dはsemantic unit未成立のままaddressやreplay familyを形成した。本Cycleはmemory構造を作らず、episodeを保存してよいかを決める**pre-memory gate**だけを検証した。

## 資源量

- 学習済み固定parameter: 0 bytes
- 48 record推定: 1,920 bytes
- 1 episode更新量推定: 40 bytes
- 干渉後record: 144
- 3 seed総実行時間: 0.9010 sec
- 推定平均照合時間: 60.16 µs
- Peak RSS: 161,120 KiB（Python runtime込み）
- Update: `O(W)`
- Retrieval: `O(MW)`
- Interference audit: `O(IMW)`

1GB未満・弱いスマートフォンCPUで成立する規模だが、スマートフォン実機では未検証。

## 他系列へ返す知見

### Aへ

Behavioral equivalenceはsemantic individual identityではない。日本語からunitをbirthする際は、trajectory continuity、不可逆痕跡、個体履歴などのwitnessを同じlatent unitへ接続し、その対応shuffleで未知表現再同定が崩れることを要求する。

### Bへ

同じ結果を生むoperationでも、対象identityを区別するwitnessがなければ「どの対象へ実行する操作か」を保存できない。Operation proposalのmemory eligibilityにはtarget witnessが必要。

### Cへ

C Cycle 001のautomorphism制約をmemory gateへ具体化した。次はtrajectory/scarを単なるID tokenにせず、観測連続性・介入履歴から自律形成できるかを検証する必要がある。

### Eへ

HF-003は凍結継続。一方、pre-memory symmetry-breaking eligibilityはCorrect 1.0 vs shuffle 0.0236のpilot差を示したため、HF-003の再開ではなく、新しい上流identity観測信号として追跡可能。

## 次の一点

**Witness-Bearing Unit Birth from Raw Japanese–Trajectory Synchrony**

次は語句境界を先に候補化せず、発話時刻とsensorimotor trajectory／不可逆痕跡の同期からlatent unitを形成する。

比較条件は正しい発話–trajectory同期、時間shuffle、scar shuffle、behavior-only、trajectory-only、joint synchrony。held-out paraphraseとrenameで同じ個体を再同定し、forward selectionとinverse queryを同じunitで実行し、同型双子対象を区別することを必須とする。

## 状態

- 能力上の進歩候補: **あり（synthetic identifiability pilot）**
- Semantic Identity Gate G1: **未達**
- Memory/consolidation mainline: **未再開**
- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
