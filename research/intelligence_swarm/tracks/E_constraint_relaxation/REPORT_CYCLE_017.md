# 系列E Cycle 017 研究報告

## 仮説

**Frustration-Driven Candidate Birth with Null-Preserving Relaxation**  
（frustration駆動候補birthとnull保持型緩和）

Cycle 016では、raw outcome差分から固定名なしのcause basisを圧縮したが、unmarked / nested / plan / longのcandidate recallがすべて0で、残差basisがjunk候補を一意化した。

当初の次案だった「可逆split/mergeによるspan・residual共同創発」は、系列A Cycle 017のboundary-action共同提案、系列B Cycle 017のboundary-program共同帰納と中心機構・反証条件が重なるため棄却した。

本Cycleでは境界split/mergeを中心に置かず、現在の活性候補がafter・future・non-target preservation制約を満たせず高frustrationを残す場合にだけ、未使用のraw span対を局所的にbirthさせる仮説を検証した。

- free phase: 現在候補を局所energyで緩和
- frustration gate: 最低energyが閾値を超えた場合のみ候補birth
- local birth: before span × command spanのうち制約改善量が大きい候補を最大8個追加
- null state: 正答候補外・margin不足・絶対energy高の場合は一意化せず棄権
- local learning: hidden labelを使わず、after/future/preservationを改善した候補のfactor weightを局所更新

## 先行研究

- Sander et al., ICML 2025, *Joint Learning of Energy-based Models and their Partition Function*: 組合せ的に大きい離散空間でEBMを学習するtractable objectiveを示すが、候補空間自体は既定。
- Pourcel et al., 2025, *Lagrangian-based Equilibrium Propagation*: 時変入力へEPを拡張し、forward-only・local learningの条件を整理する。
- Litman, 2025, *Equilibrium Propagation Without Limits*: finite nudgeでも局所energy差から学習可能な理論を与える。
- Fan et al., 2026, *Hybridizing Equilibrium Propagation with Ising Machines*: local minimaとphase-space contractionを緩和する拡張力学を提案する。
- *Conformal Structured Prediction*, ICLR 2025: 複雑な構造候補を一意点ではなく集合として保持する重要性を示す。

これらはenergy・局所学習・集合保持を支持するが、生の日本語から候補ノード自体をbirthする問題は対象外である。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | E候補との区別 |
|---|---|---|---|---|
| A | prediction-error下のboundary-action split/merge | delayed creditの適用順序を反証 | candidate recall全split 0 | 境界moveそのものは棄却 |
| B | absolute MDL付きboundary-program共同帰納 | seen 0.6944 | 未知形式0、圧縮利得負 | description length最小化は棄却 |
| C | executable operation fiber | null transport評価を分離 | transport coverage 0 | world operation transportは棄却 |
| D | provenance-gated alias reconsolidation | object/relation分離の限定read信号 | alias能力増分0、slow link 0 | 長期memory同値性は棄却 |
| **E** | **残存frustrationが新candidate nodeを局所birthさせる疎energy dynamics** | 今回検証 | open-form cause/candidate共同生成 | 系列固有 |

継承知見:
- A: candidate recall成立前の時間creditはjunkを固定する。
- B: view相互復号・圧縮だけでは候補外構造を生成しない。
- C: execution failureとcandidate absenceを同じoutcomeへ混ぜない。
- D: repeated residualや共起だけでは同一trajectoryを証明しない。

## 実験条件

- seed: 1 / 7 / 19
- train: 12 / 24 / 36 episode
- test: 8例 / split / seed
- split: seen / unseen paraphrase / nested / subject omission / multi-paragraph / plan change / counterfactual
- candidate上限: 8
- birth上限: 8
- sweep上限: 3
- 比較: fixed relaxation / frustration-driven birth / birth + null preservation
- learner input: raw command / before / after / future / order
- hidden target/value: evaluatorのみ

## 最大36 episode・3 seed平均

| 条件 | Fixed acc/wrong/recall | Birth acc/wrong/recall | Birth+Null acc/wrong/recall |
|---|---:|---:|---:|
| seen | 0.0000/0.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| unseen | 0.0000/1.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| nested | 0.0000/1.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| omission | 0.0000/1.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| paragraph | 0.0000/1.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| plan | 0.0000/0.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |
| counterfactual | 0.0000/1.0000/0.0000 | 0.0000/1.0000/0.0000 | 0.0000/0.0000/0.0000 |

## 判定

**中核仮説は強く反証。null保持だけ限定支持。**

### Candidate birthでもrecallは0

全splitでcandidate recallは0だった。frustrationから平均6.3〜8.0個の新候補を生成したが、正しいobject/value組は一件も候補集合へ入らなかった。frustrationは「何かが説明できていない」ことは示せても、どのspan境界とbindingを新生すべきかを指定しない。

### Nullなしbirthは全件誤確定

