# 系列C Cycle 026 研究報告

## 仮説

**Success-Conditioned Event Identity from Factorized Intervention Target Signatures**  
（因子別介入target signatureによるsuccess条件付きevent identity）

Cycle 025ではsuccess / wrong / null / damage / future整合の環境別残差をまとめた結果、64 eventすべてが1 classへ崩壊した。原因は、identity類似度がnull transportに支配されていたことだった。

今回はnullとwrongを類似度から完全に除外し、次を満たすeventだけをidentity候補にした。

- 4環境中2環境以上で各2回以上success
- 全環境を通してwrong 0
- success episode上だけでobject候補・value候補・state-context候補を独立swap
- target reconstruction、non-target damage、future consistencyを別成分化
- 同じ正のtarget signatureを持つeventだけをidentity classへ統合

## 先行研究整理

- Varici et al., **Score-based Causal Representation Learning** (JMLR 2025): 一般変換下の因果表現同定には、hard interventionではnodeごとの複数介入が必要であり、正の介入情報が本質となる。  
  https://www.jmlr.org/papers/v26/24-0194.html
- Li et al., **On the Identifiability of Causal Abstractions** (AISTATS 2025): 任意部分集合への介入では、回収可能な構造は介入集合に依存する高位抽象までに制限される。  
  https://proceedings.mlr.press/v258/li25g.html
- Yao et al., **Unifying Causal Representation Learning with the Invariance Principle** (ICLR 2025): 多くのCRL方式は因果性そのものよりデータ対称性へ整合している可能性がある。  
  https://proceedings.iclr.cc/paper_files/paper/2025/hash/85381f4549b5ddf1d48e2e287d7d3d15-Abstract-Conference.html
- Lee et al., **Beyond identifiability** (2026): 少数環境・有限標本での回収には、未知介入targetを識別できる摂動条件が必要。  
  https://arxiv.org/abs/2603.25796

既存研究は観測変数・潜在混合・介入環境を数学的に定義する。今回の課題は、それらを与えず、生の日本語文字列からevent・target・state variableを同時形成できるかである。

## 最新PR・他系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Cとの分離 |
|---|---|---|---|---|
| A | 責任重み付き前向きcommitment | 無条件carryで主語省略候補recall増加 | event gateが全面終了へ退化 | 談話予測責任は扱わない |
| B | Role-exchange binding seed | 三者交差でsurface anchor回収 | Rename・省略でbinding 0 | MDL・導出置換は扱わない |
| D | 因子別endpoint再固定化ladder | read/write分離で悪化抑制 | stable endpoint 0 | 長期memoryは扱わない |
| E | constraint-edge birth before commutator | null安全停止 | 交換子prototype 0 | energy dynamicsは扱わない |
| **C** | **正の実行証拠に条件付けたfactorized event identity** | 今回検証 | event identity・state target | 系列固有 |

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- environment: 標準、言い換え、Rename、別状態表現
- test: 既知、言い換え、Rename、別状態表現、主語省略、複数段落、計画変更、反実仮想
- event上限: 64
- class graph edge上限: 96
- ablation:
  1. Surface
  2. Success-conditioned identity
  3. Identity graph
- hidden object・field・old/new labelは評価器だけで使用
- 学習器はraw before / command / after / futureと環境IDだけを使用

## 最大288例・3 seed平均

| 条件 | Surface | Success-conditioned identity | Identity graph |
|---|---:|---:|---:|
| 既知 | 0.2917 | 0.2917 | 0.2917 |
| 未学習言い換え | 0.1667 | 0.1667 | 0.1667 |
| Rename | 0.1806 | 0.1806 | 0.1806 |
| 別状態表現 | 0.2014 | 0.2014 | 0.2014 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.2153 | 0.2153 | 0.2153 |
| 計画変更 | 0.1736 | 0.1736 | 0.1736 |
| 反実仮想 | 0.1667 | 0.1667 | 0.1667 |

追加診断:

- Event: 64.00
- Success条件を通過したevent: 2.33
- Identity class: 0.00
- Identity member: 0.00
- Graph edge: 0.00
- Sequential coverage: 0.1277
- Sequential conditional accuracy: 0.3286

## 判定

**中核仮説は強く反証された。**

### Null-dominant collapseは解消した

Cycle 025では64 eventが単一classへ崩壊した。今回はnullを類似度から除外し、正のsuccess supportとwrong 0を要求した結果、identity候補eventは平均 **2.33 / 64** まで絞られ、誤った全統合は消えた。

この変更は評価健全化として有効だった。

