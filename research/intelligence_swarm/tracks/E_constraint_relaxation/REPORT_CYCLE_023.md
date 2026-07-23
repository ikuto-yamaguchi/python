# 系列E Cycle 023 研究報告

## 仮説

**Environment-Decoupled Factor Birth from Intervention-Invariant Energy Responses**  
（環境分離介入に不変なenergy応答からのfactor birth）

Cycle 022では、after・future・non-target・executionを別energyとして計算しても、全項が同じ文字列包含関係に依存し、交差は独立証拠にならなかった。

今回は同一文内の複数制約投票を廃止し、object表記、語順、state表現を別々に変更した4環境で、候補因子を局所短縮した際のenergy応答vectorが再発する場合だけprototypeへ昇格した。

各候補pairについて、after再構成、future整合、non-target保存、execution、およびobject/value候補を1文字短縮した際の各energy有限差分を保持した。3環境以上・4回以上再発したsignatureだけを局所学習し、反復緩和時のenergy creditへ加えた。

## 先行研究整理

- Equilibrium Propagationはfree phaseとnudged phaseの固定点差から局所更新を得るが、状態変数と結合候補は通常事前定義される。https://doi.org/10.3389/fncom.2017.00024
- 2026年のdissipative dynamics拡張は減衰力学系でも局所学習を扱うが、未知意味node生成は対象外。https://doi.org/10.1002/aisy.202501310
- 一般環境からの因果表現学習は環境間機構変化の識別条件を示すが、観測変数と環境分割は定義済み。https://proceedings.mlr.press/v258/ng25a.html
- ICLR 2025のinvariance原理研究は、環境間で安定する表現が因果変数ではなくデータ対称性を保存しただけの場合を明示する。https://proceedings.iclr.cc/paper_files/paper/2025/hash/85381f4549b5ddf1d48e2e287d7d3d15-Abstract-Conference.html
- Attractor Modelsは固定点反復と動的計算深度を利用するが、候補表現を提案するbackboneを前提とする。https://arxiv.org/abs/2605.12466

## 最新系列との重複表

| 系列 | 最新中心 | 限定信号 | 支配的失敗 | Eとの分離 |
|---|---|---|---|---|
| A | 観測前commitmentによる前向き談話状態 | 事後逆投影で主語省略pair recall回復 | carry独立増分0、計画変更0 | 予測test・談話stateは扱わない |
| B | 三者導出交差からの可逆binding seed | 既知局所program | anti-unification grammar 0 | MDL・program帰納は扱わない |
| C | 対称情報付きevent replay | 偽方向信号を削減 | event identity未形成 | 因果world graphは扱わない |
| D | write-only classとquery-conditioned read address | write小幅改善、read崩壊停止 | slow link 0 | 長期memoryは扱わない |
| **E** | **環境横断の局所energy応答不変性** | 今回検証 | factor identity・binding | 系列固有 |

棄却した候補:

- 環境間edit graph対応program: B/Cの導出・transport研究と重複
- 前向き談話carry: Aと重複
- write/read endpoint統合: Dと重複

## 実装・停止条件

- 学習: 48 latent episode bundle
- 各bundle: base / rename / word-order / alternate-state
- Seed: 1 / 7 / 19
- object候補8、value候補8、pair最大48
- Prototype採用: 3環境以上かつ4回以上再発
- 最大5 sweep
- active集合不変、または最小energy+0.04以内の上位8候補へ収縮した時点で停止
- Null: 最良energy > 1.45、margin < 0.035、またはstable prototype外

固定ontology、手書きslot、分類器、問題別分岐、辞書、RAG、外部LLM、形態素解析は不使用。環境bundleの対応だけを実験条件として与え、hidden object/valueは評価のみで使用した。

## 3 seed平均

| 条件 | Base精度 | Invariant精度 | Invariant+Null率 | Invariant pair recall |
|---|---:|---:|---:|---:|
| 既知 | 0.8889 | 0.8889 | 1.0000 | 1.0000 |
| 未知語 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 曖昧性 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 1.0000 | 0.0278 |
| 主語省略 | 0.0278 | 0.0278 | 1.0000 | 0.0278 |
| 複数段落 | 0.0556 | 0.0556 | 1.0000 | 0.0556 |
| 計画変更 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| 反実仮想 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |

追加診断:

- 安定prototype: 18.67
- 既知平均候補: 41.81
- 既知平均active: 1.11
- 既知平均反復: 2.00
- 複数段落平均active: 3.89

## 判定

**中核仮説は強く反証された。**

### 不変prototypeの能力増分は0

