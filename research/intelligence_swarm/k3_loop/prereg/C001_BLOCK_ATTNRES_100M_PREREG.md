# C001 — 100M級 Block Attention Residuals 最小再現 preregistration

Date: 2026-07-28
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **事前登録完了 / Dはpreflightとbaseline smokeから開始**

## 1. 選定

B001の単一ボトルネックだけを扱う。候補は標準Qwen3系dense PreNorm decoderと、残差経路だけをBlock AttnResへ置換したablationである。KDA、MoE、Delta-V、特殊gate、data curriculum、post-trainingは導入しない。

公開再実装候補は `wdlctc/open-attention-residuals` commit `83d2b8de82c2fbb981c7decca67d13d9db348da6` に固定する。ただし著者公式実装ではないため、再現結果は「非公式実装の独立再現」と明記する。公式 `MoonshotAI/Attention-Residuals` は説明資料のみで、training baselineとしては使用しない。

## 2. 実験条件

### B0 — 標準baseline

- implementation mode: `baseline`
- decoder: Qwen3 dense PreNorm
- hidden size: 512
- layers: 12
- attention heads: 8
- KV heads: 4
- head dim: 64
- SwiGLU intermediate size: 1536
- max training sequence: 2048
- tied input/output embedding: true
- tokenizer family: `Qwen/Qwen3-0.6B`
- vocabulary in candidate code: 151,936

### A1 — 単一変更ablation

B0からの変更は以下だけとする。

- implementation mode: `block`
- Block AttnRes blocks: `N=4`
- static pseudo-query
- zero initialization
- parameter-free RMS normalization keys
- recency bias initialization: 0
- null source: false
- gate variant: candidate implementationのpaper-like default以外を禁止

`delta`、`delta_block`、`delta_v`、`full`、`first_layer`、`pre_gated`は本runの比較対象外。

## 3. 再現性固定

Dのpreflightは学習前に次を機械可読で記録し、1つでも未固定ならfull runを開始しない。

- source repository and commit
- Python、PyTorch、Transformers、Datasets、CUDA/cuDNN/NCCL versions
- `pip freeze` digest
- tokenizer resolved revision / local snapshot commit / file SHA256
- FineWeb-Edu resolved dataset revision、config、streaming shard listまたは取得可能な同等manifest、各参照のSHA256
- model config JSON and SHA256
- baseline/ablation exact parameter count and serialized unquantized bytes
- GPU/CPU/RAM情報
- git dirty state

候補コードはdataset streamingとshuffle bufferを使うため、単にdataset名とseedを固定しても完全再現とはみなさない。shard順序・resolved revisionを固定できない場合は、同一の固定ローカルtoken shardをB0/A1双方へ入力するadapterを**再現性修正**として許可する。ただしmodel forward、optimizer、scheduleは変更禁止。

## 4. 学習予算

### Stage S0 — build/preflight

- seed: 17
- forward/backward 1 step
- parameter数、loss有限性、gradient有限性、checkpoint save/load一致を検査

### Stage S1 — baseline smoke

- B0のみ
- seed: 17
- 100 optimizer steps
- global effective batch: 実機world sizeに依存せず64 sequences/stepへ合わせる
- sequence length: 2048
- nominal tokens: `100 * 64 * 2048 = 13,107,200`
- 合格後のみA1 smokeを同条件で実行

### Stage S2 — paired pilot

- B0/A1
- seed: 17
- 2,000 optimizer steps
- nominal tokens: 262,144,000/condition
- pilotは採用判定に使わず、loss曲線、routing分化、資源悪化、full run実行可能性を判定する

### Stage S3 — preregistered full comparison

- B0/A1
- seeds: `17 / 29 / 43`
- 20,000 optimizer steps
- global effective batch: 64 sequences/step
- sequence length: 2048
- nominal token budget: 2,621,440,000/seed/condition
- AdamW: lr `6e-4`, betas `(0.9,0.95)`, eps `1e-8`, weight decay `0.1`
- warmup: 1,000 steps
- cosine decay to `6e-5`
- gradient clipping max norm: 1.0
- dtype: BF16 training、routing softmax/reductionは最低FP32 accumulation

