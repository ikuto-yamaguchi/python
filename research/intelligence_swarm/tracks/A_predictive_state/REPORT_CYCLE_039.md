# 系列A Cycle 039 研究報告

## 仮説

**Prediction-Error Hysteresis Cells from Delayed Paraphrase Re-entry**  
（遅延言い換え再入からの予測誤差ヒステリシス状態cell）

Cycle 038の次案だった能動object-disagreement queryは、系列B・D・E Cycle 038で同型の能動不一致探索がすでに強く反証されたため重複棄却した。

今回は系列A固有の時間軸へ戻り、単発入力内の候補分割ではなく、連続対話における予測誤差の持続と解消から状態を維持・終了できるかを検証した。

- 明示命令で状態cellを起動
- 次turnの主語省略命令で同じcellを再起動
- 明示的な別対象命令が十分な反証を与えた場合だけcellを切替
- 同一cellの連続成功でhysteresisを増加
- Stateless / 無条件Carry / Hysteresis / 学習turn順shuffleを比較
- Final testのafter/futureは候補生成・rankingに不使用

## 他4系列との重複表

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B Cycle 038 | 能動不一致queryによるproduction birth | MDL・記号grammar |
| C Cycle 038 | Paired-world object-support共同分節 | 因果world graph |
| D Cycle 038 | 能動replay queryによるaddress birth | 長期memory・slow統合 |
| E Cycle 038 | 能動constraint queryによる直交sensor birth | Energy固定点 |
| **A Cycle 039** | **連続turnでの状態持続・再入・終了を誤差ヒステリシスで形成** | 今回の固有対象 |

## 先行研究整理

2025年のpredictive alignmentは局所可塑性でrecurrent trajectoryを整えられることを示すが、状態変数と回路構造は既定である。Temporal Predictive Codingの2026年研究は、局所Hebbian更新・reservoir dynamics・eligibility traceで長期依存を扱える可能性を示すが、やはり内部stateは事前定義済みである。Successor Representationの局所学習研究は時間対称性が予測表現の一般化へ影響することを示すが、生の日本語から対象・操作境界を生成する問題は扱わない。

今回の課題は、それらより上流の「どの離散状態を再帰的に維持すべきか」を自由日本語から形成することである。

## 3 seed平均

| 条件 | Stateless 精度/wrong | Carry 精度/wrong | Hysteresis 精度/wrong | Shuffle 精度/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 言い換え | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 未知語順 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 複数段落 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 計画変更 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 反実仮想 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

追加診断:

- Induced rule: **48**
- Hysteresis switch: **0**
- Hysteresis retain: **0**
- Retained rate: **0**
- Model: **約9,800 bytes**
- Training: **約0.0166 sec**
- Seen inference: **0.719 ms/example**
- Paragraph inference: **0.804 ms/example**
- Peak RSS: **160,000 KiB**（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Rule集合は形成されたが、初回状態起動が全面tie

各seedで平均48個の局所ruleが形成された。しかし明示turnでも複数ruleが同点となり、Stateless方式は全条件でnull率1.0だった。

Hysteresisは一度active cellが起動した後の持続原理である。初回turnで状態cellを一意に起動できなかったため、再帰・carry・終了判定へ一度も到達しなかった。

### CarryとHysteresisの増分0

- Accuracy: 全条件0
- Wrong commit: 全条件0
- Retain: 0
- Switch: 0
- 主語省略accuracy: 0
- 明示対象切替accuracy: 0

無条件CarryもHysteresisもStatelessと完全同一だった。

> **時間的持続は、意味的に起動可能な状態cellが既に存在するときの更新原理であり、状態cellのbirth原理ではない。**

### 学習turn順shuffleとの差0

学習dialogueのturn順を崩しても、rule数・能力・null率は同じだった。

形成されたruleは時間系列の持続構造ではなく、個別episodeの局所文字列edit signatureである。

### 自由日本語統合テスト

- 言い換え: 0
- 未知語順: 0
- 主語省略: 0
- 複数段落: 0
- 計画変更: 0
- 反実仮想: 0

Object permanence、event segmentation、goal revision、実行world／非実行world分離は未成立。

## 反証条件

仮説支持には最低限、次が必要だった。

1. 明示turnでcellが一意に起動する
2. 主語省略でHysteresisがStatelessより改善する
3. 明示対象切替で無条件Carryよりwrong carryが減る
4. 学習turn順shuffleで能力が低下する
5. 計画変更で撤回状態を終了する
6. 反実仮想で実行・非実行stateを並行保持する

すべて未達。

## 既存方式との差

Transformer attention、分類器、固定ontology、手書きslot、辞書、RAG、外部LLMは使っていない。

入力ごとに局所状態更新ruleを生成し、再帰状態とevent-driven hysteresisで継続・切替を試みた。ただし現在のruleはsurface-localな文字列編集であり、予測符号化state、active inference、時間抽象化には未到達。

## 資源量・必要計算量

- Rule induction: `O(NL)`
- Candidate proposal: `O(RVL)`
- Recurrent hysteresis update: `O(1)` / event
- Rule上限: 64
- Model: 約9.8KB
- Training: 約0.0166 sec
- Inference: 0.7〜0.9 ms/example
- Peak RSS: 160,000 KiB

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。性能0のため、効率的知能の証拠ではない。

## 系列A固有の進展

> **状態の持続・終了を先に工夫しても、初回turnで意味的state cellを起動できなければ再帰機構は空転する。時間ヒステリシスはbirth後の安定化原理であり、birth原理ではない。**

## 他系列へ返す知見

- B: Production grammarは再利用以前に一意な初回起動条件が必要。
- C: Event persistenceやobject permanenceはobject-support候補の共同分節後に検証すべき。
- D: Slow consolidationやcarryは初回semantic address起動を代替しない。
- E: Attractor安定化は意味候補が存在しなければflat/nullへ退化する。

## 次の仮説

**Delayed-Error Event Boundary Birth from Competing Microstate Lifetimes**  
（競合microstate寿命の遅延誤差からのevent境界創発）

次はruleを一意に選んでから持続させない。

1. 初回turnで複数microstate候補を並行起動
2. 各候補へ未来2〜4 turnの予測責任を持たせる
3. 主語省略・future継続・明示切替を別の遅延誤差channelとして蓄積
4. 誤差が連続して低い候補だけ寿命を延長
5. 誤差急増位置をevent boundaryとする
6. 正解after一件への即時一致ではなく、累積予測損失でcellを選択
7. Temporal order / shuffled order / one-step / no-lifetimeを比較
8. 計画変更では撤回案cellを遅延誤差で終了
9. 反実仮想では実行・非実行microstateを並行保持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
