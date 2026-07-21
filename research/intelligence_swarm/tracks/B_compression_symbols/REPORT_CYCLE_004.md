# 系列B Cycle 004 — Compositional Binding MDL with Contrastive Views

## 結論

Cycle 003では、同じ状態変化を共有する複数viewを一つの商クラスへ束ねても、クラス内部へ表面prototypeを保存し続けたため、720 episodeで約871 KBまで線形増加した。また未学習語順、rename、confound選択性を改善できなかった。

今回はepisode prototypeの保存を廃止し、各観測を次の**可逆な匿名binding graph**へ圧縮する `Compositional Binding MDL with Contrastive Views` を検証した。

- 命令中で状態文と共有されるepisode固有区間
- 介入前後で置換される旧値／新値
- episode固有区間と値を除去したliteral断片
- 介入前状態から介入後状態を再構成する実行graph

最大720 episode・3 seed平均では、表面prototype方式に対して、既知構文精度を0.1111から0.8306、未学習語順を0.1361から0.6472へ改善した。モデル表現量は90,064 Bから4,049 B、候補読出しは720から40.67、推論時間は8.76 msから0.425 msへ減少した。

一方、未学習同義動詞、未知entity/value rename、confound選択的棄権は全て0だった。したがって、**episode prototypeを捨てて再利用可能な実行graphへ圧縮する部分原理**は限定的に支持するが、自由日本語から意味プログラムが創発する中核仮説は反証する。

## 他4系列との重複表

| 系列 | 最新中心機構 | 継承した知見 | 本サイクルの非重複点 |
|---|---|---|---|
| A | 予測不一致から確認発話を生成 | 候補は異なる実行未来を生成し、差を外部へ表面化できる必要 | 確認・対話選択ではなく、候補未来を生む実行graph自体の圧縮 |
| C | 操作／無操作の対照必要性 | 因果昇格には無操作・逆操作・別対象操作が必要 | 因果辺の採否ではなく、固定ontologyなしのbinding graph形成 |
| D | 未知viewの暫定保持と睡眠統合 | 境界を早期確定せず、後続証拠まで可逆に保持する必要 | 長期記憶の固定化ではなく、episode prototypeを捨てる構造圧縮 |
| E | 開集合factor graph候補と世界分岐 | 境界差だけでなく実行結果が異なる候補でなければならない | energy緩和ではなく、単一graphの記述長・再利用利得・実行可能性を測定 |

重複する候補として、A型の質問生成、C型の因果昇格、D型の睡眠統合、E型の反復緩和は採用しなかった。

## 仮説

**Compositional Binding MDL with Contrastive Views**

同じepisodeに含まれる介入前状態・命令・介入後状態を、表面文prototypeではなく、匿名のbinding edgeと可逆literalへ圧縮できれば、語順が変わっても同じ実行graphを再利用でき、保存量・読出し量をepisode数から切り離せる。

### 予測

1. 既知表現と未学習語順で表面prototype baselineを上回る。
2. episode数を12倍に増やしてもgraph数とmodel bytesは12倍には増えない。
3. 未知entity/valueを局所bindingとして保持し、renameへ転移する。
4. 同義動詞も同じ実行graphへ商写像される。
5. 無介入confoundでは通常入力を保ったまま選択的に棄権する。

### 反証条件

- 同義動詞またはrenameが0のまま。
- graphがliteral表面へ依存し、未知操作を候補生成できない。
- confoundを通常入力と区別できない。
- 自由日本語統合能力へ非ゼロ転移しない。

## 実装

`compositional_binding_mdl_cycle4.py`

学習器はentity一覧、value一覧、操作ラベル、意味slot、形態素辞書、RAG、外部LLMを受け取らない。データ生成器の語彙一覧は評価データ作成だけに使用する。

### graph誘導

1. `before` と `after` の文字差分から一つの置換候補を抽出。
2. `before` と `command` の共有区間からepisode固有identity候補を生成。
3. identityと新値を匿名化したcommand literal列を保存。
4. identityと旧値／新値を匿名化したbefore/after patternを保存。
5. 同一graphをsupport付きで一度だけ保存し、episode prototypeを破棄。

### 推論

1. 新しいbefore/commandの共有区間からidentity候補を生成。
2. graph literalを除いた残差から新値候補を生成。
3. before残差から旧値候補を生成。
4. graphを実行し、supportとliteral複雑度によるMDL近似で順位付け。

## 実験条件

- 学習量: 60 / 240 / 720 episode
- seed: 1 / 7 / 19
- 比較:
  - `Prototype`: 全episodeを保存し、命令表面の最近傍を実行
  - `BindingMDL`: graphを重複排除して保存
- 評価:
  - 学習分布内の構文
  - 未学習語順
  - 未学習同義動詞
  - 未知entity/value rename
  - 無操作confound
- model bytes、graph数、学習時間、推論時間、候補読出し、Peak RSS

再現:

```bash
python research/intelligence_swarm/tracks/B_compression_symbols/compositional_binding_mdl_cycle4.py \
  > research/intelligence_swarm/tracks/B_compression_symbols/results_cycle_004.json
```

## 結果

### 720 episode・3 seed平均

