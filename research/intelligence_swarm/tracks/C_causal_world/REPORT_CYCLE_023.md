# 系列C Cycle 023 研究報告

## 仮説

**Temporal-Reversal Event Anchors with Directed Transition Graphs**  
（時間反転event anchorと有向transition graph）

当初予定していた `Transport-Map Birth from Cross-Episode Edit Correspondence Programs` は、
系列B Cycle 022の次仮説 `Correspondence Programs from Minimal Edit-Graph Anti-Unification`
と、中心機構・実装・反証条件が実質的に重なるため棄却した。

代わりに、局所eventを時間順方向と逆方向へ適用した際の非対称性から、
因果方向を持つevent anchorを形成できるか検証した。

各eventはraw `before / command / after / future`から生成し、次を計測した。

- 順方向で観測afterを再構成する回数
- 順方向の誤実行
- 時間反転時の再構成可能性
- event間の局所shape整合
- sequential counterfactual composition
- non-target文字列の保存

## 先行研究との位置づけ

- Interventional Causal Representation Learningは、介入データが潜在因果因子の識別に固有の情報を与えることを示すが、介入対象と観測空間は定義済み。
  - https://proceedings.mlr.press/v202/ahuja23a.html
- CITRISは時間系列と介入対象から潜在因果変数の識別を扱うが、encoderと介入targetを前提とする。
  - https://proceedings.mlr.press/v162/lippe22a.html
- Learning a Spatial Partitioning and its Causal Relations from Temporal Dataは、低水準観測からpartitionと因果関係を共同学習するが、空間的grouping仮定を持つ。
  - https://proceedings.mlr.press/v323/brouillard26a.html
- Causal-JEPAはobject-level latent interventionがcounterfactual reasoningを改善するが、object representationは先に形成される。
  - https://arxiv.org/abs/2602.11389

今回の実験は、生の日本語文字列からevent境界・状態変数・方向を同時形成できるかという、
さらに上流の問題を対象とする。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な未解決 | Cで棄却・分離した方向 |
|---|---|---|---|---|
| A | 残差逆投影と談話carryによるtest-cell共同創発 | 候補集合内の自己生成test | open-set birth増分0 | active query policyは扱わない |
| B | edit graph反単一化によるcorrespondence program | filler再利用の限定信号 | context transport 0 | edit対応program案を棄却 |
| D | value-change同値類memory | endpoint分離で誤読低下 | slow binding 0 | 長期memory統合は扱わない |
| E | 制約別basin分岐交差 | null安全停止 | value birth消失 | energy landscapeは扱わない |
| **C** | **時間反転非対称性によるevent方向と因果graph** | 今回検証 | event identity・因果方向 | 系列固有 |

## 実験条件

- Seed: 1 / 7 / 19
- 学習例: 48 / 144 / 288
- Test: 各splitで最大48例 / seed
- Event上限: 64
- Edge上限: 96
- 比較:
  1. Surface
  2. Temporal asymmetry
  3. Directed event graph
- 自由日本語条件:
  - 既知
  - 未学習言い換え
  - Rename
  - 別状態表現
  - 主語省略
  - 複数段落
  - 計画変更
  - 反実仮想

Hidden object・field・valueは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Surface | Asymmetry | Directed graph |
|---|---:|---:|---:|
| 既知 | 0.2500 | 0.2500 | 0.2500 |
| 未学習言い換え | 0.1597 | 0.1597 | 0.1597 |
| Rename | 0.2222 | 0.2222 | 0.2222 |
| 別状態表現 | 0.2083 | 0.2083 | 0.2083 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 複数段落 | 0.1667 | 0.1667 | 0.1667 |
| 計画変更 | 0.1806 | 0.1806 | 0.1806 |
| 反実仮想 | 0.1597 | 0.1597 | 0.1597 |

Sequential composition:

- Coverage: 0.1277
- Conditional accuracy: 0.3286

Graph diagnostics:

- Event: 64.00
- Directed event: 62.33
- Causal edge: 96.00
- Mean direction score: 0.2643
- Forward success: 164.67
- Forward wrong: 1.67
- Reverse success: 0.00

## 判定

**中核仮説は強く反証された。**

### Asymmetry・graphの能力増分は0

