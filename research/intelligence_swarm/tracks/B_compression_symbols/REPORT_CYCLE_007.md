# 系列B Cycle 007 — Effect-Conditioned Primitive MDL with Held-Lexeme Bridging

## 目的

Cycle 006では、episode固有のidentity/valueを命令encoderから分離することで未学習語順が0から0.4778へ改善した一方、完全未学習同義動詞は0、モデルサイズは約144.7KBへ悪化した。

本サイクルでは文字類似をprimitive統合の主目的から外し、**同じbefore/after実行効果を生む命令残差を同一primitiveへ割り当て、新しいpredicateを実行効果付きの一回観測で既存primitiveへ橋渡しできるか**を検証した。

## 開始時に集約した最新知見

- 共通状態: 高校生級、ネイティブ日本語、弱いスマートフォン実機、完成はいずれも未達。
- A Cycle 006: 候補集合を情報理論的に分割する質問policyは既知応答で機能するが、未知応答を誤解すると誤確信へ高速収束する。
- C Cycle 006: identity分離済みeventへcontext branchを追加すると既知contextではaction/no-opを選べるが、未学習contextは0でprototype保存が約292KBへ増加する。
- D Cycle 006: 予測的想起利得は正しいepisode候補が存在した後の統合監査にしか使えず、候補proposal不足を救えない。
- E Cycle 006: 候補数ではなく、異なる実行結果を持つ非同型branch graphがenergy landscape形成に必要。
- B Cycle 006: role factoringは語順variantへ部分転移するが、未知predicate primitiveの誘導は0。

## 他4系列との重複表

| 系列 | 最新仮説・中心機構 | 成功 | 失敗・未解決 | 本系列候補との重複判定 |
|---|---|---|---|---|
| A | entropy-matched multi-turn predictive repair | 既知yes/noで2〜8候補をほぼ理論bit数で識別 | 未知feedbackで誤確信、候補自体は外部供給 | 質問・feedback policyは扱わず非重複 |
| C | context-conditioned counterfactual event algebra | 既知contextでaction/no-op、rename維持 | 未学習context 0、prototype線形化 | branch gatingは扱わず、effectをprimitive同値信号に限定 |
| D | predictive retrieval gain grouping | 少数schema読出しと容量削減 | proposal recall不足、想起能力ほぼ0 | 記憶統合ではなくprimitive encoder形成なので非重複 |
| E | role-structured conditional attractor graphs | 非同型action/no-op候補で正margin | 未知命令・入れ子・複数段落・訂正0 | energy緩和は扱わず、候補primitive生成を担当 |
| B候補1 | context effect quotient | 未知contextを効果で統合可能性 | Cの次仮説と中心機構・反証条件が重複 | **棄却** |
| B候補2 | executable branch graph relaxation | 実行差でcandidate selection | Eの中心機構と重複 | **棄却** |
| B候補3 | effect-conditioned primitive MDL | 未知predicateを一回の効果付き観測でbridge | 同義primitiveのencoder形成を直接反証可能 | **採用** |

## 先行研究整理

Grounded verb semanticsを世界状態の変化として扱う研究は、動詞句と実行・状態変化の対応が語義獲得に有効であることを示している。継続的な行動観測を発話内chunkへ整列させる方が、最終状態だけより細粒度の意味獲得に有利という報告もある。一方、program inductionでは再利用可能primitive libraryと探索戦略が重要であり、言語注釈や実行例を追加しても、primitive・role・状態表現を手書きせず同定する問題は残る。

本サイクルはニューラルモデルやLLMを使わず、その最小条件として「実行効果が未知lexemeのprimitive割当て信号になるか」を小型可逆表現で反証した。

## 仮説

同一の状態遷移効果を生む複数命令について、

1. before/command/after間で再出現するepisode-local identity/valueを匿名化する。
2. before/after差分から実行可能effect signatureを形成する。
3. 同じeffect signatureを共有するsurface predicate残差を一primitiveへMDL統合する。
4. 完全未学習predicateを、その実行効果付き一回観測後に既存primitiveへ追加する。
5. episode prototypeは保存せず、effect primitive・surface fragment・supportだけを保存する。

という構成なら、Cycle 006より小さい表現で未知lexeme bridgeが成立する。

### 反証条件

- 一回bridge後の完全未学習lexemeがzero-shotを上回らない。
- 誤ったeffectへbridgeしても同程度に動く。
- 未学習語順、rename、入れ子、主語省略へ転移しない。
- state realizationが変わると全滅する。
- primitive数・fragment数がepisode数へ線形増加する。
- 自由日本語統合ゲートが0のまま。

## 構造創発設計

学習器へentity/value辞書、意味slot名、形態素解析、固定ontology、RAG、外部LLMは与えていない。

- identity候補: command・before・afterの三viewに再出現する最長区間。
- new-value候補: commandとafterに出現し、beforeにはない区間。
- effect候補: before/afterで変化した局所節を `<E>` / `<X>` へ可逆匿名化した遷移対。
- predicate residue: commandからidentity/new-value候補を除いた残差。
- primitive: effect候補、surface residue集合、supportからなる疎な実行unit。
- one-shot bridge: 新predicateを含むbefore/command/afterを一件観測し、同じ処理経路でeffect primitiveへ追加。
- 探索抑制: effect primitive数 `P`、primitiveごとのfragment数 `F`、query n-gram数 `G` に対し概算 `O(PFG)`。episode全件探索を行わない。

## 実験条件

