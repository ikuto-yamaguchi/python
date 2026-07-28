# C006 — Default-branch thin dispatcher amendment

Date: 2026-07-29
Owner: K3-C
Canonical branch: `research/intelligence-swarm-reconstruction-001`
Default branch: `main`

## 1. Purpose and single authorized candidate

D006 established `ROUTE_STOP` for the canonical-branch-only push route: ordinary branch pushes were accepted and other workflows ran, but the newly introduced environment workflow was not registered or started. This amendment does not change the model, candidate, baseline, dependency target, semantic trace, thresholds, or scientific hypothesis. It preregisters exactly one replacement execution substrate:

> a minimal `workflow_dispatch` launcher stored on `main` that receives immutable canonical provenance inputs, checks out the exact canonical commit in detached state, and runs only the already-registered D003 environment/import probe.

The only D work authorized after this amendment is implementation and one environment-only dispatch of this thin launcher. B0, PB1, and CR1 model construction remain forbidden.

## 2. Fixed references

- repository: `ikuto-yamaguchi/python`
- canonical branch: `research/intelligence-swarm-reconstruction-001`
- default branch: `main`
- environment contract: `benchmarks/k3_minimal/manifests/C003_d003_gha_environment_gate.yaml`
- semantic-trace contract, not authorized in this run: `benchmarks/k3_minimal/manifests/C004_d003_variant_semantic_trace.yaml`
- C006 manifest: `benchmarks/k3_minimal/manifests/C006_default_branch_thin_dispatcher.yaml`
- environment script: `benchmarks/k3_minimal/preflight/d003_gha_environment.sh`
- environment probe: `benchmarks/k3_minimal/preflight/d003_environment_probe.py`
- candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`
- official reference: `MoonshotAI/Attention-Residuals@85e22310fe5ee860b4a023de312d791de8a5a5e6`
- Transformers: `42791a34fdeae197f60f11ace3807c81f44b0729`

## 3. Dispatcher thinness contract

The default-branch change may add exactly one launcher workflow and no model or experiment implementation. The launcher must not contain or duplicate:

- model configuration or parameter values
- B0, PB1, or CR1 implementation
- routing, reset, boundary, recency-bias, or gate logic
- compatibility or semantic patch
- training, evaluation, benchmark, quantization, dataset, tokenizer, or checkpoint logic
- any automatic continuation to another workflow or model stage

The launcher may only:

1. validate immutable dispatch inputs;
2. checkout the exact requested canonical commit in detached state;
3. verify branch ancestry, requested SHA, clean tree, and registered file blob identities;
4. establish Python 3.11;
5. invoke the exact canonical environment script;
6. collect and upload the preregistered environment artifacts;
7. emit a machine-readable route/environment classification.

Any other executable step is an allowlist violation and yields `ENV_PROTOCOL_FAIL`.

## 4. Required immutable dispatch inputs

The workflow must require all of the following non-empty inputs:

- `canonical_branch`
- `canonical_commit_sha` — full 40-hex commit SHA
- `c003_manifest_blob_sha`
- `c004_manifest_blob_sha`
- `c006_manifest_blob_sha`
- `environment_script_blob_sha`
- `environment_probe_blob_sha`
- `attempt` — `1` normally, `2` only for one unchanged transient retry

The workflow implementation commit on `main` and its workflow blob SHA must also be captured from runtime provenance, even though they are not canonical-science inputs.

## 5. Identity and checkout gates

Before dependency resolution, all gates below must pass:

1. `canonical_branch` equals `research/intelligence-swarm-reconstruction-001`.
2. `canonical_commit_sha` is a full 40-hex SHA and resolves in the repository.
3. The requested commit is reachable from the canonical branch at dispatch time.
4. Checkout uses the exact input SHA, not the branch tip, and records detached `HEAD`.
5. `git rev-parse HEAD` equals `canonical_commit_sha`.
6. `git symbolic-ref -q HEAD` must fail, proving detached state.
7. `git status --porcelain` is empty before and after the environment probe, except for the registered output directory, which must be excluded from the source-tree cleanliness check by writing outputs outside the checkout or by an explicit path-scoped check.
8. Git blob SHAs for C003, C004, C006 manifests and the environment script/probe equal the supplied values.
9. The workflow must record SHA256 for the same files in addition to Git blob SHA.
10. No unregistered patch may be applied.

A failure before installation is `ENV_PROTOCOL_FAIL`, not `ENV_RETRY`.

## 6. Authorization contract

Fixed false:

- `training_authorized=false`
- `model_execution_authorized=false`
- `dataset_download_authorized=false`
- `tokenizer_download_authorized=false`
- `checkpoint_download_authorized=false`
- `quantization_authorized=false`
- `semantic_trace_authorized=false`
- `automatic_next_stage=false`

Allowed operations are limited to repository checkout, provenance verification, dependency resolution, import probing, raw-log capture, checksum generation, and artifact upload.

The environment script must not instantiate B0/PB1/CR1, execute forward/backward, allocate model weights, access datasets/tokenizers/checkpoints, run optimizer steps, benchmark model latency, or quantize weights.

## 7. Runtime and dependency contract

- runner provider: GitHub-hosted
- OS: Linux x86_64
- Python: exact resolved `3.11.x`, recorded with executable path and full version
- initial dependency cache: disabled
- PyTorch: exact CPU build resolved from the existing C003 script, recorded
- Transformers: exact Git commit `42791a34fdeae197f60f11ace3807c81f44b0729`
- candidate: detached checkout at `83d2b8de82c2fbb981c7decca67d13d9db348da6`
- compatibility patch: none during the first attempt

A future API-wiring-only patch is not automatically authorized by this run. If exact imports fail for a non-transient reason, D must record `ENV_PATH_STOP_PENDING_AMENDMENT`; C/E must preregister the single permitted patch before another scientific attempt.

## 8. Required import gate

The environment stage must verify and record availability of:

- `create_causal_mask`
- `GradientCheckpointingLayer`
- `merge_with_config_defaults`
- `capture_outputs`
- required Qwen3 internal classes
- the fixed candidate `modeling_attnres` module

Similar or renamed APIs must not be substituted silently.

## 9. Required artifacts

The uploaded artifact must contain at least:

- `dispatch-inputs.json`
- `run-context.json`
- `repository-provenance.json`
- `canonical-file-identities.json`
- `authorization.json`
- `python-environment.json`
- `resolver-report.json`
- `pip-freeze.txt`
- `pip-check.txt` or equivalent raw log
- `dependency-checksums.sha256`
- `required-imports.json`
- `source-and-patch.json`
- raw install, checkout, guard, and import logs
- `D003_GHA_environment_summary.json`
- `route-environment-classification.json`
- `checksums.sha256`

After upload, D must record:

- workflow run ID and attempt
- artifact ID and artifact name
- artifact archive size
- downloaded artifact ZIP SHA256
- canonical commit SHA
- default-branch dispatcher commit SHA and workflow blob SHA

An import-success run missing any mandatory provenance or archive checksum is `ENV_PROTOCOL_FAIL` and is inadmissible.

## 10. Result classification

### `ENV_PASS`

All route, identity, authorization, dependency, import, artifact, and archive-checksum gates pass. This authorizes only E review and consideration of a separately dispatched C004 semantic trace. It does not authorize model execution automatically and is not quality or efficiency evidence.

### `ENV_RETRY`

The workflow started and passed all pre-network identity/authorization gates, but failed because of a clearly transient GitHub Actions, runner, DNS, package-index, Git transport, or network service failure. One unchanged retry with `attempt=2` is allowed. Inputs, dispatcher commit, canonical SHA, manifests, scripts, dependency commands, and authorization must remain identical.

### `ROUTE_STOP_DEFAULT_BRANCH`

Repository permissions or policy prevent introducing the minimal launcher on `main`, or a correctly registered launcher on `main` cannot be dispatched. This stops the currently available GitHub Actions route only.

### `ENV_PATH_STOP_PENDING_AMENDMENT`

The route runs and provenance is valid, but fixed dependencies or imports fail non-transiently before any preregistered compatibility patch exists. No retry or patch is allowed until C/E register the single API-wiring-only patch.

### `ENV_PATH_STOP`

After a separately preregistered single API-wiring-only patch, exact dependencies/imports still require semantic changes or complete provenance cannot be produced. This stops the current third-party implementation path, not Block AttnRes as a mechanism.

### `ENV_PROTOCOL_FAIL`

Any branch, SHA, detached-checkout, dirty-tree, file-identity, allowlist, authorization, artifact, checksum, or prohibited-action violation. The run is invalid. It must not be retried without a new amendment that identifies the protocol defect.

## 11. Completion conditions for D007

D007 is complete when exactly one of the classifications above is recorded with raw evidence. For `ENV_PASS`, completion additionally requires artifact ID and downloaded ZIP SHA256. For `ENV_RETRY`, only one unchanged second attempt is permitted. D must update `STATE.md` and `BACKLOG.md` and create machine-readable output under `benchmarks/k3_minimal/preflight/`.

## 12. Carry-forward scientific constraints

This amendment does not change C001/C004 model and semantic contracts:

- B0: 12-layer width-512 Qwen3-family dense PreNorm baseline
- PB1 provisional parameters: `115,579,904`, delta `25,600`
- PB1 geometry: `L_sub=24`, `N=4`, `S=6`, ordered boundaries `[3,6,9,12]`
- source-slot contract: sublayer `84`, final `5`, total `89`
- seeds for later training evidence: `17/29/43`
- PB1 is a minimum semantic/effect-direction pilot and does not match the primary evidence geometry
- PB1 null does not reject the mechanism; PB1 positive does not justify adoption

Dataset, token budget, training stop rules, multi-axis quality evaluation, CPU inference, quantization, and same-budget comparison remain preregistered in C001 for later stages but are not executable under C006.

## 13. Prohibitions

- no additional C005 nonce/path-filter variants
- no broad push or pull-request trigger
- no copying canonical model code to `main`
- no default-branch model implementation
- no mutable branch-tip checkout
- no silent compatibility patch
- no model construction or semantic trace in the environment run
- no automatic transition after `ENV_PASS`
- no quality, efficiency, Pareto, capability, intelligence-principle, high-school-level, or 1GB-target claim from route/environment evidence
