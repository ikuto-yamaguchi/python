# 系列D Cycle 010 研究報告

## 仮説

**Boundary-Surprise Fast States with Counterfactual Replay Compression**  
（境界驚きfast stateと反実仮想replay圧縮）

Cycle 009ではraw文字類似・recency・focus・successor表面予測を組み合わせたが、未学習follow-up想起0.2333に対しevent-pair F1は0.0154、20発話gapと干渉後最新値は0だった。

本Cycleでは各発話について「既存episodeへ追記」と「新episodeを開始」の2世界をfast stateへ同時保持し、boundary surpriseと後続表面予測で選択した。さらに睡眠型replayとして、隣接segmentの共有表面signatureに記述長削減がある場合だけ圧縮統合した。

## 先行研究整理

- ES-Mem (2026) は長期対話memoryで固定粒度とflat retrievalがsemantic integrityを壊す問題に対し、dynamic event segmentationとhierarchical memoryを提案する。https://arxiv.org/abs/2601.07582
- Smith & Zacks (2025/2026) はevent segmentationが自然な経験のmemory形成を支え、境界scaffoldingが干渉を減らし得ると整理している。https://doi.org/10.1177/09637214251350690
- Adaptive Memory Replay (CVPRW 2024) は、記憶が豊富で計算が制約される設定ではreplay選択自体が重要と報告する。https://arxiv.org/abs/2404.12526
- Task-Core Memory Management (2025) は長期continual learningで、識別的sampleを選択統合する。https://arxiv.org/abs/2505.09952

これらはreplay・segmentation・consolidationの重要性を支持するが、生の日本語から手書きontologyなしで境界候補を形成する原理は未解決である。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | 本Cycle候補との判定 |
|---|---|---|---|---|
| A | multi-timescale evidence semantics | change-point下流安全機構 | prototype複製、scope原因未形成 | 証拠意味校正は重複のため棄却 |
| B | cross-episode permutation anti-unification | program数・サイズ約半減 | 未知語順・述語0、proposal recall 0.61 | program生成は棄却。cross-episode監査思想のみ継承 |
| C | order-sensitive mechanism edge automaton | order反実仮想0.6333、2.3KB | operation cluster崩壊、context gating未成立 | 因果遷移は棄却。順序再生をreplay監査へ継承 |
| E | outcome-vector factor sufficiency | candidate recall 1.0 | local factor separability不足、margin 0 | energy緩和は棄却。候補差の独立計測を継承 |
| D | boundary surprise + counterfactual write/replay | 今回検証 | open-set event/update-target | 系列固有 |

## 実装

比較方式:

1. `Temporal`
   - explicit発話をevent startとし、それ以外を直前segmentへ追加。
2. `SurpriseReplay`
   - 既存segmentへの追記世界
   - 新event開始世界
   をfast stateで保持。
   - raw 2/3-gram surpriseとSTART/CONT後続surface統計で選択。
   - replay時、隣接segment統合でsurface signature記述長が減る場合だけ圧縮。

学習器が読むのはraw日本語と順序のみ。hidden event/entity/valueは評価器専用で、write/selectionには使用しない。

## 実験

- event数: 48 / 192 / 768
- seed: 1 / 7 / 19
- 既知follow-up
- 未学習follow-up
- 20発話gap
- topic shift
- 未学習follow-up＋質問
- 50件干渉後更新
- event-pair precision/recall/F1
- retrieval、容量、時間、fast状態数、replay統合数

## 最大768 event・3 seed平均

| 条件 | Temporal retrieval | Surprise retrieval | Temporal event F1 | Surprise event F1 |
|---|---:|---:|---:|---:|
| 既知 | 0.0417 | **0.1667** | 0.4639 | 0.0216 |
| 未学習follow-up | **0.1250** | 0.0417 | 0.4639 | 0.0698 |
| 20発話gap | 0.0833 | 0.0833 | 0.0086 | 0.0000 |
| topic shift | 0.1667 | **0.2083** | 0.0000 | 0.0000 |
| combined | **0.1250** | 0.0833 | 0.4639 | 0.0698 |

干渉後最新値:

