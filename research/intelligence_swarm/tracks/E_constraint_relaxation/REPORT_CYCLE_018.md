# 系列E Cycle 018 研究報告

## 仮説

**Responsibility-Localized Frustration Flow with Reversible Candidate Birth**  
（責任局在化frustration flowによる可逆candidate birth）

Cycle 017ではglobal frustrationが高いとき、before span × command spanの直積から候補をbirthした。しかし全splitでcandidate recall 0、nullなしではwrong commit 1.0だった。本Cycleでは残差を文字位置へ局所分配し、before・command・futureで責任flowが交差する区間だけを候補化した。さらにbirth node削除時にfree/null energyへ戻る可逆性と、null常時保持を要求した。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | E候補との区別 |
|---|---|---|---|---|
| A | persistence/change二視点境界生成 | 境界探索の失敗条件を明確化 | pair recall 0、O(L²M) | 境界split/merge自体は扱わない |
| B | 匿名failure-cause商 | 反例符号化の絶対MDL監査 | 未知候補0、DL 6.66倍悪化 | 圧縮商ではなく局所energy flow |
| C | cycle-consistent transport対応写像 | null transport評価を厳密化 | correspondence未形成 | world transport graphは扱わない |
| D | relation-selective bridge link | rename writeに限定信号 | read悪化、alias過生成 | 長期alias統合は扱わない |
| **E** | **free/nudged残差の位置責任から可逆candidate birth** | 今回検証 | open-set候補生成 | 系列固有 |

## 先行研究との位置づけ

Equilibrium Propagationはfree phaseとnudged phaseの局所状態差から局所学習信号を得る。2025–2026年の研究ではfinite nudge、時間依存・散逸系、局所結合構造への拡張が進む。一方、これらは状態変数・結合・候補空間が定義済みであり、生の日本語から未知candidate nodeの境界とbindingを生成する問題は直接解かない。

本実験は正式なEP勾配計算ではなく、raw reconstruction制約のfree/null状態とnudged candidate状態の局所energy差を文字位置へ割り当てる最小反証実装である。

## 実験条件

- 学習例: 24
- seed: 1 / 7 / 19
- test: 6例 / split / seed
- split: seen / unseen paraphrase / nested / subject omission / paragraph / plan change / counterfactual
- candidate上限: 8
- responsibility target/value候補: 各6
- 最大sweep: 4
- ablation:
  1. Global birth
  2. Responsibility-localized birth
  3. Localized birth + reversible null

学習器はraw command / before / after / futureのみを使用し、hidden target/valueは評価器だけが使用した。

## 3 seed平均

| 条件 | Global recall/acc/wrong | Localized recall/acc/wrong | Localized+Null recall/acc/wrong |
|---|---:|---:|---:|
| seen | 0.0000/0.0000/1.0000 | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.0000 |
| unseen | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.2778 | 0.0000/0.0000/0.0000 |
| nested | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.5556 | 0.0000/0.0000/0.0000 |
| omission | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 |
| paragraph | 0.0000/0.0000/1.0000 | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.0000 |
| plan | 0.0000/0.0000/1.0000 | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.0000 |
| counterfactual | 0.0000/0.0000/1.0000 | 0.0000/0.0000/0.1667 | 0.0000/0.0000/0.0000 |

## 判定

**中核仮説は強く反証。局所化とnullには安全性・効率の限定信号だけがある。**

### 1. Candidate recallは全条件0

Global / Localized / Localized+Nullの全方式で正しいobject/value pairは候補集合へ入らなかった。after/future差分を位置へ配分しても、object境界・value境界・両者のbindingは生成されない。

### 2. 局所化は誤確定を一部削減

Globalは全splitでwrong commit 1.0だった。Localizedはunseen 0.2778、nested 0.5556、omission 0、counterfactual 0.1667へ低下した。しかしseen/paragraph/planでは1.0のままで、accuracyは全て0である。

これは意味能力ではなく、局所flowで候補集合が縮小・平坦化した効果である。

### 3. Null保持は誤確定0だが能力0

Localized+Nullは全splitでwrong commit 0、null rate 1.0、accuracy 0だった。候補外で無理に収束しない安全機構としてのみ支持される。

### 4. 可逆性検定は自明化

今回の削除可逆性は、candidate nodeを除去すると同じnull energy計算へ戻ることを確認しただけで、semantic reversibilityを証明しない。正答recallが0のため、可逆junk候補を選別しているに過ぎない。

### 5. 正式な平衡伝播ではない

free/nudged二相の局所差分は測定したが、状態相関差によるweight更新、固定点の厳密なenergy勾配、学習収束保証は未成立。

## 停止条件・失敗分類

- 収束: active集合が不変、または最大4 sweep
- 発散: 今回なし（上限制御）
- 局所最適: 一意junk候補への収束
- 候補崩壊: 正答pairが候補集合外
- factor崩壊: 責任flowが意味roleを分離しない
- null安全停止: absolute energy / margin / reversibility gate不成立

支配的失敗は候補崩壊とfactor崩壊。

## 資源量

- Localized+Null model: 196 bytes
- training: 0.021465 sec
- inference:
  - seen 1.6706 ms/example
  - unseen 0.9441 ms/example
  - paragraph 2.9597 ms/example
- mean sweep:
  - seen 2.00
  - unseen 1.28
- active states: 最大8
- convergence rate: 1.0（上限・平坦停止を含む）
- Peak RSS: 110796 KiB（Python runtime込み）
- complexity:
  - substring proposal `O(L²)`
  - localized birth `O(Ht·Hv·F)`
  - relaxation `O(SHF)`
  - `Ht,Hv<=6`, `H<=8`, `S<=4`

Global inferenceはseen 16.79ms、paragraph 26.83msだったが、Localized+Nullはseen 1.67ms、paragraph 2.96msへ短縮した。1GB未満・5ms未満は小規模条件で達成したが、弱いスマートフォン実機では未検証。

## 系列E固有の進展

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Absolute residual calibration
7. Residual identifiability
8. Cause-to-edge routing
9. Cause basis self-generation
10. Candidate/cause co-generation
11. Frustration-triggered birth
12. **Position-local responsibility flow and reversible null gate**
13. Role-separated residual transport
14. Attractor relaxation・局所学習

最大の新知見:

> global frustrationを位置へ局所化すると探索量と誤確定は減るが、意味roleのbirth方向は得られない。責任位置と役割同一性は別問題である。

## 他系列へ返す知見

- A: persistence/change境界を独立生成しても、位置creditだけではobject/value identityにならない。
- B: failure featureは位置局在だけでなく、異episodeで同じrole failureを説明する必要がある。
- C: correspondence edgeの責任位置が分かっても、transport可能なstate roleは別に形成する必要がある。
- D: bridge linkの誤差位置だけではalias同値性を証明できない。

## 次の仮説

**Role-Separated Residual Transport with Counterfactual Factor Swaps**  
（反実仮想factor swapによるrole分離残差transport）

次は位置責任だけでcandidate pairを作らない。

- persistence候補、change候補、scope候補を独立活性集合として保持
- 1因子だけ別episode候補へswap
- after/future/non-target energyの変化vectorを測る
- 異なるsurfaceでも同じenergy変化vectorを持つ因子だけ匿名roleへ昇格
- candidate pairはroleが分離された後だけ疎結合
- nullを常時保持
- free/nudged局所相関差をfactor edgeごとに測定

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
