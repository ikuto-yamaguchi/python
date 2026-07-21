# 系列E Cycle 008 — Intervention-Discriminative Scope Attractors with Learned Local Factors

## 結論

**中核仮説は反証された。** action/no-opへの介入差で識別可能なscope候補だけを保持し、free phaseと観測branchへclampしたperturbed phaseの局所特徴差からfactor重みを更新した。しかし、最大96例・3 seedで正答候補recallは通常0.978、入れ子1.0まで改善した一方、全splitで最良・次点energy marginが0となり、精度0・棄権1.0の平坦アトラクタへ収束した。

これはCycle 007の「候補集合に正解が入らない」失敗から一段進み、**正答候補が含まれていても、局所factor表現が候補間の役割・scope・revision差を識別できなければ緩和は選択不能**であることを示す。

## 開始時に確認した共有状態

- 共通branch `research/intelligence-swarm-coordination-001` の `STATE.md`、`EVIDENCE.jsonl`、`BACKLOG.md`を確認。
- 高校生級、ネイティブ日本語コミュニケーション、弱いスマートフォン実機検証、完成はいずれも未達。
- 最新研究PRとしてA #175、B #176、C #177、D #178、E #174を確認した。

## 他系列との重複表

| 系列 | 現在の仮説・中心機構 | 成功 | 失敗・未解決 | E候補との判断 |
|---|---|---|---|---|
| A | 証拠channel信頼度と可逆rollback | 未知・非回答の誤確定を棄権化 | 既知coverage低下、意味drift | 外部証拠校正は重複のため棄却 |
| B | 可逆role/effect格子、execution-firstへ移行 | MDLの統合・圧縮知見 | 実行可能候補生成が全面崩壊 | program proposal自体を中心にする案は棄却 |
| C | 複数operation効果signatureによる潜在condition factor | factor数を固定せず5 node形成 | zero-shot意味転移、誤bridge高確信 | 因果機構factor形成は重複のため棄却 |
| D | 効果接地型談話焦点fast weights | 学習済みcue・長gap・継続更新 | 未学習cue、曖昧時誤書込み | 長期記憶・照応統合は重複のため棄却 |
| E | 介入識別scope候補＋局所相関差学習 | 今回検証 | margin形成、scope/role識別 | 採用 |

## 継承した知見

- A: entropy低下や高confidenceは正しさを保証しない。
- B: 可逆性・短い記述長より実行可能性を先に監査する。
- C: surface scopeではなく複数operationへの異なる効果vectorが非同型性を与える。
- D: 候補は異なるworld結果だけでなく、異なる更新先・未来想起を生む必要がある。
- E Cycle 007: 全区間列挙はcandidate recallも意味的多様性も改善せず、固定factorの平坦化を招いた。

## 先行研究整理

Equilibrium Propagationはfree phaseとnudged phaseの固定点差から局所更新を得る。近年は時間変化入力・力学系への拡張や有限nudgeでの理論化が進んでいる。一方、これらは適切な状態変数・factor graphが既に与えられる前提であり、生の日本語からscope・role候補を生成する問題を直接解かない。

- Scellier & Bengio, *Equilibrium Propagation: Bridging the Gap Between Energy-Based Models and Backpropagation* (2017): https://arxiv.org/abs/1602.05179
- Pourcel et al., *Lagrangian-based Equilibrium Propagation* (2025): https://arxiv.org/abs/2506.06248
- Massar, *Equilibrium Propagation for Learning in Lagrangian Dynamical Systems* (2025): https://arxiv.org/abs/2505.07363
- Litman, *Equilibrium Propagation Without Limits* (2025): https://arxiv.org/abs/2511.22024
- Nabarro et al., *Learning in Deep Factor Graphs with Gaussian Belief Propagation* (ICML 2024): https://proceedings.mlr.press/v235/nabarro24a.html

## 新仮説

**Intervention-Discriminative Scope Attractors with Learned Local Factors**

> 入力中の候補scopeがaction/no-opで異なる局所予測を生む場合だけ保持し、観測branchへclampしたperturbed phaseとfree phaseの局所相関差でfactor重みを更新すれば、固定recency markerなしでscope・branch・plan revisionを正marginで選択できる。

### 単なるHopfield記憶との差

保存パターンへの最近傍復元ではない。入力ごとにcommand位置、scope、action/no-op branch、first/last revisionが異なる候補graphを生成し、候補ごとの局所feature energyを反復比較する。

### 停止条件

- 最良候補構造が前sweepと同一。
- 最大4 sweep。
- 最良・次点marginが0.01未満なら棄権。

### 反証分類

- 候補崩壊: 正答候補が候補集合にない。
- 平坦化: 正答候補を含むがmargin 0。
- 局所最適: 誤候補へ正marginで安定。
- 発散: 4 sweepで構造が安定しない。

## 最小実装

`intervention_scope_attractor_cycle8.py`

学習器が受け取るのはbefore state、自由日本語入力、after stateのみ。固定entity/value辞書、形態素解析、意味slot、ontology、RAG、外部LLM、問題別分岐は使用していない。世界生成器の正解scope metadataはcandidate recall評価だけに使用する。

1. 句点・改行で文候補を形成。
2. command候補上位3、連続scope最大2文を生成。
3. scopeがaction/no-op prototypeへほぼ同じなら候補を棄却。
4. command、branch差、attachment、revision、scope sparsityの局所featureを計算。
5. free最良候補と観測branchへclampしたperturbed最良候補のfeature差で局所重みを更新。
6. 最大16候補を疎緩和する。

