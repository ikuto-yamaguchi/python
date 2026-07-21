# 系列D Cycle 009 研究報告

## 仮説

**Open-Set Discourse Event Segmentation with Multi-Channel Predictive Memory**  
（複数予測チャネルによる開集合談話イベント分節記憶）

前Cycleの `Effect-Grounded Bidirectional Discourse-Focus Fast Weights` は、既知cueでは長期gap・topic shift・継続更新へ耐えた一方、未知cue即時照応は0.0963であり、対象候補も実験側が二つ与えていた。

本Cycleでは引用済み二候補と明示identity groundingを廃止し、生の時系列日本語からイベント境界・更新先を形成する最小probeを実装した。各候補は単なる検索候補ではなく、異なるsegmentへ発話を局所書込みし、その後の検索対象とイベントpairを変える。

## 先行研究整理

- ES-Mem (2026) は長期対話で固定粒度memoryが意味的整合性を壊す問題に対し、dynamic event segmentationと階層memoryを提案している。ただし高性能encoderを用いるため、本研究の「1GB未満・弱CPU・手書きontologyなし」の候補生成原理とは別問題である。  
  https://arxiv.org/abs/2601.07582
- Memory Storyboard (CoLLAs 2026) はstreaming self-supervised learningで短期memoryを時間segmentへまとめ、長期memoryへ移す二層構造を報告している。視覚streamの結果であり、生の日本語の照応・更新先生成を直接解かない。  
  https://proceedings.mlr.press/v330/yang26a.html
- 2025年のevent/entity coreference研究では、局所mentionだけでなくdiscourse coherenceが重要と報告されている。  
  https://aclanthology.org/2025.acl-long.1134/
- episodic/semantic memoryをadaptive compressionとして捉える議論は、驚きや環境変化を捨てずsemantic memory自体を更新する必要性を強調する。  
  https://www.nature.com/articles/s44159-025-00458-6

## 他系列との重複表

| 系列 | 現在の仮説・中心機構 | 成功/失敗 | 未解決点 | D候補との判定 |
|---|---|---|---|---|
| A | 証拠channelのchange-point state | abrupt/speaker-local driftの誤確定を削減。未知surface coverageと変化直後が弱い | 証拠意味の構造原因 | 外部証拠校正は重複のため棄却 |
| B | execution-first anti-unification | 単一episode再現はcandidate precisionを上げず、探索量約150以上 | cross-episode置換実行 | program inductionは重複のため棄却 |
| C | mechanism-factored intervention tensor | 同一contextのmissing operation補完1.0、order counterfactual 0 | compositional mechanism edge | 因果機構形成は重複のため棄却 |
| E | learned local factors for scope attractors | candidate recallは改善したがmargin 0・精度0 | factor sufficiency | energy緩和は重複のため棄却 |
| D | raw discourseからsegment/write-targetを形成し未来想起を変える | 本Cycleで検証 | open-set event boundary/coreference | 系列固有 |

継承した知見:
- A: 内部confidenceやentropy低下だけでは現実の正しさを保証しない。
- B: 単一episode整合ではなく、別episodeで結果が変わる候補が必要。
- C: 表面signature補完と機構理解を分離評価する。
- E: candidate recallとfactorによるcandidate precisionを別指標で測る。

## 実装

比較方式:

1. `TemporalOnly`
   - explicit発話または短い時間gapでsegmentを作る。
2. `MultiChannelMemory`
   - raw文字2/3-gram整合
   - recency
   - 局所focus fast weight
   - segmentごとのsuccessor surface prediction
   を用いて、最大6既存segment＋new-event候補を保持する。

重要: 初期実装には評価用hidden identityがwrite側へ混入する箇所があったため棄却し、再実装した。最終実装で学習器が読むのは発話文字列、順序、汎用整合信号のみ。hidden event/entity/valueは評価器だけがevent-pair F1とretrieval accuracy算出に使う。

## 実験

- event数: 48 / 192 / 768
- seed: 1 / 7 / 19
- split:
  - 既知follow-up
  - 未学習follow-up表現
  - 20発話gap
  - topic shift
  - 未学習follow-up＋質問
  - 新規identity一回提示
  - 50件干渉後の更新
- 最大仮説: 7
- segment読出し: top 8

## 最大768 event・3 seed平均

| 条件 | Temporal retrieval | Multi-channel retrieval | Temporal event F1 | Multi-channel event F1 |
|---|---:|---:|---:|---:|
| 既知 | 0.2000 | 0.1667 | 0.3325 | 0.0153 |
| 未学習follow-up | 0.0667 | **0.2333** | 0.3325 | 0.0154 |
| 20発話gap | 0.1333 | 0.1000 | 0.0000 | 0.0000 |
| topic shift | 0.0333 | 0.0333 | 0.0000 | 0.0173 |
| combined | 0.0667 | **0.2333** | 0.3325 | 0.0154 |

