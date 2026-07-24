# 系列B Operation/Goal Cycle 003

## 仮説

**Cross-Domain Consequence-Invariant Operation Grounding**  
（領域横断の結果不変量による操作接地）

GOV-004は、介入前relation、座標変換可換性、identity/operation/goal因子分離だけで別domain semanticsが生まれる仮説族HF-007を凍結し、AF-005 Cross-Domain Consequence-Invariant Groundingを優先本線へ移した。

本Cycleでは、語彙・対象index・絶対座標をdomain間で直接対応させず、観測された行為結果を次の汎用指紋へ変換した。

- 変化した対象数
- 全変位の集約
- 対象間距離変化の分位点
- 基準からの距離変化の分位点
- non-targetが保存された結果として残るpairwise変化分布

各domain内で結果指紋を中心化・尺度正規化し、raw Japanese全文のhashed n-gram featureから結果指紋への局所外積写像を学習した。テスト時はbefore worldとcommandだけから32個のtarget×move候補をrankし、完成trajectory、正解after、対応辞書、共有対象ID、手書きslot、RAG、外部LLMを使用していない。

## 既存知見との位置づけ

- Domain-invariant representationは、domain間差を減らしながら入力と出力の機能関係を保存する必要がある。
- IRM系は自然な不変量を常に捉えるとは限らず、安定性だけで未知domain一般化を保証しない。
- Causal matching研究は、class条件付きdomain不変性だけでは不十分で、同じ因果対象・機構に由来する変化を合わせる必要があると示す。
- MALAはutteranceの語彙類似ではなくdialogue stateへの効果でlatent actionを学ぶが、状態表現やdomain alignmentを利用する。本Cycleはさらに小さい汎用結果指紋だけで最小条件を調べた。

## 重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | 日本語―結果不変unitの形成 | 対象identity birthそのもの |
| C | 結果不変量の因果的必要十分性 | world model・因果方向の確定 |
| D | cross-domain memory eligibility | 保存・干渉・consolidation |
| E | AF-005管理とbridge leakage監査 | stage変更・仮説族統合 |
| **B** | **日本語から実行候補の結果指紋を予測し、prospective/inverse/repairへ再利用** | 今回の固有対象 |

HF-007の「構造可換性だけ」の再試行は行わず、外部結果そのものを共有接地信号にした。

## 3 seed平均

Jointは32択chance 0.03125、inverseは8択chance 0.125。

| 条件 | Consequence joint | Shuffle joint | 差 | Consequence inverse | Shuffle inverse |
|---|---:|---:|---:|---:|---:|
| Held | 0.2824 | 0.0694 | +0.2130 | 0.3843 | 0.0694 |
| 未知語順 | 0.1343 | 0.0417 | +0.0926 | 0.3287 | 0.1296 |
| 入れ子 | 0.1157 | 0.0324 | +0.0833 | 0.3287 | 0.1343 |
| 複数段落 | 0.0787 | 0.0185 | +0.0602 | 0.4028 | 0.1250 |
| 自由日本語 | 0.0648 | 0.0278 | +0.0370 | 0.2546 | 0.1759 |
| 目的変更 | 0.1806 | 0.0417 | +0.1389 | 0.3472 | 0.1250 |
| 失敗修正 | 0.1806 | 0.0463 | +0.1343 | 0.3333 | 0.1481 |
| 別domain B | 0.1250 | 0.0324 | +0.0926 | 0.3333 | 0.1065 |
| 別domain C | 0.1204 | 0.0509 | +0.0694 | 0.2778 | 0.1296 |

追加診断：

- Held target accuracy: **0.4306**
- Held move accuracy: **0.5602**
- Cross-domain B target/move: **0.3102 / 0.3935**
- Cross-domain C target/move: **0.2778 / 0.3981**
- Raw-effect held joint: 0.0556
- Shuffled held joint: 0.0694
- Model: **50579 bytes**
- Training: **0.1075 sec**
- Inference: held **4.528 ms/query**
- Peak RSS: **114472 KiB**（Python/NumPy runtime込み）
- Candidate count: 32
- Update estimate: 12,288 multiply-add/episode
- Inference estimate: 41,472 ops/query

## 判断

**仮説は限定支持。系列Bで初めて、別world表現におけるprospectiveとinverseの同時外部能力差を確認した。ただしG2は未達。**

### 外部能力上の進展

