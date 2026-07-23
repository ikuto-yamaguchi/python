# 系列E Cycle 028 研究報告

## 仮説

**Prospective Residual Fields from Self-Consistency Disagreement without Outcome Access**  
（正解観測なしの自己整合不一致からの前向きresidual field）

Cycle 027では候補生成器と残差生成器を分離したことで、計画変更・反実仮想に限定的な候補内選択信号が出た。しかし残差生成に評価episodeの実際のafter/futureを使っており、観測後評価だった。

今回は推論時に`before + command`だけを使用し、学習済み局所edit prototypeが生成する複数のafter候補間の位置別不一致をresidual fieldとした。実際のafter/futureは最終評価と学習時の局所weight更新にのみ使用した。

## 最新系列との重複表

| 系列 | 最新中心 | Eで棄却・分離した領域 |
|---|---|---|
| A | 時間応答kernelによるroute identity | 談話commitment・予測責任 |
| B | Program合成probe state | Program選択・MDL |
| C | Outcome-blind source-only mechanism transport | 因果transition |
| D | 時間横断予測必要性endpoint birth | 長期memory |
| **E** | **複数prospective rollout間の自己整合不一致をenergy field化** | 今回の固有対象 |

Aの応答kernelは前turn→現在turnの時間的routeを対象とする。Eは同一入力上の複数解釈rollout間のenergy競合と固定点緩和を対象とするため、中心機構を分離した。

## 実装

- 固定ontology、手書きslot、辞書、RAG、外部LLMなし
- Candidate:
  - `before`と`command`の最大共通span
  - `command`固有の最大新規span
- Edit prototype:
  - 学習episodeの局所command/state contextとold/new shape
- Prospective rollout:
  - target after/futureを見ずに最大48候補を生成
- Residual field:
  - rollout候補間で文字予測が分岐する位置bucketと不一致率
- Local weight:
  - 学習時のみ正答afterによる局所credit更新
- Relaxation:
  - energy最小値+0.04以内へactive集合を単調縮小
  - 最大6 sweep

## 3 seed平均

| 条件 | Base精度 | Field精度 | Pair recall | Null率 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 未知語 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 曖昧性 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 複数段落 | 0.0463 | 0.0463 | 0.0000 | 0.9537 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

追加診断:

- Edit prototype: 56.67
- Residual field weight: 0.00
- モデルサイズ: 7610 bytes
- 学習時間: 0.031164 sec
- 既知推論: 0.382 ms/example
- 複数段落推論: 1.604 ms/example
- Peak RSS: 160200 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Outcome非参照は達成

推論時の候補生成、rollout、residual field、energy rankingは`before + command`だけで実行した。Cycle 027に残っていた観測後after/future leakageは除去した。

### Residual field weightは0件

3 seedすべてで、prospective disagreementと正答選択の安定した対応が形成されず、field weightは平均0件だった。

候補生成をoutcome-blindにすると、学習済みedit prototypeがheld-out入力で実行可能な候補をほぼ生成できなかった。したがって不一致fieldを形成する前に候補集合が空になった。

### 全主要条件でcandidate collapse

既知、未知語、曖昧性、入れ子、主語省略、計画変更、反実仮想でpair recallは0だった。

複数段落だけ極少数の局所prototypeが偶然実行でき、accuracy 0.0463となったが、Field方式とBase方式が完全同一であり、residual fieldの成果ではない。

### Cycle 027の限定信号は再現しない

Cycle 027で計画変更0.1019、反実仮想0.0833へ改善した信号は、outcome accessを外すと両方0へ消失した。

これは前回の限定改善が、前向き自己整合性ではなく観測済みafter/futureとの整合性に依存していたことを示す。

### 自己整合不一致だけでは候補birthしない

複数rolloutが存在すれば不一致fieldは候補内選択に使える可能性がある。しかし現在は、未知span境界・object/value binding・局所edit適用先が形成されず、rollout集合自体が生まれない。

> **Prospective residual fieldは候補選択原理であり、候補birth原理ではない。候補集合が空ならenergy dynamicsは開始できない。**

## Hopfield記憶・既存NNとの差

固定pattern想起ではなく、入力ごとに複数の構造候補とrolloutを生成し、不一致field・局所energy・反復緩和で固定点を探索する点は単純Hopfield記憶と異なる。

ただし現在は離散的な局所edit prototypeと手続き的energyであり、学習された連続energy network、正式な平衡伝播、意味node間の局所力学には未到達。

## 収束保証・反証分類

候補集合は各sweepで単調に部分集合へ縮小し、最大6 sweepなので有限停止する。

- 候補崩壊: rollout候補0、今回の支配的失敗
- Field birth崩壊: 安定field weight 0
- 局所最適: 候補がある複数段落ではBaseと同じ局所prototype
- Null安全停止: candidate collapseにより実質全面棄権
- 発散: 未観測

仮説支持には、outcome非参照のまま複数seedでfield weightが形成され、Baseよりaccuracyまたはpair selectionが改善し、計画変更・反実仮想でCycle 027の信号を再現する必要があった。すべて未達。

## 資源量・計算量

- モデル: 7610 bytes
- Peak RSS: 160200 KiB
- 学習: 0.031164 sec
- 推論: 0.2〜1.6 ms/example
- 推定計算量:
  - prototype抽出 `O(NL)`
  - candidate生成 `O(L²)`
  - rollout `O(POVL)`
  - disagreement field `O(HL)`
  - relaxation `O(SH)`
  - `P≤64, O≤8, V≤12, H≤48, S≤6`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列E固有の進展

> **Outcome accessを完全に外すと、観測後residualで得られた限定信号は消える。自己整合不一致は候補内選択にはなり得るが、open-form候補を新生しない。Energy推論の前段に、outcome非参照で実行可能rolloutを生む構造候補birthが必要である。**

## 他系列へ返す知見

- A: 応答kernel比較も、介入後に有効な候補状態が生成されなければroute identity監査が空になる。
- B: Probe test以前に、別入力で実行可能なprogram候補をoutcome非参照で生成する必要がある。
- C: Source-only adapterはtarget outcomeなしで実行可能候補を生成できることを先に確認すべき。
- D: Functional endpoint kernelも、介入可能なendpoint候補がraw spanから形成されなければ全面0になる。

## 次の仮説

**Generative Candidate Birth from Energy-Lowering Boundary Split–Merge Dynamics**  
（energy低下型境界split–merge力学による生成的candidate birth）

次は既存edit prototypeの実行可能性をcandidate birthの前提にしない。

1. `before + command`全体を少数の可変境界segmentへ初期分割
2. Segmentのsplit・merge・移動を局所操作として生成
3. 各境界操作後に複数after rolloutを構成
4. Self-consistency disagreementとnon-target preservationが改善する操作だけ採用
5. Object/value/operation roleを固定せず、境界と結合を同時緩和
6. Candidate集合が空にならないbirth/death balanceを導入
7. Free/nudged二相でboundary-local creditを更新
8. 未知語・主語省略・計画変更・反実仮想のcandidate recallとexecution accuracyを主評価化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
