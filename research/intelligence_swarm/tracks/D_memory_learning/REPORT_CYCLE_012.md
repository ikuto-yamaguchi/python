# 系列D Cycle 012 研究報告

## 仮説

**Signed Retrieval–Interference Jacobian with Reconsolidation Eligibility Traces**  
（符号付き想起・干渉Jacobianと再固定化eligibility trace）

Cycle 011では境界edgeの有無が後続想起を改善するかだけを正creditとして使い、seen event F1を0.0658から0.1733へ改善した一方、held/topic-shift event F1を悪化させ、検索に都合のよい大segmentへ誤統合した。

本Cycleでは各境界候補について、以下を共同評価する。

1. target queryへの想起gain
2. latest-value保持gain
3. unrelated entity混入によるinterference cost
4. distractor発話の分離
5. delayed contradiction
6. eligibility traceの時間減衰

境界は一回の局所gainで固定せず、split/append双方のcreditをfast traceへ蓄積し、差が閾値を超えた場合だけ再固定化する。

## 先行研究整理

- Event boundaryはepisodic memoryの再編成と干渉分離に寄与し得るが、境界直後は一時的に干渉へ脆弱にもなり得る。境界は常に保護的ではなく、正負双方の影響を持つ。Laing & Dunsmoor, 2025, DOI: 10.1162/jocn_a_02244。Bernhard et al., 2025, DOI: 10.1080/09658211.2024.2408321。
- ES-Memは長期対話で固定粒度・flat retrievalがsemantic integrityを壊す問題を示し、event segmentationと階層memoryを提案する。ただし強いencoder依存で、本研究の超軽量・slotなし候補形成とは別問題である。arXiv:2601.07582。
- Sparse Memory Finetuningは局所的に活性化したmemory slotだけを更新することで忘却を軽減するが、生の日本語から更新先を形成する上流問題は未解決である。arXiv:2510.15103。
- 2026年のexperience reuse研究は、external memoryでもnegative transferとretrieval競合が残り、詳細trajectoryより抽象procedural memoryが安定することを示す。arXiv:2604.27003。

## 他系列との重複表

| 系列 | 最新中心機構 | 成功・失敗 | 未解決点 | D候補との判定 |
|---|---|---|---|---|
| A | predictive-equivalence classとshared active probe | 大候補でprobe数半減、paraphrase/nested recall 0 | candidate proposal・null検知 | 外部観測policyなので中心重複として棄却 |
| B | multi-field relation-preservation anti-unification | 既知0.375、保存制約の増分情報0 | interventional relation contrast | program inductionなので棄却 |
| C | changed/preserved chunkからrelation state候補 | whole prototypeより軽量、preservation ablation差0 | adversarial relation surgery | causal state-variable発見なので棄却 |
| E | residual classへのadaptive factor acquisition | factor評価約半減、候補外でも76.17%誤収束 | null attractor・reality calibration | energy/factor acquisitionなので棄却 |
| D | retrieval gainとinterference costを境界creditへ統合 | 本Cycleで検証 | semantic replay・open-set update target | 系列固有 |

継承知見:

- A: 候補集合外を検知しないactive inferenceは高確信誤収束する。
- B/C: observational preservationはexact reconstructionへ包含され、増分情報にならない。
- E: 追加factorは残差候補classを実際に分割する場合だけ取得すべき。

## 実装

比較:

1. `PositiveOnly`
   - target retrieval gainのみでsplit/appendを決定。
2. `SignedEligibility`
   - target retrieval、latest-value、unrelated-entity混入、distractor、delayed contradictionを符号付きcreditへ統合。
   - split/append双方のeligibility traceを指数減衰。
   - credit差が閾値を超えた場合のみ境界を再固定化。

学習器はraw日本語、時系列、generic contradiction signalだけを使用する。hidden event/entity/valueは評価器専用で、境界決定には使用しない。

## 実験条件

- event数: 16 / 48 / 96
- seed: 1 / 7 / 19
- split: seen、held follow-up、20発話gap、topic shift、delayed contradiction、combined
- one-shot
- 50件干渉後のlatest-value更新

## 最大96 event・3 seed平均

| 条件 | Positive retrieval | Signed retrieval | Positive event F1 | Signed event F1 |
|---|---:|---:|---:|---:|
| seen | 0.1667 | 0.1667 | 0.3171 | **0.6092** |
| held | 0.2083 | 0.1667 | 0.2752 | **0.6240** |
| long gap | 0.1250 | **0.1667** | 0.0492 | **0.6616** |
| topic shift | **0.1667** | 0.1250 | 0.2050 | **0.4124** |
| contradiction | 0.0833 | **0.2500** | 0.2318 | **0.5674** |
| combined | **0.2083** | 0.1667 | 0.2752 | **0.6240** |

