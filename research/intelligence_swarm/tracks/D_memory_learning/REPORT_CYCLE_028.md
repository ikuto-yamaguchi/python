# 系列D Cycle 028 研究報告

## 仮説

**Endpoint Birth by Cross-Temporal Predictive Necessity before Coalition Credit**  
（coalition credit前の時間横断予測必要性によるendpoint創発）

Cycle 027では固定value inventoryを除去するとreadが全面0となり、Shapley型credit以前にopen-form endpointが形成されていないことが確定した。

今回はraw日本語の1〜8文字spanを候補とし、そのspanを除去したときにquery応答、before→after状態変化、future observation、non-target保存の複数channelが同時に壊れる場合だけendpoint候補とした。

## 他系列との重複回避

| 系列 | 最新中心 | Dで扱わない領域 |
|---|---|---|
| A | 共有時間応答kernelによるroute identity | 談話予測責任 |
| B | program合成probe stateによる識別実験 | Program帰納・MDL |
| C | target-context mechanism adapter | 因果transition |
| E | outcome非参照prospective residual field | Energy・attractor |
| **D** | **複数時間channelを同時に壊すraw spanのmemory endpoint birth** | 今回の固有対象 |

## 最大96 event・3 seed平均

| 条件 | Support read / wrong | Necessity read / wrong | Slow read / wrong |
|---|---:|---:|---:|
| 既知 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.4861 |
| 未学習言い換え | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.4861 |
| Rename | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.4861 |
| 別状態表現 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.1111 / 0.5000 |
| 主語省略 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.4861 |
| 複数段落 | 0.0000 / 1.0000 | 0.0000 / 1.0000 | 0.0000 / 0.4861 |

追加診断:

- Endpoint候補: 64
- Slow endpoint: 33
- Necessity model: 38,135 bytes
- 学習時間: 0.017186 sec
- Necessity推論: 0.629882 ms/query
- Slow推論: 0.141329 ms/query
- Peak RSS: 168,448 KiB（Python runtime込み）

## 判定

**中核仮説は強く反証された。**

Support方式とNecessity方式は全主要条件でread accuracy 0、wrong read 1.0だった。複数channelへ再出現するspanは多数生成されたが、上位候補はobject名の部分文字列、「現在値」「補助記録」などの共通状態片、値の一部分、境界不完全spanに支配された。

Slow方式は33 endpointを形成し、既知wrong readを1.0から0.4861へ下げたが、read accuracyは0のままだった。別状態表現だけ0.1111の極小信号が出たが、一般的なsemantic endpointとは判断しない。

> **複数時間channelを同時に壊すspanでも、そのchannel予測器が文字列再出現に依存する限り、endpoint identityにはならない。**

支配的失敗は破滅的忘却ではなく、書込み前のendpoint birth失敗である。

## RAGとの差

保存文書や近傍vectorを返す方式ではない。raw spanをmemory element候補化し、複数時間channelへの除去影響を測り、必要候補を内部read状態へ注入し、複数session支持後だけslow化する。ただし現在は文字列再出現に依存する疎transducerで、semantic associative memoryには未到達である。

## 資源・計算量

- モデルサイズ: 38,135 bytes
- Peak RSS: 168,448 KiB
- Endpoint上限: 64
- Slow endpoint: 33
- raw span生成 `O(NL²)`
- channel necessity監査 `O(E)`
- read `O(BL)`、`B≤64`

1GB未満・5ms未満は小規模条件で達成。弱いスマートフォンCPU実機は未検証。

## 系列D固有の進展

**固定語彙を排除した状態で、複数channel必要性だけではendpointは創発しない。Endpoint候補には、同じ文字列の再出現ではなく、spanを介して予測状態がどのように変化するかという機能的応答identityが必要である。**

## 他系列へ返す知見

- A: 複数turnに残る文字区間をcommitment identityとみなさず、介入応答kernelを必須にする。
- B: 複数viewで再利用できるspanも実行roleではなく、probe outcomeの機能差が必要。
- C: source/target双方に再出現するcontextはmechanism adapterではなくsurface anchorの可能性がある。
- E: 複数予測channelの同時error reductionも、同じ文字sourceなら独立energy evidenceではない。

## 次の仮説

**Functional Endpoint Birth from Cross-Channel Intervention Response Kernels**  
（channel横断介入応答kernelによる機能的endpoint創発）

1. Spanをmask・短縮・置換する局所介入を生成
2. Query予測、state transition予測、future予測の誤差変化を位置別kernel化
3. 具体的文字列をidentity keyに使用しない
4. 複数surface環境で同じresponse kernelを持つspanだけendpoint class化
5. Object・relation・valueのkernelを独立channelで分離
6. One-shotではfast endpointを即時利用
7. 複数sessionでkernelが再現した場合だけslow化
8. Endpoint成立後にのみcoalition credit・選択的忘却を再開

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機: **未検証**
- 完成: **未達**
