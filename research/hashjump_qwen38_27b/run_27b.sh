#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4
export LLAMA_LOG_LEVEL=INFO
RESULTS="$GITHUB_WORKSPACE/hashjump_results"
mkdir -p "$RESULTS"
date -u | tee "$RESULTS/date_utc.txt"
free -h | tee "$RESULTS/memory.txt"
df -h / | tee "$RESULTS/disk.txt"
echo "=== Clone and compile llama.cpp with optional (experimental) 4-layer identity bypass ==="
git clone --depth=1 https://github.com/ggml-org/llama.cpp.git "$RUNNER_TEMP/llama.cpp"
cd "$RUNNER_TEMP/llama.cpp"
git rev-parse HEAD | tee "$RESULTS/llama_commit.txt"
python - <<'PY'
from pathlib import Path
p=Path("src/models/qwen35.cpp")
s=p.read_text()
needle="res->t_layer_inp[il] = inpL;"
assert s.count(needle)==1, f"unexpected location count: {s.count(needle)}"
s=s.replace('#include "models.h"', '#include "models.h"\n#include <cstdlib>', 1)
s=s.replace(needle, needle+'''
        // HashJump experimental identity-block ablation. Not a learned approximation.
        const char * skip4_env = std::getenv("HASHJUMP_SKIP4_START");
        const int skip4_start = skip4_env ? std::atoi(skip4_env) : -1;
        if (skip4_start >= 0 && skip4_start % 4 == 0 &&
            il >= skip4_start && il < skip4_start + 4) {
            continue;
        }
''',1)
p.write_text(s)
print("Identity skip instrumented. Normal path unchanged if env unset.")
PY
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
cmake --build build --target llama-cli llama-bench -j4
echo "=== Get real 27B pretrained model (prequantized GGUF, NOT compressed by HashJump) ==="
MODEL="$RUNNER_TEMP/Qwen3.8-27B-IQ2_XS.gguf"
curl --fail --location --retry 3 --retry-delay 5 --connect-timeout 30 --max-time 1200 --progress-bar -o "$MODEL" "https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-IQ2_XS.gguf"
python - "$MODEL" "$RESULTS" <<'PY'
import json,os,sys
f=sys.argv[1]; d=sys.argv[2]
with open(f,'rb') as fd: magic=fd.read(4)
assert magic==b'GGUF',f"Invalid model header {magic!r}"
out={"model":"Qwen3.8-27B","variant":"bartowski IQ2_XS","model_bytes":os.path.getsize(f),"gguf_magic":magic.decode()}
print(out,flush=True)
open(d+"/model_metadata.json","w").write(json.dumps(out,indent=2))
PY
df -h / | tee "$RESULTS/disk_after_download.txt"
echo "=== REAL model CPU benchmark ==="
set +e
timeout 320s /usr/bin/time -v ./build/bin/llama-bench -m "$MODEL" -p 32 -n 8 -t 4 -r 1 -ngl 0 > "$RESULTS/baseline_bench.txt" 2>&1
echo "$?" > "$RESULTS/baseline_bench_rc.txt"
tail -70 "$RESULTS/baseline_bench.txt"
echo "=== REAL model simple task, baseline ==="
cat > "$RUNNER_TEMP/task.txt" <<'EOF'
<|im_start|>user
Answer with only a number. What is 17 * 23?
<|im_end|>
<|im_start|>assistant<|channel|>final
EOF
timeout 240s /usr/bin/time -v ./build/bin/llama-cli -m "$MODEL" -f "$RUNNER_TEMP/task.txt" -n 12 -t 4 -c 512 --temp 0 --no-warmup --simple-io --no-display-prompt > "$RESULTS/baseline_task.txt" 2>&1
echo "$?" > "$RESULTS/baseline_task_rc.txt"
tail -50 "$RESULTS/baseline_task.txt"
echo "=== Ablation: bypass one contiguous 4-layer cycle at start 24 (identity function, zero learned parameters) ==="
export HASHJUMP_SKIP4_START=24
timeout 320s /usr/bin/time -v ./build/bin/llama-bench -m "$MODEL" -p 32 -n 8 -t 4 -r 1 -ngl 0 > "$RESULTS/skip4_bench.txt" 2>&1
echo "$?" > "$RESULTS/skip4_bench_rc.txt"
tail -70 "$RESULTS/skip4_bench.txt"
timeout 240s /usr/bin/time -v ./build/bin/llama-cli -m "$MODEL" -f "$RUNNER_TEMP/task.txt" -n 12 -t 4 -c 512 --temp 0 --no-warmup --simple-io --no-display-prompt > "$RESULTS/skip4_task.txt" 2>&1
echo "$?" > "$RESULTS/skip4_task_rc.txt"
tail -50 "$RESULTS/skip4_task.txt"
set -e
echo "=== Experiment finished ==="
ls -lah "$RESULTS"