BaseとInvariantは全条件でaccuracy、pair recall、wrong commitが完全同一だった。18.67個の環境横断prototypeを形成したが、候補classを意味的に一件も分割しなかった。

### 不変性は意味roleではない

形成されたsignatureは局所文字候補を短縮した際のafter/future類似度と実行可否の変化である。複数環境で同じ応答が再発しても、それはobject、value、scope、goal、constraint、causeの同一性ではなく、生成環境に共通するsurface symmetryだった。

> **環境横断不変性はsurface依存を減らす必要条件になり得るが、意味factorの十分条件ではない。**

### 既知・未知語の高得点は構造創発ではない

既知0.8889、未知語1.0はbase candidate generatorの時点でpair recallが1.0だった制御条件であり、Invariant方式の増分ではない。command候補がafter/futureへ明示的に露出した影響が強い。

### 難条件は改善しない

曖昧性、計画変更、反実仮想はpair recall 0。主語省略はvalue recall 1.0でもobject/pair recall 0.0278。環境不変prototypeはscope、談話focus、旧案と最終案、実行世界と未実行世界を分離しなかった。

### Nullは全面棄権

Invariant+Nullは全条件でwrong commit 0、null率1.0、accuracy 0。安全停止としてのみ機能した。

## 失敗分類

- 候補崩壊: 曖昧性、計画変更、反実仮想で正答pairが候補集合外
- Factor崩壊: 環境不変signatureが意味roleを分割しない
- 相関不変性: 生成環境の共通対称性を意味不変性と誤認
- 局所最適: Nullなしではjunk候補へ安定収束
- Null安全停止: 全条件で全面棄権
- 発散: active集合収縮と最大5 sweepにより未観測

## Hopfield・既存NNとの差

固定patternの想起ではなく、入力ごとに疎なobject/value候補pairを生成し、複数局所制約energy、環境横断prototype、active-set反復収縮で固定点を求める。

ただし今回も有限文字列候補に対する手続き的energyであり、正式な連続energy network、free/nudged相関差による厳密な平衡伝播、学習済み意味node間の局所可塑性には未到達。

## 資源量

- モデルサイズ: 1,556 bytes
- Peak RSS: 111,668 KiB（Python runtime込み）
- 学習時間: 0.257138 sec
- 推論時間: 既知1.940 ms、複数段落2.369 ms/example
- 平均反復: 2.00
- 平均活性状態: 1.11
- 収束率: 1.0（集合固定または上限停止を含む）
- 計算量: 候補`O(L²)`、局所応答`O(HF)`、prototype学習`O(NEH)`、relaxation`O(SH)`、`E=4,H≤48,S≤5`

1GB未満・5ms未満は小規模制御条件で達成。弱いスマートフォン実機は未検証。

## 系列E固有の進展

1. Candidate proposal
2. Null-preserving relaxation
3. Responsibility localization
4. Factor swap residuals
5. Basin curvature
6. Bifurcation birth
7. Constraint-wise intersection
8. **Environment-decoupled response invariance――今回反証**
9. Independent intervention equivalence
10. Local factor graph learning
11. Equilibrium propagation
12. Goal・constraint attractor planning

今回確定した知見:

> **同じ局所energy応答が複数surface環境で再発しても、意味factorである保証はない。環境生成の共通対称性を消す独立介入と、候補間の交換可能性・非交換可能性を直接測る必要がある。**

## 他系列へ返す知見

- A: 複数horizon・surfaceで同じ予測応答が出ても、同じ談話objectとは限らない。
- B: 三者view一致は、独立介入でbindingを交換した際の導出結果まで反証する。
- C: environment-stable residual signatureだけでevent identityを統合せず、介入target交換でmechanismを確認する。
- D: write/read双方の環境横断一致も、同じ生成surface由来ならslow memoryの十分条件ではない。

## 次の仮説

**Commutator-Separated Factor Roles from Independent Intervention Pairs**  
（独立介入pairの交換子によるfactor role分離）

1. 同じ候補へ介入A→BとB→Aを適用
2. 順序を変えても結果が同じ候補を独立因子候補化
3. 順序でtargetだけが変わる候補を関係・scope候補化
4. non-target damageの交換子を別energyとして保持
5. object名・value表現・語順・state表現を変えて交換子signatureが再現するか測定
6. 交換子class成立後だけ局所factor graphへ結合
7. free/nudged二相でedge-local correlation差を更新
8. 曖昧性・計画変更・反実仮想のpair recallを主評価化

C系列の因果operation commutatorとは異なり、Eは候補factor間のenergy relaxation非可換性と局所可塑性を中心にする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
