# 系列C Cycle 021 研究報告

## 仮説

**Stable Intervention Footprint Hyperedges with Non-Target-Preserving Effect Algebra**  
（非対象保存型効果代数を持つ安定介入footprint hyperedge）

Cycle 020の次案だった「最小success–failure介入cut」は、系列Bのfailure/success role因子と系列Eのcounterfactual factor swapに中心機構・反証条件が重なるため棄却した。

本Cycleでは、個々の対応edgeをcutする代わりに、raw before/after差分から各介入が状態文字列のどの局所領域へ波及したかを匿名footprintとして記録し、異なるobject・値・表現でも同じfootprintを持つruleをhyperedgeへ統合した。さらに、局所効果を合成した際にnon-target補助状態を保存するruleだけを優先した。

## 先行研究との関係

- 2025年AISTATSのgeneral-environment causal representation learningは、複数環境のmechanism changeから潜在DAGを識別できる条件を示す。ただし観測混合と環境変化の条件が定義済みで、生日本語から介入対象を生成する問題は別途残る。
- 2026年のfinite-sample causal representation研究は、少数の未知multi-node intervention環境でも潜在因果表現を回復できる保証を示すが、線形factor model等の仮定を置く。
- Causal-JEPAはobject-level maskingを潜在介入として使い、shortcutを防ぎinteraction reasoningを促す。しかしobject representationはencoder側で既に形成される。
- CausalARCは観測・介入・反実仮想feedbackを分離評価するtestbedを提供するが、world model自体は生成時に既知である。

今回の実験は、既知object slotや介入targetを与えず、raw文字差分の効果footprintだけで潜在状態変数hyperedgeを形成できるかを反証した。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との重複判定 |
|---|---|---|---|---|
| A | surprisal位相同期による予測role候補 | candidate recall部分回復 | 選択精度0.105未満、長距離崩壊 | 予測境界探索は棄却 |
| B | 置換閉包program非終端 | 既知精度0.7889 | 未知形式0、絶対MDL悪化 | grammar/MDL統合は棄却 |
| D | query-object-relation endpoint分離 | Rename write限定改善 | read悪化、link過剰 | 長期memory endpointは棄却 |
| E | factor swap残差role | object recall一部回復 | value recall全条件0 | factor swap/cutは棄却 |
| **C** | **介入footprint hyperedgeとnon-target保存型効果合成** | 今回検証 | world state variable形成 | 系列固有 |

継承知見:
- A: candidate recallと選択能力を分ける。
- B: 既知context内の置換閉包は意味抽象ではない。
- D: write transportとread endpointを混ぜない。
- E: factor swap前に最小十分factor境界が必要。

## 実験条件

- seed: 1 / 7 / 19
- 学習規模: 48 / 144 / 288 episode
- test split: seen / held paraphrase / rename / alternate state form / subject omission / multi-paragraph / plan revision / counterfactual future
- 比較: surface rule / recurrent footprint hyperedge / footprint + non-target-preserving compositional algebra
- rule上限64、hyperedge上限32
- hidden object / field / valueは評価器のみ

## 最大288 episode・3 seed平均

| 条件 | Surface | Footprint | Compositional |
|---|---:|---:|---:|
| seen | 0.0000 | 0.0000 | 0.0000 |
| held paraphrase | 0.0000 | 0.0000 | 0.0000 |
| rename | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.1991 | 0.1991 | 0.1991 |
| subject omission | 0.0000 | 0.0000 | 0.0000 |
| multi-paragraph | 0.0000 | 0.0000 | 0.0000 |
| plan revision | 0.0000 | 0.0000 | 0.0000 |
| counterfactual | 0.0000 | 0.0000 | 0.0000 |

Sequential counterfactual coverageは全方式0.0213、conditional accuracyは0.3333だった。

## 判定

**中核仮説は強く反証。**

### Footprint hyperedgeの能力増分が0

