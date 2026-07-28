# C007 — Portable Environment Gate Preregistration

Date: 2026-07-29
Role: K3-C experiment specification
Status: preregistered; environment-only execution may begin after the matching manifest is present

## 1. Single authorized candidate

The only candidate authorized by this preregistration is one portable, non-GitHub-Actions, environment-only replay of the fixed Block AttnRes candidate dependency/import gate.

This is not a model experiment. It must not instantiate B0, PB1 or CR1, execute forward/backward, download a dataset/tokenizer/checkpoint, train, benchmark, generate text or quantize.

The fixed scientific source snapshot is:

- repository: `ikuto-yamaguchi/python`
- canonical branch: `research/intelligence-swarm-reconstruction-001`
- source commit: `9edf4c7143ff1d62685ed893352df7a32090fe1e`
- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official reference: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`

The source commit intentionally precedes C007. C007 and its manifest are control-plane evidence and must be acquired separately by immutable Git blob identity. No model or environment source may silently move to a later branch tip.

## 2. Purpose and hypothesis

Hypothesis:

> A self-contained portable bundle can reproduce the exact canonical/dependency/import contract on a Python 3.11 CPU substrate while independently closing source identity, dependency identity, authorization isolation, module-origin identity, platform provenance and artifact transport.

An `ENV_PASS` only establishes that a separately preregistered semantic trace may be considered. It is not quality, speed, memory, quantization, scale or Pareto evidence.

## 3. Normative inputs

The run must receive all of the following as explicit immutable inputs:

- canonical repository URL
- canonical branch name
- full 40-character source commit
- C003 manifest path and expected Git blob SHA `5677b3ec00d7e5d8f56fce1fb96248d6bf680dd9`
- C004 manifest path and expected Git blob SHA `3814f9ef98ec10b83a4bf387302d1246cd8803d6`
- C007 prose path and its Git blob SHA resolved from the commit that created this file
- C007 manifest path and its Git blob SHA resolved from the commit that created the final manifest
- historical C006 manifest path and expected Git blob SHA `880e977f67ae093305ff517716aaa86389db17b3`; C006 is context only and cannot override C007
- environment runner path `benchmarks/k3_minimal/preflight/d003_gha_environment.sh`, expected historical blob SHA `f48040ba5cdbf0bf71343391ab132d8adbbe96c0`
- environment probe path `benchmarks/k3_minimal/preflight/d003_environment_probe.py`, expected historical blob SHA `e85ca24025ef0921d34851dd62f9740a6a1447da`
- attempt number, initially `1`
- output directory

D may add a thin portable launcher at `benchmarks/k3_minimal/preflight/d008_portable_environment.sh` only to map explicit CLI inputs into the existing environment runner/probe. It may not contain dependency substitutions, model code, model imports beyond the registered import probe, semantic patches, architecture parameters or automatic next-stage logic. Its Git blob SHA and byte SHA256 must be recorded before execution.

## 4. Acquisition modes

Exactly one acquisition mode must be selected and recorded.

### 4.1 Online Git mode

- fetch the canonical branch and exact source commit from the recorded remote;
- prove the source commit is reachable from the canonical branch at acquisition time;
- checkout the exact source commit in detached HEAD state;
- reject branch-tip execution;
- reject dirty or untracked files before and after the run.

### 4.2 Offline Git-bundle mode

- use a Git bundle containing the canonical branch ref and exact source commit;
- record the bundle SHA256 and byte size;
- verify the bundle and prove the commit is reachable from its archived canonical ref;
- checkout detached and apply the same clean-tree checks.

A plain source directory, ZIP without Git reachability evidence or copied workspace is not admissible.

## 5. Source and file identity gate

Before dependency installation, the run must verify and save:

- requested branch, requested commit and actual checkout commit;
- canonical-ref reachability proof;
- detached HEAD or exact-content mode;
- `git status --porcelain=v1 --untracked-files=all` is empty;
- no unresolved submodule;
- no unresolved Git LFS pointer in any executed or parsed file;
- repository remote URL;
- Git version;
- for C003, C004, C007 prose, C007 manifest, historical C006, runner, probe and portable launcher: repository path, Git blob SHA, byte SHA256 and byte size;
- no file is read from outside the verified repository except dependency artifacts and the selected Git bundle.

Any mismatch is `ENV_PROTOCOL_FAIL`, not a retry.

## 6. Exact dependency contract

The selected substrate must provide:

- Python `3.11.x`; exact patch and executable path recorded;
- a single exact CPU PyTorch build satisfying the fixed Transformers snapshot; version and wheel/source hash recorded;
- Transformers source exactly at commit `42791a34fdeae197f60f11ace3807c81f44b0729`;
- exact tokenizers version selected by the resolver and all transitive versions/hashes;
- installer and resolver versions;
- package-index URL or offline wheelhouse origin;
- resolver command and full resolver report;
- `pip freeze --all`;
- `pip check`;
- SHA256 and byte size for every wheel, sdist, Git archive or locally supplied package.

Editable installs are prohibited unless the editable source tree is itself clean, commit-bound, archived and included in both checksum closures. Silent substitution with a similar public API or another Transformers release is prohibited.

## 7. Import and module-origin gate

The probe may import required modules and symbols but must not instantiate B0, PB1 or CR1.

It must save:

- `sys.path` in order;
- `PYTHONPATH` and import-related environment variables;
- package location for Python, torch, transformers, tokenizers and safetensors;
- required module names and imported source file paths;
- SHA256 and byte size of each imported Python source file used by the required symbols;
- import success/failure and exception traceback;
- candidate source path and SHA256;
- proof that imported Transformers internals originate under the fixed installed Transformers tree rather than an external shadow path.

A successful import from an unverified or shadowed path is `ENV_PROTOCOL_FAIL`.

## 8. Authorization closure

The following fields must be emitted in machine-readable form and all must be `false`:

- `model_execution_authorized`
- `semantic_trace_authorized`
- `training_authorized`
- `dataset_download_authorized`
- `tokenizer_download_authorized`
- `checkpoint_download_authorized`
- `quantization_authorized`
- `automatic_next_stage`

The portable launcher must fail closed if an unregistered model-stage command or automatic continuation is detected.

## 9. Platform provenance

The archive must record:

- OS release and kernel;
- architecture and endianness;
- CPU model, visible logical CPUs and ISA flags;
- total RAM and cgroup/container memory limits;
- virtualization/container indicators;
- libc version;
- locale and timezone;
- thread-related environment variables;
- network mode and whether dependencies came from online or offline sources.

These records do not authorize resource comparison. No CPU latency or RSS delta may be interpreted from this environment-only run.

## 10. Deterministic evidence layout

The output directory must contain at least:

- `classification.json`
- `inputs.json`
- `authorization.json`
- `source_identity.json`
- `file_identity.json`
- `platform.json`
- `python_environment.json`
- `resolver_report.json`
- `pip_freeze.txt`
- `pip_check.txt`
- `dependency_checksums.json`
- `import_matrix.json`
- `module_origins.json`
- `replay_command.txt`
- `command_transcript.log`
- `stdout.log`
- `stderr.log`
- `checksums.sha256`

`checksums.sha256` must cover every evidence file except itself and the outer archive. Entries must be sorted by repository-neutral relative path.

The evidence directory must then be archived deterministically. The archive SHA256 and byte size must be written to a separate sibling record that is not packed into the archive. Archive creation command and tool version must be saved.

## 11. Replay command

The registered command form is:

```bash
bash benchmarks/k3_minimal/preflight/d008_portable_environment.sh \
  --repository-url https://github.com/ikuto-yamaguchi/python.git \
  --canonical-branch research/intelligence-swarm-reconstruction-001 \
  --canonical-commit 9edf4c7143ff1d62685ed893352df7a32090fe1e \
  --manifest benchmarks/k3_minimal/manifests/C007_portable_environment_gate.yaml \
  --attempt 1 \
  --output benchmarks/k3_minimal/preflight/d008_artifacts/attempt-1