- train sizes: 60 / 180 / 360
- seeds: 1 / 7 / 19
- 3種類の異なる状態遷移: 場所、担当、状態
- splits: 既知構文、未学習語順、完全未学習lexeme zero-shot、一回bridge、rename、入れ子、主語省略、no-op、未学習state realization
- ablation: literal完全一致、effect primitive、正しいone-shot bridge、誤effect bridge
- 測定: accuracy / abstention / latency / model bytes / primitive数 / fragment数 / Peak RSS

## 360例・3 seed平均

| 指標 | literal | effect zero-shot | 正しいone-shot bridge | 誤effect bridge |
|---|---:|---:|---:|---:|
| 既知構文 | 0.8944 | 0.7333 | 0.7333 | 0.7333 |
| 未学習語順 | 0.0000 | 0.1889 | 0.1889 | 0.1889 |
| 未学習lexeme | 0.0000 | 0.3333 | 0.4917 | 0.1083 |
| rename + 未学習lexeme | 0.0000 | 0.3111 | 0.5000 | 0.1389 |
| 入れ子 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.2972 | 0.2972 | 0.2972 |
| no-op | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 未学習state realization | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### 資源

- effect model: 2985 bytes
- one-shot bridged model: 3271 bytes
- latent effect primitives: 8
- bridge前surface fragments: 23
- bridge後surface fragments: 26
- one-shot lexeme推論: 0.1546 ms/query
- Peak RSS: 397020 KiB（Python runtime込み）

学習episode数60→360の6倍に対し、effect modelは約2.5KB→3.0KB、primitive数は7→8であり、episode prototypeの線形保存は回避した。

## 判定

### 限定的支持

完全未学習lexemeは、effect zero-shot 0.3333、正しい一回bridge後0.4917、誤effect bridge 0.1083となった。正しい実行効果付き一回観測は約+0.178の改善を生み、誤effect bridgeでは大幅に悪化した。したがって、**実行効果は新しいsurface predicateを既存primitiveへ結び付ける監督信号として情報を持つ**という部分は支持される。

またCycle 006の約144.7KBから約3.3KBへ縮小し、episode prototype線形保存を回避した。

### 中核仮説の反証

自由日本語のprimitive創発原理としては棄却する。

1. one-shot後も完全未学習lexemeは約0.492に留まり、半数以上を解けない。
2. Cycle 006の未学習語順0.4778に対し今回は0.1889へ回帰した。
3. 入れ子は0、主語省略は0.297、未学習state realizationは0。
4. 既知構文も0.733へ低下し、binding候補抽出が助詞・短い共通substringに引きずられる。
5. zero-shotでも0.333出るため、3 primitive間の偶然選択が含まれる。
6. effect signatureは固定状態表現内の局所節に依存し、異なる言語化を同じrelation transitionへ統合できない。
7. no-op 1.0は学習済み表面命令であり、因果的confound理解ではない。
8. 自由対話、指示遂行、読解、推論、計画、因果、反実仮想、自由記述、長期対話、継続学習は未達。

## 失敗原因

- **効果同値の粒度不足**: before/after差分を局所文字節として表現しており、異なるstate realizationを同一効果へ商化できない。
- **一回観測の曖昧性**: 一つのdemonstrationでは、predicate fragmentと丁寧表現・scope・条件を識別できない。
- **roleとprimitiveの分離不足**: Cycle 006のrole factoringを縮約し過ぎ、語順不変性を失った。
- **候補生成recall不足**: 正しいentity/new-value境界が候補集合にない入力は救えない。
- **合成未成立**: 入れ子・省略・複数操作をprimitive列へ分解していない。

## 系列B固有の進展

1. effect-conditioned one-shot observationは、未知lexemeのprimitive割当てに識別情報を与える。
2. primitive/effectを重複排除すると、Cycle 006より約44分の1のモデルサイズへ縮小できる。
3. effect quotientだけではrole factoring・scope induction・state relation quotientを代替できない。
4. 次のボトルネックは、**一つの命令をpredicate primitive、argument role、scope/condition、decoder residueへ可逆分解すること**である。

## 他系列へ返す新知見

- A: 未知operation候補を表面lexemeではなくeffect primitive候補として質問対象にできるが、一回効果だけでは約0.49で追加観測が必要。
- C: context/condition quotientとoperation primitive quotientは分離すべき。固定state realizationの文字差分を因果relationとみなしてはいけない。
- D: 新lexemeを低速primitiveへ統合する前に、異なるepisode・語順・state realizationで同じ効果が再現するか確認し、誤bridgeを撤回可能にする。
- E: 非同型候補graphにはprimitive割当てだけでなく、role・scope・effect relationの違いが必要。

## 次に深掘る一点

**Joint Role–Effect MDL Lattice with Reversible Primitive Bridging**

入力ごとにentity/value境界、argument role、predicate primitive区間、condition/scope attachment、state-effect quotient、surface decoder residueが異なる少数の可逆候補を生成する。候補は再構成長、primitive再利用、実行効果、誤effect反例、語順変換、別state realizationで競合させる。one-shot bridgeを即時確定せず、複数episodeで再現するまで暫定primitive edgeとして保持する。

必須成功条件:

- 未学習lexeme one-shot > 0.4917
- 未学習語順 > Cycle 006の0.4778
- 入れ子・主語省略を同時改善
- 未学習state realizationを0から改善
- 誤effect bridgeを選択的に拒否
- model < 32KB、候補数を入力当たり32以下
- episode数に対する保存量の非線形化を維持

## 再現

```bash
python research/intelligence_swarm/tracks/B_compression_symbols/effect_primitive_mdl_cycle7.py
```

## 最終状態

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
