# 系列C Cycle 034 研究報告

## 仮説

**Multi-Value Intervention Fibers from Non-Target Invariance Cross-Tests**  
（非対象不変性cross-testによる複数値介入fiber）

Cycle 033では、単一値で正しいafterを生成した広い置換区間を最小化しても、真の状態変数境界には到達しなかった。今回は同じ候補境界へ3種類以上の異なる値を介入し、値が変わっても区間外観測が保存され、同じsupportでforward／inverseが成立する境界だけをstate-variable fiber候補へ昇格できるか検証した。

Final testのafter/futureはfiber形成・候補生成・rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Cで扱わない領域 |
|---|---|---|
| A | Multi-value temporal transition fiber | 時間方向の予測状態・carry |
| B | Executable scope program | MDL・program grammar |
| D | Cycle-closing memory address | 長期memory・read/write閉路 |
| E | Multi-value scope fiber attractor | Energy固定点・局所force |
| **C** | **同じ状態supportへの複数値介入と区間外不変性** | 今回の固有対象 |

## 3 seed平均

| 条件 | Single値精度 | Multi値精度 | Exact境界 | Wrong | 候補数 | Shuffle精度 |
|---|---:|---:|---:|---:|---:|---:|
| 既知 | 0 | 0 | 0 | 0 | 17.07 | 0 |
| 未知語順 | 0 | 0 | 0 | 0 | 17.32 | 0 |
| 未知語彙 | 0 | 0 | 0 | 0 | 17.12 | 0 |
| Rename | 0 | 0 | 0 | 0 | 17.07 | 0 |
| 別状態表現A | 0 | 0 | 0 | 0 | 0 | 0 |
| 別状態表現B | 0 | 0 | 0 | 0 | 0 | 0 |
| 入れ子 | 0 | 0 | 0 | 0 | 17.54 | 0 |
| 主語省略 | 0 | 0 | 0 | 0 | 16.90 | 0 |
| 複数段落 | 0 | 0 | 0 | 0.0833 | 14.22 | 0 |
| 計画変更 | 0 | 0 | 0 | 0 | 21.33 | 0 |
| 反実仮想 | 0 | 0 | 0 | 0 | 17.78 | 0 |

追加診断:

- Multi-value fiber: 2.00
- Fiber内値数: 16.67
- Raw signature: 9.33
- Independent probe audit: 5,044.67
- Non-target check: 11.00
- モデルサイズ: 576 bytes
- 学習時間: 0.120974 sec
- 既知推論: 0.827 ms/example
- 複数段落推論: 1.172 ms/example
- Peak RSS: 111,040 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Correct probeでは平均2個のfiberが形成され、shuffled outcomeでは0になった。各fiberは3種類以上の値、forward成功、inverse restoration、区間外保存をprobe上で満たした。

しかし全主要条件でexecution accuracyとexact boundary recallは0だった。平均17前後の候補afterが同点で残り、Multi-value fiberはどの値・対象・境界を現在入力へ適用すべきかを決められなかった。

> **複数値を同じsupportへ可逆介入できることは、状態変数候補の必要条件にはなるが、現在命令の対象・値・scopeを束縛する十分条件ではない。**

No-invariance方式とMulti-value方式は能力・候補数が同一だった。今回の状態文では局所置換候補が区間外保存を自動的に満たし、invariance条件が競合fiberを追加で排除しなかった。

Single-value方式は平均2.33 fiber、Multi-valueは2.00 fiberとなり、一部候補は削減されたが能力へ繋がらなかった。別状態表現A/Bでは候補0で、左右context shapeと相対位置への依存が残った。主語省略、計画変更、反実仮想でもworld state分離は未成立だった。

## 相関暗記と因果理解の反証条件

1. 3種類以上の値で同一supportへの可逆介入: **達成**
2. Shuffled outcomeでfiber消失: **達成**
3. Exact target-boundary recall > 0: **未達**
4. Multi-valueがsingle-valueよりexecution改善: **未達**
5. No-invarianceよりwrong候補を削減: **未達**
6. Rename・別状態表現で内部境界維持: **未達**
7. 主語省略・計画変更・反実仮想でworld state分離: **未達**

形成されたfiberは因果state variableではなく、同一surface template上の介入可能区間classである。

## 先行研究との関係

2025年のcausal abstraction研究は、lossy representationでも観測・介入・反実仮想queryの整合を要求する。ICLR 2025のinvariance研究は、不変性が因果変数ではなくデータ対称性を捉える場合を示す。2026年のobject-centric world modelはobject tokenやslotを先に持つ。今回の未解決点は、生の日本語からその介入target境界とcommand bindingを生成する上流問題である。

## 資源量・計算量

- Signature生成 `O(NL)`
- Multi-value probe `O(FQVL)`
- 推論 `O(FVL)`
- Fiber上限32
- 1GB未満・5ms未満: 小規模条件で達成
- 弱いスマートフォンCPU実機: 未検証

## 系列C固有の進展

> **単一値outcome一致より厳しい、複数値・可逆・非対象不変の介入fiberを形成できた。しかしfiberは「どこを変えられるか」を表すだけで、「何を・なぜ・どの命令で変えるか」を束縛しない。**

## 他系列へ返す知見

- A: Multi-value temporal fiberにもcommandから現在fiberを選択するbinding機構が必要。
- B: Scope programは介入可能supportだけでなく、入力ごとの対象・値選択を予測する必要がある。
- D: Read/write cycleが同じsupportを共有してもquery/command bindingがなければsemantic addressにならない。
- E: Multi-value invarianceだけではenergy tieを解けず、scope fiber間の競合制約が必要。

## 次の仮説

**Command-Coupled Intervention Fibers from Cross-Value Action Contrast**  
（値横断action contrastによるcommand結合介入fiber）

1. 同じstate supportへ複数値を介入するfiberを維持
2. 各値ごとにcommand内で変化する最小区間を抽出
3. Cross-value交換時の実行成否でstate supportとcommand-value区間をedge化
4. Value Aのcommand区間をValue Bへ交換するとfiber出力もBへ変わることを要求
5. Object区間交換ではtarget supportだけが切り替わることを要求
6. Correct exchange／shuffled exchange／state-only fiber／single-valueを比較
7. Exact boundary、execution accuracy、wrong bindingを評価
8. 主語省略では前turn object edgeを再利用
9. 計画変更では撤回command edgeを抑制し最終edgeだけを活性化
10. 反実仮想では実行edgeと非実行edgeを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