追加probe:

| 指標 | Positive | Signed |
|---|---:|---:|
| 新規identity一回提示 | 1.0000 | 1.0000 |
| 50件干渉後の最新値 | 0.0000 | **1.0000** |

## 資源

- seen model: 109131 bytes
- long-gap model: 477064 bytes
- seen training: 0.1494 sec
- seen inference: 1.5398 ms/query
- long-gap inference: 12.1303 ms/query
- seen segments: 186.0
- long-gap segments: 2014.3
- Peak RSS: 301300 KiB（Python runtime込み）
- 推定計算量: local update `O(HQG)`、eligibility `O(1)`、recall top-8 `O(SG)`

## 判定

**中核仮説は反証。ただし符号付き干渉creditには限定的な有効信号がある。**

### 支持された部分

- seen event F1: 0.3171 → **0.6092**
- held event F1: 0.2752 → **0.6240**
- long-gap event F1: 0.0492 → **0.6616**
- contradiction retrieval: 0.0833 → **0.2500**
- 50件干渉後latest-value: 0 → **1.0**

正の想起gainだけでなく、unrelated entity混入とlatest-value失敗を負creditへ入れることで、Cycle 011の巨大segment誤統合を部分的に抑え、更新先保持を改善した。

### 決定的な反証

1. **retrieval accuracyは安定改善しない**
   - held: 0.2083 → 0.1667
   - topic shift: 0.1667 → 0.1250
   - combined: 0.2083 → 0.1667

   event F1が改善しても、質問への正しい最新値想起は一貫して改善しない。境界精度とwrite/read semanticsは別能力である。

2. **long-gapで過分割**
   - segment数: 2014.3
   - model: 約465.9 KiB
   - inference: 12.13 ms/query

   distractorを分離する負creditが強すぎ、意味的episodeではなく発話単位の細粒度分割へ偏る。

3. **eligibility traceは意味schemaではない**

   traceはsplit/appendの二値creditを平滑化するだけで、対象、relation、operation、目的、制約を形成しない。再固定化の時間制御部品であり、semantic consolidation原理ではない。

4. **one-shot 1.0は弱い**

   候補が一つしかない単独明示発話であり、open-set groupingや少数例概念形成の証拠ではない。

5. **自由日本語統合ゲート0**

   主語省略、複数段落、自然な訂正scope、言い換え、自由対話、読解、計画、因果推論を同一内部構造で解けていない。

## RAGとの差

本方式は保存文を検索するだけでなく、境界候補に応じて発話のwrite先と将来のretrieval stateを変更し、delayed contradictionで再固定化creditを更新する。ただし内部表現は依然character signature中心で、semantic memoryではない。

## 破滅的忘却と表面暗記の分離

- one-shot: 1.0
- interference latest-value: 1.0
- held retrieval: 0.1667
- topic-shift retrieval: 0.1250

形成済み更新を保持する能力は改善した一方、未知表現・topic shiftで正しいupdate targetを形成できない。今回の主要失敗はparametric forgettingではなく、open-set write-target semanticsとsurface dependenceである。

## 系列D固有の進展

境界・記憶統合creditを4段階へ更新する。

1. Positive retrieval utility
2. Signed interference cost
3. Reconsolidation eligibility over delayed evidence
4. **Semantic write/read invariance across paraphrase, identity and relation**

本Cycleで2・3は限定的に成立した。4が未成立であり、event F1とretrieval accuracyが乖離した。

## 他系列へ返す新知見

- A: shared active probeの目的へtarget gainだけでなくunrelated-state degradationを入れる。
- B: adversarial misapplicationでは、別field破壊だけでなく将来retrievalの誤更新を負例にする。
- C: relation surgery成功後も、event境界・write targetが別ならlatest-state retrievalは失敗する。
- E: null attractorのenergyには候補外residualだけでなく、unrelated-state interference costを含める。

## 次の仮説

**Paraphrase-Invariant Write/Read Programs with Contrastive Eligibility Consolidation**  
（対照eligibility統合を持つ言い換え不変write/read program）

次は境界edge自体をsemantic memoryとみなさない。異なる表現・identity・relationで、同じ局所writeとreadの変換を生む候補だけをschemaへ昇格する。

各候補programを、paraphrase、identity置換、relation置換、topic shift、delayed correction、unrelated queryへ再適用し、target retrievalを改善しつつ非対象memoryを壊さない場合だけeligibilityを増加させる。

最低成功条件:

- held retrieval 0.1667を改善
- topic-shift retrieval 0.1250を改善
- interference latest-value 1.0を維持
- long-gap segment数を2014から大幅削減
- model 256KB未満
- 5ms/query未満
- hidden labelをlearnerへ渡さない

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
