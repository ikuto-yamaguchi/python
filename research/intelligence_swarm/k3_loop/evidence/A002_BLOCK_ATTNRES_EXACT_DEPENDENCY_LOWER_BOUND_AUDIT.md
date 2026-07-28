# A002 — Block AttnRes exact dependency lower-bound audit

Date: 2026-07-28
Role: K3-A primary-source/public-code audit
Canonical branch: `research/intelligence-swarm-reconstruction-001`
Candidate: `wdlctc/open-attention-residuals@83d2b8de82c2fbb981c7decca67d13d9db348da6`

## Decision

Classification remains **小型化で要再設計 / 追加検証・未採用**.

This run does not audit a new K3 component. It resolves the current P0 dependency bottleneck for D003.

## Finding

The candidate repository declares only:

- `torch>=2.0`
- `transformers>=4.40`
- unpinned `datasets`, `wandb`, and other packages

That declaration is not a valid reproducibility contract for the pinned candidate source.

`Attention-Residuals/modeling_qwen3_attnres.py` imports Qwen3 internals including:

- `transformers.masking_utils.create_causal_mask`
- `transformers.modeling_layers.GradientCheckpointingLayer`
- `transformers.utils.generic.merge_with_config_defaults`
- `transformers.utils.output_capturing.capture_outputs`
- `transformers.processing_utils.Unpack`
- `transformers.utils.TransformersKwargs`

It also subclasses and directly reuses Qwen3 implementation classes. These are private/internal APIs whose availability and signatures are release-sensitive.

## Proven lower bound

Released Transformers `v4.51.3` contains Qwen3, but its Qwen3 implementation still uses the older attention-mask and decorator stack. It does not match the candidate imports.

Released Transformers `v4.57.1` has `masking_utils` and `GradientCheckpointingLayer`, but Qwen3 still imports `check_model_inputs`; it does not provide the exact `merge_with_config_defaults` plus `capture_outputs` combination used by the candidate.

Released Transformers `v5.0.0` also still uses `check_model_inputs` in Qwen3 and therefore remains below the candidate's actual API requirement.

Hugging Face Transformers commit:

`42791a34fdeae197f60f11ace3807c81f44b0729`

introduces the split from `check_model_inputs` to:

- `merge_with_config_defaults`
- `capture_outputs`

and its Qwen3 source exposes the same relevant import family used by the candidate.

Therefore the narrowest evidence-backed dependency lower bound is not a PyPI range such as `transformers>=4.40`; it is:

> `transformers @ git+https://github.com/huggingface/transformers.git@42791a34fdeae197f60f11ace3807c81f44b0729`

This is a lower-bound snapshot, not yet a proof that every candidate path executes unchanged. D003 must still run an import/instantiate test and record any one-time minimal compatibility patch.

## Runtime tuple for D003

Evidence-backed minimum tuple:

- Python: `3.10` or newer; use `3.11.x` for D003 to minimize ecosystem ambiguity.
- PyTorch: `>=2.4`; pin one exact build in the lock rather than retaining a range.
- Transformers: exact git commit `42791a34fdeae197f60f11ace3807c81f44b0729`.
- Tokenizers: the pinned Transformers snapshot declares `>=0.22.0,<=0.23.0`; pin the resolver-selected exact version and checksum.
- Safetensors: `>=0.4.3`; pin exact version and checksum.
- Hugging Face Hub: `>=1.3.0,<2.0`; pin exact version and checksum.
- For D003 non-training synthetic preflight, `datasets`, `wandb`, `matplotlib`, `gradio`, and FineWeb-Edu are not required and must not be installed merely because the candidate's broad requirements file lists them.

The Transformers snapshot itself declares Python `>=3.10` and Torch `>=2.4`. The candidate's `torch>=2.0` declaration is therefore also too broad for this exact runtime path.

## D handoff

D003 should create a minimal lock containing only the imports required by the model/preflight path and record:

1. Python full version and executable SHA/path.
2. Exact PyTorch version/build/CUDA metadata.
3. Transformers commit and installed source-tree checksum.
4. Exact versions and hashes of tokenizers, safetensors, huggingface-hub, numpy, packaging, pyyaml, regex, requests, tqdm, filelock and psutil.
5. `pip freeze`, resolver report, and wheel/source hashes.
6. Candidate commit and checksum of `modeling_qwen3_attnres.py`.
7. Import probe for every internal symbol listed above.
8. One instantiate/forward probe before resource timing.

Do not silently replace missing internals with release-version equivalents. A compatibility change must be a single explicit patch with diff and checksum and must preserve model semantics.

## Stop boundary

Stop the current unofficial implementation path if the exact lower-bound snapshot plus one documented minimal compatibility patch cannot:

- import the candidate,
- instantiate B0/A1 with residual-only differences,
- preserve finite routing gradients,
- preserve save/load outputs within the preregistered tolerance,
- or support isolated resource/operator measurement.

This would stop only the unofficial candidate path, not the Block AttnRes hypothesis.

## Evidence classification

- Parameter-light routing principle: **規模非依存候補** at the parameter-count level only.
- Current eager CPU implementation: **小型化で要再設計**.
- Candidate dependency declaration: **insufficient / non-reproducible**.
- Exact D003 runtime path: **additional verification required**.

No quality, CPU Pareto, quantization, 3-seed, general intelligence, or capability-progress claim is made.
