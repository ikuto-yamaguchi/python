# 系列B Cycle 008 — Joint Role–Effect MDL Lattice

## 結論

**中核仮説は強く反証された。** 役割境界・述語残差・効果signatureを少数の可逆候補格子として同時保持しても、候補間のMDL差と表面類似度だけでは正しい実行programを選べず、no-op以外の全splitで全面棄権した。

MDLは正しい実行候補が既に存在する場合の統合・保存原理にはなり得るが、生の日本語から実行可能な候補を生成する原理を代替しない。

## 開始時に確認した状態

- 共通branch `research/intelligence-swarm-coordination-001` の `STATE.md`、`EVIDENCE.jsonl`、`BACKLOG.md`を確認。
- 高校生級、ネイティブ日本語、弱いスマートフォン実機、完成はいずれも未達。
- 最新ログとしてA PR #170、B PR #171、C PR #172、D PR #173、E PR #174を確認。

## 他系列との重複表

| 系列 | 最新中心機構 | 成功 | 失敗・未解決 | B候補との判断 |
|---|---|---|---|---|
| A | 多ターン情報利得確認 | 既知返答なら約log2(K)回で候補分離 | 未知返答で誤確信、候補生成は外部前提 | 質問policyは重複のため棄却 |
| C | 効果同値condition quotient | 一回effect観測後の軽量bridge | branch種類固定、zero-shot意味転移が弱い | condition形成は重複のため棄却 |
| D | memory graph仮書込みと想起監査 | 明示的one-shot identityで改善 | 代名詞・更新先・長文でcandidate recall崩壊 | 記憶統合は重複のため棄却 |
| E | scope候補graphのattractor選択 | 非同型branchがある場合の短反復選択 | scope proposalの正答候補recall不足 | energy緩和は重複のため棄却 |
| B | role/effect/scope/decoderの可逆MDL格子 | 今回検証 | proposalとexecutionの同時成立が必要 | 採用 |

## 継承した知見

- A: 内部entropy低下は正しさを保証しない。
- C: 一回effect bridgeは潜在因果条件発見ではなく表面別名追加に留まり得る。
- D: 仮書込み・想起監査は正しい候補が含まれる場合のみ有効。
- E: 文区間候補数を増やしても、異なる実行結果がなければ意味的多様性にならない。
- B Cycle 007: 効果は未知述語primitive割当ての信号になるが、role・scope・state relationの共同発見にはならない。

## 新仮説

**Joint Role–Effect MDL Lattice with Reversible Primitive Bridging**

入力ごとに以下が異なる候補を最大24件生成し、元文再構成長、binding長、effect signature長、再利用支持度で競合させる。

1. entity境界
2. value境界
3. entity/value role方向
4. predicate residue
5. before/after effect signature
6. surface decoder residue

未知predicateの一回観測は暫定edgeとして保持し、別episodeで同effectが再現した場合のみ統合する。異なるeffectが観測された場合は撤回する。

### Cycle 007との差

Cycle 007は一つのentity/value境界と一つのeffect primitiveへ早期確定した。今回は境界・role方向・effectを候補格子として保持し、bridgeも可逆にした。

### 反証条件

- 既知構文を維持できない。
- Cycle 007の未知述語0.4917とCycle 006の語順0.4778を同時に超えない。
- 入れ子、主語省略、別状態表現が改善しない。
- 暫定bridge、統合bridge、矛盾撤回の能力差がない。
- 候補増加で全面棄権または計算爆発する。

### 探索爆発抑制

- 共通substring上位4×4とrole swapのみ。
- MDL上位24候補。
- 学習後は支持度上位48 residueのみ保持。
- primitiveはeffect signatureで商空間化。

## 実装と禁止事項

`joint_role_effect_mdl_cycle8.py`

学習器入力はbefore / command / afterの生文字列のみ。形態素解析、固定ontology、意味slot、正解クラス、RAG、外部LLM、問題別分岐は使用していない。実験器の世界生成用kind/entity/valueは学習器へ渡していない。

比較方式:

- `base`: 学習済み格子
- `tentative_one_shot`: 未知述語を一回観測し暫定edgeへ追加
- `consolidated_two_shot`: 別episodeで同effectが再現した場合のみ統合
- `contradiction_retracted`: 矛盾effectで暫定edgeを撤回

## 実験条件

- 学習規模: 30 / 90 / 180通常episode + no-op
- seed: 1 / 7 / 19
- 各split 12件 / seedの最小反証probe
- 評価: 既知、語順変更、未知述語、rename+未知述語、入れ子、主語省略、別状態表現、no-op

## 最大規模・3 seed平均

| 指標 | base | 一回暫定 | 二回統合 | 矛盾撤回 |
|---|---:|---:|---:|---:|
| 既知構文 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 未学習語順 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 未知述語 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| rename+未知述語 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no-op | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### 資源

- モデル: 49,930 bytes
- bridge後: 50,475 bytes
- effect primitive: 17
- 保存residue: 48
- 平均候補数: 3.61、最大平均7.33
- 学習時間: 0.0532秒
- 推論: 約1.59–8.82 ms/query
- Peak RSS: 309,168 KiB（Python runtime込み）
- 計算量: proposal `O(H*L^2)`、scoring `O(H*R*G)`、`H<=24`, `R<=48`

## 反証分析

### 正しい実行候補が安定して生成されない

共通substring候補は助詞・述語・entity/value断片を混在させる。可逆再構成できても、状態relationへ再束縛可能なrole構造にならない。

### MDLは誤候補も短くする

短いresidue、短いbinding、再利用回数の多いsurface skeletonは、意味的に誤っていても短い。記述長最小化だけでは実行可能性・因果妥当性・日本語意味を選別できない。

### 可逆bridgeは上流proposalを救わない

一回暫定、二回統合、矛盾撤回の能力が全て同じだった。撤回機構以前に、surface residueから正しいrole/effect edgeを生成できていない。

### 計算効率も不採用

約50KBで1GB未満だが、能力0に対して最大8ms超は弱いスマートフォン向け原理として無効。広い初回評価は時間上限に達し、residue上位48・小規模probeへ削減して計測した。

## 系列B固有の進展

問題を三層に分離できた。

1. **Reversible proposal**: 表面文を再構成可能な候補を生成する。
2. **Executable grounding**: 候補が別identity・別語順へ再束縛され、異なる実行結果を生む。
3. **MDL quotient selection**: 実行可能候補を再利用性と記述長で統合する。

MDLは第3層に適するが、第1層の可逆性だけから第2層は創発しない。今回1と3を同時実装したが、2が欠落して全面崩壊した。

## 他系列へ返す新知見

- A: 候補entropyを減らす前に、候補が実行可能で意味的に異なることを監査する。
- C: effect signatureだけでcondition/relationを固定すると表面差分を因果変数と誤認する。
- D: 可逆parseを記憶へ統合する前にbefore/after再実行probeを必須にする。
- E: energy選択前に候補ごとの実行成功率をproposal recallとして独立測定する。

## 次の仮説

**Execution-First Anti-Unification with MDL-Only Consolidation**

次はMDLを候補生成・初期順位付けから外す。複数episodeのbefore/command/afterを反統一し、候補が別identity・別語順・逆binding上で同じ状態変化を実行できる場合だけprogram候補として生成する。MDLは実行probe通過候補の統合・保存判断にのみ使う。

必須条件:

- 既知構文を0から回復
- 未知述語0.4917と語順0.4778を同時に上回る
- candidate recallを直接測定
- 入れ子または別状態表現を0から改善
- 32候補以下、32KB以下、5ms/query以下
- 誤effect bridgeを後続反例で撤回

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