Birth方式は全splitでwrong commit 1.0だった。candidate recall 0にもかかわらず、birthしたjunk候補のうち相対energyが最小のものへ必ず収束した。これはCycle 012–016で繰り返した「候補外なのに相対energyが一意化する」失敗の再現である。

### Null保持は誤確定を0へ抑えたが能力は0

Birth+Nullは全splitでwrong commit 0、null率1.0を達成した。ただしaccuracy・candidate recallも0。nullは安全な棄権機構としては有効だが、意味候補生成能力を増やしていない。

### Local factor学習は意味causeを形成しない

学習したweightはafter/future/preservationへの表面適合を強めるだけで、object・relation・scope・goal・revision・causal directionを形成しない。free/nudged phaseの局所相関差ではなく、raw reconstruction scoreに基づく近似更新であり、平衡伝播成立とはみなさない。

### 動的反復は計算量を増やしただけ

- Fixed unseen: 0.3430 ms
- Birth unseen: 5.0991 ms
- Birth+Null unseen: 5.3684 ms

候補birthにより推論は約15倍へ増加し、unseen / omissionでは5msを超えた。能力増分0なので効率悪化は正当化できない。

## 停止条件・失敗分類

- 一意停止: active candidate 1
- 平坦停止: active集合が変化しない
- sweep停止: 最大3
- 候補崩壊: 正答候補がactive集合外
- junk局所最適: candidate recall 0で一意誤確定
- 安全null: candidate recall 0かつ棄権
- 発散: 今回0
- cause崩壊: factor weightが意味原因を分けない

主失敗はcandidate collapse。Birth方式はjunk局所最適、Birth+Nullは安全nullへ移行した。

## 単なるHopfield・既存NNとの差

- 保存patternへ近い状態を想起するのではなく、局所制約違反からcandidate nodeを動的に追加する。
- fixed feed-forward分類ではなく、活性候補集合を反復更新する。
- ただし候補birth ruleはraw span直積であり、意味構造創発には未到達。
- neural encoder・backpropagation・Transformer attentionは使用していない。

## 資源量

- model: 164 bytes
- training: 0.003128 sec
- inference: seen 2.0928 / unseen 5.3684 / omission 6.0911 ms
- mean sweeps: seen 2.00 / unseen 2.92
- mean active: seen 8.00 / unseen 8.00
- mean born: seen 8.00 / unseen 7.29
- convergence rate: 1.0（固定sweep/平坦停止を含む）
- Peak RSS: 110644 KiB（Python runtime込み）
- complexity: initial proposal `O(L²)`, birth `O(Hb·Hc·F)`, relaxation `O(SHF)`, `H<=8`, `S<=3`

モデル1GB未満は達成。5ms未満はseen/planで達成したが、unseen・omission等では未達。弱いスマートフォン実機は未検証。

## 系列E固有の進展

必要条件を12段階へ更新する。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Adaptive factor中の絶対残差校正
7. Residual identifiability
8. Residual-cause-to-edge routing
9. Cause/edge basis self-generation
10. Open-form candidate and cause co-generation
11. **Frustration-triggered candidate birth**
12. Attractor relaxation・局所学習

今回、第11段階の表面版を実装したが、候補birthは正答構造を生成せずjunkを増やした。

> **frustrationはcandidate birthの必要条件にはなり得るが、birth方向を決める十分条件ではない。未解消制約を、どの観測差分がどのspan境界へ責任を持つかへ局所分解する必要がある。**

## 他系列へ返す知見

- A: prediction-errorが高いことだけでsplit/merge方向を選ぶとjunk boundaryを増やす。
- B: absolute MDL gainがなくてもfrustration減少だけで候補を追加すると探索が膨張する。
- C: null transportとcandidate absenceを分けても、transport residualの責任spanがないとanchorは生まれない。
- D: alias linkの失敗残差をそのままbridge候補生成へ使うと異object linkが増える。

## 次の仮説

**Responsibility-Localized Frustration Flow with Reversible Candidate Birth**  
（責任局在化frustration flowによる可逆candidate birth）

次はglobal frustrationからspan直積を生成しない。

- after / future / non-targetの各残差を文字位置へ局所分配
- before・command・future間で同じ残差flowが交差する位置だけcandidate boundary化
- birth前後のenergy差をedge-localに記録
- birth candidateを削除してenergyが戻る可逆性を必須化
- candidate recallが増えずwrong commitだけ増えるbirth familyを局所抑制
- nullを常時保持し、absolute energy閾値を下回らない限り一意化しない
- free/nudged 2 phaseで局所factor correlation差を測る

最低成功条件:
- seen/unseen candidate recall > 0
- Birth+Null accuracy > Fixed
- wrong commit <= 0.05
- mean born <= 8
- sweep <= 4
- model < 32KB
- inference < 5ms/example

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
