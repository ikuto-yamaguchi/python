# 系列D Cycle 023 研究報告

## 仮説

**Dual-Channel Value Memory with Write-Only Equivalence and Query-Conditioned Read Addresses**  
（write-only同値類とquery条件付きread addressを分離した二経路value memory）

Cycle 022では、同じ局所write consequenceを持つvalue mentionを一つのslow classへ統合した結果、write能力は増えず、read accuracyが0へ低下し、wrong readが1.0へ悪化した。

今回はwrite経路とread経路を完全に分離した。

- Write channel: command→value候補、before→after局所変化、write成功・wrong・non-target damage。value-change同値類はstate更新だけに使用。
- Read channel: query context、state側value周辺context、inverse retrieval成功・誤読。write class supportをread scoreへ流さない。
- Cross-link: 両経路が同じvalueへ到達し、複数session supportかつread wrong 0の場合だけslow link。

## 先行研究整理

- Semi-parametric Memory Consolidationはwake–sleep型のepisodic/semantic統合を提案するが、encoderとmemory itemは定義済み。https://arxiv.org/abs/2504.14727
- HiCLは疎なpattern separation、episodic autoassociation、prioritized replayを組み合わせるが、task routing用表現は事前形成される。https://arxiv.org/abs/2508.16651
- task-relevant readout subspaceとnull spaceの分離は、安定性とplasticityを区別する上で重要。https://proceedings.mlr.press/v274/anthes25a.html
- regenerative regularizationは、最近の損失に寄与しないparameterを初期状態へ戻してplasticityを維持する。https://proceedings.mlr.press/v274/kumar25a.html

今回の問題は、これらより上流にある、生の日本語からwrite routeとread address自体を形成できるかである。

## 他系列との重複表

| 系列 | 最新中心 | 限定成功 | 主な失敗 | Dとの分離 |
|---|---|---|---|---|
| A | 観測前予測commitmentによる前向き談話状態 | 残差逆投影で主語省略pair recall回復 | carry独立増分0 | active query・予測stateは扱わない |
| B | 三者導出交差からのbinding seed | 既知局所script再実行 | grammar/binding seed未形成 | MDL・program帰納は扱わない |
| C | 対称情報付き介入replayによるevent方向 | 局所event再実行 | 因果方向が情報非対称性 | 因果world modelは扱わない |
| E | 環境分離介入に不変なenergy応答 | value候補の限定信号 | pair/object binding崩壊 | energy dynamicsは扱わない |
| **D** | **write-only classとquery-conditioned read addressの分離** | 今回検証 | slow cross-link形成 | 系列固有 |

## 実験条件

- Seed: 1 / 7 / 19
- 学習event: 24 / 72 / 144
- Test: 最大36例 / split / seed
- Trace上限: 96
- Write class上限: 32
- Read address上限: 96
- Cross-link上限: 64
- 比較: Trace / Dual channel / Slow cross-link
- 条件: 既知、未学習言い換え、Rename、別状態表現、主語省略、複数段落、未知domain
- 追加: 一回提示学習、長期干渉後latest-value recall

Hidden object・field・valueは評価器だけで使用した。

## 最大144 event・3 seed平均

| 条件 | Trace write / read | Dual write / read | Slow write / read |
|---|---:|---:|---:|
| 既知 | 0.1759 / 0.3704 | 0.1944 / 0.3704 | 0.1944 / 0.3704 |
| 未学習言い換え | 0.1944 / 0.3704 | 0.2037 / 0.3704 | 0.2037 / 0.3704 |
| Rename | 0.1389 / 0.3519 | 0.1574 / 0.3519 | 0.1574 / 0.3519 |
| 別状態表現 | 0.0000 / 0.3426 | 0.0000 / 0.3426 | 0.0000 / 0.3426 |
| 主語省略 | 0.0000 / 0.3704 | 0.0000 / 0.3704 | 0.0000 / 0.3704 |
| 複数段落 | 0.1944 / 0.3704 | 0.2037 / 0.3704 | 0.2037 / 0.3704 |
| 未知domain | 0.1944 / 0.3704 | 0.2037 / 0.3704 | 0.2037 / 0.3704 |

追加診断:

- 既知wrong read: Trace 0.5370 / Dual 0.5370 / Slow 0.5370
- Write class: 12.33
- Read address: 96.00
- Cross-link: 64.00
- Slow link: 0.00
- One-shot: 全方式1.0000（同一episode直後の再実行のため一般化証拠から除外）
- 干渉後recall: 全方式0.2222

## 判定

**中核仮説は反証。write/read分離には限定信号があるが、slow consolidationは成立しなかった。**

### Write側は小幅改善