計算資源不足でS3が現実的でない場合、S2までの結果をfull evidenceとして昇格させない。C/Eへ戻し、token budgetを事後変更せず別preregistrationを作る。

## 5. 公平性

主要比較はequal-token-budgetかつ同一base architectureで行う。AttnRes追加parameterは別途報告し、以下を併記する。

1. raw B0 vs A1
2. parameter-matched control: B0の幅/FFNを恣意的に変更せず、A1追加parameterが総数の0.1%未満なら差を注記して同等parameter近似とする
3. measured-active-compute: profilerでforward/backward FLOPsまたは演算時間を測り、同一loss到達までのwall time/token数を比較

A1にだけgradient checkpointing、compile、FlashAttention、fused optimizerを適用してはならない。

## 6. 評価

### 必須品質指標

- held-out FineWeb-Edu固定token shardのNLL / perplexity
- 同一token位置・同一batchでのloss差
- loss-to-compute、loss-to-wall-time曲線

### 小規模で測定可能な複数軸

S2通過後、同一checkpoint stepで以下を固定version・固定few-shot設定により測る。

- language modeling: WikiText-2 perplexity
- commonsense/knowledge proxy: HellaSwag、LAMBADA
- reasoning proxy: ARC-Easyまたは同等の小規模固定subset
- long-context proxy: 2K内で位置別NLL（前半/後半）

この規模のモデルで指示追従能力は主張しない。instruction tuningを追加しない。

### Routing診断

- routing entropy by sublayer/token
- latest/current block mass
- source top-1 frequency
- block-source cosine similarity
- pseudo-query norm
- hidden-state RMS by depth
- gradient norm by depth
- seed間routing一致度

## 7. 資源・CPU・量子化

全conditionで必須:

- model file bytes
- total/active parameters
- peak RSS and peak VRAM
- train wall time and tokens/sec
- checkpoint load RSS
- CPU batch=1 prefill latency: prompt 128/512/2048 tokens
- CPU batch=1 decode: prompt 128、generate 128、median/p95、tokens/sec
- eager implementationを先に測定。最適化/fusionは別実験で混ぜない

量子化:

1. FP32/FP16またはBF16参照
2. weight-only INT8
3. weight-only INT4（利用可能な同一backend）

routing query、RMS reduction、softmaxは初回weight-only比較では高精度維持。activation/routing低bit化は別preregistrationまで禁止。量子化前後でvalidation loss、routing KL、top-source agreement、CPU速度、model bytesを記録する。

## 8. 停止・失敗規則

即時停止:

- B0が100-step内にloss非有限、gradient非有限、またはsave/load不一致
- B0/A1でdata token streamが一致しない
- architecture差分が残差経路以外へ波及
- A1でrouting parameterへgradientが流れない
- resource loggerがRSS/VRAM/wall timeを保存できない

S1でA1を停止:

- peak VRAMがB0比25%以上悪化し、原因が設定不一致でない
- step timeがB0比30%以上悪化
- routingが全stepで完全一様のままか、単一sourceへ数値collapse

S2後のfull-run不許可:

- validation loss改善が測定noise内かつstep timeが10%以上悪化
- source cosineがほぼ1でroutingが識別的でない
- seed 17 pilotで再現不能なdata/environment driftがある

成功判定はB001を継承する。

- 採用候補: 3 seed平均で品質改善し、同一loss compute 10%以上削減、またはCPU decode悪化3%以下・RSS悪化5%以下。量子化後に改善の70%以上保持
- 追加検証: 品質改善はあるがCPU悪化3–10%またはseed分散大
- 狭義化: 深い/大きい条件でのみ有効、deployment Paretoは負
- 棄却: 3 seed平均改善なし、CPU latency 10%以上悪化して相殺不能、routing collapse、量子化で改善消失

## 9. Dへの実行順

1. manifest検証とsource pin
2. tokenizer/data revision固定
3. B0/A1 config生成とexact parameter count取得
4. S0
5. B0 S1
6. A1 S1
7. paired S2
8. EによるS3開始判定

現時点で許可されるのは1〜6まで。S2/S3は固定dataset manifestとB0 smoke合格が必要である。
