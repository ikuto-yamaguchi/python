# 系列A Cycle 037 研究報告

## 仮説

**Counterfactual Sensor Separation for Multi-Channel Predictive State Birth**  
（反実仮想sensor分離による多channel予測状態創発）

Cycle 036ではstate rollout誤差とcommand-value誤差を相互輸送したが、両channelが同じafter文字列へ従属し、One-wayとReciprocalが同一化した。

今回は共有outcomeを唯一のoracleにせず、各境界候補を次の独立sensorで監査した。

1. Value-swap sensor: command値を別値へ交換すると、同じstate supportが対応値へ更新されるか
2. Object-swap sensor: command objectを別対象へ交換すると、更新targetだけが切り替わるか
3. Future sensor: prospective stateが独立future観測と一致するか
4. Non-target sensor: 非対象objectの状態が保存されるか
5. Inverse sensor: 更新結果から旧値へ可逆復元できるか

3 sensor以上を同時に満たす候補だけをpredictive state cellへ昇格した。Final testのafter/futureは候補生成・rankingに使用していない。

## 最新系列との重複表

| 系列 | 最新中心 | Aで棄却・分離した領域 |
|---|---|---|
| B Cycle 036 | Multi-intervention traceの商grammar | MDL・記号圧縮・観測同値類 |
| C Cycle 036 | Object×value二重介入の因果parent set | 因果方向・world graph |
| D Cycle 036 | Read/write replay残差交差によるaddress birth | 長期memory・slow統合 |
| E Cycle 036 | Frustration gradientによるenergy node birth | Energy固定点・constraint topology |
| **A Cycle 037** | **独立sensor群が共同支持する時間予測状態cell** | 現在状態→次観測・再起動・終了 |

Cのobject-selective parent setとobject swap自体は重なるため、Aでは因果親集合を主張せず、複数sensorが同一時間状態を独立に反証できるかだけを扱った。

## 先行研究整理

- PhiNets（ICLR 2025）は時間予測仮説に基づく非対照学習で安定性・適応性を評価するが、入力表現とencoder構造は既定である。
- Predictive-State Decodersは未来観測の十分統計をrecurrent stateへ直接監督するが、状態境界を生の言語から生成する問題は扱わない。
- 2025年の時間抽象化研究は長期意思決定をmacro actionへ分解するが、VQ latentやskill substrateを前提とする。

今回の未解決点は、それらより上流の「何を別sensorとして予測すべき状態変数とみなすか」である。

## 3 seed平均

| 条件 | Shared 精度/wrong | Single 精度/wrong | Separated 精度/wrong | Channel-shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0/1.0000 | 0/0.0926 | **0.5926/0.4074** | **0.5926/0.4074** |
| 未知語順 | 0/0.6667 | 0/0 | 0/1.0000 | 0/1.0000 |
| 未知語彙 | 0/0.6667 | 0/0 | 0/1.0000 | 0/1.0000 |
| 入れ子 | 0/0.6667 | 0/0 | 0/1.0000 | 0/1.0000 |
| 主語省略 | 0/0 | 0/1.0000 | 0/1.0000 | 0/1.0000 |
| 複数段落 | 0.2407/0.4259 | 0/0 | 0/1.0000 | 0/1.0000 |
| 計画変更 | 0/0.6667 | 0/0 | 0/1.0000 | 0/1.0000 |
| 反実仮想 | 0/0.6667 | 0/0 | 0/1.0000 | 0/1.0000 |

追加診断（既知条件）:

- Shared rule: 1.67
- Single sensor rule: 5.67
- Separated rule: 3.67
- Channel-shuffle rule: 3.00
- Probe audit: 136
- Value sensor accept: 23.67
- Object sensor accept: **0**
- Future sensor accept: 5.67
- Non-target sensor accept: 23.67
- Inverse sensor accept: 23.67
- Model: 約511 bytes
- Training: 0.01876 sec
- Seen inference: 0.01041 ms/example
- Paragraph inference: 0.01059 ms/example
- Peak RSS: 167,428 KiB（Python runtime込み）