## 実験条件

- train size: 24 / 48 / 96
- seed: 1 / 7 / 19
- 各split: 30件 / seed
- fixed factorとlearned local factorを比較
- split: 通常、未知context、未知command、双方未知、入れ子、複数段落、計画変更、反実仮想文
- 候補上限16、最大4 sweep

## 最大96例・3 seed平均

| 指標 | fixed | learned local factors |
|---|---:|---:|
| 通常 candidate recall | 0.9778 | 0.9778 |
| 未知context recall | 0.8444 | 0.9333 |
| 未知command recall | 1.0000 | 1.0000 |
| 入れ子 recall | 1.0000 | 1.0000 |
| 複数段落 recall | 0.4667 | 0.3778 |
| 計画変更 recall | 0.3889 | 0.3444 |
| 反実仮想 recall | 0.9778 | 0.9667 |
| 全split accuracy | 0.0000 | 0.0000 |
| 全split abstention | 1.0000 | 1.0000 |
| 全split margin | 0.0000 | 0.0000 |
| 平均sweep | 約2.0 | 約2.0 |
| 活性候補 | 約13.4〜16 | 約13.5〜16 |

学習後の平均重み:

- command: 1.0000
- branch scope差: 0.6894
- attachment: 0.1500
- revision: 0.0000
- sparsity: -0.0611

## 資源測定

- モデルサイズ: **20,660 bytes**
- 学習時間: **0.03775秒**
- 推論時間: **約0.39〜1.05 ms/query**
- Peak RSS: **306,452 KiB**（Python runtime込み）
- 計算量: proposal `O(H×V×G)`、sparse relaxation `O(S×H)`、`H≤16`, `S≤4`
- 1GB未満は満たす。弱いスマートフォン実機検証は未実施。

## 決定的な反証

### 1. Candidate recall改善だけでは選択できない

Cycle 007では通常candidate recall自体が崩壊していた。今回は通常0.978、入れ子1.0まで上がり、正答候補がほぼ集合へ入った。しかし最良・次点marginは全splitで0だった。

### 2. branchは識別できてもrole・scopeが同率

介入差でaction/no-op候補は絞れるが、同じbranchを生成する複数のcommand/scope/revision候補が同一featureを持つ。局所factorが対象、値、predicate、修飾先、訂正後目的を表現しておらず、候補graphを区別できない。

### 3. 局所学習は平坦化を解消しない

branch feature重みは1.0から約0.689へ変化したが、能力はfixed方式と完全に同じである。free/perturbed差がbranch軸にしか生じず、scope attachmentやrevisionへcreditが流れない。

### 4. revision factorは学習されない

計画変更candidate recallは0.344に留まり、revision重みは0のままだった。観測された最終stateだけでは、どの発話が撤回され、どの目的が有効かを局所的に識別できない。

### 5. 発散ではなく安定した平坦アトラクタ

約2 sweepで停止し計算は安定しているが、正しい意味状態ではなく全候補同率へ収束する。候補崩壊よりも、**factor sufficiency failure** が支配的である。

## 系列E固有の進展

系列Eの失敗を三段階へ分離できた。

1. **Candidate recall**: 正答候補を集合へ含める。今回、通常・入れ子で限定達成。
2. **Factor sufficiency**: 正答と誤答候補に異なる局所energyを与える。今回未成立。
3. **Attractor relaxation/local learning**: 十分なfactor上で安定収束し重みを局所更新する。第2段階不足のため有効性を判定不能。

> 正答候補recallが高くても、局所factorが候補間の実行・役割・談話差を表現しなければ、平衡伝播型更新は同率候補を分離できない。

## 他系列へ返す新知見

- A: 候補が存在するだけでなく、各質問候補を異なる観測予測へ写す十分なfactorが必要。
- B: execution-first候補の合否だけでなく、複数の実行可能候補を分けるrole/scope factorを監査する。
- C: 複数operation signatureはbranchを分けられるが、scope attachmentやrevision因果を別factorとして必要とする。
- D: 異なるmemory update targetが同じ局所featureならfast weightは平坦化する。未来想起差を直接factor化する。

## 次の仮説

**Outcome-Vector Factor Sufficiency with Revision-Causal Perturbations**

次は表面scope類似を主factorにしない。候補graphごとに以下の局所outcome vectorを実行生成する。

1. action/no-op結果
2. reverse結果
3. 別identityへの非干渉
4. 二段合成結果
5. 各commandを一つずつ除去したrevision反実仮想
6. 候補をmemoryへ書いた後の未来想起

観測と異なるoutcome vectorを持たない候補は同一仮説として商空間化する。perturbed phaseでは最終正答値だけでなく、command除去・逆操作・非対象保存の局所観測をclampし、scope/role/revision factorへcreditを与える。

必須成功条件:

- 通常candidate recall 0.978を維持。
- 通常accuracyを0から改善。
- 計画変更candidate recall 0.344とaccuracy 0を同時改善。
- marginを正にする。
- 候補商空間化後8候補以下。
- 平均4 sweep以下、5ms/query以下、32KB以下。
- 未知context・未知command・入れ子のいずれかで0から能力改善。

## 最終評価

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
