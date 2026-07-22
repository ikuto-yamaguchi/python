# 系列C Cycle 017 研究報告

## 仮説

**Latent-State-Specific Operation Algebra from Cross-Context Commutator Signatures**  
（文脈横断commutator signatureによる潜在状態別operation代数）

Cycle 016では、単一raw state上の文字編集の交換可能性をevent境界へ使用し、境界F1と順序反実仮想を悪化させた。原因は、文字位置の競合と、同じ潜在状態変数へ作用するworld operationの競合を同一視したことだった。

本Cycleでは各局所operation候補を、複数object・複数値・複数episodeへ再適用し、他operationとの `A→B` / `B→A` の結果をvector化した。文字位置が変わっても同じcommutator patternを示すoperationだけを同一familyへまとめれば、潜在状態変数別のoperation algebraを形成できるか検証した。

## 先行研究整理

- Varici et al., *Score-based Causal Representation Learning: Linear and General Transformations* (JMLR 2025) は、一般変換下の因果表現識別に複数の介入環境と十分な介入coverageが必要であることを示す。
  - https://jmlr.org/papers/v26/24-0194.html
- Ng et al., *Causal Representation Learning from General Environments under Nonparametric Mixing* (AISTATS 2025) は、より一般的な環境変化下での識別条件を扱う。
  - https://proceedings.mlr.press/v258/ng25a.html
- Bing et al., *Identifying Linearly-Mixed Causal Representations from Multi-Node Interventions* (CLeaR 2024) は、介入coverageと多様性が潜在因果変数の識別に重要であることを示す。
  - https://proceedings.mlr.press/v236/bing24a.html
- Mansouri et al., *Object centric architectures enable efficient causal representation learning* (ICLR 2024) は、複数objectの観測では通常のinjective表現仮定が崩れ、object-centric構造が必要になることを示す。
  - https://proceedings.iclr.cc/paper_files/paper/2024/hash/0396ca5a4c628936609aa819bfbca916-Abstract-Conference.html

これらはいずれも介入環境・潜在変数・object表現に一定の構造を仮定する。本研究の「生の日本語からoperation候補と潜在状態変数を同時生成する」問題はさらに上流に残る。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | C候補との重複判定 |
|---|---|---|---|---|
| A | 世界横断rank/null空間によるprobe basis | marked制御でprobe探索を効率化 | candidate recall低、locality増分0 | 外部probe選択は棄却 |
| B | 分離可能介入部分空間からprogram role | rank basisでprogram数削減 | role非識別、未知形式0 | program商・MDLは棄却 |
| D | provenance付きalias memory | object/relation分離でread限定改善 | write崩壊、rename過分裂 | 長期memory addressは棄却 |
| E | span/residual共同創発 | raw cause basisを固定名なしで試験 | unmarked candidate recall 0 | energy/cause routingは棄却 |
| **C** | **複数文脈で再現するoperation commutatorから潜在state family形成** | 今回検証 | operation executability・state binding | 系列固有 |

継承知見:
- A: localityやpartition gainだけでは意味的識別を保証しない。
- B: 数値rankやoutcome vectorだけではroleを識別しない。
- D: object軸とrelation軸を分けてもcross-form同値性がなければ過分裂する。
- E: candidate recall 0では下流の緩和・routingは救済不能。

## 実験

- 学習episode: 48 / 144 / 432
- seed: 1 / 7 / 19
- 保存operation上限: 64
- commutator比較operation上限: 12
- cross-context上限: 24 episode
- 比較:
  1. Surface shape family
  2. Single-context commutator family
  3. Cross-context commutator family
- 統合テスト:
  - seen
  - held paraphrase
  - alternate state representation
  - subject omission
  - multi-paragraph distractor
  - plan change
- 反実仮想:
  - 隣接operationの順序交換

学習器はraw `before / command / after`文字列と順序だけを使用する。hidden object / field / valueは評価器専用。

## 最大432 episode・3 seed平均

### 状態更新精度

| 条件 | Surface | Single commutator | Cross-context |
|---|---:|---:|---:|
| seen | 0.1420 | 0.1420 | **0.1420** |
| held paraphrase | 0.0000 | 0.0000 | 0.0000 |
| alternate state | 0.0000 | 0.0000 | 0.0000 |
| subject omission | 0.0000 | 0.0000 | 0.0000 |
| paragraph | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0000 | 0.0000 | 0.0000 |

### 順序反実仮想精度

| 条件 | Surface | Single | Cross-context |
|---|---:|---:|---:|
| seen | 0.6667 | 0.6667 | 0.6667 |
| held | 0.6429 | 0.6429 | 0.6429 |
| paragraph | 0.6653 | 0.6653 | 0.6653 |
| plan | 0.6327 | 0.6327 | 0.6327 |

