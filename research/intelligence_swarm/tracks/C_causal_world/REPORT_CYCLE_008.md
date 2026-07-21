# 系列C Cycle 008 研究報告

## 仮説

**Latent Effect-Factor Discovery from Multi-Operation Intervention Signatures**  
（複数操作介入signatureからの潜在効果factor発見）

同じ文脈に対して複数の異なる操作を実行し、各操作が成功したか無変化だったかの疎な効果ベクトルを得る。この効果signatureが同じ文脈群を、branch数・condition名を事前固定せず同一の潜在condition factorへまとめられる、という仮説を検証した。

## 開始時に確認した共有状態

- `STATE.md`: 高校生級、ネイティブ日本語コミュニケーション、弱いスマートフォン実機検証はいずれも未達。
- `BACKLOG.md`: 未知区間境界、予測・介入整合性による候補競合、内部整合性と意味妥当性の分離がP0。
- 系列A Cycle 007: 証拠channel校正は誤確定を棄権へ変えるが、未知表現を理解せず既知coverageも低下。
- 系列B Cycle 008: 可逆MDL候補は実行可能role/effect programを保証せず、no-op以外が全面棄権。
- 系列D Cycle 007: 仮書込み・想起監査は明示的one-shotで部分改善するが、代名詞・更新先で崩壊。
- 系列E Cycle 007: scope候補列挙は候補recallを改善せず、通常入力が全面棄権。

## 重複表

| 系列 | 現在の中心機構 | 成功 | 失敗・未解決 | C候補との重複判定 |
|---|---|---|---|---|
| A | 証拠channelの信頼度とrollback | 未知返答の誤確定を抑制 | open-set意味、coverage、drift | 観測信頼度を中心にする案は棄却 |
| B | role/effect MDL格子 | 圧縮・可逆候補監査 | 実行可能候補recallが0 | predicate/role格子を中心にする案は棄却 |
| D | memory graph仮書込みと想起 | 明示的one-shot binding | 照応・episode更新先 | 長期記憶統合案は棄却 |
| E | scope候補のenergy緩和 | 非同型候補がある場合の選択 | scope proposal、全面棄権 | attractor/energy選択を中心にする案は棄却 |
| C | 複数operationへの効果signature | 潜在condition数をデータから形成 | surface aliasを超えたzero-shot意味 | 採用 |

## 実装

学習器へ与えるものは、生の日本語による以下の観測だけである。

- context文
- 操作前状態
- 日本語命令
- 操作後状態

学習器へ与えていないもの:

- context名やcondition名
- condition node数
- action/no-opラベル名
- entity/value一覧
- 形態素解析
- 固定ontology
- RAG・外部LLM
- 問題別分岐

各contextについて3種類の操作を実行し、before/after文字列が変化したかから効果signatureを作る。同じsignatureを共有する観測を1つの潜在factor nodeへまとめる。新しいsurface contextは、効果付き一回観測で暫定bridgeへ追加し、矛盾signatureが後続した場合はbridgeを撤回する。

## 反証条件

1. 未学習contextを効果観測なしで既知factorへzero-shot転移できない。
2. 誤った効果へbridgeした場合も高確信のまま誤動作する。
3. 主語省略・複数段落・計画変更の高得点がcontextだけを読む設計で説明できる。
4. 潜在factorは操作signatureのクラスタであり、自由日本語から因果状態変数を発見した証拠にならない。
5. 複数relation、反実仮想、計画変更の意味理解へ接続しない。

## 実験条件

- 学習bundle: 40 / 120 / 360
- seed: 1 / 7 / 19
- operation数: 3
- generator側context群: 5
- split:
  - 既知context
  - 未学習context
  - 未学習command
  - context・commandとも未学習
  - 別状態表現
  - 主語省略
  - 計画変更
  - 正しいone-shot効果bridge
  - 誤ったeffect bridge
  - 後続矛盾によるbridge撤回

## 360 bundle・3 seed平均

| 指標 | 結果 |
|---|---:|
| 既知context | 1.0000 |
| 未学習context zero-shot | 0.4633 |
| 未学習context棄権率 | 0.2467 |
| 未学習command | 1.0000 |
| context・commandとも未学習 | 0.4411 |
| 別状態表現 | 1.0000 |
| 主語省略 | 1.0000 |
| 計画変更 | 1.0000 |
| 正しいone-shot bridge | 1.0000 |
| 誤effect bridge | 0.6022 |
| 潜在factor node | 5 |
| model size | 12,966 bytes |
| bridged model size | 13,492 bytes |
| 推論 | 約0.033–0.043 ms/bundle |
| Peak RSS | 391,148 KiB（Python runtime込み） |

