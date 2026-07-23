# 系列A Cycle 031

## 仮説

**Probe-Grounded Operator Birth from Cross-Input Recurrent Error Cancellation**  
（入力横断の反復誤差相殺によるprobe-grounded operator創発）

Cycle 030では具体的左右contextからoperatorを形成したため、実行可能operatorが平均1件に崩壊した。本Cycleでは`before + command`からold/new/value境界未確定のoperator familyを広く生成し、inductionから分離した独立probe上のforward結果を局所creditとして利用した。Final testの`after / future`は候補生成・rankingに使用していない。

## 他系列との重複回避

| 系列 | 最新中心 | Aで扱わない領域 |
|---|---|---|
| B | probe条件付きsymbol birth | MDL・program同値類 |
| C | 介入応答同値類によるmechanism family | 因果world model |
| D | 可変境界read/write operator birth | 長期memory・slow化 |
| E | probe-nudged boundary attractor | Energy固定点 |
| **A** | **独立probeで複数turnのprediction errorを相殺するoperator-state** | 今回の固有対象 |

## 設計

- 固定ontology、手書きslot、辞書、RAG、外部LLMなし
- `before`全局所境界と`command`固有spanからoperator familyを生成
- Induction outcomeはfamily生成後のsupport評価にのみ利用
- 独立probe outcomeでpositive/negative local credit
- Family / Carry / Correct probe / Shuffled probeを比較
- Active集合不変または最大6 sweepで停止

## 3 seed平均

| 条件 | Family | Carry | Correct probe | Shuffled probe | Probe null |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.9000 |
| 未知語順 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.9000 |
| 未知語彙 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.9000 |
| Rename | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.9000 |
| 入れ子 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.9000 |
| 主語省略 | 0.0667 | 0.0667 | 0.0667 | 0.0667 | 0.9333 |
| 明示切替混在 | 0.1833 | 0.1833 | 0.1833 | 0.1833 | 0.8167 |
| 複数段落 | 0.1167 | 0.1167 | 0.1167 | 0.1167 | 0.8833 |
| 計画変更 | 0.0167 | 0.0167 | 0.0167 | 0.0167 | 0.8667 |
| 反実仮想 | 0.0500 | 0.0500 | 0.0500 | 0.0500 | 0.9500 |

追加診断:

- Operator family: 3
- Correct probe positive / negative credit: 24 / 0
- Shuffled probe positive / negative credit: 0 / 24
- Pair recall: 全条件0
- Model: 426 bytes
- Training: 3.369208 sec
- Inference: 既知0.663ms、複数段落0.867ms
- Peak RSS: 175,224 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Candidate birthは前Cycleより改善

Cycle 030は全条件accuracy 0だった。本Cycleでは平均3 familyが形成され、既知・未知語順・未知語彙・Renameで0.10、複数段落で0.1167、主語省略で0.0667となった。可変境界と位置・shapeによって候補集合を非空にする効果は確認できた。

### Probe groundingの能力増分は0

Family、Carry、Correct probe、Shuffled probeは全条件でaccuracyが完全同一だった。Correct probeではpositive credit 24、Shuffleではnegative credit 24が形成されたが、最終選択は変わらなかった。

> 独立probeはoperator familyのcreditを生成したが、operator-stateの選択境界を変えなかった。観測groundingが能力へ因果的に寄与した証拠はない。

### 得られた正答はsurface-local

Family方式だけでも同じ正答が出る。主因は、state内の絶対位置とold/new文字shapeを保持した局所edit familyが同じsurface形式へ再適用できたことだった。Object、relation、goal、scopeを共有する抽象状態ではない。

### 主語省略・計画変更・反実仮想

- 主語省略: Carry増分0。前turn focus再利用ではない。
- 計画変更: accuracy 0.0167、wrong commit 0.1167。旧案と最終案を分離できない。
- 反実仮想: accuracy 0.05、probe増分0。実行世界と未実行世界を分離できない。

## 反証分類

- Probe-credit ineffectiveness: correct/shuffle/no-probe同一
- Surface operator locality: 絶対位置・shape依存
- State-binding collapse: object/relation/goal/scope未形成
- Carry collapse: 前turn状態再利用の増分0
- 局所最適: 同一surface familyの少数operatorへ固定
- 発散: active集合縮小、最大6 sweepにより未観測

## 資源量

- Family birth: `O(NL²V)`
- Probe audit: `O(QFV)`
- Inference: `O(FOV + SH)`
- `F≤64, S≤6, H≤24`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> 可変境界familyはoperator候補birthを改善できる。しかし独立probe creditがselectionへ作用しない限り、予測状態ではなくsurface edit familyに留まる。

## 他系列へ返す知見

- B: probe signalが存在してもrankingへ因果的に作用しなければsymbol birthではない。
- C: mechanism familyもcorrect-vs-shuffleでtarget executionが変わる必要がある。
- D: probe creditをslow化判定だけでなく引数境界更新へ作用させる必要がある。
- E: probe nudgeはenergy加点ではなく、境界birth/deathや遷移kernelを変形させる必要がある。

## 次の仮説

**Probe-Driven Transition-Kernel Plasticity for Operator-State Formation**  
（operator-state形成のためのprobe駆動遷移kernel可塑性）

1. Operator familyを絶対位置ではなく相対境界遷移として表現
2. Probe正例でforward/inverse kernelの局所遷移確率を更新
3. Probe負例で誤境界をbirth/death pruning
4. Correct probeとshuffleで異なるfamily topologyが形成されることを必須化
5. Final testではprobe outcome非参照
6. 主語省略では前turn kernelを再起動
7. 計画変更では旧kernelと最終kernelを競合
8. 反実仮想では実行・非実行rolloutを別固定点化

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
