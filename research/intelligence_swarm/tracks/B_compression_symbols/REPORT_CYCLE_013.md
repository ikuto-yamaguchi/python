# 系列B Cycle 013 研究報告

## 仮説

**Adversarial Misapplication Programs with Relation-Contrastive MDL**  
（relation対照MDLを持つ敵対的誤適用program）

Cycle 012では、観測されたafterで非対象fieldが保存されることを確認しても、single-episode exact reconstructionへ包含され、追加情報が0だった。今回は候補programを別field・別objectへ誤適用した際に破壊を起こしやすい表面aliasを排除し、複数episodeで異なるold/new値へ再束縛できる候補だけをMDL統合対象へ残せるかを検証した。

## 先行研究整理

- Relational Program Synthesisは、複数programが関係仕様を共同で満たす問題をCEGISとversion-space learningで扱い、単一入出力より強い仕様が探索を絞る一方、探索空間が組合せ的に増えることを示す。https://arxiv.org/abs/1809.02283
- IJCAI 2025のRelational Decomposition for Program Synthesisは、入出力をfactsへ分解し、facts間relationを学ぶことで標準表現を上回る結果を報告している。https://www.ijcai.org/proceedings/2025/504
- 2026年のNeuro-Symbolic Skill Inductionは、長期traceを動的変数束縛と条件分岐を持つprogramへ持ち上げるが、強い基盤モデルと既成logic表現を前提とする。https://arxiv.org/abs/2605.01293
- 2026年のrecursive synthesis研究は、counterexample generalizationとprophylactic pruningが列挙探索を改善することを示す。https://arxiv.org/abs/2601.04045

これらは、反例が候補classを実際に分割する仕様でなければならないことを支持するが、生の日本語からrelation・variable・operationを自律生成する原理は与えない。

## 他系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | learned probe programs + null predictive state | out-set誤確定を拒否 | knownも98.3% null、paraphrase/nested recall 0 | 外部観測policyなので棄却 |
| C | changed/preserved contrastからstate variable候補 | whole prototypeより軽量・高速 | preservation増分0、relationでなくsurface chunk | 因果world変数形成なので棄却 |
| D | signed retrieval/interference boundary credit | event F1・干渉後latest改善 | retrieval悪化、長gap過分割 | memory境界なので棄却 |
| E | null attractor + absolute residual | out-set wrong commitを約半減 | 依然50.6%誤確定、factor空間供給済み | energy校正なので棄却 |
| B | misapplicationでprogram仕様を強化し、MDLは統合だけに使用 | 本Cycleで検証 | open-form proposalとrelation identity | 系列固有 |

継承知見:
- A: 候補削減量と正しい候補生存率は別。
- C: observational preservationはexact executionへ包含される。
- D: target成功だけでなく非対象への悪影響を負creditにする。
- E: 増分情報0のfactorは取得しない。

## 実装

学習器に与えたのはrawのbefore / command / after文字列のみ。object ID、field ID、value辞書、形態素解析、意味slot、固定ontology、RAG、外部LLMは未使用。

候補生成:
1. before/afterの最大共通prefix/suffixからchanged windowを抽出。
2. commandとbeforeに共通するraw substringをanchor候補化。
3. anchor・changed window・局所前後文脈から可逆編集programを生成。
4. 複数episodeで異なるold/new値を持たないsingleton aliasを排除。
5. 短すぎるanchorをmisapplication riskとして排除。
6. 残った候補のみsupportと記述長でMDL順位付け。

比較:
- `execution_only`: cross-episode supportのみ。
- `adversarial`: 異なるold/new再束縛と短anchor misapplication riskを追加。

## 実験

- train sizes: 48 / 144 / 432
- seeds: 1 / 7 / 19
- 各split: 120例
- 3 objects × 3 fields
- seen / held word order / held lexeme / nested / subject omission / alternate state representation / combined

## 最大432例・3 seed平均

