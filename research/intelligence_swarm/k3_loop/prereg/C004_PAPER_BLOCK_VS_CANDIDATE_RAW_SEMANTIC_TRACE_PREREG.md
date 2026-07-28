# C004 — PAPER-BLOCK / CANDIDATE-RAW semantic trace preregistration

Date: 2026-07-29
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: C003 ENV_PASS後のdeterministic semantic traceのみ許可

## 1. 目的

公開候補の未reset、duplicate prefix、recency biasは、paper Block AttnResと同一介入ではない。以後、論文準拠候補と公開artifactを別variant、別ID、別出力に分離する。

単一仮説:

> tiny deterministic traceで、PAPER-BLOCKが登録済みのblock boundary、partial reset、source identity、bias/gate不在を満たすかを判定できる。同時にCANDIDATE-RAWは公開commitの挙動を変更せず記録できる。

品質、速度、学習効果は本runで評価しない。

## 2. 共通baseline B0

- Qwen3 dense PreNorm decoder
- hidden size 512
- 12 layers
- attention heads 8、KV heads 4、head dim 64
- intermediate size 1536
- vocabulary 151,936、tied embeddings
- expected total/active parameters: `115,554,304`

attention、MLP、normalization、position encoding、initializationは全variantで同一とする。

## 3. PB1 — PAPER-BLOCK

著者疑似コードに対応するcanonical候補。

- Block AttnRes blocks `N=4`
- static zero-initialized pseudo-query
- RMS-normalized routing key
- softmax weighted sum
- block境界でcompleted sourceを一度だけappend
- append直後、次block開始前に`partial_block`をreset
- completed sourceとcurrent partial sourceを別identityで管理
- unintended duplicate sourceを禁止
- recency bias、null source、sigmoid/alpha等のoptional gateを禁止

暫定parameter contract:

- total/active parameters: `115,579,904`
- delta vs B0: `25,600`
- relative delta: approximately `0.02215%`

exact state dictが一致しない場合、parameter名とshapeで完全説明できなければSTOPとする。

PB1は新規architecture提案ではなく、著者疑似コードの最小reference reproductionとして扱う。

## 4. CR1 — CANDIDATE-RAW

- source: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- fixed commitを変更しない
- expected total/active parameters: `115,579,929`
- expected delta: `25,625`
- 未reset、duplicate source、recency biasを観測対象として保持
- 結果をpaper Block AttnResへ帰属しない
- semantic修正は禁止。C003で許可されたimport wiring修正だけを認める

## 5. Tiny deterministic trace

- seed `17`
- CPU FP32、batch 1
- local synthetic hidden tensor
- 少なくとも2つのblock boundaryを含む最小depth
- PB1/CR1で同一shapeと入力bytesを使用
- input SHA256を保存
- stochastic operationを無効化

各routing eventで保存:

- variant、event、layer、sublayer role、block index
- boundary before/after
- partial reset before/after
- source index、source role、source creation event
- source tensor checksum
- duplicate checksum group
- raw logit、recency-bias contribution
- raw probability
- checksum-collapsed semantic probability
- raw/semantic entropy
- raw/semantic effective source count
- weighted output checksum

## 6. Source identity規則

- identityは生成eventとroleで定義する
- 同一生成eventのtensorを複数entryへ登録しない
- checksum重複とidentity重複を別々に報告する
- completed sourceへappend済みのpartial stateを、resetなしでcurrent partialへ再利用しない
- CR1では違反を修正せず観測結果として記録する

## 7. 判定

### PB1 PASS

- 全boundaryでreset
- unintended identity duplicateがゼロ
- source roleが事前登録どおり
- recency biasとoptional gateが不存在
- routing probabilityが有限で総和1
- parameter delta `25,600`または完全説明
- save/load後にevent構造とoutputが一致

### PB1 WARN

- checksum重複はあるがidentityが異なり原因を説明可能
- 数値差が登録tolerance内
- instrumentation overheadは大きいが意味論を変えない

### PB1 STOP

- boundary reset欠落
- unintended identity duplicate
- bias/gate混入
- source role不一致
- probability非有限または総和不一致
- parameter deltaを説明不能
- trace取得にmodel equation変更が必要

### CR1

`RAW_DIAGNOSTIC_COMPLETE`または`RAW_DIAGNOSTIC_FAILED`だけを付ける。paper適合PASSは付けない。

## 8. 出力分離

- PB1: `benchmarks/k3_minimal/semantic_trace/paper_block/`
- CR1: `benchmarks/k3_minimal/semantic_trace/candidate_raw/`

variantごとにconfig、state-dict、input、events.jsonl、duplicate groups、routing metrics、save/load check、raw log、summary、checksumsを保存する。

## 9. 実行順序

1. C003 environment stageをPASS
2. environment artifact SHAを固定
3. CR1 traceで公開artifact挙動を記録
4. PB1 traceを実行
5. EがPB1 PASS/WARN/STOPを判定
6. PB1 PASS後のみ、別amendmentでfull-model resource測定を検討

本C004ではdataset、tokenizer、optimizer、training、full-model timing、量子化を許可しない。

## 10. Evidence boundary

PB1 PASSはsource transitionの論文準拠だけを示す。品質改善、CPU軽量性、量子化耐性、3-seed安定性、1GB目標達成は示さない。
