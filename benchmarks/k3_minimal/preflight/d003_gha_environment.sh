#!/usr/bin/env bash
set -euo pipefail

OUT="${OUT:-benchmarks/k3_minimal/runs/d003-gha-environment}"
TRANSFORMERS_COMMIT="42791a34fdeae197f60f11ace3807c81f44b0729"
CANDIDATE_COMMIT="83d2b8de82c2fbb981c7decca67d13d9db348da6"

if [[ "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.11" ]]; then
  echo "D003 requires Python 3.11.x" >&2
  exit 2
fi

mkdir -p "$OUT/raw-logs"
python -m pip install --upgrade pip
python -m pip install --no-cache-dir --report "$OUT/resolver-report.json" \
  torch==2.7.1 \
  "transformers @ git+https://github.com/huggingface/transformers.git@${TRANSFORMERS_COMMIT}"
python -m pip freeze --all > "$OUT/pip-freeze.txt"
python -m pip check | tee "$OUT/raw-logs/pip-check.txt"

candidate="${RUNNER_TEMP:-/tmp}/open-attention-residuals"
rm -rf "$candidate"
git clone --filter=blob:none https://github.com/wdlctc/open-attention-residuals.git "$candidate"
git -C "$candidate" checkout --detach "$CANDIDATE_COMMIT"
test "$(git -C "$candidate" rev-parse HEAD)" = "$CANDIDATE_COMMIT"
git -C "$candidate" rev-parse HEAD > "$OUT/raw-logs/candidate-commit.txt"

python benchmarks/k3_minimal/preflight/d003_environment_probe.py --out "$OUT" \
  2>&1 | tee "$OUT/raw-logs/environment-probe.txt"
PYTHONPATH="$candidate:$candidate/Attention-Residuals" \
  python -c 'import modeling_attnres' \
  2>&1 | tee "$OUT/raw-logs/candidate-import.txt"

python - <<'PY'
import hashlib, json, os, pathlib, platform, sys
out = pathlib.Path(os.environ.get('OUT', 'benchmarks/k3_minimal/runs/d003-gha-environment'))
(out / 'D003_GHA_environment_summary.json').write_text(json.dumps({
  'schema': 'D003-GHA-environment-summary-v1',
  'status': 'ENV_PASS',
  'python': sys.version,
  'platform': platform.platform(),
  'commit_sha': os.getenv('GITHUB_SHA'),
  'run_id': os.getenv('GITHUB_RUN_ID'),
  'training_authorized': False,
  'model_execution_authorized': False,
  'next_stage_automatic': False,
  'required_next_manifest': 'C004_d003_variant_semantic_trace'
}, indent=2, sort_keys=True))
files = sorted(p for p in out.rglob('*') if p.is_file() and p.name != 'checksums.sha256')
(out / 'checksums.sha256').write_text('\n'.join(
  f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}" for p in files
) + '\n')
PY
