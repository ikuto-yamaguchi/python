# 系列D Cycle 031 研究報告

## 仮説

**Probe-Grounded Read–Write Operator Birth from Variable Boundary Families**  
（可変境界familyへの独立probe groundingによるread–write operator創発）

Cycle 030では局所write operatorを形成できたが、独立probeへ転送できる引数境界・適用位置が0件で、fast/slow memory endpointは全面棄権した。

今回は具体的な左右contextを固定せず、state内の相対境界位置とold/new文字shapeから可変境界operator familyを広く生成した。その後、inductionと分離したprobe session上でwrite結果が正しいfamilyだけへ正の局所creditを与え、複数sessionで再現するfamilyだけをslow化した。

## 重複表

| 系列 | 最新中心 | Dで棄却・分離した領域 |
|---|---|---|
| A | Probe駆動transition-kernel可塑性 | 時間予測状態・carry |
| B | Probe応答同値類からのsymbol refinement | MDL・program grammar |
| C | Intervention-equivalence mechanism family | 因果world transition |
| E | Counterexample-driven boundary expansion | Energy・attractor |
| **D** | **Queryから逆起動できるread/write operatorをfast/slow memoryへ統合** | 今回の固有対象 |

A・C・Eも可変境界とprobeを使うため、Dでは候補生成そのものを新規性としない。write後の状態結果をqueryからreadできること、one-shot fast利用、複数session slow化、干渉後保持を中心機構とした。

## 先行研究整理

2025年のSparse Memory Finetuningは、高活性memory slotだけを更新することで、同程度の新知識獲得時に通常fine-tuningやLoRAより既存能力の忘却を大幅に抑えた。これは疎更新の有効性を示すが、memory slotとaddress表現は既に存在する。

Semi-parametric memory consolidationやhippocampal-inspired dual-memory研究も、episodic/semantic分離、wake–sleep統合、疎pattern separationを扱う。しかし、生の自由日本語からread/write endpoint自体を生成する今回の課題より下流である。

## 実装

- 固定ontology、手書きslot、辞書検索、RAG、外部LLMなし
- Induction:
  - `before→after`差分から相対境界familyを生成
  - 境界を±1 bucket摂動
  - old/new文字shapeとquery応答signatureを保持
- Independent probe:
  - family形成後に別sessionへ転送
  - 正しいwrite結果のみpositive credit
  - 誤結果をnegative credit
- Read:
  - query signatureからoperatorを逆起動
  - command内のcandidate valueを内部推論状態へ注入
- Slow:
  - positive≥2、3 session以上、negative≤positive
- Ablation:
  - Surface
  - Operator
  - Slow
  - Shuffled probe outcome

## 3 seed平均

| 条件 | Surface read/wrong | Operator read/wrong | Slow read/wrong | Shuffle read/wrong |
|---|---:|---:|---:|---:|
| 既知 | 0.0417 / 0.0000 | 0.0417 / 0.0000 | 0.0417 / 0.0000 | 0.0000 / 0.0000 |
| 未学習言い換え | 0.0000 / 0.0972 | 0.0000 / 0.0972 | 0.0000 / 0.0972 | 0.0000 / 0.0000 |
| Rename | 0.1250 / 0.0000 | 0.1250 / 0.0000 | 0.1250 / 0.0000 | 0.0000 / 0.0000 |
| 別状態表現 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 主語省略 | 0.0000 / 0.1389 | 0.0000 / 0.1389 | 0.0000 / 0.1389 | 0.0000 / 0.0000 |
| 複数段落 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| 自由日本語 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

追加診断：

- Operator family: 96.00
- Slow family: 6.00
- Probe audit update: 504.00
- Positive / negative credit: 16.00 / 4.00
- One-shot: 0.0000
- 干渉前 / 干渉後 recall: 0.0000 / 0.0000
- Latest recall: 0.0000
- モデルサイズ: 9249 bytes
- 学習時間: 0.118684 sec
- 既知推論: 2.972 ms/query
- 複数段落推論: 7.013 ms/query
- Peak RSS: 160032 KiB（Python runtime込み）

## 判定

**一般的memory endpoint仮説としては強く反証。独立probe groundingに限定的な信号はあるが、semantic associative memory・継続学習は未成立。**

### Probe groundingでfamily creditは形成

Cycle 030ではindependent probe updateが0だった。今回は平均504回のprobe auditからpositive 16、negative 4が形成され、slow familyも6件形成された。