平均4個のhyperedgeを形成したが、Surface / Footprint / Compositionalのaccuracy・候補数・null率は全splitで同一だった。footprint groupingはrule classを能力上ひとつも追加分割・統合していない。

### Seenでも候補実行0

seen・held・rename・omitted・paragraph・plan・counterfactualではmean candidateが0、null率1.0だった。効果代数以前に、学習したcommand contextを新episodeへtransportできていない。

### Alternate 0.1991は表面信号

alternate stateだけaccuracy 0.1991、平均候補0.5417だった。しかし3方式同値で、区切り文字と短い局所contextの偶然一致によるもの。未知状態変数やrelation identityの証拠ではない。

### Non-target保存項も自明化

補助文字列「維持」の存在を検査したが、候補実行自体がほぼ0のため、compositional scoreはedge集合を変えなかった。non-target preservationを評価する前提となる実行可能transportが欠けている。

### 反実仮想coverageは実質0

Sequential counterfactual coverageは0.0213。両介入を順次実行できるpairがほぼ存在せず、conditional accuracy 0.3333は能力値として採用できない。

### 因果理解ではない

形成されたfootprintは、old/new長、prefix/suffix保存bit、future内文字包含bitである。object、state variable、relation、event、goal、constraint、causal directionは形成していない。

## 相関暗記と因果理解の分離

- 同一surface context再現のみ: 相関暗記
- cross-form transport 0: state-variable identityなし
- non-target保存の増分0: causal localityなし
- sequential intervention coverage 0.0213: compositionなし
- plan/omission/paragraph 0: object permanence・goal revisionなし

## 資源量

- Surface model: 38485 bytes
- Footprint model: 38623 bytes
- Compositional model: 38637 bytes
- Rules: 64
- Hyperedges: 4
- Training: 0.003434 sec
- Inference: 0.0120 ms/example
- Peak RSS: 112364 KiB（Python runtime込み）
- complexity: rule extraction `O(NL)` / footprint grouping `O(P)` / inference `O(PG)`, `P<=64`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

因果world model形成を次の11段階へ更新する。

1. Raw event proposal
2. Local transition executability
3. Null transport separation
4. Operation fiber
5. Latent state anchor
6. Sparse correspondence
7. Intervention-preserving cycle
8. **Stable intervention footprint**
9. **Executable effect hypergraph**
10. Counterfactual composition
11. Goal/constraint planning

今回は第8段階のsurface近似を実装したが、第9段階に必要な実行可能transportが未成立だった。

核心的知見:

> 効果footprintの再現性は、実行可能operationが既に存在する場合の状態変数同一性信号にはなり得る。しかしraw command contextからoperationをtransportできない段階では、footprint hyperedgeは空の分類器になる。

## 他系列へ返す知見

- A: surprise cellをactive queryで分割する前に、candidate actionがcross-contextで実行可能かを独立gate化する。
- B: derivation graph bisimulationは、同じsurface transitionでなく同じnon-target-preserving effect footprintを再現するか監査する。
- D: query/object/relation endpoint分離後も、write edgeが別state表現へ実行可能transportできることを必須化する。
- E: minimal factorのenergy consequenceを測る前に、そのfactorを含む介入が実行可能かをnull transportと分ける。

## 次の仮説

**Executable Effect Hypergraphs from Contrastive Transition Transport**  
（contrastive transition transportからの実行可能効果hypergraph）

次はfootprintを直接clusterしない。

1. raw before/afterから保存区間・変化区間の局所transition候補を生成
2. command contextを複数episodeへtransport
3. success / wrong / null transportを別edgeとして保持
4. 複数surfaceでsuccessし、同じnon-target footprintを持つtransitionだけhyperedge化
5. object変更・value変更・relation変更を別々のcontrastive transportで反証
6. 実行可能hyperedgeだけで sequential counterfactual を評価
7. 主語省略では談話focus候補を複数保持し、null endpointを許す

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
