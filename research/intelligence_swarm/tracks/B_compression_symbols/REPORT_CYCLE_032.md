# 系列B Cycle 032 研究報告

## 仮説

**Probe-Driven Symbol Refinement by Counterexample Boundary Repair**  
（反例境界修復によるprobe駆動記号精錬）

Cycle 031では独立probe応答同値類を匿名symbolへまとめることで、surface-localなprogram選択を限定改善した。しかしexact object-value pair recallは改善せず、symbol metadataの記述長もprobe-only方式より増えた。

今回はsymbol class内のnear-miss programを、inductionから分離したprobe outcomeとの最小差分に沿って修復した。

- target境界のexpand / contract / shift
- value境界のexpand / contract / shift
- 複数probeで2回以上再現するrepairのみ保持
- final test outcomeはrepair生成・rankingに不使用
- correct probe / shuffled probe / repairなしを比較

## 最新系列との重複表

| 系列 | 最新中心 | Bで棄却・分離した領域 |
|---|---|---|
| A | probe駆動transition-kernel可塑性 | 時間予測状態・再帰更新 |
| C | minimal intervention support | 因果state-variable境界・world model |
| D | read/write address topology rewiring | 長期memory・slow統合 |
| E | scope-gated boundary repair attractor | energy固定点・局所force |
| **B** | **probe反例からsymbol production ruleを修復し共同MDLで採否** | 今回の固有対象 |

系列Eもnear-miss境界修復を扱うため、単なる境界距離改善はBの新規性としない。Bではrepairが再利用可能なprogram production ruleとなり、pair recall・execution・MDLを同時改善するかを中心反証にした。

## 先行研究との位置づけ

Counterexample-guided synthesis / repairは、反例で候補空間を狭めたり、故障箇所を局所修復したりする。ただし仕様、テスト、DSL、program sketch、外部oracleが与えられている。Test-time transductionも有限program仮説集合と外部出力oracleを前提とする。

今回の課題は、生の日本語から生成された不完全なobject/value/endpoint候補の境界そのものを、反例で修復し匿名記号productionへ昇格できるかである。

## 実装

- 固定ontology・手書きslot・辞書・RAG・外部LLMなし
- Induction 190例 / independent probe 98例 / final test別seed
- Binding program上限64
- Active probe上限16
- 匿名symbol classをprobe三値応答で形成
- Probe near-missからtarget/value境界deltaを学習
- 反復2回以上のrepairのみ保持
- Correct repair / shuffled repair / repairなしを比較

## 3 seed平均

| 条件 | Graph精度 | Repair精度 | Repair pair recall | 最小境界距離 | Shuffle精度 |
|---|---:|---:|---:|---:|---:|
| 既知 | 0.0139 | 0.0000 | 0.2500 | 9.82 | 0.0139 |
| 未知語順 | 0.0278 | 0.0000 | 0.3611 | 9.82 | 0.0139 |
| 未知語彙 | 0.0278 | 0.0000 | 0.3889 | 9.82 | 0.0139 |
| Rename | 0.0000 | 0.0000 | 0.0278 | 9.64 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.3611 | 27.71 | 0.0000 |
| 入れ子 | 0.0139 | 0.0000 | 0.2500 | 9.82 | 0.0139 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 765.11 | 0.0000 |
| 複数段落 | 0.0139 | 0.0000 | 0.0833 | 9.81 | 0.0139 |

追加診断:

- Program: 64.00
- Probe: 12.67
- Symbol class / member: 5.00 / 49.00
- Global repair: 8.67
- Symbol-specific repair rule: 0.00
- 既知候補数: 11.22 → 84.81
- 既知pair recall: 0.0417 → 0.2500
- 別状態表現pair recall: 0.0000 → 0.3611
- モデルサイズ: 6462 bytes
- 学習時間: 0.653 sec
- 既知推論: 11.45 ms/example
- 複数段落推論: 24.93 ms/example
- Peak RSS: 114304 KiB（Python runtime込み）

## 判定

**一般的な記号創発・program induction仮説としては強く反証。Candidate birthだけに限定信号が得られた。**

### Repairは候補birthを改善

