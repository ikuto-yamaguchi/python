#!/usr/bin/env bash
set -euo pipefail

SILG_REPO=${SILG_REPO:-https://github.com/vzhong/silg.git}
SILG_COMMIT=${SILG_COMMIT:-2af07578e1264029a240fcfb78d4ac0aea16f5de}
WORKDIR=${WORKDIR:-$PWD/.r01-silg}
PYTHON_BIN=${PYTHON_BIN:-python3.8}

mkdir -p "$WORKDIR/logs"
exec > >(tee "$WORKDIR/logs/bootstrap.log") 2>&1

echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "uname=$(uname -a)"
echo "python_bin=$PYTHON_BIN"
"$PYTHON_BIN" --version

if ! getent hosts github.com >/dev/null 2>&1; then
  echo "BLOCKED: github.com DNS resolution failed" >&2
  exit 20
fi

if [ ! -d "$WORKDIR/silg/.git" ]; then
  git clone "$SILG_REPO" "$WORKDIR/silg"
fi
cd "$WORKDIR/silg"
git fetch --all --tags --prune
git checkout --detach "$SILG_COMMIT"
test "$(git rev-parse HEAD)" = "$SILG_COMMIT"

"$PYTHON_BIN" -m venv "$WORKDIR/venv"
# shellcheck disable=SC1091
source "$WORKDIR/venv/bin/activate"
python -m pip install --upgrade 'pip<24' 'setuptools<69' wheel

# The upstream requirements are intentionally preserved. Freeze the resolved
# environment after a successful install so later runs do not silently drift.
bash install_envs.sh
python -m pip install -r requirements.txt
python -m pip install -e .
bash download_env_data.sh
python -m pip freeze | sort > "$WORKDIR/logs/pip-freeze.txt"
git rev-parse HEAD > "$WORKDIR/logs/silg-commit.txt"

OMP_NUM_THREADS=1 python - <<'PY'
import gym
import json
import silg  # noqa: F401

env = gym.make('silg:rtfm_train_s1-v0')
obs = env.reset()
summary = {
    'env': 'silg:rtfm_train_s1-v0',
    'observation_keys': sorted(obs.keys()),
    'action_count': int(env.action_space.n),
}
print(json.dumps(summary, sort_keys=True))
env.close()
PY

echo "READY: run OMP_NUM_THREADS=1 python launch.py --local --envs rtfm"
