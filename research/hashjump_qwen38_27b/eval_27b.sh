#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4
RESULTS="$GITHUB_WORKSPACE/hashjump_eval_results"
mkdir -p "$RESULTS"
echo "=== Compile llama-server with Qwen3.8 4-layer identity ablation ==="
git clone --depth=1 https://github.com/ggml-org/llama.cpp.git "$RUNNER_TEMP/llama.cpp"
cd "$RUNNER_TEMP/llama.cpp"
git rev-parse HEAD | tee "$RESULTS/llama_commit.txt"
python3 - <<'PY'
from pathlib import Path
p=Path("src/models/qwen35.cpp")
s=p.read_text()
needle="res->t_layer_inp[il] = inpL;"
assert s.count(needle)==1, f"Unexpected qwen35 code; count {s.count(needle)}"
s=s.replace('#include "models.h"', '#include "models.h"\n#include <cstdlib>', 1)
s=s.replace(needle, needle+'''
        // HashJump 4-layer identity ablation, not a trained surrogate.
        const char * skip4_env = std::getenv("HASHJUMP_SKIP4_START");
        const int skip4_start = skip4_env ? std::atoi(skip4_env) : -1;
        if (skip4_start >= 0 && skip4_start % 4 == 0 &&
            il >= skip4_start && il < skip4_start + 4) {
            continue;
        }
''',1)
p.write_text(s)
PY
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON -DLLAMA_BUILD_SERVER=ON
cmake --build build --target llama-server -j4
echo "=== Download actual 27B pretrained GGUF ==="
MODEL="$RUNNER_TEMP/Qwen3.8-27B-IQ2_XS.gguf"
curl --fail --location --retry 3 --retry-delay 5 --connect-timeout 30 --max-time 1200 --progress-bar -o "$MODEL" "https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-IQ2_XS.gguf"
python3 - "$MODEL" <<'PY'
import sys,os
with open(sys.argv[1],"rb") as f: assert f.read(4)==b"GGUF"
print("real Qwen3.8-27B GGUF",os.path.getsize(sys.argv[1]),"bytes")
PY
cat > "$RESULTS/eval_tasks.json" <<'JSON'
[
  {"id":"multiply","prompt":"What is 17 times 23? Answer with only the integer.","expected":"391"},
  {"id":"arithmetic_chain","prompt":"You have 12 apples, give away 5 and buy 3. How many remain? Answer with only the integer.","expected":"10"},
  {"id":"negative_comparison","prompt":"Which number is greater: -12 or -9? Answer with only the greater number.","expected":"-9"},
  {"id":"logic","prompt":"All glips are flarns. All flarns are vems. Are all glips vems? Answer only yes or no.","expected":"yes"},
  {"id":"python_trace","prompt":"What is the value printed by this Python code: print(2**5 + 3)? Answer only the integer.","expected":"35"},
  {"id":"c_array_index","prompt":"In C, int a[3]={1,2,3}; what is the largest valid index of a? Answer only the integer.","expected":"2"},
  {"id":"instruction_following","prompt":"Reply exactly with the two letters OK and nothing else.","expected":"OK"},
  {"id":"modulo","prompt":"What is the remainder when 19 is divided by 4? Answer only the integer.","expected":"3"}
]
JSON
PORT=18333
for mode in baseline skip4; do
  echo "=== Start llama-server mode: $mode ==="
  if [ "$mode" = "skip4" ]; then
    export HASHJUMP_SKIP4_START=24
  else
    unset HASHJUMP_SKIP4_START || true
  fi
  ./build/bin/llama-server -m "$MODEL" --host 127.0.0.1 --port "$PORT" -c 1024 -t 4 -tb 4 -b 128 -ub 128 -np 1 --no-mmproj --reasoning off --no-warmup > "$RESULTS/server_$mode.log" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$RESULTS/server_pid_$mode.txt"
  python3 - "$PORT" <<'PY'
import sys,time,urllib.request
url="http://127.0.0.1:"+sys.argv[1]+"/health"
for i in range(180):
    try:
        with urllib.request.urlopen(url,timeout=3) as r:
            if r.status==200:
                print("SERVER READY after",i,"seconds",flush=True)
                break
    except Exception: pass
    time.sleep(1)
else:
    raise RuntimeError("server not ready after 180sec")
PY
  python3 - "$PORT" "$mode" "$RESULTS" <<'PY'
import json,sys,time,urllib.request,re
port,mode,root=sys.argv[1:]
tasks=json.load(open(root+"/eval_tasks.json"))
rows=[]
for t in tasks:
    body=json.dumps({"messages":[{"role":"user","content":t["prompt"]}],"temperature":0,"max_tokens":64,"stream":False}).encode()
    req=urllib.request.Request("http://127.0.0.1:"+port+"/v1/chat/completions",data=body,headers={"Content-Type":"application/json"})
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=210) as r:
            result=json.load(r)
        msg=result["choices"][0]["message"]
        answer=(msg.get("content") or "").strip()
        reasoning=(msg.get("reasoning_content") or "")
        normalized=answer.strip().strip(" .\\n\\r\\t")
        correct=(normalized.lower()==t["expected"].lower())
        row={"id":t["id"],"expected":t["expected"],"answer":answer[:250],"reasoning_length":len(reasoning),"correct":correct,"seconds":round(time.perf_counter()-start,2),"tokens":result.get("usage",{}).get("completion_tokens"),"finish_reason":result["choices"][0].get("finish_reason")}
    except Exception as e:
        row={"id":t["id"],"expected":t["expected"],"error":str(e),"correct":False}
    rows.append(row)
    print(json.dumps({"mode":mode,**row},ensure_ascii=False),flush=True)
summary={"mode":mode,"success":sum(r["correct"] for r in rows),"total":len(rows),"rows":rows}
with open(root+"/eval_"+mode+".json","w") as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print("SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="rows"}),flush=True)
PY
  kill "$SERVER_PID" || true
  wait "$SERVER_PID" || true
  echo "=== Finished mode: $mode ==="
  free -h
done
ls -lah "$RESULTS"
