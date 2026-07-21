# 系列C Cycle 011 研究報告

## 仮説

**Context-Gated Mechanism Edge Separation with Counterfactual State Probes**  
（反実仮想state probeによる文脈ゲート付きmechanism edge分離）

Cycle 010では、匿名effect state間の順序transitionへ分解することでorder counterfactualを0.6333まで改善した一方、command clusterが平均1.33個へ潰れ、contextをほぼ無視した頻度automatonに留まった。

本Cycleでは、同じcommand候補を異なるcontext・before stateへ再適用したときのbefore/after有限差分を匿名probe signatureとして保持し、表面cluster内でeffectが衝突するedgeを分離できるか検証した。

## 先行研究整理

- Ng et al. (AISTATS 2025) は、複数environmentにおけるmechanism changeを利用したcausal representation識別を論じ、単一環境内の相関だけではなく十分な変化条件が必要であることを示す。  
  https://proceedings.mlr.press/v258/ng25a.html
- Lee et al. (2026) は、未知のmulti-node intervention targetでも少数environmentからcausal representationを回復できる有限標本条件を示す。  
  https://arxiv.org/abs/2603.25796
- WM3C (ICLR 2025) は、unseen environment一般化にcomposable causal componentsを利用するが、強い表現学習器とlanguage supervisionを使う。  
  https://proceedings.iclr.cc/paper_files/paper/2025/hash/79d86433c2acd12b6fa98553435d226e-Abstract-Conference.html
- Causal-JEPA (2026) はobject-level latent interventionによりinteraction-dependent reasoningを強制する。object maskだけでなく、介入によってshortcutを壊す点が本Cycleのstate/context probe思想と対応する。  
  https://arxiv.org/abs/2602.11389

## 他4系列との重複表

| 系列 | 最新中心 | 成功・失敗 | 未解決点 | C候補との判定 |
|---|---|---|---|---|
| A | scope候補のactive repair | 正答候補があるとgeneric success/failureで修復。unmarked candidate recall 0 | open-set scope proposal | 外部観測選択は重複のため棄却 |
| B | counterexample-guided role boundary | proposal recall 0.9037へ上がるがprecision 0.26、全能力0、探索爆発 | relation-preserving role induction | command span境界精密化は重複のため棄却 |
| D | boundary surprise + replay | 干渉後最新値0.3333、event F1崩壊 | retrieval-Jacobian boundary credit | episodic boundary/memoryは重複のため棄却 |
| E | edge intervention Jacobian | whole outcomeで引用付き候補は分離、Jacobian追加利得0 | residual classだけへのfactor獲得 | 局所credit/energyは重複のため棄却 |
| C | context/state probeでmechanism edgeを分離 | 本Cycleで検証 | open-set operation/context/object binding | 系列固有 |

継承知見:

- A: 正しい候補が存在しない場合、active repairは救えない。
- B: 反例数を増やしてもrelation identityを区別しなければroleにならない。
- D: surface surpriseや圧縮だけでは意味eventにならない。
- E: 詳細な介入factorは、既存factorを追加分割する情報がある場合だけ有効。

## 実装

学習器が受け取るもの:

- raw Japanese context
- raw Japanese command
- raw before / after state strings
- command order

与えないもの:

- operation ID
- context ID
- object / relation / value dictionary
- semantic slot
- morphology
- fixed ontology
- RAG / external LLM

方式:

1. `SurfaceAutomaton`
   - command residueの文字n-gramだけでcluster化
   - `latent state × command cluster -> effect symbol`
2. `ProbeSeparatedAutomaton`
   - before/after editを匿名effect symbolへ変換
   - contextとbefore stateのraw fingerprintをprobe軸にする
   - 同一surface group内でprobe effectが衝突するedgeを分割
   - sparse `(context probe, state probe, command edge) -> effect` gateを保持
3. Ablation
   - context probe削除
   - state probe削除

## 実験条件

- train sizes: 32 / 96 / 192
- seeds: 1 / 7 / 19
- 各split: 30例 / seed
- splits: seen、held context、held command、held both、3-step order counterfactual、alternate state、subject omission、raw multi-sentence free-Japanese gate

## 最大192例・3 seed平均

| split | Surface | Probe separated | No context | No state |
|---|---:|---:|---:|---:|
| seen | 0.5444 | 0.1444 | 0.0000 | 0.0000 |
| held context | 0.6333 | 0.0889 | 0.0000 | 0.0000 |
| held command | 0.5778 | 0.3444 | 0.1889 | 0.1889 |
| held both | 0.6444 | 0.3556 | 0.2667 | 0.2667 |
| order counterfactual | 0.5222 | 0.0556 | 0.0111 | 0.0111 |
| alternate state | 0.7111 | 0.1111 | 0.0000 | 0.0000 |
| subject omission | 0.4556 | 0.0556 | 0.0000 | 0.0000 |

