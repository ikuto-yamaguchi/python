# 系列A Cycle 029 研究報告

## 仮説

**Intervention-Coupled Route Identity from Shared Temporal Response Kernels**  
（共有時間応答kernelによる介入結合route identity）

Cycle 028ではcommitmentとresidualを別符号器へ分離し、直接文字一致をroute scoreから除外したが、主語省略carry率は0.9259から0.0435へ崩壊した。今回は静的なcross-encoding類似度を廃止し、前turn commitmentへの局所mask介入が現在turnのprediction errorへ与える位置bucket別変化を時間応答kernelとして用いた。

現在turnのafter/futureはroute選択へ使用していない。直接文字列overlap、embedding cosine、固定ontology、手書きslot、RAG、外部LLMも使用していない。

## 先行研究整理

- Khetarpal et al. (AISTATS 2025), *A Unifying Framework for Action-Conditional Self-Predictive Reinforcement Learning*：action-conditioned self-predictive objectiveと低rank dynamicsの関係を解析するが、state/action表現は事前定義される。  
  https://proceedings.mlr.press/v258/khetarpal25a.html
- Duan et al. (AAAI NeuroAI 2026), *Multi-Modal Natural Intelligence through Active Predictive Coding*：高位状態が低位の状態遷移・policy回路を変調し、複雑な遷移を単純な遷移の系列として構成する。ただし階層回路と状態表現は設計済み。  
  https://proceedings.mlr.press/v308/duan26a.html
- Kim et al. (2025), *Self-Predictive Dynamics for Generalization of Vision-based Reinforcement Learning*：forward/inverse transitionをaugmentation間で予測するが、視覚encoderとaction-conditioned transitionを前提とする。  
  https://arxiv.org/abs/2506.05418
- Tang et al. (2022), *Understanding Self-Predictive Learning for Reinforcement Learning*：予測誤差最小化だけでは表現collapseが起こり、更新力学が重要であることを示す。  
  https://arxiv.org/abs/2212.03319

今回の課題は、それらより上流にある、生の日本語から「どの過去状態が現在の未説明部分へ機能的に寄与するか」を形成する問題である。

## 他系列との重複表

| 系列 | 最新中心 | Aで棄却・分離した領域 |
|---|---|---|
| B | Program合成probe stateによる入力横断識別 | program帰納・MDL・probe experiment |
| C | Target-context mechanism adapter | 因果state-transition transport |
| D | Cross-channel intervention response kernelによるmemory endpoint | 長期memory・再固定化 |
| E | Boundary split–mergeによるenergy candidate birth | energy固定点・attractor |
| **A** | **前turn commitment介入から現在turn prediction-errorへの時間方向kernel** | 今回の固有対象 |

Dも介入応答kernelを扱うため、spanの機能的identity一般はDへ譲り、Aでは「前turn→現在turn」の継続・切替routeに限定した。

## 実装

- 3-order transition predictor：前turn `after | future` から現在turn `before | command` を予測
- 2-order local predictor：現在turn `before` から `command` を予測
- Commitment intervention：前turn contextの上位12 spanを同長maskへ置換し、現在turn予測NLLの8位置bucket差を量子化
- Residual intervention：現在turn beforeの上位12 spanをmaskし、command予測NLLの8位置bucket差を量子化
- Route identity：commitment側とresidual側のshape・kernel pair。正support 2以上、負supportの2倍以上のみ採用
- Ablation：No carry / Unconditional carry / Intervention-kernel route

## 3 seed平均

| 条件 | No carry pair / 精度 | 無条件carry pair / 精度 | Kernel pair / 精度 |
|---|---:|---:|---:|
| 既知 | 1.0000 / 0 | 1.0000 / 0 | 1.0000 / 0 |
| Rename | 1.0000 / 0 | 1.0000 / 0 | 1.0000 / 0 |
| 入れ子 | 1.0000 / 0 | 1.0000 / 0 | 1.0000 / 0 |
| 主語省略 | 0 / 0 | 1.0000 / 0 | 0 / 0 |
| 明示切替混在 | 0.4783 / 0 | 1.0000 / 0 | 0.4783 / 0 |
| 複数段落 | 1.0000 / 0 | 1.0000 / 0 | 1.0000 / 0 |
| 計画変更 | 1.0000 / 0 | 1.0000 / 0 | 1.0000 / 0 |

