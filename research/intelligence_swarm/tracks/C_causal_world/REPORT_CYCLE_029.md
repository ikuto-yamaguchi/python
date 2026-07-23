# 系列C Cycle 029 研究報告

## 仮説

**Outcome-Blind Positive Witness Birth from Source-Only Mechanism Transport**  
（source mechanismのみの転送によるoutcome-blind positive witness創発）

Cycle 028ではtarget側の`after`からtarget eventを抽出していたため、双方向成功がsource mechanism transportではなく二つの自己再構成へ退化した。今回はtargetの`before / command`だけでcandidateを生成し、`after / future`は最終評価まで使用しない。

## 先行研究整理

2025年の因果抽象同定研究は、介入集合から回収できる因果構造が介入の被覆条件に依存することを示す。Score-based CRLも一般変換下での同定に複数介入環境を要求する。2026年のobject-centric world modelやcounterfactual planningはobject token、state、action、reward等を先に与える。今回の課題はそれらより上流の、生の日本語からsource mechanismを抽出し未知targetへ転送する問題である。

- https://proceedings.mlr.press/v258/li25g.html
- https://www.jmlr.org/papers/v26/24-0194.html
- https://proceedings.mlr.press/v267/xia25a.html
- https://ojs.aaai.org/index.php/AAAI/article/view/39642
- https://ojs.aaai.org/index.php/AAAI/article/view/40184

## 他系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | 共有時間応答kernelによるroute identity | 談話commitment・予測責任 |
| B | Program-composed probe stateによる識別実験 | Program選択・MDL |
| D | 時間横断予測必要性によるendpoint birth | 長期memory |
| E | Outcome非参照prospective residual field | Energy・attractor |
| **C** | **Source eventだけからtarget state transitionを生成するoutcome-blind transport** | 今回の固有対象 |

## 実験条件

- seed: 1 / 7 / 19
- train: 48 / 144 / 288 episode
- test: 既知、言い換え、Rename、別状態表現、主語省略、複数段落、計画変更、反実仮想
- program上限: 64
- mechanism link上限: 32
- ablation:
  1. Surface program
  2. Source-only transport link
  3. Fiber score
- inference時のtarget `after / future`利用: なし
- hidden object / field / old / new labelのlearner利用: なし

## 最大288例・3 seed平均

| 条件 | Surface | Source-only transport | Fiber |
|---|---:|---:|---:|
| 既知 | 0.2778 | 0.2778 | 0.2778 |
| 未学習言い換え | 0.2014 | 0.2014 | 0.2014 |
| Rename | 0.2014 | 0.2014 | 0.2014 |
| 別状態表現 | 0.2014 | 0.2014 | 0.2014 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.1667 | 0.1667 | 0.1667 |
| 計画変更 | 0.1458 | 0.1458 | 0.1458 |
| 反実仮想 | 0.2014 | 0.2014 | 0.2014 |

追加診断:

- Program: 64.00
- Positive eligible program: 51.67
- Source mechanism link: 3.00
- Positive executions: 158.67
- Wrong executions: 1.67
- Sequential coverage: 0.1277
- Sequential conditional accuracy: 0.3286

## 判定

**中核仮説は強く反証された。Outcome leakage除去には成功したが、mechanism linkの能力増分は0。**

### Outcome-blind制約は成立

Target candidate生成と推論では`before / command`だけを使用し、target `after / future`を参照しなかった。Cycle 028の自己再構成leakageは除去できた。

### 能力増分は全splitで0

Surface、Transport、Fiberのaccuracy・wrong commit・null率・候補数は全条件で完全同一だった。

3個のsource mechanism linkを形成しても、未知surfaceのstate transition選択を改善しなかった。

### Positive programは多いがsurface-local

平均51.67/64 programが学習集合上で2回以上success・wrong 0を満たした。しかし成功は同じ局所command/state contextの再出現に依存する。

- 既知: 0.2778
- 言い換え: 0.2014
- Rename: 0.2014
- 別状態表現: 0.2014
- 主語省略: 0

Renameや別状態表現の部分得点も、学習mixtureに対応surfaceが含まれているためopen-form transportの証拠ではない。

### Mechanism linkはshape同値類

Linkはold/new文字shapeが同じprogramをまとめたものであり、object、relation、state variable、operation targetを表さない。Scoreを加えてもcandidate rankingは変化しなかった。

### 主語省略は全面0

主語省略は全方式null率1.0。Object permanenceや談話focusは形成されていない。

### 計画変更・反実仮想は局所再実行

計画変更0.1458、反実仮想0.2014は全方式同一であり、goal revisionや未実行worldを保持した結果ではない。

## 相関暗記と因果理解の反証条件

仮説支持には以下が必要だった。

1. Target outcomeを候補生成・rankingに使わない
2. Source-only transportがSurface baselineよりheld/Rename/alternateを改善
3. Wrong executionを増やさない
4. Mechanism link利用でcounterfactual coverageが改善
5. 主語省略でobject permanenceを示す
6. 計画変更で旧goalと最終goalを分離

今回は1とwrong 0だけを満たし、能力条件は未達。

## 資源量

- Model: 10534 bytes
- Training: 0.007300 sec
- Inference: 0.020097 ms/example
- Peak RSS: 167448 KiB（Python runtime込み）
- 計算量:
  - Program抽出 `O(NL)`
  - Source-only audit `O(PN)`
  - Link形成 `O(P)`
  - 推論 `O(PL)`
  - `P ≤ 64`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォン実機は未検証。

## 系列C固有の進展

> **Target outcomeを隠してもsource-local programは一定割合で実行できる。しかし、文字shapeでprogramを束ねても未知targetへのmechanism transportにはならない。Open-form witness birthには、source programをtarget contextへ写す対応をtarget outcomeなしで生成し、競合候補を反例で選択する必要がある。**

## 他系列へ返す知見

- A: Outcome非参照だけではroute identityにならず、held-out能力増分を必須化する。
- B: Probe stateがcandidate program自身の内部規則だけで成立しないよう、別入力での能力増分を測る。
- D: Endpoint必要性はanswer非参照だけでなく、未知surface read改善を要求する。
- E: Prospective residual fieldもcandidate rankingがbaselineを変えなければ構造形成ではない。

## 次の仮説

**Target-Context Mechanism Adapters from Outcome-Blind Structural Edit Search**  
（outcome-blind構造edit探索によるtarget-context mechanism adapter）

次はshape同値programを直接linkしない。

1. Source programのcommand/state左右contextを分解
2. Target `before / command`だけからcontext edit候補を生成
3. Prefix削除、suffix削除、境界移動、局所置換を小さなadapter programとして探索
4. Source→target適用とtarget→source逆適用が同じ区間を復元するadapterだけ保持
5. Target outcomeは評価後のpositive/wrong labelにのみ使用
6. 複数環境でpositive adapterが再現した場合だけstate-variable fiberへ昇格
7. Held/Rename/alternateのoutcome-blind witness coverageとexecution accuracyを主評価化
8. Fiber成立後に因果方向・counterfactual rolloutを評価

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
