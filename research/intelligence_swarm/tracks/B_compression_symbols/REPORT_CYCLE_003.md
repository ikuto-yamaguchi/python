# 系列B Cycle 003: Cross-View MDL Program Quotient

## 結論

同一episodeに含まれる複数の言い換え・介入前状態・介入後状態を共同利用し、介入差分が同じ表面フレームを同一の潜在操作候補へまとめる `Cross-View MDL Program Quotient` を検証した。

結果は **限定的支持・中核仮説は反証** である。

- 未学習の同義動詞構文では、文字列のみのMDL baselineより改善した。
- しかし語順変更では改善せず、renameも安定改善しなかった。
- episode数を増やすとモデルサイズと候補読出しが線形増加し、商空間として十分圧縮できなかった。
- 無介入confoundは通常入力とほぼ同じmargin分布を持ち、選択的には検出できなかった。
- 状態差分の抽象化は `；` と `=` で区切られた人工的record表現へ依存する。

したがって、複数viewの合意は表面同義語の弱い橋渡し信号にはなるが、自由日本語から操作・目的・因果プログラムを創発する原理には到達していない。

## 先行研究との接続

MDLはモデル記述長とデータ記述長の合計を小さくする仮説を選ぶ原理であり、圧縮と予測を結び付ける。しかし、圧縮のみで意味的同値性や因果的十分性が保証されるわけではない。

- Li & Vitányi, *Minimum Description Length Induction, Bayesianism, and Kolmogorov Complexity*: https://arxiv.org/abs/cs/9901014
- Wang et al., *On Deep Multi-View Representation Learning*: https://proceedings.mlr.press/v37/wangb15.html
- Ahuja et al., *Interventional Causal Representation Learning*: https://proceedings.mlr.press/v202/ahuja23a.html
- Li et al., *On the Identifiability of Causal Abstractions*: https://proceedings.mlr.press/v258/li25g.html

これらから、複数viewの共有情報だけでなく、介入の多様性・十分性・必要性が抽象化の識別可能性に重要だと判断した。

## 他4系列との重複表

| 系列 | 最新中心機構 | 今回採用しなかった重複案 | 今回の独自焦点 |
|---|---|---|---|
| A | 能動識別型予測状態 | 情報利得による確認発話選択 | 複数viewを同時圧縮する潜在プログラム商 |
| C | identity保存型介入商 | 因果必要性graphそのもの | 介入差分を意味ラベルなしの圧縮同値信号として使用 |
| D | 回答なしcross-view再束縛 | 高速記憶へのwrite/read rule | 記憶前の潜在操作フレーム統合 |
| E | 学習factor energy | factor graphの反復緩和 | 記述長・再利用利得による直接的な商形成 |

### 継承した知見

- A: 未来予測だけで圧縮するとidentity差を失うため、episode固有表面を可逆に残す。
- C: 抽象操作とidentity/valueを分離してから介入差分を比較する。
- D: 同じepisodeの複数表現は回答spanなしでも構造誘導信号になる。
- E: 候補の重みを変える前に、構造的に異なる候補を生成する必要がある。

## 仮説

同じepisodeの複数言語viewが同じ介入前後差分を共有する場合、それらの表面フレームを一つの潜在操作商へ統合できる。単一文で最短のframeを選ぶより、次を共同で短くする商を選ぶ方が未知表現へ転移する。

1. 複数utteranceの記述長
2. 介入差分signatureの記述長
3. episode identity/valueの可逆束縛長
4. 同じ商を再利用する利得

### 反証条件

- 完全未学習表現でtext-only baselineを上回らない。
- renameでidentityを保持できない。
- confoundを通常入力より選択的に棄権できない。
- データ増加に対し商クラス・model bytes・candidate readsが増え続ける。
- 人工的record境界を外すと差分商が崩壊する。

## 最小実装

`cross_view_mdl_cycle3.py` は外部LLM、RAG、形態素解析、固定意味slot、正解operation labelを学習に使用しない。

- 各episode: 介入前状態、3つの言語view、介入後状態、後続観測
- before/afterの最大共通構造からreplacement signatureを作る
- 同じsignatureを持つ複数言語viewをquotient classへまとめる
- 推論時は文字2/3/4-gramの再利用適合度とclass supportで候補を比較
- 評価は予測したsignatureとepisodeのbefore/afterから算出したsignatureの一致

ただし現在のsignature正規化は、人工状態文の `；` と `=` を一般的なrecord境界として利用する。この点は重要な実験上の制限である。

## 実験条件

- train episodes: 60 / 240 / 720
- seeds: 1 / 7 / 19
- 各episodeに3つの学習view
- 評価各120件
- seen view
- 未学習語順
- 未学習同義動詞
- entity/value rename
- 単一view
- 無介入confound