- Temporal: 0.0000
- SurpriseReplay: **0.3333**

## 資源

最大規模・seen:

- model: 603,817 bytes
- training: 0.1188 sec
- inference: 6.7747 ms/query
- fast hypotheses: 2
- replay merges: 524.7
- segments after replay: 1771.3
- Peak RSS: 402,416 KiB（Python runtime込み）
- update: `O(G)`、fast worlds=2
- replay: `O(SG)`
- retrieval: top-8 segment、`O(SG)`

## 判定

**中核仮説は反証。**

### 限定的な支持

50件干渉後の最新値は0から0.3333へ改善した。既存episodeへ書く世界と新event世界を分けたことで、少数seedでは更新対象の保持に寄与した。

既知想起は0.0417から0.1667、topic shift想起は0.1667から0.2083へ上がった。

### 決定的な失敗

1. **境界精度が低い**
   - 既知event F1は0.0216。
   - 未学習event F1は0.0698。
   - 既知でTemporalの0.4639を大幅に下回る。

2. **未学習follow-upが悪化**
   - retrievalは0.1250から0.0417へ低下。
   - START/CONT successor表面統計はopen-set意味を形成していない。

3. **長gapは未解決**
   - event F1 0、retrieval 0.0833。
   - distractor列を独立eventへ過分割した。

4. **replay圧縮が意味統合ではない**
   - 約524.7 segmentをmergeしたが、最終segment数は1771.3でTemporal 768より多い。
   - 表面signature重複によるmergeで、semantic schema形成ではない。

5. **容量・速度が悪化**
   - model 603.8KB、推論6.77ms。
   - 20発話gapでは約2.8MB、47.7ms。
   - 1GB未満だが弱いスマートフォンで長期streamを扱う設計として不適格。

## RAGとの差

候補世界ごとにsegment write先を変更し、以後の内部retrieval stateを変えるため、固定文書検索ではない。しかしwrite先選択がsurface surpriseに依存し、意味的event memoryには到達していない。

## 破滅的忘却と表面暗記

干渉probeの部分改善は形成済みepisodeへの書込み保持を示す。一方、未学習follow-upとlong-gap event F1の崩壊は、形成済み知識が消えた破滅的忘却より、open-set境界・更新先生成の失敗が支配していることを示す。

## 系列D固有の進展

記憶統合に必要な信号を次へ分離できた。

1. **Boundary surprise**: 既存episodeでは説明しにくいか。
2. **Future retrieval utility**: 後続質問を改善するか。
3. **Interference cost**: 別episodeを壊さないか。
4. **Replay compressibility**: 複数episodeで再利用できるか。
5. **Semantic invariance**: 言い換え・長gap・別identityでも同じschemaか。

今回1と4を表面近似で実装したが、2・3・5を直接学習できず失敗した。

## 他系列へ返す新知見

- A: surpriseやconfidence単独では境界の正しさを保証しない。後続想起・誤干渉を独立観測にする。
- B: replay統合前にcross-form executionとevent-boundary precisionを監査する。
- C: transition replayはevent boundaryが誤ると別episode間を誤合成する。
- E: 境界候補のenergy factorにはfuture retrieval差とinterference差が必要。

## 次の仮説

**Retrieval-Jacobian Boundary Credit with Sparse Semantic Replay**  
（想起Jacobianによる境界creditと疎な意味replay）

各境界edgeだけを削除・反転し、後続質問、更新最新性、別episode誤干渉の有限差分を測る。

- `J_boundary,retrieval`
- `J_boundary,latest-value`
- `J_boundary,interference`

差を生まない境界候補は統合し、差を生むedgeだけfast stateへ保持する。睡眠replayではsurface signatureではなく、異なる表現・identityでも同じwrite/read Jacobianを持つedgeのみsemantic schemaへ圧縮する。

最低成功条件:

- seen event F1 0.0216とheld event F1 0.0698を同時改善
- held retrieval 0.0417を改善
- interference 0.3333を維持または改善
- gap event F1を0から改善
- 768 event model 256KB未満
- 5ms/query未満
- hidden label非使用

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
