# 系列B Cycle 005 — Bidirectional Executable MDL Operation Quotient

## 目的

Cycle 004では、episodeごとの表面文を保存せず匿名binding graphへ圧縮することで、保存量・読み出し量・推論時間・語順variantを改善した。一方、述語literalと完全共通substringがgraphへ残り、未学習同義動詞、open-set rename、選択的confound棄権は成立しなかった。

本サイクルは、**latent operation node** と **surface-view decoder** と **episode-local binding** を分離し、同じ状態遷移を生む複数の表面命令を一つの操作商へ圧縮できるかを検証する。

## 他系列との重複監査

| 系列 | 最新の中心機構 | 本サイクルで避けた重複 | 継承した知見 |
|---|---|---|---|
| A | 質問後の予測状態改訂 | clarificationやreply-state更新は扱わない | 一度選んだ候補を不可逆確定しない |
| C | 対照集合と実行world branch | 因果辺の認定は扱わない | 操作表現とepisode identityを分離する |
| D | 境界不確実な睡眠統合 | 長期schema固定・解除は扱わない | 単一境界へ早期確定しない |
| E | 反実仮想world-branch緩和 | energy最小化は扱わない | 別identityへ再実行できない候補は操作表現ではない |

候補仮説「予測不一致から追加質問を作る」はAと重複するため棄却した。「対照worldのenergyで選ぶ」はEと重複するため棄却した。本系列では、操作商そのものの圧縮・可逆性・再利用性だけを中心にした。

## 仮説

**Bidirectional Executable MDL Operation Quotient**

1. 介入前後から、entity/value文字列を除いた状態遷移をlatent operation nodeとして誘導する。
2. 命令固有のliteral断片はoperation nodeへ保存せず、surface decoderへ分離する。
3. 推論時は入力ごとに複数のentity/value境界候補を生成し、operation再利用度、decoder再利用度、binding符号長、未説明文字数のMDLで競合させる。
4. no-op表現は正の操作graphへ混ぜず、負のsurface viewとして学習する。

成功予測は、literalをoperationへ埋め込むablationより少ないoperation node・小さいモデルで、既知構文、未知identity/value、語順変更、同義動詞、confoundを同時改善すること。

反証条件は、(a) operation/decoder分離後も能力がliteral graphと同じ、(b) 未学習語順または同義動詞が0、(c) モデルサイズだけ減り意味的操作同値が形成されない、のいずれか。

## 実装

`bidirectional_operation_mdl_cycle5.py`

比較方式:

- `surface`: 全episodeの表面遷移を保存して最近傍検索
- `literal_graph`: operation nodeへ命令literalを含めるablation
- `bidirectional_mdl`: 状態遷移operationとsurface decoderを分離

学習器へentity/value一覧、意味slot名、形態素辞書、RAG、外部LLM、正解分類ラベルは渡していない。データ生成器は制御合成日本語であり、この点は自由日本語能力の証拠として扱わない。

## 実験条件

- 学習規模: 60 / 180 / 360 episode
- seed: 1 / 7 / 19
- 各split: 50 episode / seed
- split: 既知構文、未学習語順、完全未学習同義動詞、未知entity/value rename、rename＋同義動詞、no-opを含むconfound
- 測定: 正答率、選択的confound判定、モデルサイズ、operation/prototype数、学習・推論時間、候補読み出し量、Peak RSS

再現:

```bash
python research/intelligence_swarm/tracks/B_compression_symbols/bidirectional_operation_mdl_cycle5.py \
  > research/intelligence_swarm/tracks/B_compression_symbols/results_cycle_005.json
```

## 360 episode・3 seed平均

| 指標 | surface | literal graph | bidirectional MDL |
|---|---:|---:|---:|
| 既知構文 | 0.1600 | **1.0000** | **1.0000** |
| 未学習語順 | **0.2267** | 0.0000 | 0.0000 |
| 未学習同義動詞 | **0.1733** | 0.0000 | 0.0000 |
| 未知entity/value | 0.0000 | **1.0000** | **1.0000** |
| rename + 同義動詞 | 0.0000 | 0.0000 | 0.0000 |
| confound選択性 | 0.5000 | **1.0000** | **1.0000** |
| モデルbytes | 54,884.7 | 4,674.3 | **3,826.7** |
| 保存unit数 | 390 | 38.67 | **18.67** |
| 学習時間 | 0.000016秒 | 0.01823秒 | 0.01961秒 |
| 推論時間 | 8.5763 ms | 0.6560 ms | **0.5721 ms** |
| 読み出し | 390 | 38.67 | **38.33** |

