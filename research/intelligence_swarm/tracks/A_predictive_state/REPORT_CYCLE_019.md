# 系列A Cycle 019 研究報告

## 仮説

**Dual-View Boundary Birth from Independent Persistence and Change Predictions**  
（独立した持続予測・変化予測からの二視点境界生成）

Cycle 018では境界split/mergeとaction候補を単一のafter/future誤差で共同評価したが、全splitでpair recallが0となり、paragraphではwrong commit 0.25を生じた。今回はobject/value pairを直接生成せず、persistence viewとchange viewを独立に生成・反証してから疎結合した。

- persistence view: before→futureで保存されるraw span
- change view: before→afterで新たに現れ、commandにも存在するraw span
- command view: 各候補を匿名maskした周辺pattern
- pair: 各view上位候補の疎直積のみ
- null: pair recallが確認できない場合は一意化しない

## 重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との区別 |
|---|---|---|---|---|
| B | 匿名failure-cause商 | 既知局所program 0.6889 | 未知形式0、MDL 6.66倍悪化 | 圧縮・program商は扱わない |
| C | cycle-consistent transport対応写像 | 保存区間anchorに限定信号 | 双方向transport悪化、coverageほぼ0 | world operation transportは扱わない |
| D | relation-selective bridge link | rename write +0.0361 | read悪化、link過剰 | 長期memory aliasは扱わない |
| E | responsibility-localized frustration | 推論短縮、null安全停止 | candidate recall 0 | energy relaxationは扱わない |
| **A** | **持続予測と変化予測を独立状態として生成後に疎結合** | 今回検証 | view境界・binding identifiability | 系列固有 |

## 先行研究との位置づけ

部分観測下では観測と状態を同一視せず、将来予測に十分な表現を形成する必要がある。2024年の部分観測因果表現研究は、各観測が潜在状態の一部しか含まない場合に疎性が識別性へ寄与し得ることを示す。2025年のmemory trace研究は長履歴を指数移動平均で圧縮し得るが、観測feature自体は定義済みである。2026年のobject persistence研究も持続性を予測対象として分離するが、VLM/vision表現を前提とする。本Cycleは固定encoderなしのraw日本語区間へこの分離原理を適用した反証実験である。

## 実験条件

- seed: 1 / 7 / 19
- 学習: 24 episode
- test: 8例 / split / seed
- split: seen / held paraphrase / rename / alternate state / nested / subject omission / paragraph / plan change
- ablation:
  1. joint view
  2. dual independent gates
  3. dual + null
- persistence/change候補上限: 各6
- pair上限: 16
- learnerはraw before / command / after / futureと順序のみを使用。hidden object/valueは評価専用。

## 3 seed平均

| 条件 | Joint object/value/pair recall | Dual object/value/pair recall | Dual+Null accuracy/wrong/null |
|---|---:|---:|---:|
| seen | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| held | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| rename | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| alternate | 1.0000/0.0000/0.0000 | 1.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| nested | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| omitted | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| paragraph | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |
| plan | 0.0000/0.0000/0.0000 | 0.0000/0.0000/0.0000 | 0.0000/0.0000/1.0000 |

## 判定

**中核仮説は強く反証。**

### 1. Persistence viewも既知条件でobject recall 0

beforeとfutureの共通spanを抽出しても、top-kは長い周辺文脈へ偏り、正しいobject spanを選べなかった。別状態表現だけobject recall 1.0となったが、これは区切り記号によりobject spanが候補上位へ露出した表面効果である。

### 2. Change viewは全条件でvalue recall 0

before→afterの変化区間を参照しても、command候補の長い包含spanが上位へ来て、最小のvalue spanを形成できなかった。位置が分かっても境界粒度とroleは識別されない。

### 3. View分離の能力増分は0

全条件でpair recallとaccuracyは0。Dual gateはalternateでJointのjunk誤確定1.0をnullへ戻しただけで、意味候補を増やしていない。

### 4. 独立予測viewは必要条件だが十分条件でない

object persistenceとvalue changeを分ける評価設計は、失敗箇所を明確化した。しかし各view内で「長い説明span」と「再利用可能な最小role span」を区別する原理がなく、境界生成は未成立である。

## 資源量

- model: 32474 bytes
- training: 0.0143 sec
- inference:
  - seen 3.9055 ms/example
  - nested 5.7458 ms/example
  - paragraph 7.2038 ms/example
- Peak RSS: 112644 KiB（Python runtime込み）
- complexity: fit `O(NL²G)`, inference `O(L²G + KpKc)`, `Kp,Kc<=6`
- 1GB未満: 達成
- 5ms目標: seenでは達成、nested/paragraphでは未達
- 弱いスマートフォン実機: 未検証

## 系列A固有の進展

> **持続予測と変化予測を独立に評価すると、pair失敗をobject境界失敗とvalue境界失敗へ分解できる。しかし予測viewだけでは、包含関係にある多数spanから最小の再利用可能role境界を選べない。**

## 他系列へ返す知見

- B: failure causeを圧縮する前に、包含span間の最小十分境界を独立に識別する必要がある。
- C: correspondence mapは長い保存区間でなく、局所transitionを保つ最小anchorを選ぶ必要がある。
- D: bridge linkは長いsurface区間同士の可逆置換をalias証拠にしない。
- E: responsibility位置の周囲をそのままnode化すると包含junkが残る。factor swapで最小十分性を測る必要がある。

## 次の仮説

**Minimal Sufficient Predictive Boundaries by Occlusion–Expansion Contrast**  
（遮蔽・拡張対比による最小十分予測境界）

次は各persistence/change候補に対して、

1. 候補内部を1文字ずつ遮蔽したときの予測損失増加
2. 左右へ1文字拡張したときの予測利得
3. 別episodeへtransportしたときの再現性
4. 非対象予測の保存

を測る。遮蔽で能力が落ち、拡張しても利得が増えない最小区間だけをrole候補へ昇格する。object/value viewは引き続き独立に評価し、pair結合は両方のrecall確認後に限定する。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
