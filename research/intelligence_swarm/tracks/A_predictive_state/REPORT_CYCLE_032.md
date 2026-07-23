# 系列A Cycle 032 研究報告

## 仮説

**Probe-Driven Transition-Kernel Plasticity for Operator-State Formation**  
（operator-state形成のためのprobe駆動遷移kernel可塑性）

Cycle 031では可変境界operator familyと独立probe creditを形成できたが、Correct probe・Shuffled probe・probeなしの最終能力が完全同一だった。今回はprobeをranking加点へ使わず、相対境界transition kernelの接続・保持・削除そのものへ作用させた。

## 先行研究整理

- Ng-Kee-Kwong et al. (2026), *Learning complex temporal dependencies via local synaptic plasticity*: temporal predictive codingは局所Hebbian更新とrecurrent dynamicsで時間依存を学べるが、状態変数と回路は定義済み。
- Asabuki & Clopath (2025), *Taming the chaos gently*: recurrent networkの局所predictive alignmentは軌道形成に有効だが、network stateと出力表現を前提とする。
- N’dri et al. (2025), *Predictive Coding Light*: 軽量なpredictive coding実装を扱うが、生の日本語からoperator・state境界を生成する問題とは異なる。
- Hill (2025), *Structural Plasticity as Active Inference*: prediction errorに基づく構造可塑性を提案するが、2D cell topologyと制御課題が事前定義される。

今回の課題は、これらより上流にある「自由日本語から遷移kernel自体を生成し、probeで構造可塑性を起こす」ことにある。

## 他系列との重複回避

| 系列 | 最新中心 | Aで棄却・分離した領域 |
|---|---|---|
| B | Probe駆動symbol boundary repair | MDL・program同値類・記号圧縮 |
| C | Minimal intervention support | 因果mechanism family・world graph |
| D | Probe-plastic read/write topology | 長期memory・再固定化 |
| E | Scope-gated boundary repair attractor | Energy固定点・境界修復 |
| **A** | **時間方向operator-stateの遷移kernel構造可塑性** | 今回の固有対象 |

Dもtopology rewiringを扱うため、Aではwrite/read記憶ではなく、current state→next observationの時間方向kernelと主語省略・切替・計画変更を中心評価とした。

## 実装

- 固定ontology、手書きslot、テンプレート辞書、RAG、外部LLMなし
- `before→after`差分から相対位置bucket、区間幅、old/new文字shapeのkernel候補を生成
- Induction / independent probe / final testを分離
- Correct probe:
  - forward成功かつinverse restoration成功でkernelを保持
  - 同じold/new応答を持つ近接bucket間にtopology edgeを生成
  - probe誤りが優勢なkernelを削除
- Shuffled probe:
  - probe outcomeを循環shuffleして同じ構造可塑性を実行
- 推論:
  - final testのafter/futureはrankingに不使用
  - 最大6 sweep、active集合単調縮小

## 3 seed平均

| 条件 | Family 精度/wrong | Carry 精度/wrong | Plastic 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0.0000 / 0.1667 | 0.0000 / 0.3611 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語順 | 0.0000 / 0.0000 | 0.0000 / 0.3056 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 未知語彙 | 0.0000 / 0.0000 | 0.0278 / 0.3056 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| Rename | 0.0000 / 0.3611 | 0.0000 / 0.3611 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 入れ子 | 0.0000 / 0.1667 | 0.0000 / 0.3611 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.0278 | 0.0556 / 0.1944 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 明示切替混在 | 0.0278 / 0.1111 | 0.0833 / 0.2222 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.2778 | 0.0000 / 0.4167 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 計画変更 | 0.0000 / 0.0000 | 0.0000 / 0.3333 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 反実仮想 | 0.0000 / 0.2500 | 0.0000 / 0.3333 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断:

- Plastic kernel: 0.00
- Plastic topology edge: 0.00
- Probe audit: 602.33
- Rewire update: 0.00
- Family model size: 1176 bytes
- Plastic model size: 134 bytes
- Plastic training: 0.103392 sec
- Plastic inference: 0.002691 ms/example
- Peak RSS: 111288 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Probeは構造を変えたが、正しい構造を形成しなかった

