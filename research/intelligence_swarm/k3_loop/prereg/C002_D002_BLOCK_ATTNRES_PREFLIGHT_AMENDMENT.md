# C002 — D002 Block AttnRes executable preflight amendment

Date: 2026-07-28
Role: K3-C
Branch: `research/intelligence-swarm-reconstruction-001`
Status: **事前登録完了 / D002のみ実行許可 / S1以降は禁止継続**
Supersedes: C001のS0呼び出し、save/load判定、operator attribution schema、後続S1のglobal batch実現方法のみ
Preserves: C001のモデル、optimizer、sequence length、token budget、seed、単一変更ablation、Pareto基準

## 1. 今回の単一目的

D001で、非公式候補 `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6` のtraining entry pointは、無条件NCCL/DDP、未固定streaming data、未実装のglobal batch契約により、C001のS0をそのまま実行できないことが判明した。

本amendmentは新しいarchitectureや学習実験を追加しない。FineWeb-Eduへアクセスせず、standalone non-training harnessでB0/A1の実装経路だけを検証する。

D002の問いは次の1つに限定する。

> 同一config・同一synthetic input・同一kernel条件で、B0とA1を残差経路だけの差分としてinstantiateし、forward/backward/save-load、routing gradient、資源計測、operator attributionを再現可能に取得できるか。

D002は品質改善、学習効率、知能能力、採用可否を判定しない。

## 2. 固定条件

### B0

- Qwen3-style dense PreNorm decoder
- hidden size: 512
- layers: 12
- attention heads: 8
- KV heads: 4
- head dim: 64
- intermediate size: 1536
- vocabulary size: 151,936
- tied embeddings: true
- mode: `baseline`

### A1

B0との差分は以下だけ。

- mode: `block`
- Block AttnRes blocks: `N=4`
- static zero-initialized pseudo-query
- parameter-free RMS-normalized routing keys
- recency bias initialization: 0
- null source: false

KDA、MoE、Delta-V、Full AttnRes、Low-Rank AttnRes、data curriculum、post-trainingは禁止。

## 3. standalone harness契約

Dはcandidate training entry pointを呼ばず、`benchmarks/k3_minimal/preflight/` 配下にstandalone harnessを作る。

禁止事項:

- FineWeb-Eduまたは他の外部dataset取得
- tokenizer network downloadへの依存
- NCCL/DDP初期化
- model semanticsを変える互換patch
- B0/A1で異なるcompile、kernel、thread、dtype条件
- trace取得のためのarchitecture変更

許可事項:

- candidate repositoryのmodel module import
- config object生成
- local synthetic integer token tensor生成
- resource logger/profiler hook追加
- 互換性のための最小import修正。ただしexact diff、目的、source SHA256を保存すること

### 実行予定command

実ファイル名はDが固定するが、manifest上の標準interfaceは次とする。

```bash
python benchmarks/k3_minimal/preflight/run_d002_attnres_preflight.py \
  --candidate-root "$CANDIDATE_ROOT" \
  --output-dir benchmarks/k3_minimal/preflight/D002 \
  --seed 17 \
  --device cpu \
  --dtype float32 \
  --threads 1 \
  --warmup 5 \
  --repeats 20
```

GPUが利用可能な場合もCPU runを省略してはならない。GPUは追加証拠として同じinput checksumで実行する。

## 4. 環境固定

D002開始時に以下を保存する。

- Python version
- PyTorch、Transformers、Safetensors、NumPy versions
- CUDA/cuDNN/NCCL versions（存在する場合）
- OS/kernel、CPU model、physical/logical cores
- BLAS/OpenMP backend
- `torch.get_num_threads()` / interop threads
- eager/compile状態
- deterministic algorithms設定
- candidate repository commit、dirty diff、対象source SHA256
- harness SHA256
- `pip freeze`とSHA256

