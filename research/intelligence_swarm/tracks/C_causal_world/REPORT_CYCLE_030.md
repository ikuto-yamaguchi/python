# 系列C Cycle 030 研究報告

## 仮説

**Target-Context Mechanism Adapters from Outcome-Blind Structural Edit Search**  
（outcome-blind構造edit探索によるtarget-context mechanism adapter）

Cycle 029ではtarget outcomeを隠したsource-only transportを成立させたが、old/new文字shapeでprogramを束ねても能力増分は0だった。今回はsource programのcommand/state左右contextを分解し、targetの`before / command`だけからprefix・suffix削除を組み合わせる小型adapterを探索した。候補提案時にはtarget `after / future`を使用せず、提案後の監査にのみ使用した。

## 先行研究整理

- 2025年の一般環境下CRLは、複数環境だけでは潜在因果変数同定に十分でなく、環境変化と混合過程への条件が必要とする。
  - https://proceedings.mlr.press/v258/ng25a.html
- Score-based CRLは一般変換下で二つのhard intervention/nodeなど十分な介入被覆を要求する。
  - https://jmlr.org/papers/v26/24-0194.html
- 2026年のonline object-centric symbolic model learningはsignature・observation・transitionをオンライン学習するが、relational MDPとaction/observation構造を前提とする。
  - https://www.scitepress.org/PublishedPapers/2026/144125/
- Causal-JEPAやAAAI-26 object-centric world modelもobject tokenやlatent interventionを前提とし、生日本語から境界・状態変数を生成する今回の問題より下流にある。

## 他系列との重複表

| 系列 | 最新中心 | Cで棄却・分離した領域 |
|---|---|---|
| A | operator中心の反復prediction-error相殺 | 談話予測状態 |
| B | 能動probe文法・program elimination | MDL・program選択 |
| D | 介入応答kernelによるmemory endpoint | 長期memory |
| E | boundary split–mergeによるcandidate birth | energy・attractor |
| **C** | **source mechanismの左右contextをtargetへ可逆変換するadapter** | 今回の固有対象 |

## 3 seed平均・最大288例

| 条件 | Surface | Adapter | Adapter fiber |
|---|---:|---:|---:|
| 既知 | 0.2315 | 0.1620 | 0.1620 |
| 未学習言い換え | 0.1343 | 0.0000 | 0.0000 |
| Rename | 0.2130 | 0.1620 | 0.1620 |
| 別状態表現 | 0.1343 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.1528 | 0.0000 | 0.0000 |
| 計画変更 | 0.1759 | 0.0000 | 0.0000 |
| 反実仮想 | 0.0694 | 0.0000 | 0.0000 |

追加診断:

- Program: 32.00
- Adapter: 64.00
- Multi-environment adapter: 64.00
- Model: 7,495 bytes
- Training: 0.048996 sec
- Inference: 0.060169 ms/example
- Peak RSS: 112,560 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。Adapterは64件形成されたが、全主要条件でSurface baselineより悪化した。**

### Adapterは候補を広げず狭めた

既知精度は0.2315→0.1620、Renameは0.2130→0.1620へ低下した。言い換え・別状態表現・複数段落・計画変更・反実仮想ではAdapterが全面nullへ退化した。

### Multi-environment supportは偽

全64 adapterが複数環境supportを持ったが、これは学習mixture内で同じ局所context削除が再発したためである。未知targetへのstate-variable対応ではなく、surface contextを短くして適用条件を厳しくした局所ruleだった。

### 可逆性は意味対応を保証しない

Prefix/suffix削除はsource→targetとtarget→sourceの文字区間を形式的に復元できる。しかしobject、relation、state variable、operation targetを共有していない。

> **局所context editの可逆性と複数環境再発だけではmechanism adapterにならない。Adapterはtarget文脈で正しい変化位置を新生する必要がある。**

### 主語省略・計画変更・反実仮想

主語省略は全方式0。計画変更はSurface 0.1759に対しAdapter 0、反実仮想は0.0694に対し0だった。旧goal・最終goal・未実行worldを分離する因果状態は形成されていない。

## 相関暗記と因果理解の反証条件

支持には以下が必要だった。

1. target outcomeをcandidate生成・rankingに使用しない
2. held/Rename/alternateでSurfaceよりexecution accuracyを改善
3. wrong executionを増やさない
4. adapterが未知targetで新しいpositive witnessを生成
5. counterfactual sequential coverageを改善
6. 主語省略でobject permanenceを示す

今回は1とwrong 0のみを満たし、能力条件はすべて未達。

## 資源・計算量

- Program抽出 `O(NL)`
- Adapter監査 `O(NEPD^4)`、今回`D≤2`
- 推論 `O((P+A)L)`
- 1GB未満・5ms未満: 小規模条件で達成
- 弱いスマートフォン実機: 未検証

## 系列C固有の進展

> **Outcome-blind transportでは、source ruleのcontextを編集するだけでは未知targetの変化位置を発見できない。次はsource contextを変換するのではなく、target内の複数境界候補をsource mechanismの予測結果で競合させる必要がある。**

## 他系列へ返す知見

- A: operatorの可逆なsurface適用だけを予測状態とみなさず、未知turnでの誤差相殺増分を要求する。
- B: probe grammarの可逆編集も、独立入力で実行位置を新生できなければsemantic programではない。
- D: response kernelを複数環境で共有しても、正しいendpoint境界の新生を別評価する。
- E: boundary split–mergeでは、既存contextとの可逆性よりoutcome-blind rollout差を選択基準にする。

## 次の仮説

**Target-Boundary Competition from Source-Mechanism Predictive Cuts**  
（source mechanism予測cutによるtarget境界競合）

1. Target `before / command`の全局所境界を候補化
2. Source mechanismを各境界へ適用して複数afterをoutcome-blind生成
3. Non-target保存・command value再現・inverse restorationを独立score化
4. 複数source programが同じtarget境界を支持した場合だけcandidate化
5. Target outcomeは評価後のpositive/wrong更新にのみ使用
6. Wrong境界へnegative creditを蓄積
7. Held/Rename/alternateでpositive witness coverageを主評価
8. 境界class成立後のみstate-variable fiber・因果方向・counterfactual rolloutへ進む

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