```

D must save the exact executed command after shell quoting. Changing dependency pins, source commit, authorization flags or evidence schema requires a new preregistration.

## 12. Retry and stop boundary

Only one unchanged retry is allowed, and only when all pre-network identity gates passed and the run then encountered a clearly transient DNS, package-index, source-host or artifact-write service failure.

No retry is allowed for identity mismatch, dirty tree, shadow import, missing checksum, authorization violation, unsupported Python version, dependency conflict or semantic/API mismatch.

## 13. Result classes

- `ENV_PASS`: all source, file, dependency, import-origin, authorization, platform and inner/outer artifact gates pass.
- `ENV_RETRY`: one transient post-identity network/service failure; one unchanged retry allowed.
- `SUBSTRATE_STOP`: no available substrate can provide Python 3.11, required source/dependency access and persistent artifact output.
- `ENV_PATH_STOP_PENDING_AMENDMENT`: valid substrate and provenance reveal a fixed non-transient dependency/import mismatch before any patch is preregistered.
- `ENV_PATH_STOP`: one separately preregistered API-wiring-only patch still requires semantic change or leaves provenance incomplete.
- `ENV_PROTOCOL_FAIL`: any identity, clean-tree, allowlist, authorization, module-origin, checksum or archive violation.

None of these outcomes alone adopts or rejects Block AttnRes.

## 14. D008 handoff

D may now do exactly one of the following:

1. create the thin portable launcher conforming to this document, record its identities, and execute one environment-only attempt on a compliant Python 3.11 CPU substrate; or
2. if no compliant substrate is available, write one `SUBSTRATE_STOP` result with the inspected substrate facts and the exact replay command, then stop repeating substrate audits.

D must not touch or dispatch the quarantined default-branch workflow.

## 15. Model experiment fields intentionally not applicable

Because model execution is prohibited, the following are registered as `not_applicable_environment_only`, not zero and not measured:

- seeds `17/29/43`;
- model bytes;
- total/active parameters;
- training wall time and tokens/sec;
- peak RSS/VRAM comparison;
- CPU inference latency and generation tokens/sec;
- quantized size;
- language modeling, knowledge, reasoning, long-context and instruction-following scores;
- routing collapse and convergence stability.

A later semantic or training experiment must separately preregister these fields, same-parameter/same-active-compute/same-token-budget comparisons and the multi-axis Pareto decision.

## 16. Decision

C007 closes the portable environment evidence contract only. The next executable work is one D008 portable environment-only attempt. PB1/CR1 semantic trace, training, quantization and all capability claims remain prohibited.