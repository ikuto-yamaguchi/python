# 系列D Cycle 008 研究報告

## 仮説

**Effect-Grounded Bidirectional Discourse-Focus Fast Weights**  
（効果接地型・双方向談話焦点fast weights）

Cycle 007では、entity/value方向が明示的な一回提示ではcounterfactual fast write/readが有効だった一方、代名詞0.0139、長い未学習質問0、干渉後の最新値0.075であった。候補を列挙しても談話上の焦点を形成できず、更新先episodeを選べなかった。

本サイクルでは、談話焦点を固定規則や単純な直近順ではなく、複数照応先候補、cue表面から得る局所fast weight、候補ごとの暫定書込み、後続の操作整合証拠による昇格・撤回で扱う。

## 他系列との重複表

| 系列 | 現在の中心機構 | 成功・失敗 | 系列D候補との重複判定 |
|---|---|---|---|
| A | 証拠channel信頼度、rollback、能動状態更新 | 未知返答の誤確定を棄権へ変換したが、既知coverage低下と意味driftに失敗 | 外部feedback意味の校正はA固有。Dでは発話をどのepisodeへ接続するかを扱う |
| B | execution-first proposal、MDLは統合専用 | 可逆MDL候補は実行groundingを保証せず全面棄権 | parse/program生成を中心にすると重複。Dでは照応候補のfast write/readと統合条件を扱う |
| C | 複数operation効果signatureから潜在condition factorを形成 | factor数形成は限定成立、zero-shot意味転移と誤bridge校正に失敗 | operation/context因果factor形成はC固有。Dでは操作効果を照応edgeの監査信号に限定 |
| E | intervention-discriminative scope attractor、局所factor学習 | scope候補recall不足、通常能力0、平坦収束 | energy緩和を中心にすると重複。Dでは局所fast weightと可逆統合を検証 |
| D候補 | 効果接地型談話焦点fast weights | 照応候補を仮書込みし、後続効果で昇格・撤回 | 系列D固有 |

棄却した候補:
- 返答信頼度を学習して照応を選ぶ: Aと重複。
- MDLで最小照応parseを選ぶ: Bと重複。
- operation effect tensorから談話entityを誘導する: Cと重複。
- 照応候補をenergy緩和する: Eと重複。

## 継承知見

- A Cycle 007: entropy減少は正しさを保証しない。後続証拠でrollback可能にする。
- B Cycle 008: 可逆性と短い記述長は実行可能性を保証しない。実際のwrite/read結果で監査する。
- C Cycle 008: 複数operation効果signatureはsurface aliasより強い識別信号になり得る。ただし誤signatureでも高確信になり得る。
- E Cycle 007: 候補数ではなく、異なる未来を生成する非同型候補が必要。

## 先行研究整理

sparse/online continual memoryは局所更新と干渉抑制に有望だが、生の言語からepisode identityや照応先を生成する上流問題は別に残る。memory consolidation研究は複数時間尺度の内部状態と選択的可塑性を重視する。discourse coreference研究では、記憶内availabilityとreferential accessibilityは同一ではなく、談話焦点やtopic shiftが照応へ影響する。

参考:
- Alonso & Krichmar, A sparse quantized Hopfield network for online-continual memory, Nature Communications, 2024.
- Lindsey & Litwin-Kumar, Selective consolidation of learning and memory via recall-gated plasticity, eLife, 2024.
- Zenke & Laborieux, Theories of synaptic memory consolidation and intelligent plasticity for continual learning, 2024.
- Johns et al., Memory availability and referential access.
- van Rij et al., How WM load influences linguistic processing in adults.

## 最小実装

`effect_grounded_discourse_memory_cycle8.py`

学習器へ与えないもの:
- entity/value/relation辞書
- 固定ontology、手書き意味slot
- 形態素解析
- Transformer/RNN
- RAG、ベクトルDB、外部LLM
- 問題別分岐

文字2/3/4-gram、引用区間、局所cue表面のみを使用する。

内部状態:
- `cue_rank`: cueから候補順位への低速schema
- `fast_hypotheses`: 現在の複数照応先候補
- `pending`: 暫定書込み
- `values`: 統合済みepisode-local binding
- `revocations`: 後続証拠による誤書込み撤回

単なる検索との違いは、保存文を返すのではなく、候補ごとに内部値bindingを書き換え、その後の想起状態を変える点にある。

## 実験

- train size: 48 / 192 / 768
- seed: 1 / 7 / 19
- 主要split: 180 dialogue / seed
- 一回bridge: 100 / seed
- 継続更新: 80 dialogue / seed
- 比較: 直近entityへ常に書くrecency memory
- 条件: 学習済みcue、未学習cue、未学習cue+delayed grounding、20発話gap、topic shift、cueなし、一回bridge、継続更新

```bash
python research/intelligence_swarm/tracks/D_memory_learning/effect_grounded_discourse_memory_cycle8.py \
  --output research/intelligence_swarm/tracks/D_memory_learning/results_cycle_008.json
```