## 資源

- Probe model: 13,556 bytes
- Surface model: 3,666 bytes
- Effect symbols: 16
- Probe command edges: 16
- Sparse gated edges: 152.67
- Candidate reads: 6
- Seen inference: 0.4085 ms/query
- Order inference: 0.4473 ms/query
- Peak RSS: 296,468 KiB（Python runtime込み）
- Complexity: train `O(N*H*G)`, infer `O(T*K*G)`, `K<=6`, sparse gate lookup `O(1)`
- Model < 1GB: pass
- weak smartphone actual benchmark: not run

## 判定

**中核仮説は強く反証。**

### Probe分離で性能が悪化

surface方式のseen 0.5444に対し、probe方式は0.1444。order counterfactualも0.5222から0.0556へ低下した。

### context/state probeを外すとほぼ0

contextまたはstate probeを外すとseenは両方0。これは文脈・状態が必要という肯定結果ではない。raw fingerprint gateがepisode-specific keyとして働き、近傍probeへ一般化できないことを示す。

### edge数が意味機構数を超えて分裂

本来3 operationに対し、probe command edgeは平均16。effect symbolも16。mechanismを分離したのではなく、状態文編集差とsurface variationの組合せへ過分裂した。

### Surface baselineの高めのheld得点も因果理解ではない

surface方式はcommand clusterが平均1個へ潰れ、頻度の高いeffectを返す。held context/commandの0.58〜0.64は、context理解やoperation generalizationではなくclass imbalance/backoffで説明できる。

### subject omission・複数段落・自由日本語は未成立

subject omissionはprobe方式0.0556。raw paragraphからcontext/command/state roleを自律生成する統合gateは0。今回のcommand/state配列は評価用制御入力であり、自由日本語理解の証拠ではない。

## 相関暗記と因果理解の反証条件

因果理解なら最低限、次を同時に満たす必要がある。

1. 同じoperationが別surface・別identity・別state formでも同じedgeへ集約される。
2. contextを削除すると選択的に悪化し、contextありでは未知表現へ転移する。
3. stateを変更した反実仮想でbranchが正しく切り替わる。
4. operation orderを変えたsequenceを再帰実行できる。
5. non-target relationを保存する。

今回1〜4が成立せず、surface/fingerprint memorizationと判定する。

## 系列C固有の進展

Cycle 010の「command cluster collapse」を、単純なprobe追加では解消できないことが分かった。

必要段階を更新する。

1. **State-variable proposal**: raw before/afterから再利用可能なrelation別変数を生成する。
2. **Operation edge proposal**: どの変数を変更・保存するかを表す。
3. **Context gate proposal**: edge適用条件をrelation単位で表す。
4. **Counterfactual edge separation**: state/context/order変更で異なる結果を出すedgeだけを分離する。
5. **Planning**: goalからedge列を探索する。

本Cycleは1〜3なしに4をraw fingerprintで近似し、過分裂した。

## 他系列へ返す新知見

- A: active probe前に、候補がepisode fingerprintではなく再利用可能変数を共有するか監査する。
- B: relation-preservation反統一は、状態全文editではなく複数fieldの変更・保存vectorを必要とする。
- D: replay時にraw state fingerprintをschema keyにするとepisode別名記憶へ分裂する。
- E: residual class splittingはraw fingerprint差ではなく、relation-level intervention outcome差で行う必要がある。

## 次仮説

**Relation-Selective State Variable Discovery from Preservation Contrasts**  
（保存対照からのrelation選択的状態変数発見）

次はcontext/state全文fingerprintを廃止する。同一objectの複数記述差分を比較し、介入で変化した文字区間と保存された区間の対照から、relation候補を生成する。

各operation候補について、changed relation、preserved relation、non-target object preservation、inverse restoration、order interaction、context-dependent enable/disableのvectorを作り、異なるrelation-selective vectorを持つedgeだけを別mechanismとして保持する。

最低成功条件:

- seen 0.5444を上回る
- order counterfactual 0.5222を上回る
- held command 0.5778を上回る、または正しい選択的棄権を示す
- command edge数を3〜8へ抑える
- context/state ablationで意味のある選択的差を出す
- raw paragraph candidate recallを0から改善
- 32KB未満、5ms/query未満、複数seed

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
