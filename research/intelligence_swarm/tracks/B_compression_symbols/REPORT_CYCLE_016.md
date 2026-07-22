# 系列B Cycle 016 研究報告

## 仮説

**Intervention-Basis Discovery by Rank-Increasing Program Outcomes**  
（program outcomeのrank増加による介入basis発見）

Cycle 015では固定8次元の破壊vectorでe-classを形成したが、既知精度はExecutable 0.6222から0.1778へ崩壊した。同じ破壊vectorを持つことと、同じobject・relation・value roleを持つことが一致しなかった。

本Cycleでは固定probe集合を商の意味basisとして扱わず、raw文字列programへの削除・反転・再束縛surgeryが作る候補×outcome行列から、数値rankを増やし、かつodd/even episodeで候補partitionを再現する列だけを介入basisへ採用した。

## 先行研究整理

- Active learningではversion spaceの体積やdisagreement構造を減らすquery選択が有効だが、構造仮定なしでは一般化保証が困難である。
- Program synthesisでは代表的なI/O例の選択が探索時間・安定性を改善するが、program DSLと仕様空間は既知である。
- Latent Programmerは高水準の離散codeで探索を二段階化するが、大規模学習済み表現を前提とする。
- 介入によるlatent causal variableの識別には各変数への十分なintervention coverageが必要で、観測差があるだけでは一意性は保証されない。

今回の問題は、意味変数・DSL・query空間自体を生の日本語から作るため、既存のrank・version-space削減より上流である。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | surgeryからprobe library生成 | marked精度維持、推論短縮 | unmarked候補生成0、上位probeがdrop系へ退化 | 外部観測policyは棄却 |
| C | rank増加介入によるidentity basis | 既知局所更新1.0 | 未知・省略・計画変更0、object proposal未成立 | world object形成は棄却 |
| D | object/relation traceの因子化 | 軽量address node | write 0.0201、read 0、one-shot 0 | memory addressは棄却 |
| E | raw outcome圧縮からresidual basis | 既知basis間routingを復元 | residual/edge basisは供給済み、unmarked 0 | energy cause発見は棄却 |
| **B** | **program商を識別する最小介入basis** | 今回検証 | role-identifying basis | 系列固有 |

系列A・Cもrank増加介入を次候補にしているため、Bでは外部probe選択やobject world node形成を扱わず、**program libraryのe-class quotientに必要な列選択**だけへ限定した。

## 他系列から継承した知見

- A: partition gainだけでは意味的probeにならず、cross-world localityが必要。
- C: target/non-target結果差が候補classを分割しなければidentity情報は増えない。
- D: object軸とrelation軸を一つのraw span intersectionへ潰すと過剰統合する。
- E: 既知edge間のrouting回復とedge basis自体の生成は別段階である。

## 実装

learner入力はrawの `before / command / after` 日本語文字列のみ。hidden object/field/valueは評価器専用。

1. 句読点・改行・隣接clauseから最大12区間のclause latticeを生成
2. before/after局所差分とcommand中contextから最大96 program候補を生成
3. 観測afterを一意に再現する候補だけを保持
4. programのcommand/state contextへ削除・交換・peer再束縛を最大12種類生成
5. 各surgeryを最大16 episodeへ実行し、`実行可能 / exact / 一意 / state変更` のraw outcomeを得る
6. odd/even episodeで同じ候補同値partitionを60%以上再現する列だけを残す
7. 候補×outcome行列の数値rankを増やす列を最大8本greedy選択
8. 選択basis上で同じsignatureを持つprogramだけをe-classへ統合

固定ontology、形態素解析、意味辞書、手書きslot、RAG、外部LLMは不使用。

## 反証条件

仮説は以下のいずれかで反証とした。

- rank basis quotientがExecutableの既知精度を維持できない
- 固定vector quotientを明確に上回らない
- rankを増やしても未知語順・未知言い回し・主語省略・別状態表現が0のまま
- program数削減がrole-preserving圧縮でなく能力喪失による
- basisがcross-episodeで安定してもobject/relation/valueを区別しない

## 最大432 episode・3 seed平均

| 条件 | Executable | 固定vector商 | Rank-basis商 |
|---|---:|---:|---:|
| 既知 | 0.7000 | 0.2944 | **0.2222** |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知言い回し | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.7000 | 0.2944 | 0.2222 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 |
| 複数文自由形式 | 0.6306 | 0.2806 | 0.2028 |

## 資源量

