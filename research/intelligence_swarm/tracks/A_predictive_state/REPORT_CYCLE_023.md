# 系列A Cycle 023 研究報告

## 仮説

**Predictive Test–Cell Co-Creation by Residual Backprojection with Discourse Carry**  
（談話carry付き残差逆投影による予測test・cell共同創発）

Cycle 022では候補間の予測不一致から局所観測testを自己生成でき、正答pairが候補集合内にある場合の識別は成立した。一方、観測窓とcommand区間の表面類似からのfeedback birthは全splitでpair recall増分0だった。

今回はafter・future1・future2で再発する局所残差windowを保持し、before・commandへ複数の対応仮説として逆投影した。さらに直前turnで未解消だったobject候補をdiscourse carryとして保持し、複数horizonの予測整合が改善した組だけをactive predictive cellへ残した。

## 先行研究整理

- Predictive State Representationは将来のaction-observation test結果を内部stateとして扱うが、testと観測空間は定義済み。
- REPRISEは予測誤差を過去へ遡及してcontext stateを更新し、将来制御も同時最適化するが、連続sensorimotor stateとRNN表現を前提とする。
- ICML 2025のMulti-view Fusion State for Controlはmissing viewやdistractor下で複数観測viewを融合するが、encoderとtask stateが定義済み。
- Active binary testingのInfoMax理論は候補集合内の逐次識別を扱うが、open-set候補生成は扱わない。

今回の課題は、生の自由日本語文字列からobject/value cellと残差対応を同時形成する点で、これらより上流にある。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な未解決 | Aとの分離 |
|---|---|---|---|---|
| B | edit graph反単一化correspondence program | 既知局所導出 | context transport 0 | MDL・grammarは扱わない |
| C | 対称情報付きevent direction | 局所event再実行 | 因果方向が情報非対称 | world operationは扱わない |
| D | write-only value classとread address分離 | endpoint分離で誤読低下 | slow class誤統合 | 長期memoryは扱わない |
| E | 環境分離介入に不変なenergy応答 | null安全停止 | factor binding崩壊 | energy dynamicsは扱わない |
| **A** | **観測残差の逆投影と談話carryによる再帰予測state** | 今回検証 | open-set object/value cell | 系列固有 |

## 実験条件

- Seed: 1 / 7 / 19
- 学習例: 24 / 48 / 72
- Test: 8例 / split / seed
- 比較: Base / Residual backprojection / Backprojection+carry / Backprojection+carry+null
- Object/value候補: 各最大8
- Pair候補: 最大48
- Residual window: 最大18
- Hidden object/valueは評価器だけで使用
- environmentのafter/futureはraw観測としてのみ使用

## 最大72例・3 seed平均

| 条件 | Base pair recall | Backprojection pair recall | Carry pair recall | Carry+Null accuracy | Null率 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.1667 | 0.1667 | 0.2083 | 0.0833 | 0.9167 |
| 未学習言い換え | 0.4167 | 0.5417 | 0.5417 | 0.4583 | 0.5417 |
| Rename | 0.3750 | 0.4167 | 0.3750 | 0.2500 | 0.7500 |
| 別状態表現 | 0.1667 | 0.2500 | 0.2500 | 0.0833 | 0.9167 |
| 入れ子 | 0.0000 | 0.0833 | 0.0833 | 0.0833 | 0.9167 |
| 主語省略 | 0.0000 | 0.2917 | 0.2917 | 0.2917 | 0.7083 |
| 複数段落 | 0.0000 | 0.0417 | 0.0417 | 0.0417 | 0.9583 |
| 計画変更 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## 判定

**残差逆投影には限定支持。談話carryの独立増分はほぼなく、一般知能原理としては反証。**

### 主語省略でpair recallが0から0.2917へ回復

Baseはobject recall 0、value recall 0.75、pair recall 0だった。Residual backprojectionはobject recall 0.3333、value recall 0.75、pair recall / accuracy 0.2917まで改善した。

観測後のafter/futureに再発するobject spanをbefore側へ逆投影することで、省略されたobject候補を一部再構成できた。

