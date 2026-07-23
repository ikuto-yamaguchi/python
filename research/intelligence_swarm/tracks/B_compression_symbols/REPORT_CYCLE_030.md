# 系列B Cycle 030

## 仮説

**Active Probe Grammar from Maximum Expected Program Elimination per Description Bit**

Cycle 029で独立probeが局所triangle選択に小さな正の増分を出した。本Cycleでは全probeを受動利用せず、各probeが識別するtriangle pair数をprobe記述bitで割った効用を計算し、上位16件だけを採用した。

## 重複表

| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | probe-grounded operator birth | 予測状態・時間更新 |
| C | target boundary competition | 因果transition |
| D | operator-centered memory endpoint | 長期memory |
| E | probe-nudged boundary attractor | energy固定点 |
| **B** | **記述bit当たりprogram除外効率によるprobe文法・共同MDL** | 今回の固有対象 |

## 最大288例・3 seed平均

| 条件 | Graph | Passive probe | Active 16 | Shuffled active |
|---|---:|---:|---:|---:|
| 既知 | 0 | 0.1250 | 0.1250 | 0 |
| 未知語順 | 0 | 0.0278 | 0.0278 | 0 |
| 未知語彙 | 0 | 0.0278 | 0.0278 | 0 |
| Rename | 0 | 0 | 0 | 0 |
| 別状態表現 | 0 | 0 | 0 | 0 |
| 入れ子 | 0 | 0.0278 | 0.0278 | 0 |
| 主語省略 | 0 | 0 | 0 | 0 |
| 複数段落 | 0 | 0.0278 | 0.0278 | 0 |

追加診断:

- Binding triangle: 64
- Probe候補: 25
- Passive選択: 25
- Active選択: 16
- Passive discrimination: 198.67
- Active discrimination: 157.67
- Passive description: 33,304 bits
- Active description: 27,853 bits
- Literal/Graph baseline: 283,045 bits
- Active model: 8,807 bytes
- 学習時間: 約0.50 sec
- 既知推論: 約5 ms/example
- 複数段落推論: 約19.4 ms/example
- Peak RSS: 111,904 KiB（Python runtime込み）

## 判定

**一般知能・記号創発仮説としては未達。probe圧縮仮説は限定支持。**

Active 16 probeはPassive 25 probeと同じaccuracyを維持した。既知0.125、未知語順・未知語彙・入れ子・複数段落0.0278で、wrong commitは全条件0だった。probe preferenceを反転したshuffleでは全条件0へ戻った。

Description lengthは33,304 bitsから27,853 bitsへ16.4%減少した。したがって「識別数/bit」によるprobe選択は、既存triangleを選ぶ局所probe libraryの圧縮として支持される。

ただしRename・別状態表現・主語省略は0であり、candidate birth、semantic variable、relation、scope、goalは形成されない。probeは既存program選択を効率化しただけで、新しいprogramを生成していない。

## 反証条件

一般仮説支持には、ActiveがPassiveより少ないbitで同等以上の性能を維持するだけでなく、Rename・別状態表現・主語省略へ転移し、exact binding recallとexecution accuracyを増やす必要があった。前半のみ達成。

## 探索爆発抑制

- triangle上限64
- probe pool内でpair disagreementを事前集約
- utility上位16のみ採用
- 推論時triangle上限64
- 計算量: induction `O(NKoKv)`、probe監査 `O(VT²)`、選択 `O(V log V)`、推論 `O(TL²+T²)`

1GB未満は達成。短文は約5ms級だが、複数段落約19.4msで弱いスマートフォン条件は未達、実機未検証。

## 系列B固有の進展

**独立probeの局所選択信号を、約36%少ないprobe数・16.4%短い記述長で保持できた。**

MDLが初めて「能力0の失敗library」ではなく、極小ながら正のheld-out execution信号を保持したまま圧縮した。

## 他系列へ返す知見

- probeは候補birthの代替ではないが、候補形成後の独立反証を少数bitへ圧縮できる。
- probe outcome shuffleで信号が消える監査を必須化する。
- 構造数や自己整合性より、独立観測で除外できた候補数/bitを評価する。

## 次の仮説

**Probe-Conditioned Symbol Birth from Minimal Equivalence-Class Splits**

1. 既存triangleをprobe応答同値類へ分割
2. 同値類内で共通するobject/value/endpoint変換だけを匿名記号候補化
3. 異なるsurfaceのprobe応答が同じ場合にのみ概念再利用
4. Rename・別状態表現で同値類が維持されるか監査
5. 主語省略は前turn同値類の再起動として検証
6. symbol library + probe grammarの共同MDL
7. 能力増分がない記号は圧縮できても棄却

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