既知条件のpair recallは約0.04から0.25、未知語順は約0.04から0.36、未知語彙は約0.06から0.39、別状態表現は0から約0.36へ増加した。

正しいtarget境界への平均距離も、主要surface条件で約12.4から約9.8へ低下した。Shuffled probeではこの変化がほぼ消えた。

> **独立probeのnear-miss差分は、既存programを分類するだけでなく、正しい境界近傍へcandidate集合を移動できる。**

### Execution accuracyは0へ悪化

一方、Repair方式は候補数を既知約11から約85、複数段落約12から約122へ増やした。多数候補が同点になり、全条件でcommit率・accuracyは0へ退化した。

Graph / Symbol baselineには少数の正答commitがあったため、candidate birthの改善がprogram selectionを破壊した形である。

### Symbol production ruleは形成されない

Global repairは平均約9件形成されたが、同じ匿名symbol class内で複数probeに再現するsymbol-specific repair ruleは0件だった。

つまりrepairは、再利用可能なobject/value/relation操作ではなく、probe集合全体に共通する粗い境界deltaである。

### MDL条件も未達

Repair込みdescriptionは約20.6K bitsとliteral保存より短い。しかし、repairなしの局所program libraryに対してexecutionを改善せず、候補探索・推論時間だけを増加させた。

圧縮できるrepair libraryであっても、予測性能との均衡を満たさないため採用できない。

### 主語省略・未知構造

主語省略ではpair recall 0、accuracy 0。前turn objectの再利用やvariable bindingは形成されていない。

別状態表現ではpair recallだけ0.36へ上がったが、execution 0であり、状態変数・relation・operationの抽象化ではない。

## 反証条件

仮説支持には最低限、以下が必要だった。

1. Correct probeでrepair ruleが形成され、shuffleで消える: **部分達成**
2. Pair recall増加: **達成**
3. Execution accuracyも同時増加: **未達**
4. Symbol-specific repairが複数probeで再利用: **未達（0件）**
5. Rename・別状態表現・主語省略でsemantic bindingへ転移: **未達**
6. Repair込み共同MDLが能力維持/改善と両立: **未達**

## 探索爆発抑制と計算量

- Program induction: `O(N K_o K_v)`
- Probe response: `O(VT)`
- Near-miss edit distance: `O(V H L²)`
- Repair expansion: `O(T R)`
- Inference: `O(TL² + TR)`
- `T≤64, V≤16, R≤6, candidate≤128`

候補上限128、repair上限6で有限探索に制限したが、既知推論約11ms、長文約25msとなり、弱いスマートフォンCPUでの5ms条件は未達。

- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 系列B固有の進展

> **Probe反例による境界修復はpair recallと境界距離を改善できる。しかし粗いrepairを一斉展開すると候補entropyが増え、MDLで圧縮可能でも実行選択を破壊する。Symbol refinementには「どのrepairを生成するか」だけでなく、repair適用scopeを圧縮記号として同時創発する必要がある。**

## 他系列へ返す知見

- A: Probe可塑性でoperator topologyを増やす場合、候補entropyとtie増加を独立計測すべき。
- C: Minimal supportで境界を縮めても、family固有scopeがなければ広域候補へ誤適用される。
- D: Address rewiringはread/write候補数だけでなくlatest selection entropyを監査すべき。
- E: Near-miss repairはcandidate birthには効くが、scope gateなしではflat landscapeか誤attractorを生む。

## 次の仮説

**Scope-Compressed Symbol Productions from Repair Applicability Codes**  
（repair適用可能性codeによるscope圧縮型symbol production）

1. 各repairが成功・失敗・noexecとなるprobe応答を保持
2. Repair適用scopeを最短binary applicability codeとして符号化
3. 同じrepairでもscopeが異なるものを別productionへ分割
4. `repair bits + scope bits + residual errors`の共同MDLを最小化
5. 入力ごとに適用productionをtop-kだけ展開
6. Correct probe / shuffled probe / no-scope / no-repairを比較
7. Pair recall・execution・candidate entropyを同時評価
8. Rename・別状態表現でscope codeが維持されるか監査
9. 主語省略では前turn symbol scopeを再起動

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