Shuffled probeではpositive/negativeが0となり、全条件で全面棄権へ戻った。したがって、今回の極小read信号は独立probe outcomeに依存している。

### Readに極小信号、writeは全面0

既知read 0.0417、Rename 0.1250が得られた一方、write accuracyは全条件0だった。

これはqueryから一部value候補を選べた例があるだけで、同じoperatorが状態を書き換え、その結果を再びreadできる双方向endpointにはなっていない。

### Operator方式はSurfaceを上回らない

Surface、Operator、Slowのread値はほぼ同一だった。Probe creditをscoreへ加えても、正しいoperator/value選択を改善していない。

Slow化も同じ候補を絞っただけで、意味memoryへの統合ではない。

### Rename信号はsemantic transferではない

Rename read 0.125はobject identityの獲得ではない。相対位置・文字shape・query形式が同じstate template内で再現したため、一部valueだけを返せた。

別状態表現、自由日本語、複数段落は0であり、表現非依存endpointではない。

### One-shot・干渉・最新値保持は全0

一回提示、干渉前後、latest recallがすべて0だった。

したがって支配的失敗は破滅的忘却ではなく、write/readを同一addressへ束縛するoperator identityの初期形成失敗である。

> **独立probeは可変境界familyに外部creditを与えられるが、相対位置と文字shapeで定義されたfamilyはsemantic addressにならず、read/write双方向性を形成しない。**

## RAG・検索との差

文書や近傍vectorを返す方式ではない。

1. Raw日本語から可変境界write familyを生成
2. Independent probeでfamily consequenceを監査
3. Queryからfamilyを逆起動
4. Valueを内部推論状態へ注入
5. 複数session支持後のみslow化

ただしwrite結果とread結果が同じoperator addressへ統合されていないため、一般的memory機構には未到達。

## 破滅的忘却と表面暗記の反証条件

仮説支持には次が必要だった。

1. One-shotの独立表現readが正
2. Write accuracyとread accuracyが同時に改善
3. Correct probeがSurface/Shuffleを上回る
4. Rename・別状態表現・自由日本語へ転移
5. 干渉後に旧記憶を保持
6. Latest valueだけを選択
7. Slow化でwrong readを減らしaccuracyを維持

今回は3の「probe outcome依存性」だけ部分的に成立し、能力条件は未達。

## 資源量・計算量

- Family上限: 96
- Slow family: 6
- Family birth: `O(NL)`
- Probe grounding: `O(QFBV)`
- Read/write: `O(FBL)`
- モデル: 約9.25KB
- Peak RSS: 約156.3MiB
- Operator推論: 短文2.5〜3.3ms、複数段落7.0ms
- Slow推論: 0.17〜0.50ms

1GB未満は達成。Slow方式は5ms未満だが、Operator方式の複数段落は未達。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

> **Cycle 030のprobe update 0から、可変境界familyにより外部creditとslow候補を形成できる段階へ進んだ。しかしfamily topologyは相対位置・shape同値類に留まり、read/writeの同一address束縛、one-shot、干渉耐性、latest-value選択は成立しない。**

## 他系列へ返す知見

- A: Probe creditが存在してもfamily topologyを変えなければ予測state選択は改善しない。
- B: Probe応答同値類は局所tieを解けるが、boundary/value候補birthと共同で改善しなければsemantic symbolではない。
- C: Relative-boundary familyも別状態表現へ移らず、因果mechanism identityには不足。
- E: Probe nudgeをscoreだけでなくboundary生成・消滅へ作用させる必要がある。

## 次の仮説

**Probe-Plastic Read–Write Address Topology from Consequence-Preserving Boundary Rewiring**  
（結果保存型boundary rewiringによるprobe可塑的read–write address topology）

次はprobe creditをfamily scoreへ加えるだけにしない。

1. Probe正例で境界nodeをmerge・split・shift
2. Write成功とquery read成功が同時に増えるrewiringだけ保持
3. Probe負例で誤address edgeを削除
4. Correct probeとshuffleで異なるaddress topologyが形成されることを必須化
5. Value文字列ではなくwrite→read consequence signatureをaddress key化
6. One-shot fast topologyを即時利用
7. 複数sessionで再現するsubgraphだけslow統合
8. Old/new edgeを同一address内で競合させ、latestだけを選択
9. Sparse top-k indexで長文5ms未満を維持

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
