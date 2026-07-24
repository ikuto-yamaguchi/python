#!/usr/bin/env bash
set -euxo pipefail

ROOT="${1:-$PWD/.r0_silg}"
SILG_SHA=2af07578e1264029a240fcfb78d4ac0aea16f5de
RTFM_SHA=58f17955595b5a127c96d045d896fcbcc7d4b570

mkdir -p "$ROOT"
# Gym 0.21 has metadata rejected by newer setuptools. Pin the 2021-era build
# toolchain before generating metadata; this is a compatibility repair only.
python -m pip install --upgrade \
  'pip==22.3.1' 'setuptools==59.5.0' 'wheel==0.37.1'

if [ ! -d "$ROOT/RTFM/.git" ]; then
  git clone https://github.com/facebookresearch/RTFM.git "$ROOT/RTFM"
fi
git -C "$ROOT/RTFM" fetch --depth 1 origin "$RTFM_SHA"
git -C "$ROOT/RTFM" checkout --detach "$RTFM_SHA"

if [ ! -d "$ROOT/silg/.git" ]; then
  git clone https://github.com/vzhong/silg.git "$ROOT/silg"
fi
git -C "$ROOT/silg" fetch --depth 1 origin "$SILG_SHA"
git -C "$ROOT/silg" checkout --detach "$SILG_SHA"

# PyTorch 1.13.1 is the newest CPU wheel that still supports Python 3.8 and
# preserves the pre-Torch-2 execution assumptions of the 2021 code.
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu \
  'torch==1.13.1+cpu' 'torchvision==0.14.1+cpu'
python -m pip install \
  'gym==0.21.0' 'py-getch==1.0.1' 'pyyaml==6.0.1' \
  'submitit==1.4.5' 'expman==0.0.7' \
  'vocab>=0.0.4' 'embeddings>=0.0.7' 'revtok>=0.0.3'
python -m pip install --no-deps -e "$ROOT/RTFM"
python -m pip install --no-deps -e "$ROOT/silg"

python - <<'PY'
import gym, torch, silg, rtfm
print('gym', gym.__version__)
print('torch', torch.__version__)
print('silg', getattr(silg, '__version__', 'source'))
print('rtfm', getattr(rtfm, '__version__', 'source'))
PY
