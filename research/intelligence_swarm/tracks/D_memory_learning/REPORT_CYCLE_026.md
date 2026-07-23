# 系列D Cycle 026 研究報告

## 仮説

**Counterfactual Credit Isolation by Memory-Element Removal before Reconsolidation**
（再固定化前のmemory要素除去による反実仮想credit分離）

Cycle 025では再出現supportをslow creditにした結果、誤ったsurface factorが固定された。今回はobject・relation・value・bindingを一つずつ除去し、held-out sessionのread損失増分だけをpositive creditとした。

## 重複回避

| 系列 | 最新中心 | Dとの分離 |
|---|---|---|
| A | 局所残差routingによる予測責任 | 談話予測・active inferenceを扱わない |
| B | negative witness cutによるbinding graph選択 | Program・MDLを扱わない |
| C | 双方向局所alignmentによるpositive witness birth | 因果world transitionを扱わない |
| E | 残差媒介triadic energy hyperedge | Energy・attractorを扱わない |
| **D** | **held-out記憶損失に対するmemory要素除去credit** | 今回の固有対象 |

## 実験

- seed: 1 / 7 / 19
- train size: 24 / 36 / 48 event
- sparse cap: object 16 / relation 16 / value 12 / binding 32
- removal audit: 上位8 factor/種別、上位16 binding、最大3 held-out session
- ablation: Support / Removal credit / Slow-only
- test: 既知、言い換え、Rename、別状態表現、主語省略、複数段落、未知domain
- 追加: 一回提示、長期干渉、最新値保持
- hidden labelは評価器だけで使用

## 最大48 event・3 seed平均

| 条件 | Support read / wrong | Removal read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.2500 / 0.6528 | 0.2500 / 0.6528 | 0 / 0 |
| 未学習言い換え | 0.2778 / 0.6111 | 0.2778 / 0.6111 | 0 / 0 |
| Rename | 0.3056 / 0.5556 | 0.3056 / 0.5556 | 0 / 0 |
| 別状態表現 | 0.2222 / 0.5694 | 0.2222 / 0.5694 | 0 / 0 |
| 主語省略 | 0.2917 / 0.6250 | 0.2917 / 0.6250 | 0 / 0 |
| 複数段落 | 0.2500 / 0.6528 | 0.2500 / 0.6528 | 0 / 0 |
| 未知domain | 0.2639 / 0.6250 | 0.2639 / 0.6250 | 0 / 0 |

追加診断:

- Write accuracy: Support/Removal 0.2083 / Slow 0
- Wrong write: Support/Removal 0.6389 / Slow 0.0833
- Positive binding credit: 1.67
- Negative binding credit: 1.33
- Mean binding credit: 0.004359
- Slow object / relation / value: 0.33 / 0.33 / 1.00
- Slow binding: 0
- Removal audit: 64
- One-shot read/write: Support 1.0/0.6667、Removal 1.0/0.6667、Slow 0/0
- 干渉後recall: 0.2778 / 0.2778 / 0
- 最新値recall: 0.1389 / 0.1389 / 0

## 判定

**中核仮説は強く反証された。**

要素除去によって平均1.67 bindingにpositive credit、1.33 bindingにnegative creditが生じた。しかしRemoval方式はSupport baselineに対して全splitで能力増分0だった。除去必要性の測定だけでは、誤ったobject・relation・value identityを修正しない。

Slow bindingは0件だった。Slow-only方式はwrong readを0へ抑えたがread accuracyも0で、全面棄権へ退化した。

単一要素を除去しても似たsurface factorが代替するためlossが変わらず、相互補強する誤bindingは単独除去では責任が混線した。

> **単一memory要素のleave-one-out必要性は、冗長な代替表現と相互依存したbindingを分離できない。**

一回提示は同一episode直後の表面再読に限られ、Slow方式はfast acquisitionからstable consolidationへ移行できなかった。干渉後recall・最新値recallも改善していない。支配的失敗は破滅的忘却ではなく、再固定化前のendpoint identityとbinding creditの初期誤りである。

## RAGとの差

保存文章やvector近傍を返さず、raw日本語から因子・bindingを形成し、内部read/write状態へ注入し、memory要素を反実仮想的に除去してheld-out損失変化を局所credit化する。ただし現状は文字gram・substring由来の疎transducerでありsemantic memoryではない。

## 資源量

- Model: 3,585 bytes
- Training: 0.178419 sec
- Inference: 0.123191 ms/read-or-write
- Peak RSS: 118,168 KiB（Python runtime込み）
- Memory: object 16 / relation 16 / value 12 / binding 8
- Update: 691
- Removal audit: 64
- 計算量: candidate `O(NL²)`、removal audit `O((O+R+V+B)SNB)`、inference `O(BL)`

1GB未満・5ms未満は疎化後の小規模条件で達成。弱いスマートフォン実機は未検証。

## 系列D固有の進展

> **再出現回数よりleave-one-out必要性の方がcreditとして健全だが、単独要素除去では冗長性と相互依存を分離できない。Slow reconsolidationには、要素集合の共同必要性と代替可能性を同時に測るcreditが必要である。**

## 他系列へ返す知見

- A: 単一commitment除去が無効でも代替cellが同じ残差を説明している可能性がある。
- B: 単一triangleのnegative cutだけでなく競合triangle集合の代替可能性が必要。
- C: 単一alignment edge除去よりwitnessを共同説明する最小edge集合の必要性が重要。
- E: 単一node energy除去ではtriadic synergyを分離できず集合介入が必要。

## 次の仮説

**Shapley-Sparse Credit Sets with Redundancy-Aware Reconsolidation**
（冗長性を考慮したShapley型疎credit集合による再固定化）

Top-k候補の単独・pair・全除去を比較し、代替可能factorをcredit setへまとめる。複数sessionでpositive marginal contributionが再現した集合だけslow化し、obsolete value集合だけ選択的に忘却する。k≤6の疎近似で計算量を制限する。

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
