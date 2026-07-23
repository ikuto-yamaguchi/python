# 系列E Cycle 024 研究報告

## 仮説

**Commutator-Separated Factor Roles from Independent Intervention Pairs**  
（独立介入pairの交換子によるfactor role分離）

Cycle 023では、複数環境で安定するenergy応答signatureを18.67個形成したが、Base方式に対する能力増分は全splitで0だった。形成されたのは意味roleではなく、環境生成器に共通するsurface symmetryだった。

今回は単純な応答一致を捨て、同じ候補へ介入A→BとB→Aを適用したときの順序差を交換子signatureとして測定した。

介入pairは次の4組である。

1. object短縮 × value短縮
2. object交換 × value短縮
3. object短縮 × value交換
4. object交換 × value交換

各順序で、after再構成energy、future整合energy、non-target damage、execution failureを計測し、3環境以上・4回以上再発し、かつ非ゼロ交換子を持つsignatureだけをfactor-role prototypeへ昇格した。

## 先行研究との位置づけ

- 2025年のGeneralized Lagrangian Equilibrium Propagationは、時変入力と境界条件を含む局所学習へEPを拡張するが、状態変数と系の力学は定義済み。
- 2025年ICMLのEnergy-based Model研究は巨大離散空間でのtractable learningを提案するが、候補集合とenergy parameterizationは既知。
- 2026年のAttractor Models / Equilibrium Reasonersは固定点収束と動的計算深度の有効性を示すが、候補表現を生成するbackboneを前提とする。
- 今回は、そのさらに上流にある、生の日本語文字列から意味factor候補と局所constraint graphを形成できるかを扱う。

## 他4系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な失敗 | Eとの分離 |
|---|---|---|---|---|
| A | Event-gated prospective state | 主語省略pair recallの候補回復 | commitment選択精度が低い | 談話carry・active queryは扱わない |
| B | Role-exchange binding seed | 明示surface anchorの回収 | Rename・省略binding 0 | MDL・導出置換は扱わない |
| C | Success-conditioned event identity | Null collapseの診断 | event identity未形成 | state transition identityは扱わない |
| D | 双方向query-state endpoint reconstruction | write/read分離で悪化停止 | slow link 0 | 長期memoryは扱わない |
| **E** | **介入順序交換子からfactor roleを分離** | 今回検証 | 候補roleと局所constraint | 系列固有 |

B系列のrole-exchangeは導出・MDL、C系列のfactorized interventionは実行可能state transition、D系列はendpoint memoryであり、今回はenergy landscape上の順序非可換性と局所緩和に限定した。

## 実験条件

- Seed: 1 / 7 / 19
- 学習bundle: 24
- 1 bundleあたり4 surface環境
- Test: 12例 / split / seed
- Object候補: 最大4
- Value候補: 最大4
- Pair候補: 最大16
- 介入pair: 4
- 最大緩和sweep: 5
- 比較: Base energy / Commutator prototype / Commutator + Null
- 自由日本語条件: 既知、未知語、曖昧性、入れ子、主語省略、複数段落、計画変更、反実仮想

Hidden object・value正解は評価器だけで使用した。

## 3 seed平均

| 条件 | Base精度 | Commutator精度 | Null率 | Pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.5833 | 0.5833 | 1.0000 | 0.5833 |
| 未知語 | 0.2222 | 0.2222 | 1.0000 | 0.2222 |
| 曖昧性 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 主語省略 | 0.0278 | 0.0278 | 1.0000 | 0.0278 |
| 複数段落 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 計画変更 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

追加診断:

- 形成prototype: 0.00
- 既知平均反復: 2.00
- 既知平均active state: 1.08
- 既知平均候補: 10.06
- 既知wrong commit: 0.4167

## 判定

**中核仮説は強く反証された。**

### 非ゼロ交換子prototypeは0件

最大24 bundle × 4環境・3 seedで、採用条件を満たす非ゼロ交換子prototypeは一件も形成されなかった。

Object短縮・value短縮・候補交換をA→BとB→Aで適用しても、現在の局所文字列energyでは順序差がほぼ常に0だった。

これはobject/valueが独立因子として発見されたことを意味しない。現在の介入演算が単純な文字列置換・短縮であり、互いの適用領域や内部状態を書き換えないため、手続き上ほぼ可換だった。

