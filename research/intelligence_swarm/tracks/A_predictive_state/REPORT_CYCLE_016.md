# 系列A Cycle 016 研究報告

## 仮説

**Invariant Counterfactual Probe Graphs from Cross-World Locality**  
（世界横断局所性からの不変反実仮想probe graph）

Cycle 015では、候補への削除・交換・再束縛からprobeを自動生成できたが、probe libraryは`drop_target`・`drop_value`など文字破壊量の大きい操作へ退化した。marked制御条件の能力は維持したものの、引用なし日本語のcandidate recallは0だった。

本Cycleではprobe utilityを候補分割量だけで決めず、異なるobject名・値・state表現へ再適用しても、

- 同じ局所変化だけを起こす
- non-target記録を保存する
- future observationとの整合を保つ
- cross-episodeで同じoutcome partitionを再現する

probeだけをgraphへ昇格させる仮説を検証した。

## 先行研究整理

- ICLR 2025のinvariance-based causal representation learningは、多くの因果表現学習法が既知のdata symmetryへ表現を整列させていると整理し、invarianceだけでは必ずしも因果変数の識別を保証しない。
- AISTATS 2025のgeneral-environment causal representation learningは、latent変数とDAGの識別に十分なmechanism change条件が必要であることを示す。
- CLeaR 2025のcounterfactual influence研究は、反実仮想が観測されたtrajectoryの影響から外れると、単なる介入予測へ退化する問題を明示する。
- 2026年のactive-inference structure learning reviewは、hidden-state inference、parameter learning、model structure selectionを別階層として扱う必要を整理している。

これらはcross-world invarianceとstructure selectionの重要性を支持するが、候補変数・intervention family・generative modelが既に存在することが多い。生の日本語から候補とprobeの双方を創発する今回の課題はさらに上流である。

## 共通記憶・失敗系列からの制約

共通状態は、高校生級・ネイティブ日本語コミュニケーション・弱いスマートフォン実機検証がすべて未達であり、局所成功を一般知能達成とみなさない。Backlogは未知日本語区間境界の生成、将来予測・置換可能性・介入整合性の共同競合、内部整合性と意味妥当性の分離をP0としている。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | A候補との判定 |
|---|---|---|---|---|
| B | rank増加program outcome basis | program・basis数を削減 | seen 0.2222、role非識別 | program商・MDLは棄却 |
| C | intervention commutativityによるevent regime | 局所next-state再実行 | boundary F1悪化、raw edit algebra | world event形成は棄却 |
| D | object/relation address traceの因子化 | read 0→0.3472 | write 0.0633、rename過分裂 | 長期memory addressは棄却 |
| E | raw outcome圧縮によるcause basis | 固定名なしbasis圧縮 | unmarked recall 0、junk誤収束 | energy cause形成は棄却 |
| **A** | **cross-world localityで外部probeを選択し再帰状態更新** | 今回検証 | candidate proposal・probe semantics | 系列固有 |

継承知見:
- B: 数値rankやpartition増加は意味roleを保証しない。
- C: raw文字編集の交換可能性はworld operation代数ではない。
- D: object/relation軸を分けてもcross-form同値性がなければ表面分裂する。
- E: candidate recall 0の状態でraw residualを強めるとjunk誤収束する。

## 実装

学習器の入力はraw `command / before / after / future`文字列と順序のみ。hidden target/valueは評価器と環境のoutcome生成にのみ使用した。

1. commandとbeforeの最大共通substringからtarget候補を生成
2. command中でbeforeにない短いsubstringからvalue候補を生成
3. 最大16個のtarget/value候補を保持
4. `drop_target / drop_value / swap / rebind_target / rebind_value / future_check`を共有probe候補にする
5. 各probeの候補別prediction signatureを、実行可能性・局所変更・non-target保存・future整合・state内target存在・正規化diff shapeから構成
6. environmentはtrue candidateのsignatureのみを返し、候補文字列そのものは返さない
7. 比較:
   - 全probe
   - partition gain校正
   - cross-world locality校正
8. 最大6 probeで候補集合が変化しなくなった時点で停止

固定ontology、形態素解析、意味辞書、手書きslot、RAG、外部LLM、Transformer、attentionは不使用。

## 実験条件

- 学習量: 6 / 18 / 36 episode
- seed: 1 / 7 / 19
- test: 6例 / split / seed
- candidate上限: 16
- probe上限: 6
- split:
  - seen
  - paraphrase
  - rename
  - alternate state
  - nested
  - subject omission
  - multi-paragraph

初期実装は計算量が大きく120秒以内に完走しなかった。候補上限・学習量・test数を縮小して完走させたため、今回の結果は小規模反証実験である。

## 最大36 episode・3 seed平均

| 条件 | Candidate recall | 全probe精度 / wrong | Partition精度 / wrong | Locality精度 / wrong |
|---|---:|---:|---:|---:|
| seen | 0.0556 | 0.0556 / 0.1667 | 0.0556 / 0.1667 | **0.0556 / 0.1667** |
| paraphrase | 0.2222 | 0.0000 / 0.0556 | 0.0000 / 0.0556 | 0.0000 / 0.0556 |
| rename | 0.4444 | 0.0556 / 0.1111 | 0.0556 / 0.1111 | 0.0556 / 0.1111 |
| alternate | 0.1111 | 0.1111 / 0.2222 | 0.1111 / 0.2222 | 0.1111 / 0.2222 |
| nested | 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| subject omission | 0.0000 | 0.0000 / 0.2778 | 0.0000 / 0.2778 | 0.0000 / 0.2778 |
| paragraph | 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

