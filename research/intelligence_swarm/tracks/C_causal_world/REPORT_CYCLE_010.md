# 系列C Cycle 010 研究報告

## 仮説

**Order-Sensitive Mechanism Edge Automata from Intervention Deltas**  
（介入差分からの順序依存mechanism edgeオートマトン）

Cycle 009では、context全体を1つの結果vector nodeとして保存すると、同一surface context内の未観測operation補完は1.0だった一方、未知contextは0.2875、操作順序反実仮想は0だった。

本Cycleではcontext全文を結果nodeとして保存せず、次の匿名構造を形成する。

1. before/afterの可逆編集差分から匿名effect symbolを生成
2. command表面をepisode固有状態文字列から分離し、surface clusterへ統合
3. `現在effect state × command cluster -> 次effect state` の疎なtransition edgeを局所学習
4. operation sequenceをedge連鎖として実行し、順序変更時の結果を生成

固定の機構名、意味slot、entity/value辞書、形態素解析、外部LLM、RAGは使用しない。hidden operation/context/mechanism IDはデータ生成器と評価器だけが保持する。

## 先行研究整理

- 介入下の因果表現学習では、複数環境・介入の違いから潜在因果変数を識別する条件が中心課題となる。  
  https://proceedings.mlr.press/v258/ng25a.html
- score-based causal representation learningは、一般変換下でも介入環境を使った潜在変数・因果graph識別条件を扱う。  
  https://www.jmlr.org/papers/v26/24-0194.html
- compositional causal effect modelは、unit全体を単一nodeとせずcomponent-level intervention effectへ分解すると未知component組合せへ一般化しやすいことを示す。  
  https://proceedings.mlr.press/v275/pruthi25a.html
- 複数介入の順序は結果へ影響し、単一介入評価だけではcompositionを評価できない。  
  https://proceedings.iclr.cc/paper_files/paper/2025/hash/7f5f9a88c6516469c83d074c6f2976fb-Abstract-Conference.html
- causal orderはsingle-variable interventionsの環境間差から抽出できるが、interventional faithfulness等の識別仮定が必要である。  
  https://proceedings.iclr.cc/paper_files/paper/2025/hash/7a41a2bc087b6d1981235d1718e53f51-Abstract-Conference.html

## 過去知見集約

- 共通STATE: 高校生級、ネイティブ日本語、弱いスマートフォン実機、完成はいずれも未達。
- 共通BACKLOG: 未知区間境界、将来予測・置換・介入整合性の共同競合、内部整合と意味妥当性の分離がP0。
- A Cycle 009: multi-timescale storeを作るだけでは同じsurface prototypeの複製となり、scope原因edgeと誤差帰属が必要。
- B Cycle 010: cross-episode permutationは既知programを半減できるが、candidate recall 0.6102、precision 0.5679でopen-form encoderは未成立。
- D Cycle 009: raw lexical/recency/focusでevent boundaryを作るとevent F1約0.015、長gap・干渉0。
- E Cycle 009: candidate recallとoutcome非同型性が成立しても、edge-local factor差が0ならmargin 0。
- C Cycle 009: context結果vectorは同一context補間に留まり、order counterfactual 0。

## 他4系列との重複表

| 系列 | 最新仮説・中心機構 | 実装 | 成功 | 失敗・未解決 | C候補との判定 |
|---|---|---|---|---|---|
| A | Causal-scope predictive state forks | 証拠scope候補とedge別error routing | change-point系で一部drift追従 | scope構造・world候補生成 | 外部証拠意味が中心なので棄却 |
| B | Counterexample-guided role boundary refinement | cross-episode置換実行とMDL統合 | 既知program数・サイズ半減 | 未知語順/述語0、proposal recall不足 | command program誘導が中心なので棄却 |
| D | Boundary-surprise fast states | memory boundary候補の仮書込み・replay | held retrievalの局所改善 | event F1・gap・干渉 | 長期記憶境界が中心なので棄却 |
| E | Edge-intervention Jacobian factors | graph edge有限差分とlocal credit | candidate recall/outcome差の分離 | local factor separability | energy/credit routingが中心なので棄却 |
| C候補 | effect-state transition edge composition | 匿名effect symbolと順序transition | 本Cycleで検証 | open-set object/operation/condition生成 | 採用 |

継承した部分知見:

- A: 保存階層ではなく、異なる将来予測を生成する状態edgeが必要。
- B: episode固有identityと再利用programを分離し、cross-episode再実行を監査する。
- D: 表面類似の局所改善をevent/world理解と混同しない。
- E: graph全体のoutcome差だけでなく、edgeごとの状態遷移差を内部表現へ持たせる。

## 実装

比較方式:

1. `SurfaceCompletion`
   - raw context n-gramが最も近いepisodeのoperation outcome列をコピー。
2. `MechanismAutomaton`
   - before/after文字列の共通prefix/suffix差分を匿名effect symbol化。
   - commandと状態文字列の最長共通spanを除き、command residueをsurface cluster化。
   - `(current effect symbol, command cluster) -> next effect symbol` を疎な局所countで更新。
   - sequence推論ではtransition edgeを再帰適用。

探索爆発抑制:

- effectは観測差分の完全同値で商空間化。
- command clusterは最大surface prototypeとの局所比較。
- transitionは疎dictionaryでO(1)読出し。
- 推論時にcontext episode全文を走査しない。

## 実験条件

- train size: 32 / 128 / 512
- seed: 1 / 7 / 19
- 各split: 60件/seed
- split:
  - 既知context・command
  - 未知context言い換え
  - 未知command表面
  - context/command両方未知
  - 3段operation order counterfactual
  - 別状態表現