### 能力増分は全split 0

Base方式とCommutator方式は全条件でAccuracy、Wrong commit、Object/value/pair recall、Active state数、反復回数が完全に同一だった。

交換子creditは候補classを一件も分割せず、attractor landscapeを変えなかった。

### 可換性は独立意味因子の証拠ではない

交換子が0であることは、Objectとvalueが意味的に独立、Relation・scopeが正しく分離、局所constraint graphが成立したことを示さない。

今回の演算ではjunk span同士も同様に可換だった。したがって、介入演算自体が意味状態へ作用していなければ、交換子0は独立性ではなく操作の弱さを示すだけである。

### 難条件ではcandidate collapseが継続

- 曖昧性: pair recall 0
- 入れ子: pair recall 0
- 複数段落: pair recall 0
- 計画変更: value / pair recall 0
- 反実仮想: value / pair recall 0
- 主語省略: value recall 1.0、object / pair recall 0.0278

Scope、談話focus、旧案／最終案、実行世界／未実行世界をfactor graphとして保持できていない。

### Nullは全面棄権

Commutator + Nullは全条件でwrong commit 0、null率1.0、accuracy 0だった。安全停止としてのみ機能した。

## 単なるHopfield記憶・既存NNとの差

固定patternを保存して最近傍想起するのではなく、複数候補を同時保持する疎active set、局所energy、介入順序の交換子、prototypeによるedge-local credit、反復緩和と動的停止を使う点は異なる。

ただし今回の実装は学習された連続energy networkでも正式なEPでもなく、有限文字候補上の手続き的energy solverである。意味状態と結合weightの局所学習は未成立。

## 収束・停止条件・失敗分類

停止条件:

1. Active pair集合が前sweepと一致
2. 最小energy + 0.04以内の最大8候補へ収縮
3. 最大5 sweep

失敗分類:

- 候補崩壊: 正答object/value/pairが候補集合外
- 交換子崩壊: 介入演算が弱く全候補で交換子0
- Role崩壊: 可換性が意味roleを分割しない
- 局所最適: Nullなしではjunk候補へ収束
- Null安全停止: 全面棄権
- 発散: 上限制御により未観測

## 資源量

- モデルサイズ: 118 bytes
- 学習時間: 0.160991 sec
- 既知推論: 2.020 ms/example
- Peak RSS: 168284 KiB（Python runtime込み）
- 平均反復: 2.00
- 平均active state: 1.08
- 最大候補: 16
- 推定計算量: 候補生成 O(L²)、交換子評価 O(PHF)、Prototype学習 O(NEH)、緩和 O(SH)、P=4, E=4, H≤16, S≤5

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォン実機は未検証。

## 系列E固有の進展

交換子を意味roleの証拠に使うには、介入演算が内部意味状態へ実際に作用しなければならない。表面文字列の独立置換が可換でも、それはobject/valueの独立性を示さない。まずfactor候補間のconstraint edgeを生成し、そのedgeを介して順序効果が伝播する必要がある。

## 他系列へ返す新知見

- A: Focus継続・終了eventが内部stateを変えないなら、event順序差は談話roleの証拠にならない。
- B: Role交換が導出graphの別nodeやbindingを変えないなら、置換可能性はsurface exchangeに留まる。
- C: Object/value swapがtransition mechanismを変えない実装では、factorized intervention signatureは空になる。
- D: Query/state再構成が共通endpoint edgeを介さなければ、双方向一致はsurface再現に留まる。

## 次の仮説

**Constraint-Edge Birth before Commutator Tests from Cross-Candidate Energy Credit**  
（交換子検定前のcandidate間energy creditによるconstraint edge創発）

次は独立候補へ交換子を直接適用しない。

1. Object候補・value候補・scope候補を別active setとして保持
2. 一候補を固定したとき、他候補のenergy順位が変化するpairだけedge候補化
3. Edgeあり／なしでfree fixed pointを比較
4. Edgeを介した介入A→B / B→Aの順序差を測定
5. Non-targetへ伝播するedgeは削除
6. 複数surface環境で再発するedgeだけ局所weight化
7. Free/nudged fixed point差からedge-local update
8. 曖昧性・計画変更・反実仮想のpair recallとscope selectionを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
