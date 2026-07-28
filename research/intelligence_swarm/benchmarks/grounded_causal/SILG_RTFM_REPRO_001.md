# R0.1 SILG / RTFM Public Baseline Reproduction 001

## Status

- Public benchmark selected: **SILG RTFM stage 1**
- Environment installation and reset/step probe: **completed**
- Historical non-canonical random probe (`0,1,2`): **completed; retained only as setup evidence**
- Canonical seeds: **`1,7,19`**
- Official recurrent 131,072-frame training: **executed previously, but no immutable accepted bundle exists**
- Canonical matched recurrent/random/language-blind/state-only/language-shuffle values: **not accepted until an immutable bundle is recovered**
- Public baseline reproduction: **not completed**
- Capability or novelty claim: **none**

This work fixes public source versions, the install path, environment split,
observation/action schema and the canonical execution contract. It introduces no
new architecture or toy hypothesis.

## Official sources and pins

| Component | Source | Pin |
|---|---|---|
| SILG | `vzhong/silg` | `2af07578e1264029a240fcfb78d4ac0aea16f5de` |
| RTFM | `facebookresearch/RTFM` | `58f17955595b5a127c96d045d896fcbcc7d4b570` |
| SILG package | PyPI | `0.0.1` |
| Paper | NeurIPS 2021 | SILG shared recurrent architecture |

The executable workflow and request additionally pin:

- train environment: `silg:rtfm_train_s1-v0`
- evaluation environment: `silg:rtfm_test_s1-v0`
- model: official SILG `multi` recurrent
- pretrained language model: disabled
- requested frames: `131072` per seed
- canonical seeds: `1, 7, 19`

## Official entry points and split

The official launcher defines:

- train: `silg:rtfm_train_s1-v0`
- validation/test: `silg:rtfm_test_s1-v0`
- model: `multi`
- entropy costs: `0.05`, `0.005`
- launcher seeds: `range(4)` in the public launcher

Published local entry point:

```bash
python launch.py --local --envs rtfm
```

Default public training is substantially larger than R0.1 qualification:

- `total_frames = 100,000,000`
- `num_actors = 30`
- `batch_size = 24`
- `unroll_length = 80`
- `num_threads = 4`

R0.1 is therefore a pinned public-baseline qualification run at 131,072 frames
per canonical seed, not a numerical reproduction of the published 100M-frame
score.

## Dependency reconstruction

The public repositories do not provide a complete lock file. Four concrete
compatibility failures were reproduced and minimally repaired:

1. Gym 0.21 metadata is rejected by modern setuptools. The build toolchain is
   pinned to pip 22.3.1, setuptools 59.5.0 and wheel 0.37.1.
2. `expman` is unpinned. Version 0.0.7 has a broken source distribution that
   omits `requirements.txt`; installable wheel 0.0.5 is used.
3. `transformers` and the local BERT tokenizer files are required by
   `silg.envs.base` but absent from requirements. Transformers 4.30.2 and the
   three assets referenced by the official download script are installed.
4. `silg.envs.__init__` imports every optional environment, causing an RTFM-only
   run to require NLE, ALFWorld, Messenger and Touchdown. The installer limits
   registration to RTFM without modifying RTFM itself.

Pinned runtime target:

- Python 3.8
- Gym 0.21.0
- PyTorch 1.13.1+cpu
- torchvision 0.14.1+cpu
- Transformers 4.30.2
- SILG pinned source
- RTFM pinned source

The exact installed environment must be preserved in the run artifact via
`pip freeze`; this document is not a substitute for that immutable evidence.

## Measured observation/action schema

The successful probe observed:

| Field | Shape |
|---|---|
| `name` | `[6, 6, 1, 8]` |
| `name_len` | `[6, 6, 1]` |
| `wiki` | `[80]` |
| `wiki_len` | `[1]` |
| `task` | `[40]` |
| `task_len` | `[1]` |
| `inv` | `[8]` |
| `inv_len` | `[1]` |
| `valid` | `[5]` |
| `rel_pos` | `[6, 6, 2]` |
| `pos` | `[2]` |

Actions are discrete: stay, up, down, left, right. All learned and control
conditions must consume the same initial environment instances and the same
valid-action handling.

## Historical random setup probe — not canonical evidence

An early setup probe used seeds `0,1,2` before the canonical seed contract was
fixed. It is retained only to show that installation, reset, stepping and basic
resource capture worked:

- episodes: 20 per seed, 60 total
- wins: 6 / 60
- mean win rate: `0.1000`
- mean return: `-1.0823`
- mean episode length: `15.1167`
- peak RSS: `232,992 KiB`
- trainable model size: `0 bytes`
- workflow run: `30100194601`
- artifact digest: `sha256:c4f4102dce4d5929b1ea2a54c98572c5ea6e8c251d87625965752f42c1f11fe6`

These numbers must not be mixed with, substituted for, or statistically compared
against the canonical `1,7,19` learned-baseline bundle.

## Canonical matched evaluation contract

The current R0.1 job must use seeds `1,7,19` and compare on identical evaluation
instances:

- Correct recurrent
- Random
- Language-blind
- State-only
- Language-shuffle

The accepted immutable bundle must contain:

- three checkpoints
- per-seed and aggregate matched-condition results
- model bytes
- peak RSS
- training wall time
- CPU inference latency
- raw install, training and evaluation logs
- host and commit provenance
- sorted `pip freeze`
- SHA-256 manifest

A previous long run completed training and matched controls but failed during
later R0.2 work before artifact upload. Those unpreserved values remain
inadmissible. The workflow now freezes and uploads the R0.1 bundle before the
separate R0.2 job starts.

## Leakage boundary

Random reads only the current observation and public valid-action mask.
Language-blind and state-only must differ from Correct only by preregistered input
masking; they must not receive future state, gold action, reward, done status,
completed trajectory, test labels or hidden language-to-entity mappings.
All methods must be evaluated on the same instance identities.

## Next minimal work

1. complete one split-job run from the current canonical branch;
2. recover and checksum the immutable R0.1 artifact before any R0.2 result is used;
3. audit checkpoint count, canonical seeds, condition coverage, instance identity,
   dependencies, model bytes, RSS, wall time and CPU latency;
4. classify any missing or inconsistent evidence as `initial_reproduction_failure`;
5. only after qualification, consider a faithful larger-frame public reproduction.

## Research decision

R0.1 remains **in progress**. Installation and schema evidence exist, and a prior
long run demonstrated executability, but the accepted learned public baseline
count remains zero because no immutable canonical bundle has passed audit. No
new intelligence principle, semantic-identity progress, novelty, capability
progress or high-school-level intelligence is claimed.
