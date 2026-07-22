# 系列C Cycle 014 研究報告

## 仮説

**Temporal Co-Reference Object Nodes from Intervention Persistence Signatures**  
（介入持続signatureからの時系列照応object node形成）

Cycle 013では、object identity nodeが存在しない状態でclause交換・inverse・idempotenceを試し、surface edit監査へ退化した。本Cycleではrelation edgeより先に、複数時点の介入trajectory、局所状態anchor、直前focusから同一対象nodeを形成できるか検証した。

## 先行研究整理

- CVPR 2025のTemporally Consistent Object-Centric Learningは、object表現へtemporal consistencyを直接課すことで長期安定性とobject discoveryを改善した。ただしslot architectureと視覚表現を前提とする。
- 2026年のGrounded Correspondenceは、temporal identity維持を学習済みdynamicsではなく対応問題として扱える可能性を示す。ただし強い視覚backbone由来のinstance featureを前提とする。
- Causal Tripletおよびobject-centric CRLは、object-level表現が介入一般化に有利だが、latent object structure自体の識別は依然難しいと報告する。

参照:
- https://openaccess.thecvf.com/content/CVPR2025/html/Manasyan_Temporally_Consistent_Object-Centric_Learning_by_Contrasting_Slots_CVPR_2025_paper.html
- https://arxiv.org/abs/2605.03650
- https://arxiv.org/abs/2301.05169
- https://arxiv.org/abs/2310.19054

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との判定 |
|---|---|---|---|---|
| A | survival校正active probe | 一部条件で誤確定低下 | candidate recall低迷、probe意味なし | 外部観測policyは棄却 |
| B | adversarial misapplication program | 軽量候補削減 | accuracy不変、relation未形成 | clause/program帰納は棄却 |
| D | paraphrase write/read consolidation | episodeをschemaへ圧縮 | object-relation address喪失 | memory統合は棄却 |
| E | dual-residual null attractor | 平坦化解除の信号 | 誤候補一意化または全面停止 | energy routingは棄却 |
| C | temporal intervention persistenceからobject node形成 | 本Cycleで検証 | open-set identity | 系列固有 |

継承知見:
- A: 候補生存率だけでは意味的正しさを保証しない。
- B: candidate削減とrelation発見は別。
- D: 圧縮前にobject-relation addressが必要。
- E: 残差を原因edgeへ帰属できなければ誤収束する。

## 実装

比較方式:

1. `Surface`: 過去commandとの文字類似で全文editを再生。
2. `TemporalOnly`: clause anchorと直前focusだけでnode統合。
3. `Persistence`: clause anchor、command介入trajectory、直前focusを共同利用。
4. `NoTemporal`: temporal focusを除くablation。

学習器が読むのはraw before/command/after文字列と順序だけ。object ID、field ID、value辞書、形態素解析、固定ontology、RAG、外部LLMは未使用。

## 実験

- train sequence数: 12 / 36 / 72
- 1 sequence: 4 intervention
- seed: 1 / 7 / 19
- split: seen、rename、別状態表現、未知command、主語省略、複数段落、計画変更
- 3 objects × 3 fields

## 最大72 sequence・3 seed平均

| 条件 | Surface | Temporal only | Persistence | No temporal |
|---|---:|---:|---:|---:|
| seen | 0.0035 | 0.0000 | 0.0000 | 0.0000 |
| rename | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.0104 | 0.0000 | 0.0000 | 0.0000 |
| held command | 0.0174 | 0.0000 | 0.0000 | 0.0000 |
| subject omission | 0.0069 | 0.0000 | 0.0000 | 0.0000 |
| multi paragraph | 0.0104 | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0208 | 0.0000 | 0.0000 | 0.0000 |

## 資源量

- Persistence model: 25,820 bytes
- object-node候補: 3.67
- raw intervention: 288
- node merge: 284.33
- seen inference: 0.3298 ms/query
- rename inference: 0.3344 ms/query
- multi-paragraph inference: 0.4472 ms/query
- Peak RSS: 115,052 KiB（Python runtime込み）
- 推定計算量: train `O(N T H G)`、infer `O(H C G)`、`H<=64`

## 判定

**中核仮説は強く反証。**

### 介入持続signatureがobject nodeを過剰統合

288個の介入を平均3.67 nodeへ圧縮したが、全split accuracyは0。これはobject identityを発見したのではなく、似たclause anchorとcommand表面を同一nodeへ潰した結果である。

### temporal ablationとの差が能力へ現れない

PersistenceはNoTemporalよりnode数を減らしたが、双方ともaccuracy 0。直前focusはnode統合を変えただけで、正しい対象への再束縛を生まなかった。

### rename trajectoryを追跡できない

rename後も同じ介入trajectoryを持つという仮説だったが、surface anchorが変わると対応付け不能。rename accuracyは全方式0。

### 主語省略と計画変更は未成立

直前focusを保持しても、どのobjectへ書くかを表すaddress edgeがない。主語省略accuracy 0。撤回前後のgoalやoperation scopeも未形成。

### 圧縮は意味nodeではない

Persistenceは約25.8KB・3.67 nodeへ縮約し高速だったが、能力0。圧縮率やnode少数性をobject discoveryの証拠にできない。

## 相関暗記と因果理解の分離

- 相関暗記: command/clause文字類似によるcluster
- 因果理解に必要: 同一objectへ介入したときだけtrajectoryが変わり、別object・別relationが保存され、rename・省略後も同一nodeへ到達すること

今回、後者を満たす結果は0件相当であり、因果object nodeは形成されていない。

## 系列C固有の進展

object形成を次の段階へ分解した。

1. temporal mention proposal
2. intervention trajectory signature
3. **identity-selective non-target invariance**
4. rename/omission correspondence
5. relation-bearing edge attachment
6. event/goal/order dynamics

今回は1・2のsurface近似を実装したが、第3段階が欠落し、過剰統合した。

> 同じ時系列・介入patternを持つだけではobject identityにならない。候補nodeを別対象へ再束縛したとき、対象選択的に異なる未来を生む必要がある。

## 他系列へ返す知見

- A: object候補を分割するprobeは、文字trajectoryではなくtarget/non-target結果差を生成する必要がある。
- B: clause quotient前にidentity-selective misapplicationを独立評価する。
- D: memory addressはparaphrase数ではなく、別object query非干渉で識別する。
- E: persistence残差はcandidate node全体でなく、identity binding edgeへroutingする。

## 次の仮説

**Identity-Selective Intervention Partitions with Null Object Nodes**  
（帰無object nodeを持つ対象選択的介入分割）

候補object nodeごとに、同じoperationをtarget候補・別候補・rename候補へ実行し、targetだけが変化し非対象trajectoryを保存するoutcome partitionを生成する。どの候補も対象選択性を説明できない場合はnull objectへ棄権する。

最低成功条件:
- seen 0を改善
- rename 0を改善
- subject omission 0を改善
- no-intervention/no-temporal ablationとの差をaccuracyで示す
- object node 3〜12
- 32KB未満
- 5ms/query未満

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
