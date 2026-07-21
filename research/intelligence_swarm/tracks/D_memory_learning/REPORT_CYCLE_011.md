# 系列D Cycle 011 研究報告

## 仮説

**Retrieval-Jacobian Boundary Credit with Sparse Semantic Replay**  
（想起Jacobianによる境界creditと疎な意味replay）

Cycle 010では、境界surpriseと表面signature圧縮により一部想起・干渉耐性は改善したが、seen event F1 0.0216、held event F1 0.0698、long-gap event F1 0で、意味的event segmentationには失敗した。

本Cycleでは各境界edgeについて、直前episodeへ追記する候補と新episodeを開始する候補を仮実行し、後続のraw質問とraw応答がどのsegmentから再現されるかの差を有限差分creditとして用いた。

学習器はhidden event/entity/value labelを読まない。利用するのはraw日本語、順序、疑問符で識別される質問とその直後のraw応答だけである。hidden labelは評価器によるevent-pair F1と最新値精度の算出にのみ使用する。

## 先行研究整理

- ES-Mem (2026) は固定粒度memoryとflat retrievalが長期対話のsemantic integrityを壊すとして、dynamic event segmentationとhierarchical retrievalを提案する。https://arxiv.org/abs/2601.07582
- HiMem (2026) はtopic-aware event/surprise segmentationとreconsolidationを組み合わせるが、強い意味抽出pipelineへ依存する。https://arxiv.org/abs/2601.06377
- SeCom (2025) はmemory granularityがretrieval精度を左右し、segment-level constructionとcompression denoisingが有効と報告する。https://arxiv.org/abs/2502.05589
- ACL 2025のevent/entity coreference研究は、局所mentionだけでなくdiscourse coherenceが重要と報告する。https://aclanthology.org/2025.acl-long.1134/
- replay研究では保持と可塑性のtrade-offが残り、replay自体がsemantic abstractionを保証しない。https://arxiv.org/abs/2509.00047

これらはevent粒度・coherence・replayの重要性を支持するが、1GB未満・弱CPU・固定ontologyなしでraw日本語から境界を生成する原理は未解決である。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | 本Cycle候補との判定 |
|---|---|---|---|---|
| A | scope候補のactive executable repair | 正しい候補がある制御条件では修復1.0 | unmarked日本語candidate recall 0、逐次probe O(H) | 外部観測policyは重複のため棄却。候補差を実行で測る知見のみ継承 |
| B | counterexample-guided role boundary refinement | proposal recall 0.9037 | precision 0.26、全能力0、推論候補約400–480 | role/program誘導は重複のため棄却。relation-preservation監査思想のみ継承 |
| C | context-gated mechanism edge separation | surface baselineに限定信号 | probe方式が過分裂、order 0.0556 | 因果edge生成は棄却。raw fingerprint過分裂の反証を継承 |
| E | edge-intervention Jacobian factors | whole-outcomeで引用付き候補を分離 | Jacobian固有改善0、unmarked candidate recall 0 | energy/credit学習は重複のため棄却。増分情報0のfactorを取らない原則のみ継承 |
| D | boundary edgeが未来想起を変えるかを局所記憶creditにする | 本Cycleで検証 | open-set event/update-target/consolidation | 系列固有 |

## 実装

### 比較方式

1. `Surprise`
   - 現在segmentとのraw 2/3-gram noveltyだけで境界を作る。
2. `RetrievalJacobian`
   - 直前segmentへ追記する世界と、新segmentを作る世界を仮実行。
   - 直近10発話内のraw質問と直後応答について、直近8segmentから応答surfaceを再現できる差を計測。
   - `J = score(split) - score(append)` が閾値を超える場合だけ境界を変更。
   - 差が小さい場合はraw noveltyだけで保守的に決定。
3. `Sparse replay copy`
   - 各segmentのretrieval-active character featureを上位48個、replay tailを8発話へ削減。
   - hidden labelを使わない圧縮ablation。

### 実装上の反証と修正

初期版は各発話ごとに全segmentをdeep-copyし、60秒以内に完走しなかった。これは境界反実仮想の素朴実装が探索・コピー爆発することを示す。

最終版ではactive tailだけをcopyし、Jacobian評価も直近10発話・8segmentへ制限した。48 / 192 / 384 event、5 split、3 seedの全実験は21.11秒で完走した。

## 実験条件

- event数: 48 / 192 / 384
- seed: 1 / 7 / 19
- split:
  - 既知follow-up
  - 未学習follow-up
  - 20発話gap
  - topic shift
  - 未学習follow-up＋質問
  - 新規identity一回提示
  - 50件干渉後の最新値
- event-pair precision / recall / F1
- retrieval、圧縮後retrieval、容量、時間、credit活性率

## 最大384 event・3 seed平均

| 条件 | Surprise retrieval | Jacobian retrieval | Surprise event F1 | Jacobian event F1 |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 | **0.1667** | 0.0658 | **0.1733** |
| 未学習follow-up | 0.2500 | **0.2917** | **0.0516** | 0.0176 |
| 20発話gap | 0.0000 | **0.0833** | 0.0000 | **0.0278** |
| topic shift | 0.0000 | **0.0417** | **0.1075** | 0.0688 |
| combined | 0.2500 | **0.2917** | **0.0516** | 0.0176 |

追加probe:

| 指標 | Surprise | Jacobian |
|---|---:|---:|
| 新規identity一回提示 | 1.0000 | 1.0000 |
| 50件干渉後最新値 | 0.0000 | 0.0000 |

### 資源（384 event, seen）

- Jacobian model: 315706 bytes
- sparse replay copy: 272025 bytes
- sparse replay retrieval: 0.1250
- training: 0.1609 sec
- inference: 2.1901 ms/query
- segments: 663.3
- active boundary-credit rate: 0.1466
- mean absolute credit: 0.0817
- Peak RSS: 529248 KiB（Python runtime込み）
- online update: 局所窓では概ね `O(H*Q*S*G)`、H=2、Q<=10、S<=8
- recall: top-8 segment

## 判定

**想起Jacobianを境界creditへ使う部分には限定信号があったが、中核仮説は反証。**

### 限定的に支持された部分

同一benchmark内では、surface surpriseだけに比べて次を改善した。

- seen event F1: 0.0658 → 0.1733
- seen retrieval: 0.0000 → 0.1667
- long-gap event F1: 0 → 0.0278
- held retrieval: 0.2500 → 0.2917

したがって、境界が将来のraw question/answer retrievalを変えるかを直接測る信号は、seen条件のsurface noveltyより有益になり得る。

### 決定的な反証

1. **held event構造が悪化**
   - held event F1: 0.0516 → 0.0176。
   - retrievalだけを改善する大segmentへ誤統合し、意味的event boundaryを壊した。

2. **topic shiftでも誤結合**
   - event F1: 0.1075 → 0.0688。
   - target retrieval gainだけではunrelated topicの混入costを表現できない。

3. **長gapはほぼ未解決**
   - F1は0から改善したが0.0278にすぎない。
   - 20 distractorを跨ぐobject permanenceや照応を形成していない。

4. **干渉耐性は0**
   - 50件干渉後最新値は両方式0。
   - 更新対象episodeをopen-setで同定できない。

5. **sparse replayは意味圧縮ではない**
   - seen modelは約308.3KiBから265.6KiBへ約13.8%減っただけ。
   - held圧縮後retrievalは0.1667。
   - character feature trimmingであり、episodic→semantic memory統合ではない。

6. **長gapの容量・速度が失格**
   - long-gap model: 1291174 bytes。
   - long-gap inference: 12.2847 ms/query。
   - 1GB未満だが、弱いスマートフォンCPUで5ms以下という見込みを満たさない。

7. **raw質問応答pairへの依存**
   - learnerはhidden labelを使わないが、明示的な質問と直後応答という自己教師信号が必要。
   - 質問が存在しない経験、暗黙的結果、自由な主語省略から境界を作れない。

## RAGとの差

固定文書を検索するだけではなく、境界edgeの選択によって内部segment構造と後続retrieval stateを変更する。ただし、現在はraw質問応答の再現性を境界scoreに使うだけで、再利用可能な対象・relation・operation schemaは形成していない。

## 破滅的忘却と表面暗記の分離

- one-shot: 1.0
- interference latest: 0.0
- held retrieval: 0.2917
- long-gap event F1: 0.0278

一回保存自体は可能だが、長距離で正しいepisodeへ更新し続けられない。主問題は保存済み知識が消える破滅的忘却より、境界・更新先・照応のopen-set形成失敗である。

## 系列D固有の進展

記憶境界creditを次の三段階へ分離できた。

1. **Retrieval-sensitive boundary credit**
   - 境界の有無が後続想起を変えるか。seen条件で限定信号。
2. **Signed interference-sensitive credit**
   - unrelated topic・別episodeへの悪影響を負creditにする。未成立。
3. **Invariant semantic replay**
   - 表現・identityを跨いで同じwrite/read ruleへ圧縮する。未成立。

future retrieval差だけでは、retrievalに都合のよい大segment化を促し、event precisionを破壊することが分かった。

## 他系列へ返す新知見

- A: active probeは候補classを分けても、topic混合を悪化させ得る。retrieval gainとinterference costを同時に最適化する必要がある。
- B: relation-preservation program監査へ、後続質問の改善だけでなく別topic retrieval劣化を負例として加える。
- C: world transitionのsequence整合だけではepisode boundaryを決められない。異なるevent間の誤合成costが必要。
- E: retrieval Jacobianは増分情報を持ったが、単目的factorでは誤結合する。residual class splittingにはnegative-interference factorが必要。

## 次の仮説

**Signed Retrieval–Interference Jacobian with Reconsolidation Eligibility Traces**  
（符号付き想起・干渉Jacobianと再固定化eligibility trace）

次は境界edgeへ、正のretrieval gainだけでなく負のinterference costを同時に割り当てる。

- target query retrieval gain
- unrelated query degradation
- latest-value update gain
- topic-shift false merge
- delayed contradiction
- eligibility trace decay

境界は一度で低速memoryへ固定せず、複数ターンにわたり正の総creditを持つ場合だけreconsolidateする。負creditが蓄積したedgeは分割し、関連するfast writeをrollbackする。

最低成功条件:

- held retrieval 0.2917を維持または改善
- held event F1 0.0176を0.0516以上へ回復
- topic-shift event F1 0.0688を0.1075以上へ改善
- long-gap event F1 0.0278を改善
- interference 0を改善
- long-gap 5ms/query以下
- model growthをevent数線形未満へ近づける
- hidden label非使用

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