追加probe:

| 指標 | Temporal | Multi-channel |
|---|---:|---:|
| 新規identity一回提示 | 1.0000 | 1.0000 |
| 50件干渉後の最新値 | 0.0000 | 0.0000 |

資源（768 event, seen）:

- Multi-channel model: 919,117 bytes
- Temporal model: 879,764 bytes
- Multi-channel training: 0.1556 sec
- Multi-channel inference: 4.2397 ms/query
- peak hypotheses: 7
- top reads: 8
- Peak RSS: 486,176 KiB（Python runtime込み）
- 推定計算量: update `O(HG)`、recall `O(SG)`、`H<=7`

## 判定

**中核仮説は強く反証。**

### 1. 未学習表面での局所改善はイベント分節成功ではない

未学習follow-up/combined retrievalは0.0667から0.2333へ上がったが、event-pair F1は0.0154である。正しいevent構造を形成したのではなく、質問との偶発的なsegment retrievalが改善したにすぎない。

### 2. event boundary precisionが崩壊

既知条件でMulti-channel event-pair precisionは0.0080、F1は0.0153。raw文字類似、recency、focus、successor表面予測は、同じeventと似た文型を区別できない。

### 3. 長gap・topic shift・干渉更新を解けない

20発話gapのevent F1は0、50件干渉後の最新値も0。前Cycleの既知cue 1.0は、形成済みcue schemaがある条件に限定されていた。open-set segmentationを導入すると、その前提が失われる。

### 4. 一回提示1.0は弱い

単独の明示発話が一segmentしかないprobeなので、構造創発・干渉回避の証拠ではない。

### 5. 容量が線形増加

768 eventで約897.6 KiB。1GB未満ではあるが、発話本文とsegment signatureを保持するため長期対話で線形増加する。semantic consolidationは成立していない。

## RAG/検索との差

本方式は各候補segmentへ発話を局所書込みし、以後のretrieval stateを変更するため、固定文書を検索するだけのRAGとは異なる。しかし今回の失敗は、局所書込みが意味的episodeではなくsurface clusterを形成したことを示す。

## 破滅的忘却と表面暗記の反証

- 一回提示: 1.0
- 50件干渉後更新: 0.0
- 未学習follow-up retrieval: 0.2333
- event F1: 0.0154

よって、形成済み記憶が単に消えたというより、更新発話を正しいepisodeへ接続できない。表面暗記とopen-set grouping failureが支配的である。

## 系列D固有の進展

今サイクルで、記憶問題をさらに明確に分離した。

1. **Boundary proposal**: どこでeventが切れるか。
2. **Update-target proposal**: どの既存episodeへ書くか。
3. **Counterfactual write/read audit**: 候補ごとに未来想起がどう変わるか。
4. **Semantic consolidation**: 複数episodeで再利用されるwrite/read schemaへ圧縮する。

前Cycleは2〜4を既知cue下で試した。今回は1を追加したが、surface-local channelでは1と2が同時崩壊した。

## 他系列へ返す新知見

- A: evidence channelの信頼性だけでなく、その証拠をどのevent stateへ適用するかのposteriorが必要。
- B: cross-episode program probeに、event boundaryとupdate-target precisionを追加する。
- C: 同じcontext signatureでも談話eventが違えば別のmemory updateになる。因果conditionとepisodic boundaryを分離する。
- E: candidate recallが高くても、event pair precisionが低い候補集合ではfuture-retrieval factorが平坦化する。

## 次の仮説

**Boundary-Surprise Fast States with Counterfactual Replay Compression**  
（境界驚きfast stateと反実仮想replay圧縮）

次は表面類似を主境界信号にしない。各新発話について、既存episodeへ書いた場合と新episodeを作った場合の双方を短期保持し、以下の予測差を測る。

1. 次発話の局所予測誤差
2. 後続質問での想起
3. 無関係episodeへの誤干渉
4. 更新後の最新値
5. 操作effectとの整合
6. replay時の圧縮利得

境界驚きが一度高いだけでは確定せず、複数channelで異なる未来を生成し、反復して支持された境界だけを低速memoryへ統合する。

必須成功条件:

- held retrieval 0.2333とevent F1 0.0154を同時改善
- 20発話gap event F1を0から改善
- interference latest valueを0から改善
- model growthをepisode全文線形保存より削減
- hidden identity/valueをlearnerへ渡さない
- 高校生級・自由日本語統合ゲートを別途維持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
