# R0.1 SILG / RTFM Public Baseline Reproduction 001

## Status

- Public benchmark selected: **SILG RTFM stage 1**
- Environment installation and reset/step probe: **completed**
- Three-seed random control: **completed**
- Official recurrent baseline: **not completed**
- Language-blind: **not completed**
- State-only: **not completed**
- Capability or novelty claim: **none**

This work fixes public source versions, the install path, environment split,
observation/action schema and an executable three-seed control. It introduces
no new architecture.

## Official sources and pins

| Component | Source | Pin |
|---|---|---|
| SILG | `vzhong/silg` | `2af07578e1264029a240fcfb78d4ac0aea16f5de` |
| RTFM | `facebookresearch/RTFM` | `58f17955595b5a127c96d045d896fcbcc7d4b570` |
| SILG package | PyPI | `0.0.1` |
| Paper | NeurIPS 2021 | SILG shared recurrent architecture |

## Official entry points and split

The official launcher defines:

- train: `silg:rtfm_train_s1-v0`
- validation/test: `silg:rtfm_test_s1-v0`
- model: `multi`
- entropy costs: `0.05`, `0.005`
- launcher seeds: `range(4)`

Published local entry point:

```bash
python launch.py --local --envs rtfm
```

Default training is large rather than a smoke test:

- `total_frames = 100,000,000`
- `num_actors = 30`
- `batch_size = 24`
- `unroll_length = 80`
- `num_threads = 4`

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

Successful runtime versions:

- Python 3.8.18
- Gym 0.21.0
- PyTorch 1.13.1+cpu
- torchvision 0.14.1+cpu
- SILG 0.0.1 source
- RTFM pinned source

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

Actions are discrete: stay, up, down, left, right.

## Three-seed random control

Condition: uniformly sample one action from the public `valid` mask.

- seeds: `0, 1, 2`
- episodes: 20 per seed, 60 total
- wins: 6 / 60
- mean win rate: **0.1000**
- mean return: **-1.0823**
- mean episode length: **15.1167**
- mean wall time: **0.8522 s per 20-episode seed batch**
- mean action-selection latency: **8.087 microseconds/action**
- total probe wall time: **3.8286 s**
- peak RSS: **232,992 KiB**
- trainable model size: **0 bytes**

Per seed:

| Seed | Wins | Win rate | Return | Mean length |
|---:|---:|---:|---:|---:|
| 0 | 3 | 0.15 | -0.938 | 12.90 |
| 1 | 1 | 0.05 | -1.158 | 13.90 |
| 2 | 2 | 0.10 | -1.151 | 18.55 |

Canonical result:

- `results/SILG_RTFM_RANDOM_3SEED.json`
- workflow run `30100194601`
- artifact digest `sha256:c4f4102dce4d5929b1ea2a54c98572c5ea6e8c251d87625965752f42c1f11fe6`

## Leakage audit

The control reads only current observation fields and the public valid-action
mask. It does not consume future state, gold action, episode outcome, completed
trajectory, test label or language-to-entity mapping. Model bytes are zero.

## Next minimal work

1. instantiate official `multi` recurrent model and measure parameter bytes;
2. run reduced-frame training/evaluation for seeds 0,1,2;
3. add language-blind and state-only input masks without changing episodes,
   valid-action handling, optimizer or model capacity;
4. compare all controls on identical validation instances;
5. only after the sanity run, schedule a faithful 100M-frame reproduction.

## Research decision

R0.1 remains **in progress**. One public environment/control is now reproducible,
but the published recurrent baseline count remains zero. No intelligence
principle, semantic-identity progress, novelty or high-school-level capability
is claimed.