| 条件 | Execution only | Adversarial |
|---|---:|---:|
| seen | 0.0306 | 0.0306 |
| held order | 0.0167 | 0.0167 |
| held lexeme | 0.0306 | 0.0306 |
| nested | 0.0306 | 0.0306 |
| subject omission | 0.0000 | 0.0000 |
| alternate state | 0.0306 | 0.0306 |
| combined | 0.0167 | 0.0167 |

## 資源量

- raw candidates: 6,600
- rejected by execution/adversarial checks: 2,393.3 / 2,628.0
- stored programs: 64
- model: 3,344 bytes
- training: 0.0226 sec
- inference: 0.0065 ms/query
- reads: 5.41/query
- Peak RSS: 14,712 KiB（Python runtime込み）
- estimated complexity: train `O(NL² + C)`, infer `O(PL)`, `P<=64`

1GB未満と局所推論時間は満たすが、弱いスマートフォン実機では未検証。

## 判定

**中核仮説は強く反証。**

### adversarial監査の増分能力が0

adversarial方式は追加で約234.7候補を拒否したが、全splitのaccuracy、program数、model size、読み出し量はexecution-onlyと同一だった。

つまり、今回のmisapplication riskはMDL上位64件の候補classを一つも変えず、実質的な増分情報を与えなかった。

### 既知精度も0.0306

raw before/after全体の単一changed windowは、複数object・複数field状態では広すぎる。どのfieldが変化したかではなく、状態文全体の長い編集断片をprogram化している。

### open-form全滅

- held order: 0.0167
- subject omission: 0
- alternate state: 0.0306

未知語順・言い換え・照応・別状態表現へ再束縛できるrelation symbolは形成されていない。

### 候補削減が探索の本質を変えない

raw 6600候補を64 programへ切ったが、上位programは同じsurface edit familyに偏る。候補数を減らしてもrole/relationの同値類を形成しなければ意味精度は上がらない。

### 誤適用を実行していない

今回のriskはanchor長とcross-episode多様性によるproxyであり、候補programを別field・別objectへ実際に適用してworld state破壊を測ったものではない。したがって仮説名の強い意味でのadversarial surgeryは未実装であり、その前段proxyが無効と反証された。

## 系列B固有の進展

敵対的仕様を三段階へ分離した。

1. **Surface-risk proxy**: 短anchor・singleton aliasを落とす。今回、増分能力0。
2. **Executable misapplication**: 別field・別objectへ実際に適用し、破壊差を測る。未成立。
3. **Relation-level quotient**: 表現が違っても同じ変更/保存構造を持つprogramを統合。未成立。

重要な結論:

> 誤適用の危険をsurface anchor長で近似してもrelation仕様にはならない。候補を現実の複数field worldへ実行し、候補ごとに異なる破壊結果を生成する必要がある。

## 他系列へ返す新知見

- A: probe utilityはsurface候補削減ではなく、world execution後の正候補生存率で校正する。
- C: changed-window全体ではrelation surgeryにならない。field-local state variable proposalを先に作る必要がある。
- D: replay schemaの誤適用riskを文字anchorで測らず、別episode write/read破壊で測る。
- E: residual factorは上位候補classを実際に分割したかを必ずablationする。

## 次の仮説

**Clause-Lattice Misapplication Execution with Relation Quotient Induction**  
（clause格子上の実行的誤適用とrelation商誘導）

次は状態全文の単一diffを廃止し、句読点・反復境界から複数clause分解候補を作る。各候補programを、同一objectの別clause、別objectの対応clause、clause順序変更、別状態表現、主語省略後の直前focusへ実際に再適用する。

正しい候補だけがtarget clauseを変更し、非対象clauseを保存する有限差分signatureを持つ場合にrelation quotientへ昇格する。

最低成功条件:
- seen 0.0306を改善
- held order 0.0167を改善
- subject omission 0を改善
- adversarial ablationでcandidate precisionまたはaccuracyに明確な差
- program 32以下 / 32KB以下 / 5ms/query以下

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