D002は環境を自動選択してはならない。resolved versionを結果へ記録する。instantiate不能の場合は、互換versionを1回だけ明示的に変更できる。2回目の環境探索は禁止し、Path-STOP候補とする。

## 5. 固定synthetic input

network tokenizerを使わず、seed 17の決定的integer tensorを生成する。

必須cases:

- `(batch=1, sequence=1)`
- `(1,128)`
- `(1,512)`
- `(1,2048)`

各caseで:

- token rangeは`[0, vocab_size)`
- `input_ids` raw bytes SHA256
- shape、dtype、min、max
- B0/A1へ渡したtensorのstorage/data checksum一致

を保存する。

forward/backward/save-load gateは最低`(1,128)`で実行する。メモリ不足時のみ`(1,32)`へ縮小できるが、その理由と失敗logを保存し、Path-WARN以上にはしない。

## 6. architecture差分gate

instantiate後に次を機械可読で比較する。

- serialized config JSON
- config key diff
- parameter names、shape、dtype、requires_grad
- state_dict key diff
- module class tree diff
- total/active parameters
- unquantized serialized bytes

期待値:

- B0 parameters: `115,554,304`
- A1 parameters: `115,578,904`
- difference: `24,600`

許容diffはAttnRes routing query、routing RMSNorm、routing bias、およびそれらを保持するresidual-path moduleだけ。attention、MLP、embedding、LM head、normalization本体のshape/key差は即Path-STOP候補。

## 7. forward/backward gate

seed 17、同一inputでB0/A1を別processまたは完全再初期化して実行する。

- optimizer: AdamW
- learning rate: `6e-4`
- betas: `(0.9, 0.95)`
- epsilon: `1e-8`
- weight decay: `0.1`
- gradient clipping: 1.0
- 1 optimizer step

D002は品質比較をしないため、B0/A1の初期loss差に閾値を置かない。次だけを要求する。

- logits有限
- loss有限
-全gradient有限
- optimizer step後parameter有限
- A1の全routing parameterにgradient tensorが存在
- routing gradient normが厳密に0ではない

zero-initialized pseudo-queryにより特定routing parameterが数学的に初回0-gradientとなる場合、Dは式と実traceを保存し、2回目のoptimizer stepで非ゼロ化するかを一度だけ確認できる。2 step後も構造的0ならPath-STOP候補。

## 8. save/load equivalence

B0/A1それぞれについて、optimizer step前とstep後のcheckpointを保存し、fresh process相当でreloadする。

比較対象:

- state_dict key集合
- parameter checksum
- fixed input logits

許容誤差:

- CPU FP32: `max_abs <= 1e-6` かつ `max_rel <= 1e-5`
- CPU BF16/FP16またはGPU BF16/FP16: `max_abs <= 5e-3` かつ `max_rel <= 5e-2`

`torch.equal`結果も記録するが、合否は上記dtype別閾値で判定する。閾値超過、missing/unexpected keys、config再構成差はPath-STOP候補。

## 9. B002 operator attribution

CPUではthread数を固定し、各caseでwarmup 5回以上、measurement 20回以上を行う。median/p95とraw samplesを保存する。

必須測定:

- full B0 forward
- full A1 forward
- full B0 forward+backward
- full A1 forward+backward
- source list traversal control
- source collect/stack/layout
- RMSNorm
- routing score dot/einsum
- softmax
- weighted sum/einsum
- complete routing event
- no-op Python control

routing eventごとに次を保存する。

- layer/sublayer/event id
- `M,d,S`
- source/output shape
- stride
- contiguous flag
- activation/parameter/score dtype
- source count
- temporary tensor numel/bytes
- profiler operator name、self CPU time、CPU total time、call count、input shape（取得可能な範囲）

導出値:

- A1/B0 forward overhead
- A1/B0 forward+backward overhead
- layout、norm+score、softmax、mix、unattributed/framework share
- peak RSS ratio
- temporary bytes/token

## 10. 資源計測

必須:

- process peak RSS
- routing前後RSS delta
- peak VRAM（GPU run時）
- model instantiate wall time
- forward median/p95
- backward median/p95
- save/load wall time
- serialized checkpoint bytes
- source/config/input/output/environment checksums

D002ではCPU generation speed、INT8/INT4量子化、FineWeb validationを実施しない。それらはS1以降の別gateであり、本preflightへ混ぜない。

## 11. machine-readable result schema

結果は`benchmarks/k3_minimal/preflight/D002/result.json`へ保存し、最低限次を持つ。

```json
{
  "schema_version": 1,
  "id": "D002_block_attnres_executable_preflight",
  "status": "PASS|WARN|STOP",
  "seed": 17,
  "environment": {},
  "source": {},
  "input_cases": [],
  "models": {
    "B0": {},
    "A1": {}
  },
  "config_diff": {},
  "parameter_diff": {},
  "gradient_gate": {},
  "save_load_gate": {},
  "operator_attribution": {},
  "resources": {},
  "checksums": {},
  "warnings": [],
  "failures": []
}
```

必須artifact:

- `environment.json`
- `pip_freeze.txt`
- `candidate_source.sha256`
- `candidate_patch.diff`（patch時のみ）
- `harness.sha256`
- `input_manifest.json`
- `config_B0.json`
- `config_A1.json`
- `parameter_diff.json`
- `module_tree_diff.json`
- `gradient_report.json`
- `save_load_report.json`
- `operator_trace.jsonl`
- `resource_report.json`
- `raw.log`
- `checksums.sha256`
- `result.json`

## 12. PASS/WARN/STOP

### PASS

すべてを満たす。

- instantiate成功
- residual-only diff成立
- expected parameter count一致
- finite forward/backward/optimizer step
- 全routing parameterが2 step以内に有限非ゼロgradient
- save/load閾値内
- required trace/resource/checksum保存完了
- A1 forward overhead <10%
- peak RSS ratio <1.10
- dtype/layoutの想定外変換なし

PASSはS1許可ではない。Eが結果を確認し、CがS1/data contractを別途修正した後に限り準備へ進む。

### WARN

実行可能で基本gateを満たすが、以下のいずれか。

- `layout + framework` share >=50%
- A1 forward overhead >=10%
- peak RSS ratio >=1.10
- unexpected dtype/layout conversion
- required `(1,2048)`だけが資源制約で実行不能
- FP32以外でのみsave/load閾値内

WARNは品質失敗ではない。Eがtraining-onlyまたはfusion-dependent候補への狭義化を判断する。

### STOP

一度の明示的な最小互換修正後も以下のいずれか。

- instantiate不能
- residual以外のmodel semantics差分
- expected parameter count不一致を説明不能
- routing gradient欠落、非有限、2 step後も構造的0
- save/load閾値超過
-同一input/kernel/dtype条件を維持不能
- resource/trace/checksumを保存不能
-実行に未登録architecture変更が必要

STOPはこの非公式implementation pathだけの棄却であり、Block AttnRes仮説全体の棄却ではない。

## 13. 後続S1 global batch契約

D002後もS1は未許可。将来EがS1準備を許可した場合、candidateの未使用`--batch_size`には依存せず、次を満たすadapterまたは独立training loopを事前に固定する。

`global_sequences_per_step = micro_batch_sequences_per_rank * world_size * gradient_accumulation_steps = 64`

各optimizer stepで、全rankのsequence countとtoken countをassertし、B0/A1で同一token manifest順序を使う。world size変更時はgradient accumulationを再計算し、nominal token budgetを変えない。S1 commandとbatch realizationは別amendmentで固定する。

## 14. Dへの次の実行可能manifest

- `benchmarks/k3_minimal/manifests/D002_block_attnres_preflight.yaml`

このmanifestだけが次に実行可能である。C001のS1/S2/S3 commandは引き続き無効・禁止とする。
