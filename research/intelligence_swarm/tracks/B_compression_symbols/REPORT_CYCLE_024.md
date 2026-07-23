# 系列B Cycle 024

## 仮説
**Reversible Binding Seeds from Three-Way Derivation Intersections before MDL Compression**

command、before→after変化、future再出現の三者交差から、MDL圧縮より先にobject/value binding seedを形成できるか検証した。

## 重複回避
| 系列 | 最新中心 | Bで扱わない領域 |
|---|---|---|
| A | Event-gated prospective discourse state | 予測commitment・active query |
| C | Environment-stable event identity | 因果mechanism identity |
| D | Bidirectional query-state endpoint reconstruction | 長期memory endpoint |
| E | Commutator-separated energy factors | energy・attractor |
| B | 三者導出交差→可逆binding seed→MDL | 今回の固有対象 |

## 最大288例・3 seed平均
| 条件 | Intersection object/value/pair | MDL object/value/pair |
|---|---:|---:|
| 既知 | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| 未知語順 | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| 未知語彙 | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| Rename | 0 / 1.0000 / 0 | 0 / 1.0000 / 0 |
| 入れ子 | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| 主語省略 | 0 / 1.0000 / 0 | 0 / 1.0000 / 0 |

## 判定
**中核仮説は反証。三者交差には強い制御条件信号があるが、意味bindingではない。**

既知・語順変更・語彙変更・入れ子でpair recall 1.0となった。しかし、同じobject/value文字列がcommand・state・futureへ明示的に再出現する合成データ条件に依存する。Renameと主語省略ではobject seedが消え、pair recallは0だった。

形成された平均object seedは4、value seedは5、programは20。これは匿名変数・関係・操作の創発ではなく、反復文字列の交差集合である。

MDL方式は能力値を変えず、意味一般化を追加しなかった。圧縮前binding seedという順序仮説は限定支持されるが、現在のseedはsurface identityであり、可逆semantic bindingではない。

## 反証条件
支持には、Rename・主語省略でobject/pair recall増加、held-out双方向再構成、wrong binding抑制、metadata込み絶対MDL利得が必要だった。今回は満たさない。

## 資源
- Intersection model: 288 bytes
- Object seed: 4
- Value seed: 5
- Program: 20
- 全実験時間: 0.246 sec
- Peak RSS: 約111,000 KiB（Python runtime込み）
- 計算量: span生成 `O(NL²)`、交差 `O(S)`、pairing `O(OV)`、推論 `O(O+V)`

1GB未満・小規模5ms級の成立見込みはあるが、弱いスマートフォン実機は未検証。

## 系列固有の進展
**MDLより前にbinding候補を作る必要性は再確認できた。ただし、複数viewの文字列交差はbinding seedではなくsurface anchorに留まる。**

## 他系列へ返す知見
- A: 複数horizon再出現はobject identityではなくsurface anchorの可能性がある。
- C: 複数環境で同じ文字列が残ることをevent identityとみなさない。
- D: query/state双方向再構成でも同一文字列再出現だけならendpoint identityではない。
- E: 複数介入応答の一致はsurface anchorを独立因子と誤認し得る。

## 次の仮説
**Role-Exchange Binding Seeds from Cross-Episode Permutation Tests**

同じ文字列の再出現ではなく、episode間でobject候補だけ、value候補だけを交換し、導出結果が予測通り交換されるか測る。object/valueの独立置換可能性、non-target保存、逆導出、絶対MDLを独立gateにする。

- 高校生級: 未達
- ネイティブ日本語コミュニケーション: 未達
- 弱いスマートフォン実機: 未検証
- 完成: 未達
