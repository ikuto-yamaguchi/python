# 系列B Cycle 022 研究報告

## 仮説

**Open-Transport Context Relations from Partial Derivation Homomorphisms**  
（部分導出準同型からのopen-transport context関係）

Cycle 021では success / wrong / noexec の完全なbehavioral bisimulationを要求したため、context nonterminalが0件だった。今回は `noexec` を意味差ではなく未観測transportとして除外し、両contextが実行可能なepisode上でのみ部分準同型を評価した。

候補relationは次を満たす場合だけ採用した。

- 2 episode以上で共通success
- odd/even held-out viewの双方でsuccess/wrong挙動が一致
- wrong transport率35%以下
- state transitionの左右保存shapeが一致
- surface command contextの完全一致は要求しない

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 未解決 | B候補との分離 |
|---|---|---|---|---|
| A | 候補不一致残差からの予測test自己生成 | 候補集合内の識別 | open-set birth 0 | query policyは棄却 |
| C | edit対応programによるtransport map | success/wrong/null評価分離 | 約99% null transport | world operation mapは棄却 |
| D | value-change同値類memory | endpoint分離で誤読低下 | slow binding 0 | 長期memoryは棄却 |
| E | 制約別basin分岐 | null安全停止 | value birth消失 | energy dynamicsは棄却 |
| **B** | **既知導出間の部分準同型からcontext関係を圧縮** | 今回検証 | open-form grammar | 系列固有 |

継承知見:

- A: 識別testは候補集合外の構造を生成しない。
- C: `null/noexec` と `wrong` を混ぜない。
- D: value表現のsurface分裂をrelation/object identityと混ぜない。
- E: 固定点切替・残差分類は意味roleの十分条件ではない。

## 実験

- seed: 1 / 7 / 19
- train size: 48 / 144 / 288
- test: 48例 / split / seed
- program上限: 32
- relation上限: 32
- split: 既知、未知語順、未知語彙、Rename、入れ子、主語省略、別状態表現、複数文
- ablation:
  1. Executable baseline
  2. Strict bisimulation control
  3. Partial homomorphism

学習器はraw `before / command / after`のみ使用し、object・field・valueラベルは評価器だけで使用した。

## 最大288例・3 seed平均

| 条件 | Executable | Strict | Partial |
|---|---:|---:|---:|
| 既知 | 0.6111 | 0.6111 | 0.6111 |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知語彙 | 0.0000 | 0.0000 | 0.0000 |
| Rename | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.6111 | 0.6111 | 0.6111 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 |
| 複数文 | 0.6111 | 0.6111 | 0.6111 |

## 判定

**中核仮説は強く反証。**

### Partial relationは0件

最大288学習例・全seedで、部分導出準同型relationは0件だった。

`noexec`をsignatureから外しても、異なるsurface context間で、2件以上の共通success、odd/even双方での再現、低いwrong率、state transition shapeの一致を同時に満たす組が存在しなかった。

したがってCycle 021の失敗原因は「完全bisimulationが厳しすぎた」だけではない。**共通の実行可能導出support自体が形成されていない。**

### 能力増分は0

Executable / Strict / Partialは全splitで完全に同一だった。

- 既知・入れ子・複数文: 0.6111
- 未知語順・未知語彙・Rename・主語省略・別状態表現: 0

Partial relationはcandidate生成、候補recall、実行精度、wrong commitのいずれも変えていない。

### 既知の0.6111は局所substring再実行

入れ子・複数文でも同じ0.6111だが、学習済みcommand substringを長い入力内で再発見した結果である。scope理解、談話構造、object identity、relation abstraction、program compositionの証拠ではない。

### `noexec`をunknownにするだけではtransportは生まれない

`noexec`を意味差として扱わない判断は評価上正しい。しかしunknown transportを除外するだけでは、未知contextへの写像候補を生成しない。

> **未知を罰しないことと、未知を跨ぐ対応programを作ることは別問題。**

### MDL利得なし

- Program: 32
- Relation: 0
- Description length: 9,128 bits
- Merge: 0

Executable baselineと総符号長は同一であり、圧縮・記号創発ともに増分0。

## 反証条件

仮説を支持するには最低でも次が必要だった。

1. Partial relationが複数seedで1件以上形成される
2. 未知語順・未知語彙・Rename・別状態表現のcandidate recallが増える
3. Wrong commitを増やさずaccuracyがbaselineを上回る
4. Relation metadata込みの総description lengthがbaseline未満
5. Held-out surfaceで新しい導出を生成する

今回は全条件を満たさない。

## 探索爆発抑制

- raw program候補: 288
- 保存program: 32
- relation探索: 最大 `32×31/2`
- held-out odd/even gate
- shared success 2以上
- wrong率35%以下
- relation上限32

計算量は抑制できたが、有効relationが0のため能力上の価値はない。

## 資源量

- Partial model: 24,899 bytes
- Training: 0.243769 sec
- Inference: 0.021878 ms/example
- Peak RSS: 160,148 KiB（Python runtime込み）
- 推定計算量:
  - proposal `O(NC²)`
  - behavior matrix `O(PN)`
  - partial relation `O(P²N)`
  - inference `O((P+R)L)`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 系列B固有の進展

Program symbol形成段階を更新する。

1. Clause候補生成
2. 局所実行可能性
3. 誤適用反証
4. Intervention outcome
5. Numerical rank basis
6. Multi-view separation
7. Held-out可逆復号
8. Positive/negative witness共同符号化
9. Anonymous failure quotient
10. Filler nonterminal
11. Context bisimulation――反証
12. **Partial derivation homomorphism――今回反証**
13. Correspondence-program synthesis
14. Hierarchical MDL consolidation

今回の核心的知見:

> **`noexec`をunknown transportとして分離することは必要だが十分ではない。部分準同型には共通success supportが先に必要であり、既存program間の比較だけでは未知surfaceへのtransport写像を生成できない。**

## 他系列へ返す新知見

- A: testで候補を分割する前に、新surfaceへ候補programを運ぶ写像が必要。
- C: success/wrong/nullの分離後、既存ruleをgroupingするだけではtransport mapは生まれない。
- D: endpoint候補間の共通read/write supportが0ならslow relation比較は空になる。
- E: unknown basinを除外してもfactor birth方向は得られない。

## 次の仮説

**Correspondence Programs from Minimal Edit-Graph Anti-Unification**  
（最小edit graph反単一化からの対応program創発）

次は既存program同士のbehavior比較をやめ、raw導出からtransport program自体を生成する。

1. `command before after`を局所edit graphへ変換
2. 異なるepisodeのedit graphを反単一化
3. 共通保存edgeを定数、差分edgeを匿名変数として小さなcorrespondence programを生成
4. Source→target / target→sourceの双方で局所導出を再現
5. Noexecはunknown、wrongは反例として別保持
6. 未知語順・語彙・Rename・別状態表現で新candidateを生成できるか測定
7. 総description lengthがExecutable baselineより短い場合だけlibraryへ採用

C系列のworld-state transport mapとは異なり、Bは**導出記述の反単一化と総符号長**を中心機構・採否条件とする。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