## 判定

**中核仮説は強く反証。**

### 1. Cross-context commutatorの能力増分が0

Surface / Single / Cross-contextは全splitで状態更新精度と順序反実仮想精度が完全に同一だった。

commutator署名はfamily構造を変えたが、実行時に正しいoperationを追加選択できていない。

### 2. Family数だけが増加

seenで形成されたfamily数は、

- Surface: 17.67
- Single: 21.67
- Cross-context: 23.33

だった。

潜在状態変数へ縮約したのではなく、context-dependent surface signatureによりoperationを細分化した。

### 3. 未知表現では実行候補0

held / alternate / omitted / paragraph / planの平均実行候補数は全方式0で、状態更新精度も0だった。

commutator algebra以前に、表現を跨いでoperationを再実行するvalue bindingとstate bindingが成立していない。

### 4. seen精度も0.142

seenでも平均実行候補数は0.1698、精度は0.1420だった。

保存した64個のoperationの大半がquery commandへ適用できず、operation familyとして利用可能な水準ではない。

### 5. 順序反実仮想指標は過大評価

未知表現では両operationが実行不能で状態が変化しない場合でも、「異なるrelationなら順序交換結果が同じ」という評価を偶然満たす。そのため0.63～0.67の値は因果理解の証拠にならない。

この指標は次Cycleで「両operationが実行可能であること」を前提とするconditional metricへ変更する必要がある。

### 6. commutatorは意味state variableを識別しない

raw prefix/suffix editor間の可換性は、
- object
- relation
- latent state variable
- causal direction
- goal
- constraint

のどれに作用したかを表現しない。

異なる意味operationでも同じfailure patternを持ち、同じrelationでも表現変更により別signatureになる。

## 相関暗記と因果理解の反証条件

- seenのみ部分成功、未知表現0 → surface correlation
- family数増加、accuracy不変 → causal abstractionなし
- 実行不能でもcounterfactual得点 → metric leakage
- cross-object / cross-formで同じoperationを再実行不能 → operation identityなし
- plan changeで0 → goal/revision dynamicsなし
- subject omissionで0 → object permanence / discourse bindingなし

すべて因果理解側の条件を満たさなかった。

## 資源量

- Cross-context model: 9931 bytes
- operations: 64
- families: 23.33
- training: 0.1756 sec
- inference: 0.0119 ms/example
- Peak RSS: 160048 KiB（Python runtime込み）
- 推定計算量:
  - operation proposal `O(NL)`
  - cross-context commutator `O(PKC G)`
  - inference `O(PG)`
  - `P<=64`, `K<=12`, `C<=24`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列C固有の進展

因果世界モデル形成を9段階へ更新する。

1. raw object/event proposal
2. local transition executability
3. temporal regime proposal
4. operation candidate proposal
5. cross-context commutator signature
6. **cross-form operation executability and latent-state binding**
7. conditional counterfactual composition
8. goal/constraint planning
9. open-form Japanese integration

今回は第5段階のsurface版を実装したが、第6段階がないため能力増分0となった。

最大の新知見:

> 複数文脈で同じcommutator failure patternを示すことはoperation identityではない。各operationが異なる表現・object上で実際に同じ局所状態変数を更新できることを先に要求しなければならない。

## 他系列へ返す新知見

- A: cross-world outcome tensorへ実行不能状態を通常outcomeとして入れると、failure patternのrankだけが増える。
- B: tensor program roleは各viewで実行可能性を満たす候補だけを因子化すべき。
- D: provenance alias linkはread類似だけでなく、同じoperationをcross-formで実行できることを要求する。
- E: raw residual basisでは「実行不能」をcause basisとして過剰圧縮しないnull-cause分離が必要。

## 次の仮説

**Executable Operation Fibers with Conditional Commutator Algebra**  
（条件付きcommutator代数を持つ実行可能operation fiber）

次はoperationをcommutator signatureだけで統合しない。

1. raw edit候補を複数state representationへtransport
2. 同じ局所before→after変換を再現する候補だけをoperation fiberへ接続
3. object名・value・語順を変更してもfiber内で実行可能か検証
4. 両operationが実行可能なcontextだけでcommutatorを測定
5. 実行不能はoperation outcomeでなくnull transportとして分離
6. cross-form executionとconditional counterfactualの双方を満たすfamilyだけをlatent-state operation候補へ昇格

最低成功条件:
- seen 0.142を改善
- held / alternate / omittedの少なくとも1条件を0から改善
- conditional counterfactualでsurfaceを上回る
- family数32以下
- model 32KB以下
- inference 5ms以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
