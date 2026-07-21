# Relational Role Quotient

## 目的

直近の `surprise / delayed consolidation / interference budget` 系実験は、更新の保存則を変えても固定文字特徴空間では意味干渉を測れないことを反証した。

本実験では、語彙表面を直接状態として使わず、各tokenを左右の遷移関係から誘導した役割へ商空間化し、役割系列上の可変長予測状態を構成する。

## 仮説

異なる語が他の語・操作・属性と同じ関係を持つなら、それらを同じ役割へ束縛することで、名称変更後も再利用できる予測状態を形成できる。

ニューラルネットワーク、Transformer、問題別モデル、タスクラベル、RAG、外部LLM、正解候補検索、完成回答記憶は使用しない。

## 比較

- `lexical_causal_state`: 生tokenのsuffix状態
- `role_quotient`: 左右の関係signatureから誘導したrole suffix状態

## 条件

- 96 / 384 / 1536 episode
- seed 1 / 7 / 19
- 上書き記憶、場所移動、剰余加算を同じ予測器で学習
- 未知人名・未知色への全面rename
- 同じ構文役割だが `反転` により意味が異なるdecoy
- 9系列の厳格な自由日本語統合ゲート
- モデルサイズ、Peak RSS、学習時間、推論時間、候補数、読み出し量、role数

## ローカル結果

最大1536例・3 seed平均:

| 方法 | 語彙内記憶 | 全面rename | decoy | 算術 | 自由ゲート |
|---|---:|---:|---:|---:|---:|
| lexical causal state | 0.2674 | 0.0000 | 0.0000 | 0.2604 | 0.0000 |
| role quotient | 0.2153 | 0.0000 | 0.0000 | 0.2604 | 0.0000 |

資源:

- 最大直列化サイズ: 約19.3KB
- Peak RSS: 約290MB（Python / NumPy込み）
- 学習時間: 最大約0.19秒
- 推論時間: lexical 約0.0011ms、role quotient 約0.0028ms
- 平均候補数: 最大4
- 読み出し: 最大6 suffix state
- 誘導role数: 19〜20

## 判定

仮説は棄却。

関係役割へ商空間化しても、未知語は `<unk-role>` へ潰れ、未知の値tokenを出力へ再束縛できない。役割抽象は「何の種類か」をまとめても、「現在の対話内でどの個体・どの値を指すか」を保持しない。

さらに語彙内精度も改善せず、同じ構文位置を持つtokenをまとめることで必要な個体差を失った。

したがって次の最大ボトルネックは、より精巧なrole clusteringではなく、抽象roleと現在episode固有のentity/valueを可逆に結ぶ動的variable binding、および未知表面形をcopy・生成するrealizerである。

`highschool_level_passed=false`

`native_japanese_communication_passed=false`

`weak_smartphone_verified=false`

`completion=false`