| 指標 | Executable | 固定vector商 | Rank-basis商 |
|---|---:|---:|---:|
| program数 | 32.00 | 18.33 | **13.00** |
| モデルbytes | 7228 | 7344 | **5435** |
| basis数 | 0 | 8 | **4.33** |
| 学習秒 | 0.0302 | 0.0288 | 0.0569 |
| 推論ms/query | 0.0263 | 0.0102 | **0.0094** |
| 実行候補/query | 0.867 | 0.450 | 0.361 |

- raw候補: 1274.67
- rank basis候補: 4.33
- e-class merge: 51.00
- Peak RSS: 113208 KiB（Python runtime込み）
- 推定計算量:
  - proposal `O(NC²)`
  - surgery/outcome `O(KPH)`
  - rank選択 `O(K³)`（K≤12）
  - inference `O(PL)`

モデルは1GB未満、制御推論は5ms未満。ただし弱いスマートフォン実機では未検証。

## 判定

**中核仮説は強く反証。**

### Rankを増やすbasisでもExecutableを維持できない

既知精度は:

- Executable: **0.7000**
- 固定vector商: 0.2944
- Rank-basis商: **0.2222**

rank basisは固定8列を平均4.33列へ減らし、programを32から13へ圧縮したが、既知精度を0.7000から0.2222へ破壊した。

### Rank増加はrole識別ではない

選択列はprogram候補間の数値独立性を増やすが、その軸がobject・relation・valueのどれを変えたかは表現していない。異なるroleのprogramが同じraw execution summaryを持ち、同じe-classへ統合された。

### Cross-episode再現性でも救えない

odd/even episodeで候補partitionが60%以上一致するsurgeryだけを採用したが、安定したsurface behaviorを再現しただけで、未知形式への転移は全て0だった。

### 固定vectorよりも悪い

Rank-basisは固定vectorよりbasis数・program数・モデルサイズを削減したが、既知精度は0.2944から0.2222へさらに悪化した。これは最小basisが「意味に必要な列」を残したのではなく、「行列rankに冗長な列」を捨てただけである。

### 未知構造への能力は0

未知語順、未知言い回し、主語省略、別状態表現は全方式0。自由形式0.6306は既知command断片をそのまま含むためで、自由日本語理解ではない。

### 探索爆発は上限へ移動

最大96候補/episode、64 unique program、12 surgery、16 episode windowで切断している。rank選択は商の列数を減らすが、raw候補生成の組合せ爆発は解消していない。

## 系列B固有の進展

program商形成を次の8段階へ更新した。

1. Clause-lattice proposal
2. Local executable reconstruction
3. Executable misapplication precision
4. Outcome/destruction matrix
5. Rank-increasing intervention basis
6. **Role-factorized outcome coordinates**
7. Open-form binding・談話focus
8. MDL library consolidation

今回は第5段階を実装し、basis列とprogram数の削減には成功した。しかし第6段階がないため、rankは増えてもroleを識別しなかった。

> **outcome matrixのrankは識別可能性の必要信号になり得るが、座標がobject・relation・valueのどの独立因子に対応するかを保証しない。rank最大化だけでは意味商にならない。**

## 他系列へ返す新知見

- A: probe graphのrank増加だけでなく、異なるobject・relation・valueで同じ局所因子へ再束縛できるか監査する。
- C: identity basisのrankが増えても、relation/value変更と混ざる軸ならobject identityではない。
- D: object traceとrelation traceを独立に作る方向は妥当。結合後rankだけでaddress nodeを統合してはいけない。
- E: raw outcome圧縮でcause basisを作る際、rank増加signatureが異なるrole原因を混ぜる可能性を独立反証する。

## 次の仮説

**Tensor-Factor Program Roles from Separable Intervention Subspaces**  
（分離可能な介入部分空間からのtensor因子program role）

次は候補×介入の2次元行列を一括rank最大化しない。

- raw state内の再出現span軸
- command内の可変span軸
- changed clause軸
- preserved clause軸
- cross-episode identity置換軸

を独立なviewとして保持し、介入outcomeを `candidate × episode × view` tensorにする。

ある因子が:

1. identity置換で変わりrelation置換で不変
2. relation置換で変わりidentity置換で不変
3. value置換で局所的に変わる
4. 別表現でも同じ因子分解を再現する

場合だけobject / relation / valueの匿名role候補へ昇格する。

反証条件は、factor化がExecutable 0.7000を維持できない、未知形式0のまま、または因子をpermuteしても性能が変わらないこと。

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