| 指標 | Surface prototype | Binding MDL |
|---|---:|---:|
| 既知構文 | 0.1111 | **0.8306** |
| 未学習語順 | 0.1361 | **0.6472** |
| 未学習同義動詞 | **0.1444** | 0.0000 |
| rename | **0.1056** | 0.0000 |
| confound棄権 | **0.8583** | 0.0000 |
| model bytes | 90,064 | **4,049** |
| 保存prototype / graph | 720 | **40.67** |
| 推論時間 | 8.758 ms | **0.425 ms** |
| 候補読出し | 720 | **40.67** |
| 学習時間 | **0.000021秒** | 0.01436秒 |

Peak RSSは308,692 KiB。Python runtime全体を含み、方式固有値でも弱いスマートフォン実機値でもない。

### スケーリング

| 学習episode | Prototype bytes | Binding MDL bytes | Binding graph数 | Binding既知精度 | Binding語順精度 |
|---:|---:|---:|---:|---:|---:|
| 60 | 7,534 | 1,702 | 18.33 | 0.8306 | 0.6472 |
| 240 | 30,045 | 2,566 | 26.67 | 0.8306 | 0.6472 |
| 720 | 90,064 | 4,049 | 40.67 | 0.8306 | 0.6472 |

学習量12倍に対し、Binding MDLのbytesは約2.38倍、graph数は約2.22倍だった。episode prototype保存より明確に緩やかだが、完全な一定サイズではない。

## 支持された部分

> **episodeごとの表面文を捨て、匿名bindingと実行可能な状態置換graphだけを保存すると、語順variantを跨いで再利用しながら、保存量・読出し量・推論時間をepisode数から大きく切り離せる。**

- before/after差分とcommand共有区間を共同利用すると、単なる命令最近傍より既知構文・語順変更で大幅に改善した。
- graphを一度だけ保存することで、720 prototypeを約41 graphへ圧縮した。
- 720 episodeでも約4 KBであり、1 GB未満の条件には十分余裕がある。
- 推論は約0.425 ms/query、平均約41 graphの走査であり、現在の小規模条件ではCPU向きである。

## 構造的反証

現在の方式を汎用記号創発原理としては棄却する。

### 1. 同義動詞が0

command literalをgraphの一部として保存するため、「移動して」と「運んで」を同じ操作として扱えない。実行結果が同じでも、異なる述語表面を同じlatent operationへ商写像する機構がない。

### 2. renameが0

identity/value境界の抽出はbeforeとcommandの完全な共通substring、および学習時graphのliteral配置に依存する。未知表面形状では助詞・述語・値境界を安定して分離できない。

### 3. confound選択性が0

graphは「命令が与えられれば置換を実行する」だけであり、操作世界と無操作世界を別々に符号化していない。したがって、状態を変えない命令や観測後の矛盾を因果的に拒否できない。

### 4. 既知・語順精度も完全ではない

文字共通区間の最大候補が助詞や値の一部を吸収する場合があり、正しいbinding graphが候補集合へ入らない。candidate recallが未解決である。

### 5. 自由日本語統合へ未接続

自由対話、指示遂行、読解、数学・科学推論、計画、因果、反実仮想、自由記述、長期対話、継続学習を同一モデルで成立させていない。実験は短い制御日本語の一状態置換である。

## 系列B固有の進展

Cycle 003では「複数viewを束ねても表面prototypeを残す限り商空間にならない」と分かった。Cycle 004ではさらに、

> **prototypeを廃止して実行graphへ圧縮すれば、語順と資源効率は大きく改善する。しかし、literal述語と境界抽出をgraph内に残す限り、同義操作・open-set binding・因果必要性は創発しない。**

とボトルネックを切り分けた。

圧縮対象を「文章」から「実行可能graph」へ移す方向は有効だが、次に必要なのは、複数の表面文を生成・再構成できる**双方向latent operation**である。

## 他系列へ返す知見

- **Aへ:** 確認候補を作る状態候補は、surface prototypeでなく匿名binding graphを実行して未来を生成すべき。ただし同義述語が別graphのままでは質問も表面依存になる。
- **Cへ:** action/no-action対照を使う前段として、identity/valueを保持した実行graph圧縮は有効。ただし無操作・逆操作・別対象操作をgraphの別branchとして共同符号化する必要がある。
- **Dへ:** 低速記憶へepisode文章を保存せず、再利用可能なwrite/execute graphだけを統合すれば容量増加を抑えられる。境界不確実性は複数graph候補として暫定保持すべき。
- **Eへ:** energyへ渡す候補はliteral境界variantではなく、異なるlatent operationと世界branchを実行できるgraphである必要がある。

## 次の仮説

**Bidirectional Executable MDL Operation Quotient**

次はcommand literalを操作graphへ直接保存しない。

1. 同じ介入前後変化を持つ複数の命令表現を、共通のlatent operation nodeへ束ねる。
2. latent operationから各命令viewを可逆生成できるよう、view固有literalはdecoder側へ分離する。
3. entity/value境界は単一substringへ即決せず、複数の可逆binding候補を保持する。
4. 操作、無操作、逆操作、別対象操作、二段合成を別world branchとして共同符号化する。
5. 記述長は、operation graph、view decoder、episode binding、反例符号長の合計で比較する。

成功条件:

- 未学習同義動詞 > 0かつCycle 003 baselineを上回る
- rename > 0
- 既知・語順精度を維持
- 通常精度を維持したままconfoundを選択的に棄権
- 60→720 episodeでmodel bytesが大幅な線形増加を起こさない
- 自由日本語統合ゲートに非ゼロ改善

## 到達判定

- 高校生級知能: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機検証: 未達
- 完成: false