### しかしidentity classは0件

絞り込まれたevent同士で、object/value/context swap後のtarget reconstruction・damage・future signatureが一致する組は一つもなかった。

したがって、

> **正の実行証拠へ条件付けるだけでは不十分であり、raw span交換から得たtarget signatureはsurfaceを跨ぐevent identityを作れない。**

### 能力増分は全split 0

Surface / Success-conditioned identity / Identity graphは、accuracy・wrong commit・null率・候補数が全条件で完全同一だった。

- 既知: 0.2917
- 言い換え: 0.1667
- Rename: 0.1806
- 別状態表現: 0.2014
- 主語省略: 0
- 複数段落: 0.2153
- 計画変更: 0.1736
- 反実仮想: 0.1667

### Graphは形成不能

Identity classが0のためgraph edgeも0。counterfactual coverage / conditional accuracyも **0.1277 / 0.3286** のままで、因果合成増分はない。

### Factor swapは意味targetを分離していない

Object候補・value候補は、command / state / futureに再出現する最短substringから生成した。これは系列B Cycle 024でsurface anchorと判定された信号と同種であり、別名object・省略object・relation identityを表現しない。

成功episodeに限定しても、swapが壊すのは文字contextであって潜在state variableではなかった。

### 主語省略・planning・反実仮想は未成立

主語省略は全面null。計画変更・反実仮想の部分得点はSurface baselineと同一であり、旧goal・新goal・未実行worldを分離した結果ではない。

## 相関暗記と因果理解の反証条件

因果event identity支持には最低限、次が必要だった。

1. 複数環境で正のsuccess support
2. object swapでobject target成分だけ変化
3. value swapでvalue target成分だけ変化
4. non-target保存
5. Rename・別状態表現でも同一classへ回収
6. class利用によりcounterfactual coverageまたはaccuracy改善
7. null/wrong一致をidentity evidenceに使わない

今回は1と7だけを満たし、2〜6は未達。

## 資源量

- Model: 11059 bytes
- Training: 0.010180 sec
- Inference: 0.056145 ms/example
- Peak RSS: 111552 KiB（Python runtime込み）
- Graph規模:
  - event 64
  - eligible event 2.33
  - class 0
  - edge 0
- 推定計算量:
  - event抽出 `O(NL)`
  - positive replay `O(PNE)`
  - factor swap `O(PSF)`
  - partition `O(P)`
  - graph `O(C²)`
  - inference `O(PL)`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

1. Raw event proposal
2. Local transition extraction
3. success / wrong / null分離
4. symmetric-information replay
5. environment residual identity――null collapseで反証
6. **success-conditioned target signature――collapse解消、identity形成0**
7. positive witness alignment
8. state-variable fiber induction
9. counterfactual composition
10. goal・constraint planning

核心的知見:

> **Null支配を除去すると偽のidentity collapseは止められる。しかし、成功例だけのsurface span swapもstate-variable targetを形成しない。次に必要なのはevent同士を直接似せることではなく、同じ介入結果を生む正例群の中で、どの局所対応が複数の独立witnessを同時に説明するかを探索することである。**

## 他系列へ返す新知見

- A: 正の継続予測を持つcommitmentだけを比較しても、surface span responsibilityでは談話identityにならない。
- B: role交換検定では、成功導出に限定してもsurface anchor swapをsemantic bindingとみなさない。
- D: fast endpointを正のread/write supportへ限定しても、因子対応がsurface依存ならslow classは形成できない。
- E: constraint edgeは正の実行候補間だけで形成すべきだが、文字列swap由来のedgeを意味因果edgeとみなさない。

## 次の仮説

**Multi-Witness State-Variable Fibers from Positive Intervention Alignment**  
（正の介入witness整列からの多証拠state-variable fiber）

次はevent pairのsignature一致でidentityを作らない。

1. 同じbefore→after変化を説明する成功episode群をwitness set化
2. command、state、futureの局所区間間に複数の対応候補を保持
3. 1対応を削除したときに複数witnessの再構成が同時に壊れるか測定
4. object/value/contextを個別swapせず、対応edgeの共同必要性を評価
5. 3環境以上で同じ必要edge集合が再現した場合だけstate-variable fiber化
6. Wrong・nullは棄却証拠に限定
7. Fiber成立後にのみevent identity・direction・counterfactual rolloutを評価
8. Rename・別状態表現・未知objectでfiber precision / recallを主評価化

系列Bのrole-exchange/MDLとは異なり、Cは**複数の実行成功witnessを共同説明するstate transition対応edge**を中心機構とする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
