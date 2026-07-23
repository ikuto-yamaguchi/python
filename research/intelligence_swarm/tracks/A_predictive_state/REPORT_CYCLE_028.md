# 系列A Cycle 028 研究報告

## 仮説

**Cross-Encoded Residual Routing by Predictive Information Exclusion**  
（予測情報除外によるcross-encoded residual routing）

Cycle 027では前turn commitmentとcurrent residualを同じ文字表現で照合したため、局所creditは正になってもrouteがsurface overlapへ退化した。

今回は次を分離した。

- Commitment encoder:
  - 前turnのafter・future持続応答のみ
  - 2〜4文字windowのsigned hash
  - 16次元の疎random projection
- Residual encoder:
  - current turnのbeforeとcommandを別々に符号化
  - 2つのprojected viewの絶対差
  - Commitment側とは異なるsalt・projection
- Route:
  - 直接文字列overlapをscoreから除外
  - current turnのafter・futureは選択に使用しない
  - 複数train dialogでcontinuation supportがnegative supportを上回るresponse bucketだけを保持

## 先行研究整理

- Action-conditional self-predictive learningは、行動条件付き表現が低rank dynamicsを捉える条件を解析する。ただしstate/action表現は既知。
  - https://proceedings.mlr.press/v258/khetarpal25a.html
- 2025年のmultimodal information bottleneck研究は、view固有情報を除去しつつtask-relevant情報を残す必要性を示す。
  - https://proceedings.mlr.press/v267/almudevar25a.html
  - https://proceedings.mlr.press/v267/wu25x.html
- 2026年のIntermittent Active Inferenceは、prediction error最小化に基づく断続的な推論・行動更新を扱うが、生成モデルと状態空間は定義済み。
  - https://doi.org/10.3390/e28030269

今回の問題は、これらより上流にある、生の日本語からどの過去状態が現在の未説明部分へ責任を持つかを生成することである。

## 他系列との重複表

| 系列 | 最新中心 | Aで棄却・分離した領域 |
|---|---|---|
| B | 競合binding graphの出力不一致からcounterfactual test生成 | program test・MDL |
| C | outcome-blind source-only mechanism transport | 因果transition witness |
| D | 時間横断予測必要性によるendpoint birth | 長期memory endpoint |
| E | outcome非参照のprospective residual field | energy landscape |
| **A** | **前turn持続応答とcurrent self-disagreementの時間方向routing** | 今回の固有対象 |

Bのtest program、Cのsource-only transport、Dのendpoint necessity、Eのprospective residual fieldと中心機構が重なる候補は棄却した。Aでは談話stateのprospective carryだけを評価した。

## 実験条件

- Seed: 1 / 7 / 19
- Train: seen / Rename / 明示切替と主語省略の混在 / 複数段落、各48 turn
- Test: 既知 / Rename / 入れ子 / 主語省略 / 明示切替混在 / 複数段落 / 計画変更、各24 turn
- Ablation:
  1. No carry
  2. Unconditional carry
  3. Cross-encoded routing
- Hidden object/value labelは評価器だけで使用
- Transformer・attention・RAG・外部LLMなし
- Route選択時にcurrent after/futureを使用しない
- Route scoreに直接文字列overlapを使用しない

## 3 seed平均

| 条件 | No carry pair recall | Unconditional pair recall | Cross-encoded pair recall | Cross-encoded accuracy |
|---|---:|---:|---:|---:|
| 既知 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Rename | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| 入れ子 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| 主語省略 | 0.0000 | 1.0000 | 0.0435 | 0.0000 |
| 明示切替混在 | 0.4783 | 1.0000 | 0.4783 | 0.0000 |
| 複数段落 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| 計画変更 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

Route診断:

- Route prototype: 1.67
- 主語省略carry率: 0.0435
- 主語省略continuation hit: 0.0435
- 主語省略wrong carry: 0
- 明示切替混在carry率: 0
- 計画変更wrong carry: 0.0290

## 判定

**中核仮説は強く反証された。**

### Surface overlap由来の高carryは抑制

Cycle 027では主語省略のrouted carry率が0.9259だった。今回は独立符号化と直接overlap除外により0.0435まで低下し、主語省略ではwrong carry 0となった。

