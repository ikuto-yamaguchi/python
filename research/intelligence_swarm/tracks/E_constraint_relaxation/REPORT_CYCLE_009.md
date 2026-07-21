# 系列E Cycle 009 研究報告

## 仮説

**Outcome-Vector Factor Sufficiency with Revision-Causal Perturbations**  
（結果ベクトルによるfactor十分性と訂正因果摂動）

Cycle 008では、通常・未知command・入れ子で正答candidate recallがほぼ1まで改善した一方、全候補が同じ局所featureを持ち、margin 0・精度0・全面棄権となった。

本Cycleでは、候補graphごとに次の反実仮想結果ベクトルを実行生成し、final-stateだけをclampする方式と比較した。

1. 最終world一致
2. inverseによる初期状態復元
3. 非対象identityの保存
4. command除去時の結果差
5. future recall結果

free phaseとperturbed phaseで選ばれる候補の局所feature差を用い、固定weightではなく局所更新でscope・revision・branchへcreditを流せるか検証した。

## 先行研究整理

- Generalized Lagrangian Equilibrium Propagation (2025) は、time-varying系へEPを拡張する際、境界条件と軌道全体の変分記述が重要であり、forward-only・局所学習を保つ方式が限定されることを示す。  
  https://arxiv.org/abs/2506.06248
- Equilibrium Propagation Without Limits (2025) は有限nudgeでも局所energy微分の期待値差から正確なgradientを得られる条件を整理した。  
  https://arxiv.org/abs/2511.22024
- Conditional NCEの研究では、局所energy差だけではmulti-modalなmode間の相対energyを学びにくく、modeを直接またぐ比較が必要とされる。  
  https://openreview.net/forum?id=07OWUWmUHp

これらは「十分な状態変数・局所factorが存在する」ことを前提とする。本Cycleは、生の日本語候補graphにその前提が成立しているかを直接反証する。

## 他4系列との重複表

| 系列 | 最新中心機構 | 成功・失敗 | 未解決点 | E候補との判定 |
|---|---|---|---|---|
| A | evidence-channel change-point state | abrupt/speaker-local driftの誤確定を削減。変化直後・gradual drift・未知surfaceが弱い | 証拠意味の構造原因 | 外部証拠校正は重複のため棄却 |
| B | execution-first anti-unification | 単一episode再現ではcandidate precisionが上がらず、候補読出し約150以上 | cross-episode置換実行 | program生成は重複のため棄却 |
| C | mechanism-factored intervention tensor | 同一context内missing-operation補完1.0、order counterfactual 0 | compositional mechanism edge | 因果機構発見は重複のため棄却 |
| D | open-set discourse event segmentation | held retrievalは局所改善、event F1約0.015、長gap・干渉更新0 | boundary/update-target proposal | memory形成は重複のため棄却 |
| E | outcome-vector factor sufficiency | 今回の固有対象 | 局所factorへ結果差を流せるか | 採用 |

継承した知見:

- A: confidence・entropy・marginの内部量だけでは現実の正しさを保証しない。
- B: 単一episode整合ではなく、置換・反実仮想で候補precisionを監査する。
- C: outcome vectorの補完と機構理解を区別する。
- D: 候補recallとcandidate precisionを独立評価する。

## 既存方式との差

単なるHopfield記憶では、固定patternへの再生誤差を最小化する。本方式では候補graphが生成する複数のworld outcomeを局所factorへ分解し、free/perturbed phase差からweightを更新する。

- dense embedding・attention・backpropagationを使わない
- 候補は疎な離散graph
- 更新は候補featureの局所差のみ
- 推論は最大32候補・4 sweepの離散緩和
- 動的停止は最良構造の安定または最大sweep

ただし今回は局所factor表現自体が不足し、学習原理の有効性を支持しなかった。

## 実装

入力中の文境界と一般的な引用区間から、以下が異なる候補を最大32件生成した。

- command文
- target候補
- destination候補
- action/no-op branch
- first/last revision choice

意味辞書、形態素解析、固定entity/value一覧、RAG、外部LLMは使用していない。ただし引用記号に依存する制御probeであり、完全に無標識な日本語ではcandidate recallが0となる。

比較方式:

1. `final_only`: final-state一致だけでperturbed候補を選ぶ。
2. `outcome_vector`: final-state、inverse、non-target preservation、command removal、future recallを共同clampする。

## 停止条件と反証分類

停止条件:

- 最良候補構造が前sweepと同一
- 最大4 sweep
- 最良・次点margin < 0.005なら棄権

反証分類:

- **候補崩壊**: 正答実行候補が候補集合に存在しない
- **factor平坦化**: 正答候補は存在するが局所featureが同一
- **局所最適**: 誤候補へ正marginで収束
- **発散**: 最大sweepまで構造が安定しない
- **全面棄権**: margin 0で全入力を拒否

## 実測結果

学習量24 / 96 / 384、seed 1 / 7 / 19、各split 120件。