Surface / Asymmetry / Directed graphは、全splitでaccuracy・wrong commit・null率・候補数が同一だった。

時間方向scoreと96本の有向edgeを追加しても、正しいevent選択や未知表現へのtransportを一件も改善していない。

### Reverse success 0は因果方向の証拠ではない

平均62.33/64 eventが正のdirection scoreを持ったが、reverse executionは設計上、
過去の具体的old valueを保持していないため全面的に棄権した。

その結果、direction scoreは「順方向は少し実行できるが逆方向は実装不能」という
**機構上の非対称性**を測っており、世界の因果方向を識別していない。

### 有向graphはshape互換性の密結合

Graphは上限96 edgeまで形成されたが、能力値はSurfaceと完全同一だった。

Edgeは `new_shape == old_shape` または局所context一致で接続され、
object・relation・state variable・goalの因果edgeではない。

### 主語省略は0

主語省略では全方式0、null率1.0だった。
談話focusをobject permanenceとして保持する仕組みは未成立。

### 計画変更・反実仮想は局所substring信号

計画変更0.1806、反実仮想0.1597はgraph増分ではなくSurfaceと同一であり、
入力内に残る既知局所command substringの再実行である。

旧goal・新goal・revision・未実行世界を内部状態として保持していない。

### Sequential counterfactual coverageが低い

Coverageは0.1277、conditional accuracyは0.3286だった。
実行可能なevent pairが少なく、順序合成による因果planning能力とはみなせない。

## 相関暗記と因果理解の分離

相関暗記の証拠:

- 既知substringを含む条件だけ部分成功
- Surfaceとgraphが完全同値
- graph edge追加による能力増分0
- direction scoreが逆実行未実装に依存

因果理解に必要だが未成立:

- eventの可逆・不可逆性を同じ情報条件で比較
- object・relation別の介入target
- confounderを変えた未知対象転移
- model自身の反実仮想world rollout
- goal revisionとconstraint planning
- 主語省略を跨ぐobject permanence

## 資源量

- Graph model: 12150 bytes
- Training: 0.014899 sec
- Inference: 0.082921 ms/example
- Peak RSS: 160328 KiB（Python runtime込み）
- 推定計算量:
  - event抽出 `O(NL)`
  - transport audit `O(PN)`
  - graph形成 `O(P²)`
  - 推論 `O(PL)`
  - `P ≤ 64`

1GB未満・5ms未満は制御条件で達成した。
弱いスマートフォン実機では未検証。

## 系列C固有の進展

因果world model形成段階を更新する。

1. Raw event proposal
2. Local transition extraction
3. Success・wrong・null transport分離
4. Effect hypergraph
5. **Temporal direction audit――今回反証**
6. Symmetric-information reversal test
7. Event identity and state-variable induction
8. Counterfactual composition
9. Goal・constraint planning

核心的知見:

> **順方向だけが実行できるという非対称性は、因果方向の証拠にならない。順逆で同じ情報を与えた上で、介入後の独立mechanismとnon-target保存の差を比較する必要がある。**

## 他系列へ返す新知見

- A: testの方向性を比較する際、片方向だけ観測情報を多く与えると情報利得が自明化する。
- B: forward derivationとinverse derivationを比較する場合、双方に同じ変数情報を与える必要がある。
- D: read/write非対称性を因果的memory edgeとみなす前に、両方向の情報量を揃える。
- E: basin方向差が候補生成手続きの非対称性に由来しないか監査する。

## 次の仮説

**Symmetric-Information Event Direction from Paired Intervention Replays**  
（対称情報付き介入replayからのevent方向創発）

次はreverse側にもraw観測から抽出した局所old-value候補を与え、順逆の情報条件を揃える。

1. 同一eventについてforward replayとreverse replayを生成
2. 両方向で同じ数の局所候補・同じcontext幅を使用
3. Object候補・value候補・relation候補を独立swap
4. Forwardだけでnon-targetを保存し、reverseで独立mechanismが壊れる場合だけ方向edge化
5. 未知object・Rename・別状態表現でdirection consistencyを評価
6. Model自身が実行可能と判定したedgeだけで反実仮想rollout
7. reversible eventは無向edge、不可逆eventだけ有向edgeとして保持

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
