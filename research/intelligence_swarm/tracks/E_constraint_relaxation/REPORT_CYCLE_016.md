# 系列E Cycle 016 研究報告

## 仮説

**Open-Basis Residual Discovery from Raw Outcome Compression**  
（raw outcome圧縮からの開放残差basis発見）

Cycle 015では、既知のresidual channelとedge種別の対応を最小edge surgeryからほぼ完全に復元できた。しかし、reconstruction / inverse / revision / recall等のresidual名と、target / value / scope / address等のedge ontology自体は実験側が供給していた。

本Cycleでは固定residual名・固定edge名を廃止し、raw `before / candidate execution / after / future observation` の文字差分から、cross-episodeで再現する局所変化patternを圧縮してcause basisを作れるか検証した。

## 重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | E候補との区別 |
|---|---|---|---|---|
| A | cross-world localityによるprobe graph | marked条件でprobe libraryを高速化 | unmarked候補生成0、破壊量偏重 | 外部観測policyは棄却 |
| B | tensor因子program role | rank basisでprogram削減 | role非識別、未知形式0 | program商・MDLは棄却 |
| C | latent-state別operation algebra | 状態更新の局所実行 | raw commutatorがevent境界を悪化 | world operation形成は棄却 |
| D | provenance-gated alias memory | object/relation分離でreadに限定信号 | write崩壊、rename過分裂 | 長期memory統合は棄却 |
| **E** | **raw outcome差分からcause basisを圧縮し、疎なアトラクタへ接続** | 今回検証 | candidate/cause open-set生成 | 系列固有 |

継承知見:
- A: partition gainだけでは破壊量の大きい操作へ偏る。
- B: 数値rank増加だけでは意味roleを識別しない。
- C: raw文字編集の交換可能性はworld operation代数ではない。
- D: 軸分離だけではcross-form equivalenceを形成できない。

## 実験

- 学習例数: 30 / 90 / 180
- seed: 1 / 7 / 19
- test: 30例 / split / seed
- candidate上限: 8
- raw cause basis上限: 8
- 最大sweep: 4
- 条件: marked / unmarked / nested / plan change / long distractor
- 比較: raw global residual / random compressed basis / recurrent raw basis / hidden-label oracle

学習器はraw文字列・raw execution outcome・future observationのみを利用し、hidden target/valueは評価器専用。

## 最大180例・3 seed平均

| 条件 | Global | Random basis | Raw basis | Oracle | Candidate recall |
|---|---:|---:|---:|---:|---:|
| marked | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 |
| unmarked | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| nested | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| plan change | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| long distractor | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 判定

**中核仮説は強く反証。**

### marked条件ではbasis不要

marked条件はGlobal・Random・Raw・Oracleがすべて1.0だった。引用区間から候補が1組だけ生成されるため、cause basisの識別能力を測っていない。

### unmarked candidate recallは0

unmarked / nested / plan / longのcandidate recallはすべて0だった。raw substring proposalは対象と値の組を候補集合へ入れられず、Oracleでさえaccuracy 0である。

したがって残差圧縮・制約緩和・アトラクタ推論は、上流のcandidate collapseを救えない。

### Raw basisは誤収束を生む

long distractorではRaw basisのwrong commitが0.3000、null率が0.7000だった。candidate recall 0にもかかわらず、raw差分patternがjunk候補間の差を増幅した。

これはCycle 012–013で観測した「候補外なのに相対energyで一意化する」問題の再発である。

### raw basisは意味causeではない

圧縮されたbasisは文字差分gramの再現頻度とpurityで選ばれる。対象・relation・scope・revision・future recallの原因概念を形成していない。

### ランダムbasisとの差が能力上ほぼない

markedは全方式1.0、unmarked系は全方式0である。Raw basisがrandom basisを意味的に上回る能力差はない。

### 平衡伝播・局所学習は未成立

疎な候補削減と反復停止は実装したが、free phase / nudged phaseの局所相関差でweightを更新していない。

## 停止条件・失敗分類

- 一意停止: active候補1
- 平坦停止: active集合が変化せず複数候補
- 発散: 4 sweep以内に安定しない
- 局所最適: 一意候補だが誤答
- 候補崩壊: 正答候補が候補集合外
- cause崩壊: raw basisが意味原因を分離しない

今回の主失敗は候補崩壊。long条件では候補崩壊に加えてjunk局所最適が発生した。

## 資源量

- Raw basis model: 5269 bytes
- basis数: 8
- training: 0.006110 sec
- inference: marked 0.1045 / unmarked 1.5773 / long 2.5503 ms/example
- 平均factor評価: marked 8.0 / unmarked 64.0
- 平均sweep: marked 1.00 / long 1.84
- Peak RSS: 167880 KiB（Python runtime込み）
- 推定計算量: proposal `O(L²)`、raw signature `O(HL)`、basis評価 `O(BH)`、relaxation `O(SH)`

1GB未満・5ms未満は制御実験で達成。弱いスマートフォン実機では未検証。

## 系列E固有の進展

必要条件を11段階へ更新する。

1. Candidate recall
2. Outcome non-isomorphism
3. Local factor separability
4. Factor minimality
5. Reality calibration / null
6. Adaptive factor中の絶対残差校正
7. Residual identifiability
8. Residual-cause-to-edge routing
9. Cause/edge basis self-generation
10. **Open-form candidate and cause co-generation**
11. Attractor relaxation・局所学習

今回、固定名なしのraw basis圧縮を実装したが、第10段階のcandidate/cause共同生成は未成立。

## 他系列へ返す新知見

- A: raw outcomeからprobeを作ってもcandidate recall 0なら意味能力は増えず、junk partitionだけが増える。
- B: raw outcome tensorを圧縮する前に、role候補が候補集合へ入っているかを独立gateにする。
- C: commutator signatureもobject/relation proposal失敗時にはsurface差分basisへ退化する。
- D: alias provenanceを圧縮する前に、同一対象候補のopen-set recallを測る必要がある。

## 次の仮説

**Joint Span–Residual Co-Creation by Reversible Predictive Compression**  
（可逆予測圧縮によるspan・残差共同創発）

次はspan proposalをraw rarityだけで固定しない。

1. raw日本語を複数の可逆分割候補へ分解
2. 各分割をcandidate executionへ束縛
3. before / after / futureを共同再構成できる分割とresidual basisを同時最適化
4. span境界を変更するとraw residual basisも変わる双方向更新
5. description length短縮だけでなく、別episode・言い換え・非対象保存で同じ局所因子を再現する場合だけ昇格
6. 説明不能な入力はunknown span / unknown causeとして保持

最低成功条件:
- unmarked candidate recallを0から改善
- random basisをaccuracyとwrong commitの双方で上回る
- basis 3～12
- candidate 16以下
- sweep 4以下
- 32KB以下
- 5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