### 384例・3 seed平均

| 指標 | final-only | outcome-vector |
|---|---:|---:|
| 通常candidate recall | 1.0000 | 1.0000 |
| 通常精度 | 0.0000 | 0.0000 |
| 通常棄権率 | 1.0000 | 1.0000 |
| 未学習revision recall | 1.0000 | 1.0000 |
| 未学習revision精度 | 0.0000 | 0.0000 |
| 入れ子recall | 1.0000 | 1.0000 |
| 入れ子精度 | 0.0000 | 0.0000 |
| 反実仮想recall | 1.0000 | 1.0000 |
| 無標識日本語recall | 0.0000 | 0.0000 |
| 平均margin | 0.0000 | 0.0000 |
| 平均sweep | 2.0000 | 2.0000 |
| 活性候補数 | 32.00 | 32.00 |
| 推論時間 | 0.8569 ms | 0.9916 ms |
| モデルサイズ | 140 B | 140 B |

追加測定:

- Peak RSS: 399,528 KiB（Python runtime込み）
- 推定計算量: proposal `O(L²)`、relaxation `O(SH)`、`H<=32`, `S<=4`
- 学習後weightは両方式とも `[0.0, 0.05, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0]`

## 判定

**中核仮説は強く反証された。**

### 1. candidate recall 1.0でも精度0

引用付きの通常・未学習revision・入れ子・反実仮想では、正答を実行できる候補が全件候補集合へ入った。

それでもfinal-onlyとoutcome-vectorの精度は全条件0、棄権率1.0、margin 0だった。

Cycle 008の「candidate recall不足」から一段進み、今回の主因はfactor sufficiency不足と確定できる。

### 2. outcome vectorをclampしても局所weightが変わらない

final-onlyとoutcome-vectorのweightが完全に同一で、学習前priorから変化しなかった。

正答候補と誤候補は異なるworld outcomeを生成するが、局所feature tupleでは、scope、target role、revision cause、command removal effect、future recall targetの差が表現されていない。

そのためfree候補とperturbed候補が異なっても、feature差が0となりcreditが流れない。

### 3. EP/局所学習以前の表現失敗

最大2 sweepで安定しており発散はない。停止先は全候補同率の平坦アトラクタである。

これはEPのupdate ruleが失敗した証拠ではなく、局所energy derivativeが候補間で同じになる状態表現しか用意できていないことの反証である。

### 4. 無標識日本語はcandidate recall 0

引用区間を外した自由日本語ではcandidateを一件も生成できなかった。

したがって、生の自由な日本語から対象・変数・操作・目的・制約を創発した証拠はない。

### 5. 動的計算深度は無効

outcome-vectorは通常約0.992 msで32候補を評価したが、能力改善は0。弱いCPU向け計算量は小さいものの、無能力な反復なので採用できない。

## 系列E固有の進展

系列Eの必要条件を四段階へ更新した。

1. **Candidate recall**: 正答候補を含める。引用付き制御入力では今回1.0。
2. **Outcome non-isomorphism**: 候補が異なるworld結果を生成する。今回成立。
3. **Local factor separability**: outcome差が局所feature差として現れる。今回未成立。
4. **Attractor relaxation / local learning**: 分離可能factor上で安定収束・局所更新する。第3段階不足のため評価不能。

今回の新知見:

> 候補が異なる結果ベクトルを生成するだけでは不十分。各結果差が、どのscope・role・revision edgeに由来するかを局所的にfactor分解できなければ、free/perturbed phase差はweight更新へ伝わらない。

## 他系列へ返す新知見

- A: 異なる未来を生成する候補でも、証拠差をどの状態edgeへ帰属するかがなければ能動質問後の更新は平坦化する。
- B: cross-episode実行結果を得るだけでなく、結果差をrole/scope edgeへ局所帰属できる表現が必要。
- C: outcome tensor補完とmechanism edge attributionを分ける。結果vector一致だけでは因果edgeは学べない。
- D: future retrieval差を得ても、どのboundary/update-target edgeが差を生んだか局所creditが必要。

## 次の仮説

**Edge-Intervention Jacobian Factors with Sparse Causal Credit Routing**  
（edge介入Jacobian factorと疎な因果credit routing）

次は候補graph全体のoutcome vectorを一括特徴にしない。

各candidate edgeについて、そのedgeだけを削除・反転・別targetへ再束縛・scope外へ移動・revision前後で交換した場合のoutcome差を有限差分Jacobianとして計測する。

局所factorは `J(edge,outcome) = outcome(G) - outcome(G minus edge)` を保持し、perturbed phaseで観測outcomeをclampした際、差を生んだedgeだけへcreditを流す。

必須成功条件:

- candidate recall 1.0を維持
- 通常・held・nestedのmarginを0から正へ
- final-onlyより精度を改善
- 無標識日本語candidate recallを0から改善
- 候補16以下
- sweep 4以下
- 32KB以下
- 5ms/query以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