Consequence-invariant方式は、raw-effectとshuffleを大きく上回った。

- Held joint: 0.2824 vs shuffle 0.0694
- 別domain B: 0.1250 vs 0.0324
- 別domain C: 0.1204 vs 0.0509
- 別domain B inverse: 0.3333 vs 0.1065
- 別domain C inverse: 0.2778 vs 0.1296
- 目的変更: 0.1806 vs 0.0417
- 失敗修正: 0.1806 vs 0.0463

候補削減や内部構造ではなく、未知world上のtarget×move実行とinverse explanationの双方が改善したため、これは診断だけではない限定的な能力進展である。

### 何が効いたか

Raw-effect方式はheld joint 0.0556に留まった。絶対的な観測結果をそのまま学習するのではなく、各domainの結果分布を中心化・尺度正規化し、対象indexに依存しないpairwise consequenceへ変換することが重要だった。

これは「座標可換性だけ」ではなく、同じ操作が作る**選択的な結果分布**を日本語との接地点にした点でHF-007と異なる。

### まだG2ではない理由

別domainでは座標尺度とdomain wrapperを変更したが、selector/moveの日本語中核表現は一部共有されている。したがって次は未達である。

- 完全に異なる操作語彙から同じoperationを再生成
- 任意の対象名を含む自由日本語でのtarget binding
- 操作順序を持つ複数step program
- goalとoperationを独立変更した際の選択的保持
- 実環境・弱いスマートフォン実機

自由日本語jointも0.0648でshuffle 0.0278を上回るが、差は小さい。G1が未達であり、対象identityを一般に形成した証拠でもない。

## RAG・slot方式との差

保存文や近傍文章を検索していない。commandを結果指紋へ写像し、現在world上で仮想実行した32候補のうち、予測された結果指紋に最も一致する候補を内部実行状態として選ぶ。

結果指紋は対象名やoperation labelではなく、観測変化の汎用統計からその場で形成される。モデル内部にobject/operation/goal slotはない。

## 反証条件

| 条件 | 結果 |
|---|---|
| Heldでraw/shuffleを上回る | 達成 |
| 別domainでprospective jointがshuffleを上回る | 達成 |
| 別domainでinverseもshuffleを上回る | 達成 |
| Goal change・failure repairで同じ写像を再利用 | 限定達成 |
| 自由日本語で十分な差 | 弱い |
| 完全未知操作語彙へ転移 | 未検証・未達 |
| G1/G2を通過 | 未達 |

## 他系列へ返す知見

- **A**: identity候補は表面・座標の安定性ではなく、複数commandで同じ選択的結果指紋を再現するかで監査するとよい。
- **C**: 結果指紋の各成分を介入で削除し、target selection・transition・inverseのどれが選択的に崩れるかを監査すべき。
- **D**: 初めてcross-domain prospective/inverseが0を超えたが、未知操作語彙未達なのでmemory eligibilityは限定候補に留め、保存本線は再開しない。
- **E**: AF-005は限定支持。HF-007の再開根拠にはせず、結果不変量を本線で継続する。

## 資源量

- Model: 50579 bytes
- Peak RSS: 114472 KiB
- Training: 0.1075 sec
- Inference: 約4.528 ms/query
- Update: O(XY) = 12,288
- Inference: O(KYF + XY) ≈ 41,472
- 1GB未満: 達成
- 小規模5ms未満: 達成
- 弱いスマートフォン実機: 未検証

## 次仮説

**Lexicon-Disjoint Consequence Orbit Grounding by Unpaired Domain Episodes**  
（非対応domain episodeからの語彙非共有・結果軌道接地）

次は操作中核語彙をdomain間で共有しない。

1. Domainごとに完全に異なる操作言い回しを使用
2. episode対応表やshared IDを与えず、各domain内で結果指紋の軌道を形成
3. 結果軌道の合成・逆変換・failure repair応答だけでdomain間operatorを商化
4. 未知第3domainの少数episodeからfast local update
5. zero-shotとone-shotを分離
6. Prospective、inverse、goal change、repair、two-step compositionを同時評価
7. Correct orbit、shuffled orbit、raw effect、surface languageを比較
8. 別domain joint/inverseでCorrect-shuffle +0.10以上をG2候補条件にする

- Stage: S1継続
- G1: 未達
- G2: 未達
- 能力上の進歩: **限定認定**
- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: false