比較:

- `TextOnlyMDL`: 言語viewのみから最も近いtransition signatureを選ぶ
- `CrossViewQuotient`: before/after差分で言語viewを商へ統合して選ぶ

## 結果

### 720 episodes・3 seed平均

| 指標 | Text-only MDL | Cross-view quotient |
|---|---:|---:|
| seen view accuracy | 0.6611 | **0.6944** |
| 未学習語順 | **0.2750** | 0.1861 |
| 未学習同義動詞 | 0.3667 | **0.5278** |
| rename | **0.7417** | 0.7361 |
| single-view | 0.6583 | **0.7111** |
| confound棄権 | **0.6194** | 0.3472 |
| model bytes | **8,175** | 870,843 |
| train seconds | **0.0120** | 0.0185 |
| inference latency | baselineは小規模 | 0.3542 ms/query |
| candidate reads | baseline少数 | 72 |
| quotient classes | - | 6 |
| Peak RSS | colspan | 323,168 KiB |

Peak RSSはPython runtimeを含み、方式固有値でもスマートフォン実測でもない。

### スケーリング

| train | synonym: baseline | synonym: quotient | quotient bytes | reads |
|---:|---:|---:|---:|---:|
| 60 | 0.7083 | **0.8167** | 75,286 | 70 |
| 240 | 0.6944 | **0.8472** | 291,173 | 72 |
| 720 | 0.3667 | **0.5278** | 870,843 | 72 |

同義動詞では改善したが、720例で両方式が悪化した。表面prototypeの競合が増え、再利用クラスが意味的に純化されていないことを示す。

## 反証解析

### 1. 商形成が意味クラスへ収束しない

理想的には3つの操作商へ収束するはずだったが、6クラスが残った。状態差分の表面境界や値形状が同じ操作を分断している。

### 2. 語順一般化に失敗

同義動詞では複数viewの共同証拠が役立ったが、語順を大きく変えた表現では0.1861でbaselineより悪い。文字n-gram frameの一致に依存しており、変数束縛構造を学習していない。

### 3. confound検出は選択的でない

通常viewとconfoundの平均marginはほぼ同一であった。confoundは命令文だけから判別不能であり、低margin棄権は通常例も同様に棄権する。したがって因果必要性を理解した証拠ではない。

### 4. 圧縮に失敗

quotient class数は小さいが、各class内に多数の表面prototypeを保持したため、model bytesは720例で約871KBまで増えた。1GB未満ではあるが、知識量に対するsublinear scalingを示していない。

### 5. renameは改善しない

identity/valueをmaskした学習frameでも、未知値の表面形状が差分signatureに影響し、renameはbaselineを上回らなかった。可逆束縛と商形成がまだ分離し切れていない。

## 判定

### 限定的に残す知見

> 同じepisodeの複数言語viewを、共通の非言語的変化signatureで束ねると、表面上異なる同義動詞を同じ候補へ近づけられる場合がある。

### 棄却する主張

> 複数viewのMDL共同圧縮だけで、自由日本語から潜在操作・目的・因果プログラムが創発する。

これは反証された。改善は人工record、既知の3-view episode、文字n-gram、弱い差分正規化に依存し、未知語順・因果confound・自由日本語統合へ一般化しない。

## 他系列へ返す知見

- A: 確認候補は言語表面だけでなく、どの介入差分商を分離するかで順位付けできる。ただし商が表面分断している間は確認生成も不安定。
- C: 同義表現を束ねるには介入差分が有用だが、無介入・逆介入・別対象介入なしでは因果必要性にならない。
- D: cross-view schemaを低速記憶へ定着させる前に、model bytesがepisode数へ線形増加しないか監査すべき。
- E: factor graph候補には、異なる語順で同じbindingを持つ構造候補を明示的に含める必要がある。

## 次の仮説

**Compositional Binding MDL with Contrastive Views**

次は表面prototypeをclass内へ保存する方式を廃止する。

1. 各utteranceを可逆なliteral片と匿名binding edgeへ分解する。
2. 語順が異なっても同じentity/value edge構造なら同じprogram graphへ写像する。
3. 実行・無介入・逆介入・別対象介入を別viewとして共同符号化する。
4. class内prototype数ではなく、program graph + episode bindingだけを保存する。
5. 未知語順、同義動詞、rename、confound選択性を同時改善できなければ棄却する。

成功条件:

- 完全未学習語順 > text-only baseline
- 同義動詞改善を維持
- rename改善
- confound selective abstention > 0
- model bytesがepisode数に対してsublinear
- 自由日本語統合gateに非ゼロの改善

## 到達判定

- highschool_level_passed: false
- native_japanese_communication_passed: false
- weak_smartphone_verified: false
- completion: false
