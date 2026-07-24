# R0.1 SILG / RTFM Public Baseline Reproduction 001

## Status

- Public benchmark selected: **SILG RTFM stage 1**
- Official recurrent baseline completed: **no**
- Random control completed: **pending GitHub Actions execution**
- Language-blind completed: **no**
- State-only completed: **no**
- Capability or novelty claim: **none**

This cycle fixes public source versions, the install path, environment split,
observation/action schema and a three-seed random-control probe. It does not
introduce a new architecture.

## Official sources and pins

| Component | Source | Pin |
|---|---|---|
| SILG | `vzhong/silg` | `2af07578e1264029a240fcfb78d4ac0aea16f5de` |
| RTFM | `facebookresearch/RTFM` | `58f17955595b5a127c96d045d896fcbcc7d4b570` |
| SILG package | PyPI | `0.0.1`, released 2021-10-20 |
| Paper | NeurIPS 2021 | SILG shared recurrent architecture |

The official repository has only six commits and no tagged GitHub release;
therefore the latest public commit and the matching PyPI version are both
recorded. RTFM is archived and read-only.

## Official entry points and split

The official launcher defines:

- train: `silg:rtfm_train_s1-v0`
- validation/test: `silg:rtfm_test_s1-v0`
- model: `multi`
- two entropy-cost settings: `0.05`, `0.005`
- default launch seeds: `range(4)`

The published local command is:

```bash
python launch.py --local --envs rtfm
```

The default training program is not a small smoke test. Its parser uses:

- `total_frames = 100,000,000`
- `num_actors = 30`
- `batch_size = 24`
- `unroll_length = 80`
- `num_threads = 4`

A full faithful learning-curve reproduction therefore requires substantially
more compute than the environment/import probe.

## Observation schema

The SILG RTFM wrapper declares these fields:

| Field | Shape / meaning |
|---|---|
| `name` | `(height, width, max_placement, max_name)`, word IDs describing grid occupants |
| `name_len` | descriptor lengths per cell |
| `text` / `text_len` | combined text input |
| `wiki` / `wiki_len` | environment-dynamics document |
| `task` / `task_len` | task/goal language |
| `inv` / `inv_len` | inventory language |
| `valid` | valid-action mask |
| `rel_pos` | relative positions |
| `pos` | agent position |

Text fields exposed by the wrapper are `wiki`, `task`, and `inv`.

## Action schema

RTFM stage 1 exposes five discrete actions in this order:

0. stay
1. up
2. down
3. left
4. right

The wrapper reports a win when environment reward is greater than `0.5`;
SILG's TorchBeast training code generally treats reward greater than `0.8` as
a win. This mismatch is explicitly logged rather than silently normalized.

## Dependency contract

SILG itself specifies only broad/unpinned dependencies:

```text
gym>=0.15.4
py-getch==1.0.1
pyyaml
torch
torchvision
expman
submitit
```

RTFM adds:

```text
vocab>=0.0.4
embeddings>=0.0.7
revtok>=0.0.3
gym>=0.15.4
py-getch==1.0.1
```

For the compatibility probe, the workflow pins Python 3.8, PyTorch 1.13.1 CPU,
Gym 0.21.0, pip below 24 and setuptools below 69. These are reproduction
compatibility pins, not claimed official experiment versions; the public code
does not supply a complete lock file.

## Probe

Files:

- `install_silg_rtfm.sh`
- `silg_rtfm_probe.py`
- `.github/workflows/r0_silg_rtfm_probe.yml`

The probe performs:

1. exact-source checkout;
2. dependency installation;
3. import and environment registration;
4. schema capture;
5. 20 episodes × seeds `0,1,2` using uniformly sampled valid actions;
6. win rate, return, episode length, wall time, action-selection latency and
   peak RSS measurement;
7. pip freeze, raw logs and SHA-256 checksum artifact upload.

The random policy contains zero trainable model bytes. It is an evaluation
control, not an official recurrent baseline.

## Leakage audit

The random probe selects only from the observation's `valid` mask. It does not
consume:

- future state;
- gold action;
- episode outcome;
- completed trajectory;
- test labels;
- language-to-entity mapping.

Using `valid` is part of the public observation interface. A later matched
state-only and language-blind comparison must use the same mask.

## Current blocker

The tool execution container could not resolve `github.com`, so installation
could not be run locally. The canonical branch now contains a GitHub Actions
probe that runs in an internet-enabled Ubuntu environment and always uploads
installation/probe logs, including on failure.

A successful random probe is necessary but not sufficient. The next minimal
steps are:

1. inspect the workflow artifact and repair only the first concrete dependency
   failure, if any;
2. instantiate the official `multi` recurrent model and record parameter bytes;
3. run a reduced-frame sanity training for seeds 0,1,2;
4. implement language-blind and state-only input ablations without changing
   the optimizer, actor count, instances or valid-action interface;
5. only then schedule the full official-frame reproduction.

## Research decision

R0.1 remains **in progress**. Public baseline reproduction count remains zero
until the recurrent model trains and evaluates successfully. No intelligence
principle, semantic-identity progress or high-school-level capability is
claimed.