### discourse carryの独立増分は0

主語省略ではBackprojectionとCarryが完全同値だった。今回のcarryは直前turnの上位object候補を保持したが、残差逆投影で既に同じsurface objectを回収しており、追加能力を生まなかった。

### 限定信号

- 未学習言い換え: pair recall 0.4167 → 0.5417
- 別状態表現: 0.1667 → 0.2500
- 入れ子: 0 → 0.0833
- 複数段落: 0 → 0.0417

Renameはpair recallが増えてもaccuracyは0.2917のままで、正しいcandidateを選択できない。

### 計画変更は全面失敗

object recallは0.1667から0.5417へ増えたが、value recall・pair recall・accuracyは0。旧案・最終案・revision scopeを区別する時間的抽象化は未成立。

### 逆投影経路が過剰

1例あたり平均120〜168本のbackprojection pathを生成した。正答pair recallは増えたが、nullなしではwrong commitが0.46〜1.0残る。形成されたのは意味的因果対応ではなく、多数のsurface対応仮説である。

### Nullは安全だが能力を削る

Carry+Nullは全splitでwrong commitを0にした。一方、既知accuracyは0.2083から0.0833へ低下し、null率0.9167。主語省略ではaccuracy 0.2917を維持しwrong 0だったため限定的に有効。

## 反証条件

一般原理として支持するには、discourse carryがbackprojection単独を複数seedで上回り、観測前の談話stateからobjectを復元し、経路数を増やさず精度を改善し、主要条件5ms未満を達成する必要があった。今回は満たさず、計画変更も0だった。

## 資源量

- Model: 11,911 bytes
- Training: 0.005117 sec
- Inference: 主語省略 12.322 ms/example
- 既知 inference: 13.398 ms/example
- Predictive prototype: 64
- Active pair: 主語省略 11.50
- Backprojection path: 主語省略 151.42
- Peak RSS: 112,132 KiB（Python runtime込み）
- 計算量: character prediction `O(NL)`、residual window `O(WL)`、backprojection `O(W(C+B))`、pairing `O(KoKv)`、`Ko,Kv≤8, W≤18`

1GB未満は達成したが主要条件で8〜14msとなり5ms目標は未達。弱いスマートフォン実機では未検証。

## 系列A固有の進展

1. Raw prediction-error stream
2. Surprisal event cell
3. Candidate disagreement test
4. Observation-conditioned recursive update
5. **Multi-horizon residual backprojection――限定支持**
6. **Discourse carry――独立増分なし**
7. Pre-observation persistent object state
8. Goal/revision temporal abstraction
9. 自由日本語world state

> **after/futureで再発する残差をbefore/commandへ逆投影すると、主語省略を含むopen-set pair recallを部分回復できる。しかし観測後の文字列にobject名が現れる条件へ依存し、談話carryそのものは増分を示さなかった。これは遡及的説明であり、観測前のobject permanenceではない。**

## 他系列へ返す知見

- B: 逆導出で未知contextを回収できても、forward生成と同じ意味変数を形成した証拠にはならない。
- C: Future/afterからの逆投影成功を因果方向とみなさず、観測前予測で反証する。
- D: 観測後にobject addressを再構成することと、長期memoryから事前に呼び戻すことを分離する。
- E: 複数horizon残差の一致も同一surface object出現依存なら独立energy evidenceではない。

## 次の仮説

**Prospective Discourse State from Pre-Observation Prediction Commitments**  
（観測前予測commitmentからの前向き談話状態）

1. 各turn終了時に次turnで持続すると予測したobject cellをcommit
2. 次commandが主語省略の場合、commit済みcellだけを候補に使用
3. 観測後は予測誤差で更新するが初期選択には使わない
4. Multiple object候補を保持し、query cost込みでactive testを選ぶ
5. 予測前object recallと観測後object recallを分離測定
6. 複数段落・計画変更ではfocus stackとgoal revision cellを別状態化
7. Carryなし、事後逆投影、前向きcommitmentを独立ablationする

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