推定計算量:

- 学習: `O(N × O × G)`
- 推論: `O(C × G + O)`
- 今回 `O=3`, `C=5`

## 支持された部分

次の下流原理は限定的に支持された。

> 複数operationに対する介入結果を疎なsignatureとして比較すると、branch種類やcondition node数を事前固定せず、異なる効果patternを少数の潜在factorへまとめられる。

実験器には5種類のcontext効果patternが存在し、学習器も5個のfactor nodeを形成した。episode全文のprototype保存ではなく、5 signature nodeとsurface residueへ圧縮でき、13KB未満・0.05ms未満で動作した。

正しい効果付きone-shot bridgeでは未知contextが1.0へ改善し、誤effect bridgeでは0.6022へ低下した。したがって複数操作signatureはsurface aliasの接続先を識別する情報を持つ。

## 決定的な反証

中核のopen-set因果世界モデル仮説は反証する。

### zero-shot意味転移は弱い

未学習contextは0.4633に留まり、約24.7%を棄権した。異なる表現を同じ阻害・許可条件として理解したのではなく、文字n-gram類似で既知factorを選んでいる。

### one-shot bridgeは効果教師付き別名追加

bridge時には3操作の結果signatureを直接観測している。因果条件を言語だけから発見したのではなく、既知factorへのsurface aliasを追加しただけである。

### 誤bridgeに高確信

誤ったsignatureへ接続すると0.6022まで崩れるが、marginは1.0のままである。内部factorの確信度は現実の正しさを表さない。

### 高得点の一部は統合能力ではない

主語省略・別状態表現・計画変更が1.0なのは、branch判定がcontext文字列だけを利用し、命令の照応・訂正・state relationを理解しなくても解けるためである。自由日本語統合能力として採用しない。

### 因果方向・反実仮想・計画は未成立

signatureは観測された相関patternのクラスタであり、なぜ特定operationだけが阻害されるか、未観測介入、反実仮想、目的状態、制約充足を説明できない。

## 系列C固有の進展

系列Cの因果条件学習を三段階へ分離できた。

1. **surface condition bridging**  
   効果付き観測で未知表現を既知conditionへ接続する。限定成立。
2. **multi-operation effect-factor discovery**  
   branch数を固定せず、複数operationの効果patternを潜在factorへまとめる。今回、制御条件で成立。
3. **causal mechanism induction**  
   factorが各operationへ作用する機構、因果方向、反実仮想、未観測結果を生成する。未成立。

今回の進展は第2段階であり、第3段階の証拠ではない。

## 他系列へ返す知見

- A: 証拠channel信頼度に加え、複数operationで同じ意味が再現するかを信頼性監査へ使える。ただし誤signatureは高確信になり得る。
- B: predicate primitiveとcondition factorを分離し、MDL統合前に複数operation signatureの再現性を監査する。
- D: condition aliasは一回で低速記憶へ固定せず、別identity・別operationでsignatureが再現してから統合する。
- E: condition候補はsurface scope差ではなく、複数operationに対して異なるbranch vectorを生成する非同型graphでなければならない。

## 次仮説

**Mechanism-Factored Intervention Tensor with Counterfactual Completion**  
（機構分解型介入テンソルと反実仮想補完）

次は単一のsignatureクラスタをcondition nodeとみなさない。context × operation × identity × prior-state の疎な介入テンソルを作り、観測された効果patternを少数の機構factorの合成として説明する。

候補factorは次を満たす場合だけ保持する。

1. 未観測operation結果を予測する。
2. 別identityへ転移する。
3. operation順序を変えた反実仮想を予測する。
4. 部分的な計画変更後の結果を予測する。
5. 後続反例でfactor edgeを撤回できる。
6. factor数と保存量がepisode数へ線形増加しない。

必須成功条件は、効果観測なしの未学習context 0.4633を改善し、誤bridge時の高確信を校正し、複数relationまたは計画変更の実行結果を0から改善すること。

## 再現

```bash
python research/intelligence_swarm/tracks/C_causal_world/latent_effect_factor_cycle8.py \
  --output research/intelligence_swarm/tracks/C_causal_world/results_cycle_008.json
```

## 統合評価

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