## 最大768例・3 seed平均

| 指標 | recency | focus fast weights |
|---|---:|---:|
| 学習済みcue・即時 | 0.5389 | **1.0000** |
| 未学習cue・即時 | **0.5630** | 0.0963 |
| 未学習cue・delayed | 0.5315 | **1.0000** |
| 20発話gap | 0.5685 | **1.0000** |
| topic shift | 0.5426 | **1.0000** |
| cueなし曖昧 | **0.5833** | 0.1019 |
| 効果付き一回bridge | 0.5433 | **1.0000** |
| 継続更新後の最新値 | 0.3611 | **0.9444** |

資源:
- model: 972 bytes
- learned cue schema: 6
- local reads: 最大5
- training: 0.0528 sec
- immediate inference: 約0.058–0.063 ms/dialogue
- delayed inference: 約0.112 ms/dialogue
- fast candidate writes: 2/update
- Peak RSS: 389,344 KiB（Python runtime込み）
- 計算量: 学習 `O(NG)`、cue proposal `O(PG)`、fast write/rollback `O(H)`, H=2

## 限定支持

学習済みcueでは直近baseline 0.5389に対し1.0で、20発話gap、topic shift、継続更新でも高い値を維持した。未知cueを効果付きで一回明示groundingした後、別identityへ同じcueを再利用するone-shot bridgeも1.0であった。

残せる部分原理:

> episode-local bindingを直近順へ即決せず、談話焦点候補をfast weightとして保持し、異なるidentityで再現する後続効果証拠によって低速write/read schemaへ昇格する。

## 決定的な反証

中核の自由日本語記憶原理は反証。

1. 未学習cue即時は0.0963。新しい言い回しから談話焦点を理解していない。
2. delayed 1.0は明示identity証拠への依存。代名詞を即時理解したのではなく、後から対象を直接示されて書き直した結果。
3. cueなし条件は精度0.1019、棄権率0.0722。情報不足なのに誤ったfast writeを行う。
4. 実験器が引用された二候補構造を与えている。任意数候補、主語省略、暗示、同義語、複数relationを生成していない。
5. 自由対話、読解、推論、計画、因果、反実仮想、自由生成、弱いスマートフォン実測は未達。

## 破滅的忘却と表面暗記の分離

継続更新後の最新値0.9444は学習済みcue条件でfast bindingが干渉に耐えた証拠。一方、未学習cue即時0.0963とcueなし0.1019は一般的照応概念ではなく表面cue schemaであることを示す。形成済みbindingの破滅的忘却は小さいが、open-set候補生成と意味転移は未成立。

## 系列D固有の進展

記憶形成を4段階へ分離した。

1. Antecedent proposal
2. Discourse-focus fast weighting
3. Counterfactual fast write/read
4. Effect-grounded consolidation/revocation

Cycle 007は1と3を試し、代名詞候補が平坦化した。Cycle 008は2と4を追加し、学習済みcueとone-shot alias追加では改善した。しかし最大ボトルネックは依然1である。

## 他系列へ返す新知見

- Aへ: 証拠channelの信頼度だけでなく、証拠がどのepisode edgeを更新するかも不確実状態として保持する。
- Bへ: execution-first probeへ談話cue変更、長gap、topic shift、更新後想起を追加する。
- Cへ: operation effectは照応edgeの監査にも使える。ただし明示identityを含むdelayed evidenceは漏洩として分離評価する。
- Eへ: scope候補は異なるaction branchだけでなく、異なるmemory update targetと後続想起を生成する必要がある。

## 次の仮説

**Open-Set Discourse Event Segmentation with Multi-Channel Coreference**

次は引用2候補と明示groundingを廃止し、入力時系列からepisode境界、discourse focus、entity、relation、update対象、operation effect、後続想起候補を同時生成する。

候補は次発話予測、operation effect、更新後想起、別episode非干渉、話者訂正、時間的持続性で競合させる。異なるfuture memory stateを生成しない候補は保持しない。

必須成功条件:
- 未学習cue即時0.0963を改善
- cueなし条件で誤確定を棄権へ変換
- 3～8候補のopen-set antecedent
- 主語省略・複数段落を0から改善
- delayed明示identityなしで修復
- model 32KB未満、local reads 16以下、5ms/dialogue以下
- 継続更新最新値0.9444を維持

## 統合判定

- 系列D固有の進展: 学習済み談話cueをfast focus weight化し、効果付き一回観測で別identityへbridgeできた。
- 他系列へ返す知見: memory update target自体を候補状態に含め、明示identityを含むdelayed evidenceを即時理解と分離する。
- 次に深掘る一点: **明示候補・明示groundingなしのopen-set談話焦点生成**。

**高校生級知能: 未達**  
**ネイティブ日本語コミュニケーション: 未達**  
**弱いスマートフォン実機検証: 未達**  
**完成: 未達**
