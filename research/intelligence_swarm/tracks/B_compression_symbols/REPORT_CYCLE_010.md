# 系列B Cycle 010 研究報告

## 仮説

**Cross-Episode Permutation-Complete Anti-Unification**（episode横断・置換完備反統一）

Cycle 009では、単一episode内でbeforeからafterを再現できる候補だけへ絞っても、既知精度0.0278、候補読出し約150となり、表面編集候補を排除できなかった。

本Cycleでは、同じ可逆templateが複数の異なるentityとnew valueで成立した場合のみprogramへ昇格させた。MDLは候補生成・初期順位付けには使わず、置換実行probeを通過したprogramの統合と保存順位にのみ使用した。

## 先行研究整理

- nominal anti-unificationはbindingを含む一般化の一意性・計算条件を扱う。https://arxiv.org/abs/2504.21097
- LAPS/DreamCoderはprogram libraryとsearch heuristicの共同形成が探索効率と一般化に重要だと示す。https://proceedings.mlr.press/v139/wong21a.html
- minimum-complexity interpolationの一般化保証は、仮説クラスの識別可能性に依存する。https://proceedings.mlr.press/v267/chen25ar.html
- representational compositionalityでは、単純な部分記述だけでなく、部分から全体を表す関数の表現力が必要となる。https://proceedings.mlr.press/v267/elmoznino25a.html

したがって、MDLは識別可能な実行候補集合の後段でのみ使うべきだという立場を検証した。

## 他4系列との重複表

| 系列 | 最新中心 | 成功 | 失敗・未解決 | B候補との判定 |
|---|---|---|---|---|
| A | 証拠channel change-point | abrupt/speaker-local driftの誤確定低減 | 変化直後、漸進drift、未知表面 | evidence semanticsは棄却 |
| C | mechanism-factored intervention tensor | 同一contextのmissing operation補完1.0 | order counterfactual 0、surface factor | 因果condition形成は棄却 |
| D | open-set discourse event segmentation | held retrievalのみ0.2333 | event F1約0.015、長gap・干渉0 | memory boundaryは棄却 |
| E | outcome-vector factor sufficiency | 引用付きcandidate recall 1.0 | local factor差0、margin 0 | energy/credit routingは棄却 |
| B | cross-episode permutationでprogram precisionを上げる | 本Cycleで検証 | open-form proposal | 系列固有 |

継承知見:
- A: confidenceや記述長低下は現実の正しさを保証しない。
- C: 同一surface内補完と機構一般化を分離する。
- D: candidate recallだけでなく構造precisionを測る。
- E: outcome非同型でもedge帰属可能性がなければ選択できない。

## 実装

学習器への入力はrawのbefore / command / afterのみ。entity/value辞書、形態素解析、意味slot、固定ontology、RAG、外部LLMは不使用。

1. before/afterの最長共通prefix/suffixからold/new spanを得る。
2. beforeとcommandの共通部分からentity span候補を列挙する。
3. entity、old、newを匿名tokenへ置換し、可逆state/command template候補を作る。
4. 同一templateが異なるentityを2種類以上、異なるnew valueを2種類以上で再現した場合のみ採用する。
5. 採用後のみtemplate記述長とsupportで統合する。

探索爆発対策:
- maximal common substringを最大12件へ制限。
- cross-episode supportと置換多様性がない候補を保存前に削除。
- 推論では統合済みprogramだけを読む。

## 実験

- train: 60 / 180 / 360 episode
- seed: 1 / 7 / 19
- 各split: 120件
- split: 既知、未知語順、未知述語、入れ子、主語省略、別状態表現
- ablation: single-episode保存 vs cross-episode置換完備

## 360例・3 seed平均

### 候補生成

| 指標 | 結果 |
|---|---:|
| candidate recall | 0.6102 |
| candidate precision | 0.5679 |
| 平均候補数 | 1.0750 |

### 能力・資源

| 指標 | Single episode | Cross episode |
|---|---:|---:|
| 既知構文 | 1.0000 | 1.0000 |
| 未知語順 | 0.0000 | 0.0000 |
| 未知述語 | 0.0000 | 0.0000 |
| 入れ子 | 0.0000 | 0.0000 |
| 主語省略 | 0.0000 | 0.0000 |
| 別状態表現 | 0.0000 | 0.0000 |
| program数 | 27.67 | **12.67** |
| model bytes | 5,451 | **2,836** |
| program reads/query | 27.67 | **12.67** |
| 推論ms/query | 0.1592 | **0.0843** |

- raw candidate: 387
- accepted program: 12.67
- Peak RSS: 308,468 KiB（Python runtime込み）
- 計算量: train `O(NL²)`、infer `O(PL)`
- 1GB未満: 達成
- 弱いスマートフォン実機: 未検証

## 判定

**置換監査による圧縮部品は限定支持、中核の自由日本語program induction仮説は反証。**

### 支持された部分

既知性能1.0を維持したまま、program数を27.67から12.67、モデルを5,451Bから2,836B、読み出しを27.67から12.67、推論を0.1592msから0.0843msへ削減した。

よって、異なるidentity/valueへの置換で再現する候補だけをMDL統合対象にすることは、単一episodeで偶然成立する表面programを削る後段監査として有効。

### 決定的な反証

1. 未知語順・未知述語・入れ子・主語省略・別状態表現は全て0。未知表現からprimitive・role・scopeを生成していない。
2. candidate recallは0.6102。監査は誤候補を削れるが、正しい候補を提案できないepisodeを救えない。
3. candidate precisionも0.5679。部分entity spanや固定句が残り、置換多様性だけでは意味roleを完全識別できない。
4. 既知1.0は制御state形式と既知command templateに限定され、自由対話・読解・推論・計画・因果・自由記述の証拠ではない。

## 系列B固有の進展

program inductionを四段階へ分離した。

1. Proposal recall: 正しい変数・role・predicate候補を生成する。
2. Permutation execution precision: 別identity/valueへの再実行で誤候補を削る。
3. Open-form encoder: 未知語順・述語・scopeから既知/新規primitiveへ接続する。
4. MDL consolidation: 実行可能候補を再利用libraryへ圧縮する。

Cycle 010では2と4が限定成立。最大ボトルネックは1と3。

## 他系列へ返す新知見

- A: 確認対象programは複数identity/valueへの置換再実行を通過させる。
- C: effect signature候補は別identity/valueでも同じ機構edgeを維持するか監査する。
- D: memory schema統合前に別episodeへのwrite/read permutationでsurface groupingを排除する。
- E: energy適用前に置換同値programを商空間化すると候補数と平坦化を減らせる。

## 次の仮説

**Counterexample-Guided Role Boundary Refinement with Cross-Form Execution**（反例誘導role境界精密化と表現横断実行）

候補entity境界を部分span・助詞込み・全spanで同時保持し、別episodeへの置換で非対象部分を壊す、new位置が不整合、inverse復元不能、alternate state表現で同じeffectを生成しない候補を反例として境界を拡張・縮小する。

必須条件:
- candidate recall 0.6102とprecision 0.5679を同時改善
- 未知語順または未知述語を0から改善
- 既知1.0維持
- program 16以下、32KB以下、5ms/query以下
- 複数seed、正解漏洩なし

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