これはsurface overlapによる偽routeを抑制したという評価健全化の信号である。

### しかし正しいcontinuationもほぼ消失

主語省略のpair recallは0から0.0435へわずかに増えたが、Unconditionalの1.0を大きく下回り、accuracyは0だった。

形成されたroute prototypeは平均1.67件しかなく、別符号器間で安定するcontinuation responseをほぼ学習できていない。

> **直接文字一致を除くと偽routeだけでなく、これまでのcontinuation信号の大半も消えた。Cycle 027の正の局所creditはsurface依存だったことが強く支持された。**

### 候補recallと選択能力は依然として別問題

既知・Rename・入れ子・複数段落・計画変更ではpair recallが1.0だがaccuracyは0である。

正しい文字区間が候補集合に含まれていても、longest-span選択は説明断片を選び、object/value/operationを束縛できない。

### 明示切替と主語省略を識別できない

明示切替混在ではCross-encoded carry率が0で、No-carryと完全同値になった。

誤carryを抑えたが、継続すべきturnの正しいcommitmentも選べない。談話focusの継続・終了・切替は未成立である。

### 計画変更は未成立

計画変更ではrouteが少数発火したが、その全てがwrong carryだった。旧goal・新goal・revision scopeを別stateとして保持していない。

## 反証条件

仮説支持には最低でも次が必要だった。

1. 直接文字overlapなしで主語省略continuation recallがNo-carryを明確に上回る
2. 明示切替時のwrong carryを増やさない
3. Route利用で観測前accuracyが改善
4. Rename・複数段落でも同じroute identityが再現
5. 計画変更で旧goalと新goalを分離
6. 3 seedで再現

今回は1の極小signal以外を満たさず、accuracy増分は0だった。

## 資源量

- Model: 9,599 bytes
- Training: 0.098758 sec
- Inference:
  - seen 0.7178 ms/example
  - omitted 0.7082 ms/example
  - paragraph 0.8731 ms/example
- Peak RSS: 161,852 KiB（Python runtime込み）
- 推定計算量:
  - hash encoding `O(L)`
  - sparse projection `O(BD)`
  - routing `O(R)`
  - raw span生成 `O(L²)`
  - pair候補 `O(KoKv)`

1GB未満・5ms未満は小規模条件で達成した。弱いスマートフォンCPU実機は未検証。

## 系列A固有の進展

> **Commitmentとresidualを別符号器へ分離し、直接文字一致を除くと、Cycle 027の高carry信号はほぼ消える。これまでのrouting evidenceは潜在状態ではなくsurface共有情報へ依存していた。別符号器間で共有すべきなのは静的類似度ではなく、同じ介入に対する時間的応答である。**

## 他系列へ返す知見

- B: program testも入力surfaceから独立な予測応答差でなければ偽識別になる。
- C: source/targetを別符号化するだけではmechanism transportにならず、同じ介入応答が必要。
- D: endpoint除去signatureを別channel化しても、時間的応答を共有しなければidentityは形成されない。
- E: outcome非参照residual fieldでも、異なる予測器間の静的類似度だけではconstraintにならない。

## 次の仮説

**Intervention-Coupled Route Identity from Shared Temporal Response Kernels**  
（共有時間応答kernelによる介入結合route identity）

次はcommitment/residualの静的embedding類似度を廃止する。

1. 前turn commitment候補へ局所mask・短縮介入を加える
2. current before/commandの予測誤差streamが時間位置ごとにどう変化するか測定
3. Residual側にも対応する局所介入を加える
4. 両者の誤差応答kernelが複数turn・複数surface環境で一致する場合だけroute化
5. Exact文字列・embedding cosineをroute scoreから除外
6. 主語省略ではobject残差kernelへ接続するrouteだけcarry
7. 明示objectのkernelが同じ役割を説明した場合は旧routeを終了
8. 計画変更では旧goal・新goalの応答kernelを分離
9. Kernel response precision、continuation recall、wrong carry、観測前accuracyを主評価化

## 最終状態

- 高校生級知能: **未達**
- ネイティブ日本語コミュニケーション: **未達**
- 弱いスマートフォン実機検証: **未達**
- 完成: **未達**