Dual channelはTrace baselineに対し、既知0.1759→0.1944、言い換え0.1944→0.2037、Rename0.1389→0.1574へ小幅改善した。

Write-only classをread identityへ流さず、state更新scoreだけへ使う設計はCycle 022の全面悪化より安全だった。ただし絶対精度は0.16〜0.20程度で、未知表現へ一般化したとは言えない。

### Read悪化は止まったが改善も0

Cycle 022ではclass化により既知readが0へ落ちた。今回はDual / SlowともTraceと同じread accuracyを維持した。二経路分離によってwrite consequence supportがread scoreを汚染する問題を除去できた。

しかし既知read 0.3704、wrong read 0.5370であり、query-conditioned read address自体はsemantic endpointになっていない。

### Slow linkは0件

Cross-linkは上限64件形成されたが、slow linkは全条件0件だった。両経路が同じvalueへ到達しても、複数session support、read wrong 0、安定したinverse retrievalを同時に満たさなかった。Slow方式はDual方式と全指標で同一だった。

### 干渉耐性増分0

干渉後latest-value recallは全方式0.2222で同一だった。二経路分離は誤統合を止めたが、長期保持・選択的忘却・再固定化を改善していない。

### 支配的失敗は破滅的忘却ではない

slow linkが形成時点で0、read wrongが初期から高い、alternate writeが0、omission writeが0であるため、主問題は記憶保持ではなく、query/object/relation endpointとvalue identityの初期形成失敗である。

## RAG・検索との差

保存文章を返すだけではなく、write channelがcommandからvalue候補を抽出して内部stateを局所更新し、read channelがqueryとstate contextからvalueへ逆引きし、両経路の一致だけをslow consolidation候補化する。

ただし現在は最大96 trace/addressを文字gramで走査する小規模episodic transducerであり、semantic memoryではない。

## 資源量

- モデルサイズ: 39,273 bytes
- 学習時間: 0.169937 sec
- 推論時間: 0.555004 ms / read-or-write
- Peak RSS: 160,164 KiB（Python runtime込み）
- 記憶容量: Trace 96 / Write class 12.33 / Read address 96 / Cross-link 64 / Slow link 0
- 推定計算量: Trace抽出 O(NL)、Write grouping O(T)、Read address形成 O(NL)、Cross-link O(CA)、推論 O(TL+AL)

1GB未満・5ms未満は小規模制御条件で達成した。弱いスマートフォン実機では未検証。

## 破滅的忘却と表面暗記の分離

表面暗記の証拠:

- 既知・言い換え・複数段落・未知domainでほぼ同じ局所write精度
- alternate state write 0
- omission write 0
- query/state文字gramによるread
- one-shotが同一episode再実行

破滅的忘却の証拠として必要だが未成立:

- 初期read/write高精度
- 干渉前後の同一binding比較
- slow link形成
- canonical/alias × relation × latest-valueの安定recall
- 選択的忘却でobsolete valueだけを消去

## 系列D固有の進展

1. Episodic raw trace
2. Object/relation/value候補分離
3. Write consequence class
4. Query-conditioned read address
5. **Write/read二経路分離――限定支持**
6. Slow cross-link――今回未成立
7. Endpoint identity stabilization
8. Selective forgetting
9. Sleep consolidation
10. Episodic-to-semantic integration

> **Write consequence equivalenceをread identityから切り離すと誤統合の追加悪化は止められる。しかし、二経路の一致だけではslow memoryにならない。read endpointが誤っている限り、cross-linkは形成できず、干渉耐性も増えない。**

## 他系列へ返す新知見

- A: 同じfuture outcomeを持つcandidateはwrite予測共有には使えても、談話object identity共有には使えない。
- B: forward derivation classとinverse decoding addressを分離し、双方一致後だけlibrary symbol化する。
- C: forward transition equivalenceとinverse state-variable retrievalを別々に反証する。
- E: 同じenergy consequenceを持つfactorをread endpointへ直接統合しない。

## 次の仮説

**Endpoint Identity from Bidirectional Query–State Reconstruction before Slow Linking**  
（slow link前の双方向query–state再構成によるendpoint identity）

次はwrite classを深掘りせず、read endpointの同一性を先に安定化する。

1. Query区間からstate内value周辺contextを再構成
2. State側contextからquery区間を逆再構成
3. Object・relation・value候補を独立に遮蔽し、どの因子で再構成が壊れるか測定
4. Source→target / target→source双方で成功したendpointだけ保持
5. Alias・言い換え・別状態表現で同じendpointへ戻ることを必須化
6. Endpoint成立後だけwrite classとのcross-linkを許可
7. obsolete value updateでは旧endpointだけ選択的に忘却
8. 主評価をwrong read、干渉前後latest-value recall、slow link precisionにする

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
