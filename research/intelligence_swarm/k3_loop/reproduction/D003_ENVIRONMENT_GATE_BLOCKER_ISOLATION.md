# D003 Environment Gate — blocker isolation

Date: 2026-07-29  
Branch: `research/intelligence-swarm-reconstruction-001`

## Scope completed in this run

C002で事前登録されたD003のうち、最初の必須段階である **exact dependency / import gate** を実装し、現行実行環境で実行した。

追加artifact:

- `benchmarks/k3_minimal/preflight/d003_environment_probe.py`
- `benchmarks/k3_minimal/preflight/D003_environment_probe_summary.json`

このrunではdataset、tokenizer、checkpoint、optimizer、学習、量子化を一切使用していない。

## Fixed provenance

- candidate repository: `wdlctc/open-attention-residuals`
- candidate commit: `83d2b8de82c2fbb981c7decca67d13d9db348da6`
- candidate model blob SHA: `649aa0067e5b9d0fc2a3cc68784a6794090a26a4`
- required Transformers commit: `42791a34fdeae197f60f11ace3807c81f44b0729`
- result SHA256: `aee26a00ae6b7e6400144dce4c95b57500c3b74b705fb027e40552fda7efe8f3`

候補実装はQwen3部品をinstalled Transformersから直接再利用し、`create_causal_mask`、`GradientCheckpointingLayer`、`merge_with_config_defaults`、`capture_outputs`等の内部APIへ依存するため、単に`transformers>=4.40`を満たすだけでは再現契約にならない。

## Observed environment

- Python: `3.13.5`
- executable: `/opt/pyvenv/bin/python`
- PyTorch: `2.10.0+cpu`
- Transformers: absent
- tokenizers: absent
- safetensors: `0.7.0`
- huggingface_hub: `1.16.1`
- platform: `Linux-6.12.13-x86_64-with-glibc2.41`
- logical CPU count visible to process: `5`

## Gate result

Status: **BLOCKED_ENV**

Blockers:

1. Python `3.13` is not the preregistered Python `3.11.x` runtime.
2. Transformers is absent, so the pinned commit's internal import family cannot be tested.
3. The execution sandbox could not resolve `github.com`, so the missing pinned source/dependencies could not be fetched or installed during this run.

This is an **environment classification**, not a failure of Block AttnRes and not a STOP classification for the candidate implementation path.

Current implementation-path classification remains:

> **Path-WARN / additional verification / not adopted**

## Failure isolation value

D003を曖昧な「依存関係が足りない」で停止させず、次回実行に必要なgateを機械可読化した。

The probe now:

- records Python/PyTorch/package provenance,
- checks every candidate-internal Transformers symbol explicitly,
- records candidate commit and model blob SHA,
- refuses silent API substitution,
- emits a nonzero exit code when the preregistered environment is not satisfied,
- keeps `training_authorized=false` regardless of import success.

## What was not measured

The following D003 completion conditions remain unexecuted:

- exact candidate B0/A1 instantiate
- exact parameter/config/state-dict diff
- fixed-input forward/backward and routing gradients
- save/load tolerance
- fresh-process `AB/BA/AB/BA`
- isolated RSS and wall time
- operator attribution
- T<=512 fit and T=2048 ratio

No quality, training-efficiency, CPU-generation, quantization, or 3-seed claim is permitted.

## Next minimum action

Run the committed probe inside a network-capable Python 3.11 environment, install the pinned Transformers commit and an exact PyTorch build, preserve resolver report and wheel/source hashes, then execute the import gate before attempting model instantiation.

No compatibility patch is authorized until the exact pinned import probe produces a concrete failure. If a patch becomes necessary, C002 permits at most one import/API-wiring-only patch with diff and checksum; semantic, shape, initialization, and forward-equation changes remain prohibited.
