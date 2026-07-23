# 系列D Cycle 017 研究報告

## 仮説
**Provenance-Gated Alias Links with Reconsolidating Sparse Address Traces**
（provenance gate付きalias linkと疎address trace再固定化）

Cycle 016ではobject/relation分離によりseen readが0から0.3472へ改善した一方、writeは0.0633へ崩壊し、renameでは8 canonical objectに対して30.33 traceへ過分裂した。今回はfast traceを即時mergeせず、episode provenanceを保持した一時alias linkを作り、別名経由のread/write改善・非対象破壊・複数session supportを観測してからslow linkへ再固定化できるかを検証した。

## 先行研究整理
- THEANINE (NAACL 2025) は古い記憶を削除せず、時間・因果linkでtimeline化する。
- RMM (ACL 2025) はmemory granularityとretrievalを前向き・後向きreflectionで更新する。
- PREMem (EMNLP 2025) は推論負荷を保存前のmemory構築へ移す。
- HiCL (2025) は疎pattern separation・episodic memory・replayを組み合わせる。
- 2026年のmulti-timescale memory研究はfast/slow内部変数からepisodic sensitivity・consolidation・forgettingを一体化する。

ただしこれらの多くはLLM encoder、既定memory item、task prototypeを前提とする。本Cycleはraw日本語spanから一時alias linkを作る上流問題を扱う。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | D候補との区別 |
|---|---|---|---|---|
| A | 可逆split/mergeによる境界・action共同提案 | 時間creditの危険条件を特定 | candidate recall 0 | 境界生成そのものは扱わない |
| B | 絶対MDL利得付き境界・program共同帰納 | seenで微小改善 | 未知形式0、圧縮利得負 | program商・MDLは扱わない |
| C | before/after transport anchor | conditional評価漏れを除去 | transport coverage 0 | world operation fiberは扱わない |
| E | span・residual共同創発 | raw basisの限界を特定 | candidate collapse | energy/cause basisは扱わない |
| **D** | **一時alias linkをread/write反証でslow schemaへ再固定化** | 今回検証 | 長期memory同値性 | 系列固有 |

## 実験
- event数: 36 / 108 / 216
- seed: 1 / 7 / 19
- 条件: seen / held paraphrase / rename / alternate state / long distractor / combined
- ablation:
  1. no alias
  2. temporary alias
  3. provenance-gated reconsolidation
- one-shot
- 36-event interference
- learner input: raw before / command / after / query / order
- hidden canonical object・field・valueは評価器専用

## 最大216 event・3 seed平均

| 条件 | No alias write/read | Temporary write/read | Reconsolidated write/read |
|---|---:|---:|---:|
| seen | 0.0556 / 0.2639 | 0.0556 / 0.2639 | 0.0556 / 0.2639 |
| held | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| rename | 0.1034 / 0.3958 | 0.1034 / 0.3958 | 0.1034 / 0.3958 |
| alternate | 0.1559 / 0.2222 | 0.1559 / 0.2222 | 0.1559 / 0.2222 |
| long | 0.0509 / 0.2639 | 0.0509 / 0.2639 | 0.0509 / 0.2639 |
| combined | 0.1651 / 0.2917 | 0.1651 / 0.2917 | 0.1651 / 0.2917 |

## 判定
**中核仮説は強く反証。**

### 1. alias linkの能力増分が0
全splitでtemporary / reconsolidatedはno-aliasとwrite/readが完全に同一だった。linkを作っても候補class・address選択・state updateを一件も改善しなかった。

### 2. slow linkが0
renameで平均12.33 link、combinedで11.67 linkを提案したが、slow linkは全条件0。複数session provenanceだけではread/write改善とnon-target非破壊を同時に満たさなかった。

### 3. linkは表面query共起へ退化
候補linkはquery gramとcross-session共起で作られた。canonical/alias同一性ではなく、同じrelation質問に現れた異objectまで候補化したため、信頼creditを得られなかった。

### 4. writeの上流失敗が継続
seen write 0.0556、held 0、combined 0.1651。relation traceが39〜52個へ分裂し、正しいwrite ruleの再利用前にaddress proposalが崩壊している。

### 5. one-shotは限定的、interferenceは0
one-shotは0.6667だが、同一episodeのbefore/command/afterを直後に使う局所再実行である。36-event interference後のalias readは0.0000で、長期address再発見は成立しない。

### 6. RAGとの差
内部memoryはstateを局所更新しようとするため文書検索だけではない。しかしreadは保存state上のsurface span一致、linkはquery共起であり、semantic integrationには未到達。

### 7. 破滅的忘却と表面暗記の分離
支配的失敗は形成済み知識の消失ではなく、初期address/link形成の誤り。
- slow link 0
- interference 0
- held write/read 0
- temporary/reconsolidated差0
よって破滅的忘却を論じる前に、表現を跨ぐ同値性証拠が不足している。

## 資源量
- reconsolidated model: 22977 bytes
- object traces: 16.00
- relation traces: 51.67
- links: 11.67
- slow links: 0.00
- addresses: 26.33
- fast updates: 35.67
- training: 0.3030 sec
- inference: 0.2612 ms/query
- Peak RSS: 160324 KiB（Python runtime込み）
- complexity: proposal `O(L²)`, link credit `O(AH)`, read/write `O((A+K)G)`, `A<=64`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列D固有の進展
1. raw mention proposal
2. object/relation trace separation
3. sparse address binding
4. temporary alias proposal
5. provenance retention
6. read/write counterfactual credit
7. **bridge episodeによるalias同値性証明**
8. reconsolidation
9. episodic-to-semantic consolidation

今回、第4〜6段階を実装したが、bridge episodeなしではslow linkが一つも形成されなかった。

> 同じrelation queryと時間的共起だけではalias同値性を証明できない。二つのsurface spanが同一のhidden state trajectoryへ可逆にtransportされるbridge episodeが必要。

## 他系列へ返す知見
- A: 時間supportやquery共起を境界同一性creditへ直接使わない。
- B: multi-view復号に同一trajectoryへ戻るbridge viewを追加しないとsurface roleが混ざる。
- C: latent state anchorは別表現のbefore/afterを同一trajectoryへtransportするbridgeで評価する。
- E: repeated residualをcause同一性にせず、surface変換後も同じtrajectoryを説明するかをenergy termにする。

## 次の仮説
**Bridge-Episode Alias Equivalence by Reversible State-Trajectory Transport**
（可逆state trajectory transportによるbridge episode alias同値性）

- 同一episode内または近接episodeで二つのsurface spanが同じbefore/after trajectoryへ接続されるbridgeを生成
- A→B表現置換とB→A置換の双方でwrite/readが保存される場合だけalias候補化
- non-target object・relation queryを壊すlinkは即時切断
- bridgeが複数sessionで再現したlinkだけslow schemaへ固定
- raw episodeは少数provenance反例だけ保持
- interference後にcanonical/alias両queryから同一stateへ戻れることを必須gateにする

## 最終状態
- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
