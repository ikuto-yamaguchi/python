# R0.1 SILG/RTFM public benchmark reproduction — cycle 007

## Decision

Public baseline reproduction remains **not completed**. No capability or novelty claim is made.

This cycle did not add a toy mechanism. It fixed the official RTFM interface, dependency surface, split names, action/observation schema and a deterministic bootstrap path, then repeated the executable source-acquisition attempt.

## Official source audit

Official SILG materials establish:

- repository: `vzhong/silg`, branch `main`
- package: `silg==0.0.1`, Python `>=3.7.10`, MIT
- reference container: `pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime`
- required environment repository: `facebookresearch/RTFM`
- installation: `bash install_envs.sh`, `pip install -r requirements.txt`, `pip install -e .`, `bash download_env_data.sh`
- experiment entrypoint: `run_exp.py`
- local launcher: `OMP_NUM_THREADS=1 python launch.py --local --envs rtfm`
- upstream requirements are mostly unresolved ranges: `gym>=0.15.4`, `torch`, `torchvision`, `pyyaml`, `expman`, `submitit`; only `py-getch==1.0.1` is exact

The exact resolved environment must therefore be frozen after the first successful installation. The upstream Docker base is retained as the closest official compatibility anchor rather than silently substituting a modern PyTorch stack.

## RTFM split and schema

SILG registers four train/test difficulty pairs:

- `rtfm_train_s1-v0` / `rtfm_test_s1-v0`
- `rtfm_train_s2-v0` / `rtfm_test_s2-v0`
- `rtfm_train_s3-v0` / `rtfm_test_s3-v0`
- `rtfm_train_s4-v0` / `rtfm_test_s4-v0`

The first reproduction target is S1 only.

Default S1 observations contain grid occupant names and lengths, generic text, wiki, task, inventory, valid-action mask, relative positions and absolute position. With default wrapper arguments, the grid is 6×6, maximum episode length is 80, and the action set is five discrete actions: stay, up, down, left and right.

The RTFM wrapper marks `won` when raw reward is greater than 0.5. The shared TorchBeast note elsewhere treats reward greater than 0.8 as a win. Both thresholds are recorded because conflating them can change task-success accounting.

## Repeated executable attempt

Command:

```bash
git clone https://github.com/vzhong/silg.git /tmp/silg
```

Result:

```text
Cloning into '/tmp/silg'...
fatal: unable to access 'https://github.com/vzhong/silg.git/': Could not resolve host: github.com
```

The failure occurs before package installation, RTFM data acquisition, model construction or training. It is therefore classified as:

`initial_public_environment_installation_failure`

It is not a model failure and supplies no benchmark score.

## Added reproducibility assets

- `SILG_RTFM_MANIFEST_R01_007.json`
- `bootstrap_silg_rtfm_r01.sh`
- `SILG_INSTALL_ATTEMPT_R01_007.log`

The bootstrap script checks DNS before cloning, verifies the exact commit, creates a Python 3.8 virtual environment, preserves upstream installation order, freezes all resolved packages, performs an S1 environment reset and prints the observed keys/action count before allowing training.

## Required controlled run after installation

All methods must consume the same episode instances and seeds 1, 7 and 19:

1. official shared recurrent baseline without pretrained LM
2. random valid action
3. language-blind recurrent baseline
4. state-only recurrent baseline
5. language-shuffle recurrent baseline

Required outputs:

- S1 train and test task success
- action accuracy where an oracle/demonstration action is available
- episode return and win rate
- model bytes
- peak RSS
- training wall time
- CPU inference milliseconds per environment step
- exact split, episode IDs, package lock and commit SHA

## Status

- official code/interface audit: completed
- executable source acquisition: blocked by runtime DNS
- official recurrent baseline: not run
- random/language-blind/state-only controls: not run
- public baseline reproduced: no
- model/resource measurements on public SILG: unavailable
- high-school-level intelligence: not passed