Peak RSSは288,576 KiB。Pythonランタイム全体を含み、方式固有値でも弱いスマートフォン実測でもない。

## アブレーション結果

operation nodeからsurface literalを分離すると、360例で:

- model bytes: 4,674.3 → 3,826.7（約18.1%減）
- 保存unit: 38.67 → 18.67（約51.7%減）
- 推論: 0.6560 → 0.5721 ms（約12.8%短縮）

一方、能力指標はliteral graphと完全に同一だった。

## 判定

### 限定的支持

次の圧縮原理は支持された。

> 表面命令decoderを状態遷移operation nodeから分離すると、既知構文と未知identity/valueへの再束縛を維持したまま、重複operation unitと保存量を減らせる。

operation node数が約半分になり、モデルサイズと推論時間も減った。episode表面prototypeを全保存する方式より大幅に軽い。

### 中核仮説は反証

未学習語順、完全未学習同義動詞、rename+同義動詞はすべて0だった。operation/decoder分離は圧縮には効いたが、**異なる表面表現を同じ潜在操作へ写像する新しい認識原理**にはならなかった。

特に、literal graph ablationとbidirectional MDLの能力が完全に同一であるため、今回の正の結果は意味的操作商ではなく、保存形式の正規化で説明できる。

confound 1.0も、学習済みno-op surface viewに似る入力を状態不変として扱った結果であり、操作／無操作／逆操作worldを理解した因果判定ではない。

## 失敗原因

1. **decoder選択が表面literal一致に依存**: operation nodeを分離しても、未知命令を既知decoderへ結ぶ根拠がない。
2. **語順不変のargument-role graphがない**: entity/value境界候補は生成するが、誰が何をどこへ変えるかという役割構造を表現しない。
3. **同義動詞を結ぶ共有証拠が不足**: 完全未学習の「運ぶ」を既知の「移す」へ結ぶには、同一episodeの別view、実行結果、後続対話などが必要。
4. **no-op監査がsurface負例に依存**: 因果必要性ではなく、既知の不変命令表現への類似で棄権している。
5. **制御合成日本語**: 自由な文章、主語省略、入れ子、複数段落、会話状態を扱っていない。

## 系列B固有の進展

今回、次を分離できた。

- operation/decoder分離は圧縮問題を改善する
- operation/decoder分離だけでは意味同値問題を改善しない

したがって、双方向性は「operationから既知surface viewを復元できる」だけでは不十分である。未知surface viewをoperationへ符号化するencoder側が、表面literal以外の共有証拠から役割・操作同値を誘導しなければならない。

## 他系列へ返す知見

- A: 候補未来を生成するoperation nodeは軽量化できるが、未知reply/viewをoperationへ結ぶencoderは別途必要。
- C: identity/value再束縛は成立したが、no-op類似は因果必要性ではない。world branch監査を別評価にする。
- D: 低速記憶にはepisode文ではなくoperation nodeとdecoderを別々に統合できる。ただしdecoder同値を意味schemaと誤認しない。
- E: operation/decoder分離はcross-world identity leakageを減らす前提部品になるが、異なるworldを生成するargument-role graphは未形成。

## 次の仮説

**Role-Factored Multi-View MDL Encoder**

次は未知命令を既知operationへ結ぶencoder側を研究する。

同一episodeの複数命令表現、before/after、操作なし、逆操作、別対象操作、後続確認・訂正を共同viewとし、各文を以下へ可逆分解する複数候補を生成する。

1. episode identity binding
2. old/new value binding
3. argument-role edge
4. latent operation node
5. surface decoder residue

MDLは、surface再構成長だけでなく、別identity再実行、逆操作復元、非対象非干渉、後続予測の共同符号長を比較する。

成功条件は、既知・rename性能と小型性を維持しながら、未学習語順と同義動詞を同時に0から改善し、no-op surface類似に依存せずconfoundを選択的に拒否すること。

## 完成条件

- 高校生級知能: 未達
- 自由な日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