Correct probeでは平均602.33件のkernel実行を監査した。しかしforward正解とinverse復元を複数probeで満たすkernelが残らず、Plastic方式のkernel数・topology edge数はともに0になった。

つまりCycle 031の「probe creditは形成されるが順位が変わらない」状態から、今回は「probeがfamily topologyを変える」段階には進んだ。しかし変化は全削除であり、predictive state形成ではない。

> **Probe-driven structural plasticityは、候補kernelが意味的に妥当な場合の選択・再配線原理にはなり得るが、surface-local kernelから抽象operator-stateを生む原理にはならない。**

### Plastic方式は安全だが全面棄権

Plastic方式は全条件でwrong commit 0だが、accuracy 0・null 1.0だった。Family/Carry方式の誤commitを抑えたが、能力改善ではなく全kernel pruningによる安全停止である。

### Carryは誤りを増やす

Unconditional carryは主語省略・switchmixで一部正答を生んだ一方、ほぼ全条件でwrong commitを大幅に増やした。Object permanenceやfocus継続ではなく、前turn文字区間を現在turnへ混入した結果である。

### Correct probeとShuffleの双方が空になる

Shuffled probeもkernel 0へ収束した。Correct probe固有の正しいtopology差は形成されなかったため、独立観測に基づくstate topology学習とは認められない。

### 計画変更・反実仮想

Plastic方式は全面nullで、旧案・最終案・実行world・非実行worldを別固定点へ分離できなかった。Family/Carryのcommitも誤りであり、goal stateやcounterfactual stateではない。

## 反証条件

仮説支持には最低限以下が必要だった。

1. Correct probeとShuffleで異なるkernel topologyが形成される
2. Correct probeで複数kernel・edgeが残る
3. Plastic方式がFamily方式よりexecution accuracyを改善する
4. 主語省略continuationをwrong carryなしで改善する
5. 計画変更で旧案と最終案を分離する
6. 反実仮想で実行・非実行rolloutを分離する

今回はすべて未達。

## 資源量・計算量

- Kernel induction: `O(NL)`
- Probe plasticity: `O(QKV)`
- Topology rebuild: `O(K²)`
- Inference: `O(KOV + SH)`
- `K≤64, S≤6, H≤24`

- Model: 134 bytes（全pruning後）
- Peak RSS: 111288 KiB
- Training: 約0.103392 sec
- Inference: 約0.002691 ms/example

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **Probeをscore加点ではなくkernel topologyへ作用させると構造差は生じる。しかし、正しい境界・引数を持たないsurface kernelでは、可塑性は抽象状態形成ではなく全削除へ向かう。次は誤差による削除だけでなく、probe residualから新しいtransition edgeと引数境界を生成するbirth機構が必要である。**

## 他系列へ返す知見

- B: probe同値類の選択だけでなく、repairがprogram topologyを変えたかを必須評価にすべき。
- C: minimal intervention supportでも正候補がない場合、support縮約は全削除へ退化し得る。
- D: read/write topology rewiringは、correct probeで有効subgraphが残ることをshuffleとの差として要求すべき。
- E: negative forceだけではflat/null attractorへ退化するため、candidate birthとpruningの均衡が必要。

## 次の仮説

**Residual-Born Transition Kernels from Probe-Localized Error Transport**  
（probe局所誤差輸送からのresidual-born遷移kernel創発）

1. Probeで失敗したoperator候補と観測outcomeの最小局所差分を計測
2. 誤差位置をstate境界候補へ逆輸送
3. 既存kernelを削除するだけでなく、境界shift・width split・argument relinkingを生成
4. Correct probeでのみ新kernel topologyが生まれることを必須化
5. Shuffled residual・no birth・pruning onlyを比較
6. 複数probeで同じ誤差輸送を示すkernelだけstate cell化
7. 主語省略では前turn state cellを再起動
8. 計画変更では旧goal/new goal kernelを別固定点化
9. 反実仮想では実行/non-execution kernelを並行保持
10. Kernel birth数、topology差、execution accuracy、wrong carryを独立評価

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
