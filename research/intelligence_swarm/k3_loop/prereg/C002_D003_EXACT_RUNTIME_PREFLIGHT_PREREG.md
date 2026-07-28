# C002 — D003 exact-runtime / fresh-process Block AttnRes preflight preregistration

Date: 2026-07-29
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **D003のみ実行許可 / 学習・dataset取得・新規architectureは禁止**

## 1. 目的と単一仮説

C001の候補を変更せず、非公式公開実装 `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6` を、A002で固定したTransformers snapshot上で正確に構築できるかを検証する。

単一仮説:

> B0とA1を残差経路だけの差分として構築し、別fresh process・AB/BA均衡順序・固定synthetic inputで、forward/backward、routing gradient、save/load、条件別RSS、時間、operator attributionを再現可能に測定できる。またD002の2048-token breakpointが測定artifactか実装上のdeployment costかを区別できる。

本runは品質、学習効率、CPU生成速度、量子化、3-seed性能を評価しない。

## 2. 条件

### B0

- Qwen3 dense PreNorm decoder
- hidden size 512
- 12 layers
- attention heads 8
- KV heads 4
- head dim 64
- SwiGLU intermediate size 1536
- vocabulary 151,936
- tied embeddings true
- total/active parameters expected: `115,554,304`

### A1

B0からの許可差分はBlock AttnRes残差経路だけ。

- mode `block`
- AttnRes blocks `N=4`
- static zero-initialized pseudo-query
- parameter-free RMS-normalized routing keys
- recency bias 0
- null source false
- total/active parameters expected: `115,579,929`
- expected delta: `25,625` (`~0.02218%`)

KDA、MoE、Delta-V、Full AttnRes、Low-rank AttnRes、特殊gate、compile/fusionの片側適用を禁止する。

## 3. 環境固定

必須:

- Python `3.11.x` exact patch version
- PyTorch: Transformers snapshotの要求 `>=2.4` を満たす単一exact build
- Transformers git commit `42791a34fdeae197f60f11ace3807c81f44b0729`
- tokenizers: snapshot要求範囲内の単一exact version
- safetensors、huggingface-hub、numpy等の全resolved version
- `pip --report`、`pip freeze`、wheel/source hash、Python executable path
- CPU名、ISA、物理/論理core数、RAM、OS/kernel
- PyTorch thread数、interop thread数、MKL/OpenMP設定

PyTorch/tokenizersのexact versionをCが推測で指定しない。Dがresolver結果をlockし、全hashとimport probeを保存する。別releaseの類似APIへの黙示置換は禁止。

Compatibility patchは最大1件。許可条件:

1. import/API wiringだけを修正する
2. model semantics、tensor shape、initialization、forward equationを変えない
3. unified diff、patch SHA256、変更前後file SHA256を保存する
4. patchなし実行不能のraw logを保存する

## 4. 固定入力

- seed: `17`
- token IDsはlocal synthetic generatorのみ
- dataset/tokenizer download禁止
- vocabulary範囲内のinteger tensor
- cases: `(batch=1, T=1/128/512/2048)`
- model-semantic probe用の最小forward/backward caseはOOMを避ける固定長をmanifestで明示
- 各input tensorのshape、dtype、min/max、raw bytes SHA256を保存
- B0/A1はbitwise同一inputを使用

## 5. 実行順序と反復

B0/A1は同一processで連続比較しない。各measurement cellを別fresh processで実行する。

- order blocks: `AB`, `BA`, `AB`, `BA`
- 各condition/caseでwarmup `10`、measured repetitions `30`
- T=2048が実行時間上限を超える場合も、事後に反復数を片側だけ変更しない。両conditionを同数へ減らし理由を記録する
- CPU affinityとthread設定を固定
- GC状態を記録し、measurement直前に同じ処理を行う
- median、p95、MAD、min/maxを保存

full-modelとrouting microbenchmarkを分離する。

## 6. 必須semantic checks

1. B0/A1 instantiate成功
2. config差分が登録済みAttnRes項目だけ
3. parameter-name差分がrouting関連だけ
4. exact parameter countが期待値と一致
5. forward出力とlossが有限
6. backward gradientが有限
7. 全AttnRes routing parameterに有限かつ非ゼロgradient
8. save/load後logits max absolute difference `<= 1e-6` (FP32 CPU)
9. state-dict key/shape/dtype/checksumを保存

いずれかが失敗した場合、resource Paretoへ進まずSTOP候補とする。

## 7. CPU/operator計測

各Tで以下を個別計測する。

- no-op harness
- Python/list traversal
- source collection
- `stack` / layout / contiguous
- RMSNorm + routing score
- softmax
- weighted source mix
- complete routing event
- B0 full-model forward
- A1 full-model forward

必須記録:

- tensor shape、stride、contiguity、dtype
- source count
- temporary tensor logical bytes
- profiler operator names、call counts、self CPU time、input shapes
- process-isolated peak RSS (`ru_maxrss`に加え可能ならexternal sampler)
- user/system CPU timeとwall time
- allocation evidence（利用可能な標準profiler範囲。取得不能なら理由を明記し、推測値を実測扱いしない）

D002との整合比較のため、T=1/128/512に線形fitを行い、T=2048の予測値、residual、`actual_2048 / predicted_2048`を機械可読で保存する。

## 8. 判定schema

### Path-PASS

すべて満たす:

- exact runtimeとprovenanceを固定
- residual-only差分、gradient、save/load合格
- timing/RSS/operator証拠がAB/BAで再現
- breakpointが消失、またはoperator/temporary証拠で説明可能
- A1/B0 full-model median time overhead `<10%`
- A1/B0 peak RSS overhead `<10%`

### Path-WARN

semantic checksは合格するが、いずれかを満たす:

- A1 CPU full-model時間またはRSSがB0比 `>=10%`
- stack/layout + framework/list/allocator相当が追加routing時間の `>=50%`
- fresh-processでも `actual_2048 / predicted_2048 >= 2.0`
- order block間の効果方向が不安定で、安定したPareto値を確定できない

この場合はtraining-only候補またはfused-kernel依存候補へ狭義化し、品質仮説は未判定のまま保持する。

### Path-STOP

1回の登録済み最小compatibility patch後も、いずれかが残る:

- import/instantiate不能
- AttnRes以外のsemantic差分
- parameter count不一致を説明不能
- routing gradientなし、非有限、構造的ゼロ
- save/load差 `>1e-6`
- fresh-process条件別resource/operator証拠を保存不能
- 実行のため未登録architecture変更が必要

STOP対象は現在の非公式実装経路であり、Block AttnRes仮説全体ではない。

## 9. 必須artifact

- `environment.json`
- `resolver-report.json`
- `pip-freeze.txt`
- `dependency-checksums.sha256`
- `source-and-patch.json`
- `patch.diff`（patch時のみ）
- `model-config-diff.json`
- `parameter-and-state-dict-diff.json`
- `inputs.json` と input SHA256
- condition別raw logs
- condition別resource JSON
- profiler traces
- `D003_result_summary.json`
- artifact全体の`checksums.sha256`

## 10. Dへの実行許可

許可するのはD003のみ。FineWeb-Edu、tokenizer、checkpointの外部取得、optimizer step、S1/S2/S3、量子化、モデル改変は禁止する。

D003後はEがPath-PASS/WARN/STOPを判断する。Path-PASSでも自動的にS1を開始せず、Cがglobal batch 64を実コード上で保証する別amendmentを作るまで学習禁止とする。