## 判定

**一般的な予測状態創発仮説としては強く反証。既知surface条件の局所選択信号にのみ限定支持。**

### 既知条件ではshared outcomeより改善

既知条件でSeparated方式はaccuracy 0.5926を示し、Shared方式の0から改善した。Shared方式はwrong commit 1.0であり、単一after一致で形成したruleがsurface位置へ誤適用されていた。複数sensorの同時支持は、この一部を除外した。

### Channel shuffleと能力が同一

最重要反証として、channelをepisode間で独立shuffleしても既知accuracyは0.5926のままだった。Rule数は3.67から3.00へ減ったが、最終予測は変わらなかった。

改善はsensor間の正しい対応関係ではなく、Valueを同じ位置へ挿入できること、非対象文字列が残ること、一回の置換が逆操作可能であること、という粗いsurface条件で説明できる。

### Object sensorは全件0

Object-swap sensorのacceptは全seedで0だった。現在のcellはcommand objectを使ってtarget supportを選択していない。状態文中の絶対位置とvalue区間だけで動作している。

> Object選択性を欠くcellは、対象を持つworld stateではない。

### 表現転移で全面失敗

未知語順・未知語彙・入れ子・計画変更・反実仮想ではSeparated方式のaccuracyは0、wrong commitは1.0だった。主語省略もaccuracy 0・wrong 1.0で、前turn focusやobject permanenceは形成されていない。

## 反証条件

仮説支持に必要だった条件:

1. Correct separated channelsがShared・Singleを改善する
2. Channel shuffleで改善が消失する
3. Object-swap sensorが正のsupportを持つ
4. 未知語順・未知語彙・入れ子へ転移する
5. 主語省略で前turn stateを再起動する
6. 計画変更で撤回案と最終案を分離する
7. 反実仮想で実行・非実行stateを並列保持する

1は既知条件のみ達成。2〜7は未達。

## 既存方式との差

Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは不使用。

単一出力誤差ではなく、複数の反実仮想sensor channelを候補cellへ接続し、複数channel支持で状態を形成した。ただし各sensorの候補生成が同じ相対位置表現へ依存しており、意味的に独立したsensor networkには未到達。

## 資源量

- Candidate生成: O(L²)、64候補へ制限
- Probe監査: O(QC)
- 推論: O(R)
- Rule上限: 48
- Model: 約511 bytes
- Training: 約0.0188 sec
- Inference: 約0.01 ms/example

1GB未満・5ms未満は小規模条件で達成。ただし意味転移がないため弱いスマートフォン上の汎用知能成立見込みを支持しない。実機未検証。

## 系列A固有の進展

> 複数sensor gateは共有afterだけのruleより局所誤適用を減らせる。しかしobject sensorが0で、channel shuffleでも能力が維持されるなら、sensor separationは形式上だけであり、時間予測状態は形成されていない。

## 他系列へ返す知見

- B: 複数介入traceの商化前に、各traceが独立に候補rankingを変えるかを必須監査すべき。
- C: Object×value interactionが0だった結果と整合し、object sensorを欠くsupportを因果変数と認めるべきではない。
- D: Read/write残差channelも正しい対応shuffleで能力が変わることをaddress birth条件にすべき。
- E: Frustration channel数ではなく、各channel除去・shuffleで固定点が選択的に変わることを要求すべき。

## 次の仮説

**Sensor-Causal State Cells from Selective Channel Lesions and Object-Target Birth**  
（選択的channel lesionとobject-target新生によるsensor因果状態cell）

1. Candidate cellごとに各sensorを一つずつ削除
2. 対応能力だけが落ちるsensor-causal profileを要求
3. Object-swap失敗残差をcommand object境界からstate target境界へ輸送
4. Object変更に追従するtarget edgeを新生
5. Correct sensor／channel shuffle／lesionなし／object birthなしを比較
6. Correct object sensorでのみtarget supportが切り替わることを必須化
7. 次turn再起動、主語省略、明示切替を時間状態ゲートへ追加
8. 計画変更・反実仮想では複数cellを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
