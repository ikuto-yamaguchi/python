# 系列B Cycle 033 研究報告

## 仮説

**Scope-Compressed Symbol Productions from Repair Applicability Codes**  
（repair適用可能性codeによるscope圧縮型symbol production）

Cycle 032では独立probeのnear-miss差分から境界repairを生成するとpair recallと境界距離は改善したが、候補数が8〜10倍へ増え、実行精度は全面0へ崩壊した。

本Cycleでは各repairを全programへ展開せず、inductionから分離したprobe上のsuccess / wrong executable / noexec応答を、command長、before長、common/novel span数、command先頭・末尾shapeからなる短い観測codeへ圧縮した。`repair bits + scope bits + residual error bits`を共同記述長として評価し、入力ごとにutility上位4 repairだけを展開した。Final testのafter / futureはscope選択・rankingに使用していない。

## 他系列との重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | residual-born temporal transition kernel | 時間予測状態・再帰更新 |
| C | multi-value intervention fiber | 因果state-variable・world model |
| D | cycle-closing memory address | 長期memory・read/write閉路 |
| E | multi-value scope fiber attractor | Energy固定点・局所force |
| **B** | **repair applicabilityを符号化するsymbol productionと共同MDL** | 今回の固有対象 |

## 3 seed平均

| 条件 | Graph精度 | Global pair / 候補数 | Scoped pair / 候補数 | Scoped精度 |
|---|---:|---:|---:|---:|
| 既知 | 0.0139 | 0.0833 / 32.83 | 0.0833 / 34.17 | 0 |
| 未知語順 | 0.0139 | 0.1528 / 31.08 | 0.1528 / 32.97 | 0 |
| 未知語彙 | 0.0139 | 0.1111 / 30.51 | 0.1111 / 30.63 | 0 |
| Rename | 0 | 0.0139 / 32.42 | 0.0139 / 33.99 | 0 |
| 別状態表現 | 0 | 0 / 0 | 0 / 0 | 0 |
| 入れ子 | 0.0139 | 0.0833 / 35.82 | 0.0972 / 37.22 | 0 |
| 主語省略 | 0 | 0 / 7.85 | 0 / 8.03 | 0 |
| 複数段落 | 0.0139 | 0 / 45.58 | 0 / 44.83 | 0 |

追加診断:

- Program: 64
- Global repair: 12
- Scope rule: 19.33
- Repair training example: 120.67
- 入力あたり展開repair: 4.00
- Scoped model: 7,394 bytes
- Training: 1.240 sec
- Inference: seen 5.489 ms / paragraph 19.864 ms
- Peak RSS: 176,844 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

### Scope codeは候補爆発を抑えない

Global方式とScoped方式は、すべての入力で平均4 repairを展開した。既知条件の候補数はGraph 11.22、Global 32.83、Scoped 34.17で、Scoped方式はGlobal方式より減らず、むしろ増加した。未知語順・未知語彙・入れ子でも同様で、scope codeは入力ごとのrepair適用可能性を識別できなかった。

### Pair recall改善は維持したが実行精度0

Repair方式はGraphよりpair recallと境界距離を改善した。既知ではpair recall 0.0278→0.0833、境界距離6.99→4.24となった。しかし多数候補がtieし、Scoped execution accuracyは全条件0だった。

> Repair適用scopeを粗い入力統計で符号化しても、正しいprogramだけを選択する適用条件にはならない。

### Shuffleでrepairが消失

Probe outcomeを循環shuffleするとrepair 0、scope rule 0となりGraph相当へ戻った。Repair生成信号は独立probeの正しい観測対応に依存するが、独立観測依存性とsemantic scope形成は別である。

### Semantic scopeは未形成

長さ・span数・文字shapeだけでは同じsurface template内の入力が同一codeへ衝突した。Object identity、relation、operation、goal、scope、主語省略focusを区別できない。Rename pair recallは0.0139、別状態表現は候補0、主語省略はpair recall 0である。

### MDL

- Literal baseline: 283,507 bits
- Global repair: 14,624 bits
- Scoped production: 15,784 bits

Scoped productionはliteral保存より短いがGlobal repairより長く、実行性能も改善しない。Scope metadataの追加コストを予測性能や候補削減で回収できなかった。

## 探索爆発抑制と資源量

- Program上限64
- Probe上限16
- Repair 12
- 入力ごとtop-4 repair
- Candidate上限128
- Program induction `O(NKoKv)`
- Probe repair `O(VHL²)`
- Scope coding `O(RV log V)`
- Inference `O(TL² + kTR)`

1GB未満は達成。既知・未知語順・入れ子・長文では5ms超過があり、弱いスマートフォンCPU実機は未検証。

## 系列B固有の進展

> Repair applicabilityを圧縮codeへ変換しても、長さ・span数・shapeの粗いcodeでは全repairが同じ入力群へ適用され、候補entropyを抑えられない。Scope codeは入力表面の記述ではなく、repairを適用した際の外部結果差を予測する小さなprogramでなければならない。

## 他系列へ返す知見

- A: kernel birth後の適用scopeを長さ・shapeで決めても時間state identityにはならない。
- C: intervention familyのscopeは入力統計ではなくmulti-value non-target invarianceで定義すべき。
- D: read/write cycleの起動条件をsurface codeにするとaddress衝突が残る。
- E: repair attractorのscope gateには候補統計ではなく適用後の独立constraint consequenceが必要。

## 次の仮説

**Executable Scope Programs from Repair-Induced Probe Consequence Predictions**  
（repair誘発probe結果予測による実行可能scope program）

1. Repair適用前後のprobe consequence差を短いbinary programとして記録
2. Success / wrong / noexecを予測する最小decision DAGを誘導
3. Repair後のforward・inverse・non-target結果をscope feature化
4. Successを予測したrepairだけ展開
5. Program bits + repair bits + residual error bitsの共同MDLを最小化
6. Correct probe / shuffled consequence / static code / no-scopeを比較
7. 候補数・pair recall・execution accuracyを同時評価
8. Rename・別状態表現でscope program転移を監査
9. 主語省略では前turn scope stateを再起動

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