## 判定

**中核仮説は強く反証。**

### 1. Locality校正の能力増分が0

全probe・partition・localityのaccuracy、wrong commit、null率が全splitで完全に同一だった。

cross-world locality scoreはprobe順序を変えたが、最終候補classを一件も追加分割していない。

### 2. Probe libraryが再び固定順序へ収束

3 seedすべてでlocality libraryは同一だった。

1. `future_check`
2. `drop_target`
3. `rebind_target`
4. `swap`
5. `drop_value`
6. `rebind_value`

意味的probe graphを発見したのではなく、現在のraw signature設計上、future文字列とtarget存在を直接変える操作が常に高得点になった。

### 3. Candidate proposalが支配的ボトルネック

candidate recallは:
- seen: 0.0556
- paraphrase: 0.2222
- rename: 0.4444
- alternate: 0.1111
- nested / omission / paragraph: 0

最大共通substringでtarget候補を改善しても、value境界とtarget/value組合せの上位16候補への保持に失敗している。

### 4. Candidate recallがあっても識別できない

paraphrase recall 0.2222、rename recall 0.4444でもaccuracyはそれぞれ0と0.0556だった。

正答候補が存在しても、各probeのraw signatureが多くの候補で同一になり、意味的なworld outcome partitionを形成していない。

### 5. Subject omissionで危険な誤確定

主語省略はcandidate recall 0にもかかわらずwrong commit 0.2778だった。

直前focusをraw文字列として候補へ追加しても、value・relation・scopeとの正しい束縛がなく、junk候補を一意化した。

### 6. Cross-world localityは実際の別worldを表していない

今回のlocalityは正規化文字shape、局所diff長、補助記録保存、future文字包含である。object・relation・goal・constraint・causal stateを持つ複数world modelを実行したものではない。

### 7. 探索爆発

初期設定は完走せず、最終実験ではcandidate 16、probe 6、学習36例へ切断した。計算量を原理的に抑えたのではなく、上限へ押し込んだだけである。

## 反証条件

- locality ablationがpartition/allを上回らない → cross-world localityの増分なし
- probe libraryが全seedで固定破壊順序へ収束 → probe semantics未形成
- candidate recallが低い → active inference以前のproposal failure
- recall>0でもaccuracy 0 → outcome partition非識別
- recall 0でwrong commit>0 → open-set校正失敗
- 別worldを内部状態として持たずraw文字shapeだけ → causal invarianceではない

すべて反証側となった。

## 資源量

- locality model: **389 bytes**
- candidate: 最大16、平均 16.00
- probe: 最大6
- training: 0.0824 sec
- inference:
  - seen 1.9054 ms/example
  - nested 2.3554 ms/example
  - paragraph 2.7098 ms/example
- Peak RSS: **111512 KiB**（Python runtime込み）
- 推定計算量:
  - candidate proposal `O(L²)`
  - probe training `O(NPH)`
  - inference `O(PH)`
  - `H≤16`, `P≤6`

モデルは1GB未満。seenは5ms未満だが、弱いスマートフォン実機では未検証。初期規模でtimeoutしたため計算効率の十分性も未証明。

## 系列A固有の進展

予測状態・能動推論を10段階へ更新した。

1. Raw candidate proposal
2. Candidate precision / null
3. Executable predictive outcome
4. Outcome-equivalence partition
5. Shared active probe scheduling
6. Recursive reversible update
7. Probe surgery proposal
8. Cross-world locality
9. **Probe outcome basis identifiability**
10. Open-set semantic abstraction

今回、第8段階をraw近似で導入したが、同じ候補classを分割できず、第9段階で失敗した。

> **複数入力で局所性が再現することと、そのprobe outcomeが意味変数を識別することは別である。局所性だけでprobeを昇格すると、future文字包含やtarget存在を直接変える表面操作へ退化する。**

## 他系列へ返す新知見

- **Bへ:** tensor viewがcross-episodeで不変でも、候補classを意味role別に分割しなければprogram商には使えない。
- **Cへ:** cross-context commutator familyにも、異なるlatent state候補を実際に分けるidentifiability gateが必要。
- **Dへ:** provenance付きalias linkは、write/read局所性だけでなくaddress候補を分割する増分情報を要求すべき。
- **Eへ:** span-residual共同圧縮でも、局所再現性とcause basis識別性を分離して測る必要がある。

## 次の仮説

**Probe-Outcome Basis Discovery by Cross-World Rank and Null-Space Tests**  
（世界横断rank・null空間検定によるprobe outcome basis発見）

次はlocality scoreだけでprobeを昇格しない。

1. 候補×world×probeのoutcome tensorを作る
2. object名・value・state表現を変えても同じ候補商を作るprobeを抽出
3. 既存probe集合のnull空間にない、候補識別rankを増やすprobeだけを追加
4. rankを増やしてもnon-target破壊やabsolute residualを悪化させるprobeは棄却
5. 正答候補が集合外ならrank増加で無理に一意化せずnullへ保持
6. candidate generator自体も、probe後予測誤差を最も減らすspan境界へ再帰更新

最低成功条件:
- locality ablationをaccuracyまたはwrong commitで明確に上回る
- seen candidate recall 0.0556を改善
- paraphrase/renameでrecallとaccuracyを同時改善
- omitted recall 0かつwrong 0.2778を改善
- probe basis 3～10
- candidate 16以下
- 32KB以下
- 5ms/example以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