追加診断：

- Kernel route prototype：**0**
- 主語省略kernel carry率：**0**
- 主語省略continuation hit：**0**
- 明示切替wrong carry：**0**
- Kernel model：**19,433 bytes**
- 学習時間：**0.261498秒**
- 既知推論：**1.361 ms/example**
- 主語省略推論：**1.209 ms/example**
- Peak RSS：**160,012 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Route prototypeは0件

3 seedすべてで採用条件を満たす時間応答kernel pairは形成されなかった。Commitment maskが現在turn予測誤差へ与える応答と、current residual maskの応答は、同じ談話対象が継続するepisodeでも安定して一致しなかった。

### Kernel方式はNo-carryへ完全退化

全splitでKernel方式のpair recall・accuracy・carry率はNo-carry方式と完全同一だった。

主語省略では、無条件carryだけが正答objectを候補集合へ入れたが、accuracyは0だった。Kernel方式は誤carryを抑える代わりに正しい継続も全棄却した。

### 応答kernelが内部状態介入になっていない

Mask介入はraw文字spanを置換してtransition predictorのcontextを変える。これはobject permanence、goal、relation、scopeなどの内部状態を除去したものではない。

> **静的表現類似度を介入応答kernelへ置き換えても、介入単位がraw spanである限り談話route identityは形成されない。**

### 候補recallと実行選択は依然分離

既知・Rename・入れ子・複数段落・計画変更ではpair recall 1.0だがaccuracy 0だった。正解spanが候補集合へ含まれても、object/value/operation/scopeを束縛して正しい状態更新へ変換できていない。

### 計画変更は未成立

旧案・撤回・最終goalを別の時間状態へ分けられなかった。

## 反証条件

支持には次が必要だった。

1. 直接文字一致なしで複数seedにroute prototypeが形成
2. 主語省略continuation recallがNo-carryを上回る
3. 明示切替wrong carryを無条件carryより抑制
4. Kernel方式がexecution accuracyを改善
5. 計画変更で旧goalと最終goalのkernelが分離
6. 複数surface環境で同じkernel identityが再現

今回はすべて未達。

## 資源量・計算量

- Predictor学習 `O(NL)`
- Commitment介入 `O(KL)`
- Residual介入 `O(KL)`
- Route照合 `O(KcKr)`
- Candidate span `O(L²)`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **予測状態候補を先に構成し、その状態の遷移operatorを介入単位にする必要がある。raw spanの応答kernelから状態identityを逆算する順序は成立しない。**

## 他系列へ返す知見

- B：raw spanへのprobeだけではprogram stateへの介入にならず、識別testが空になる可能性がある。
- C：Target-context adapterの介入単位は文字contextではなく、実行可能なtransition operator候補である必要がある。
- D：Span response kernelはmemory endpoint identityの十分条件ではなく、状態更新operatorとread consequenceを結ぶ必要がある。
- E：Boundary split–mergeのenergy低下だけでは生成segmentが状態変数である保証がなく、transitionへの機能的寄与を別監査すべき。

## 次の仮説

**Operator-Centered Predictive State Birth from Recurrent Error-Cancellation Loops**  
（反復誤差相殺loopからのoperator中心予測状態創発）

1. `before + command`から複数の局所edit operator候補を生成
2. 各operatorを適用したprospective stateを形成
3. State→next observation予測とobservation→state逆更新を反復
4. 複数turnで同じ局所prediction errorを相殺するoperatorだけstate cell化
5. Operator除去で対応errorが再発することを反証条件化
6. 主語省略では前turn operator-stateをcurrent candidateとして再利用
7. 明示切替では新operatorが旧errorを説明した場合に旧stateを終了
8. 計画変更では旧goal operatorと最終goal operatorを競合
9. Candidate recallではなくprospective execution accuracy・error cancellation・wrong carryを主評価化

- 高校生級：**未達**
- ネイティブ日本語コミュニケーション：**未達**
- 弱いスマートフォン実機：**未検証**
- 完成：**未達**
