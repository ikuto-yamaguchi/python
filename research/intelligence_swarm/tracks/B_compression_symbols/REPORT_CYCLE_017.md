# 系列B Cycle 017 研究報告

## 仮説

**Reversible Multi-View Factor Codes by Held-Out Reconstruction**  
（held-out復号による可逆multi-view因子コード）

Cycle 016では、候補×介入outcome行列の数値rankを増やすbasisを選択したが、seen精度を0.7000から0.2222へ破壊した。rank増加はobject・relation・value roleを識別せず、安定したsurface behaviorを圧縮しただけだった。

本Cycleでは単一rankを中心機構から外し、raw program候補を4つの匿名viewへ分解した。

1. command gapの左右context shape
2. state gapの左右context shape
3. 非対象保存・実行一意性の集約
4. cross-episode transport outcome

あるviewを隠しても、残り3 viewから一意に復号できる候補だけを可逆factor codeとみなし、同じfactor codeを持つprogramをMDL代表へ統合する。

## 先行研究整理

- MDLの一般化理論は、単なる表現サイズではなく、train/test間で再利用可能な圧縮構造が重要であることを示す。
- 2025年のprogram synthesis研究では、明示的分解そのものより、反復的な実行駆動合成が性能を支える場合がある。
- per-instance program synthesisは構造feedbackを使うが、候補生成にLLMを利用しており、本研究のraw日本語からの候補創発とは異なる。
- interventionによるdisentanglementは、複数contextで選択的な変化を与えることで因子分離を狙うが、通常はencoder/decoder表現を前提とする。
- role separation研究では、見かけの役割分離がtask typeや位置shortcutへ退化することが示されている。

したがって、系列Bでは「圧縮されたか」ではなく、**別viewを隠しても復号でき、cross-context executionを保持するか**を反証条件にした。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との区別 |
|---|---|---|---|---|
| A | 遅延予測誤差再発状態 | 時間的supportの順序条件を明確化 | candidate recall 0、主語省略誤確定 | 予測状態形成は棄却 |
| C | executable operation fiber | 実行不能をnull transportへ分離する必要性 | cross-context commutator増分0 | world operation algebraは棄却 |
| D | provenance-gated alias memory | object/relation分離に限定read信号 | write崩壊、rename過分裂 | 長期memory再固定化は棄却 |
| E | span–residual共同創発 | candidate/cause共同生成を次課題化 | unmarked recall 0、junk収束 | energy最小化は棄却 |
| **B** | **multi-view相互復号可能性による匿名program role圧縮** | 今回検証 | role創発・open-form transfer | 系列固有 |

## 実験条件

- 学習量: 48 / 144 / 432 episode
- seed: 1 / 7 / 19
- test: 120例 / split / seed
- raw candidate: 最大96 / episode
- 保存program: 最大32
- 比較:
  1. executable個別保持
  2. surface-view MDL商
  3. held-out可逆multi-view factor商
- split:
  - seen
  - 未知語順
  - 未知語彙表現
  - 入れ子
  - 主語省略
  - 別状態表現
  - 複数文自由形式

学習器はraw before / command / afterのみを使用し、hidden object / field / valueは評価器専用。

## 最大432 episode・3 seed平均

| 条件 | Executable | Surface MDL | Multi-view factor |
|---|---:|---:|---:|
| seen | 0.6889 | 0.1750 | **0.6944** |
| 未知語順 | 0.0000 | 0.0000 | 0.0000 |
| 未知語彙表現 | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.6889 | 0.1750 | **0.6944** |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 |
| 複数文 | 0.6889 | 0.1750 | **0.6944** |

## 判定

**中核仮説は反証。ごく小さいseen内信号のみ。**

### 1. seen改善は0.0056だけ

Executable 0.6889に対しMulti-view factorは0.6944で、改善は0.0056に留まる。3 seed平均で一貫した大幅改善ではなく、program代表の並び替えによる微差の可能性が高い。

### 2. 未知語順・語彙・主語省略・別状態表現は全て0

可逆view codeは学習済みsurface program間の誤統合を抑えたが、新しいcommand gapやstate gapを生成できない。正しいprogramが候補集合へ存在しない場合、相互復号は能力を増やさない。

### 3. 圧縮がほぼ起きない

- Executable programs: 32.00
- Multi-view programs: 32.00
- Multi-view merge: 1.33
- Factor groups: 46.67

64候補中、平均1.33件しか統合できず、held-out復号条件が厳しすぎてほぼ個別保持へ戻った。

### 4. モデルがExecutableより大きい

Multi-view metadataのため、モデルは7,343 bytesから9,579 bytesへ増えた。説明長を下げるはずの因子化が、現在の小規模条件では説明長を悪化させている。

### 5. 入れ子・複数文の高得点は自由日本語理解ではない

入れ子と複数文には学習済みcommand断片がそのまま含まれるため、0.6944は既知substringの局所実行である。構成的一般化、談話理解、目的・制約形成の証拠ではない。

### 6. viewは匿名でも意味roleではない

4 viewはraw context shapeとexecution集約であり、object・relation・value・scopeを表現していない。相互復号可能でも、同じsurface execution familyを再記述しただけである。

## 系列B固有の進展

program role形成を次の9段階へ更新する。

1. clause-lattice proposal
2. local executable reconstruction
3. misapplication precision
4. intervention outcome
5. numerical rank basis
6. multi-view separation
7. **held-out reversible view reconstruction**
8. open-form boundary / binding generation
9. hierarchical MDL library consolidation

今回、第7段階の制御版を実装した。重要な否定結果は次である。

> **view間相互復号は誤統合を抑えるが、候補外のprogramを生成せず、圧縮利得も保証しない。可逆性はrole創発の十分条件ではない。**

## 他系列へ返す知見

- A: 予測誤差stateを複数view化しても、held-out復号だけではfailure bucketを意味状態へ変換しない。
- C: operation fiberはcross-form実行可能性に加え、state / command / preservation viewの相互復号を監査すべき。
- D: alias linkはread/write双方のviewから復号できても、モデルサイズを減らさないならsemantic consolidationではない。
- E: span–residual共同生成は相互復号可能性に加え、候補recallと絶対description lengthを独立gateにする必要がある。

## 資源量

- Executable model: 7343 bytes
- Surface MDL model: 2504 bytes
- Multi-view model: 9579 bytes
- training: 0.0384 sec
- inference: 0.0197 ms/example
- raw candidates: 432
- programs: 32
- Peak RSS: 111564 KiB（Python runtime込み）
- 推定計算量:
  - proposal `O(NC²)`
  - view coding `O(PW)`
  - held-out reconstruction `O(PV)`
  - inference `O(PL)`

1GB未満・5ms未満は制御条件で達成。弱いスマートフォン実機では未検証。

## 次の仮説

**Reversible Boundary–Program Co-Induction with Absolute MDL Gain**  
（絶対MDL利得を持つ可逆境界・program共同帰納）

次は既存program候補を因子化するだけでなく、文字境界split/mergeとprogram実行を共同探索する。

- command / stateの境界を局所split・mergeで可逆更新
- 各境界案からprogramを生成し、before→afterを再構成
- 別episodeのcommand/state/preservation viewをheld-out復号
- executable baselineより総description lengthが実際に短くなる場合だけlibraryへ統合
- 未知語順・未知語彙・主語省略でcandidate recallを独立測定
- 圧縮できない候補はunknown programとして保持し、誤統合しない

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