- command種類・context機構・stateは評価器側だけが既知
- learnerはraw context / command / before / afterのみ使用

## 最大512例・3 seed平均

| 指標 | Surface completion | Mechanism automaton |
|---|---:|---:|
| 既知sequence | 0.3833 | **0.6611** |
| 未知context | 0.4222 | **0.6444** |
| 未知command | 0.2833 | **0.5500** |
| context+command未知 | 0.4056 | **0.6167** |
| order counterfactual | 0.3111 | **0.6333** |
| 別状態表現 | 0.3889 | **0.6611** |
| model bytes | 235,258 | **2,320** |
| seen inference | 8.2808 ms | **0.0961 ms** |

追加構造測定:

- anonymous effect symbols: 21
- command clusters: 1.33
- transition edges: 19.33
- candidate reads: 1.33
- Peak RSS: 396,888 KiB（Python runtime込み）
- 全実験時間: 12.610 sec
- 推定計算量:
  - train `O(N × K × P)`
  - infer `O(T × C × G)`、transition lookup `O(1)`

## 判定

**順序依存transition edgeという部分原理は限定支持するが、中核のopen-set因果世界モデル仮説は反証。**

### 支持された部分

1. order counterfactualが0.3111から0.6333へ改善。
2. context episode全文を保存するbaseline約229.7KBに対し、mechanism modelは約2.3KB。
3. 推論時間も約8.28msから0.096msへ短縮。
4. 別状態表現でも0.6611を維持し、surface context vectorコピーよりtransition再利用が強い。

よって、**介入結果列をcontext nodeとして丸ごと保存せず、匿名effect state間の疎な順序transitionへ分解する**ことは、順序反実仮想と軽量性の部品として有効。

### 決定的な反証

1. 既知sequenceでも0.6611に留まり、一般的なworld transition実行器ではない。
2. 未知commandは0.5500。command clusterが平均1.33個へ過剰統合され、異なるoperation roleを十分分離していない。
3. 未知contextが0.6444なのはcontext意味理解ではない。現実装はcontextをtransition選択へほぼ使用せず、学習頻度の高いtransitionへbackoffしている。
4. effect symbolは意味変数ではなく、状態文の編集差分21種類。object、relation、constraint、goalを自律生成していない。
5. order改善は制御世界の既知surface commandと固定状態形式に依存する。自然な複数段落、主語省略、計画変更、自由対話・読解・計画は未成立。
6. command clusterを強く商空間化したため、異なるoperationを同一clusterへ混同する。小型化と因果識別性のtrade-offが未解決。

## 相関暗記と因果理解の分離

- baselineはcontext表面からwhole outcome列をコピー。
- mechanism方式は順序を変えた3段sequenceへtransitionを再帰適用し、baselineを上回った。
- ただし未知command/contextで完全転移せず、operation identityとcondition mechanismを獲得していない。

したがって「単純なwhole-sequence相関暗記を超えた局所transition再利用」は示すが、「因果方向・機構・目的・制約理解」は示さない。

## 自由日本語統合ゲート

次は能力証拠として採用しない:

- 主語省略: 対象候補を自律解決していない。
- 複数段落: discourse eventを形成していない。
- 計画変更: revision scopeを扱っていない。
- 自然な反実仮想: 制御operation sequenceのみ。
- 自由対話/自由記述: 未実装。

統合ゲートは0。

## 系列C固有の進展

因果世界モデル形成を次へ分離できた。

1. **Effect-state discovery**: 観測差分を匿名状態symbolへ商空間化。
2. **Operation-conditioned transition**: action表面と現在effect stateから次stateを予測。
3. **Context mechanism gating**: 文脈条件で有効edgeを選ぶ。
4. **Object/relation binding**: 別identity・relationへ同じedgeを再束縛。
5. **Goal/constraint planning**: 目的状態からoperation列を選ぶ。

本Cycleでは1と2を限定的に実装。3〜5は未成立。

## 他系列へ返す新知見

- A: 予測状態候補はcontext nodeではなく、順序を変えると異なる未来を生成するtransition edgeへ分解すべき。
- B: program監査へ単発afterだけでなく、current-effect-stateを変えたsequence再実行を追加すべき。
- D: event memoryには発話列だけでなく、operation後にどの匿名stateへ遷移したかを保存するとsequence replayを圧縮できる可能性がある。
- E: edge Jacobian factorは、単一graph outcomeだけでなく、transition前stateを変えた有限差分を含める必要がある。

## 次の仮説

**Context-Gated Mechanism Edge Separation with Counterfactual State Probes**  
（反実仮想state probeによる文脈ゲート付きmechanism edge分離）

次はcommand surface similarityだけでclusterを作らない。

各候補command edgeを、異なるcurrent effect state・context・identityへ再実行し、

- outcomeが変わるstate
- outcomeが変わらないstate
- 別identityへの非干渉
- reverse/restore
- operation order交換

の有限差分signatureで分離する。

必須条件:

- command cluster数を実質operation多様性へ近づける
- seen 0.6611を改善
- held command 0.5500を改善
- held contextの見かけのbackoff成功を、context ablationで監査
- order counterfactual 0.6333を維持または改善
- 32KB未満、5ms/query未満、複数seed
- 主語省略・複数段落・計画変更の漏洩gateを維持

## 再現

```bash
python research/intelligence_swarm/tracks/C_causal_world/order_sensitive_mechanism_edges_cycle10.py \
  --output research/intelligence_swarm/tracks/C_causal_world/results_cycle_010.json
```

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
