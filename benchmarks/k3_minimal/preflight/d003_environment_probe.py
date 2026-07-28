#!/usr/bin/env python3
"""D003 exact-runtime environment/import preflight.

Non-training probe only. It records runtime provenance and checks the exact
candidate-internal Transformers symbols required by C002. It never substitutes
another API silently.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

TRANSFORMERS_COMMIT = "42791a34fdeae197f60f11ace3807c81f44b0729"
CANDIDATE_COMMIT = "83d2b8de82c2fbb981c7decca67d13d9db348da6"
CANDIDATE_MODEL_BLOB_SHA = "649aa0067e5b9d0fc2a3cc68784a6794090a26a4"
REQUIRED_IMPORTS = [
    "transformers.models.qwen3.configuration_qwen3.Qwen3Config",
    "transformers.models.qwen3.modeling_qwen3.Qwen3RMSNorm",
    "transformers.models.qwen3.modeling_qwen3.Qwen3MLP",
    "transformers.models.qwen3.modeling_qwen3.Qwen3Attention",
    "transformers.models.qwen3.modeling_qwen3.Qwen3RotaryEmbedding",
    "transformers.models.qwen3.modeling_qwen3.Qwen3PreTrainedModel",
    "transformers.masking_utils.create_causal_mask",
    "transformers.masking_utils.create_sliding_window_causal_mask",
    "transformers.modeling_layers.GradientCheckpointingLayer",
    "transformers.utils.generic.merge_with_config_defaults",
    "transformers.utils.output_capturing.capture_outputs",
]
PACKAGES = ["torch", "transformers", "tokenizers", "safetensors", "huggingface_hub"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_text(args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, check=False, timeout=30)
        return {
            "argv": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as exc:
        return {"argv": args, "error": repr(exc)}


def package_info(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    row: dict[str, Any] = {"present": spec is not None}
    if spec is None:
        return row
    module = importlib.import_module(name)
    row["version"] = getattr(module, "__version__", None)
    row["origin"] = getattr(spec, "origin", None)
    return row


def import_symbol(path: str) -> dict[str, Any]:
    module_name, symbol = path.rsplit(".", 1)
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, symbol)
        return {"path": path, "ok": True, "object_type": type(obj).__name__}
    except Exception as exc:
        return {"path": path, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    packages = {name: package_info(name) for name in PACKAGES}
    imports = [import_symbol(path) for path in REQUIRED_IMPORTS]
    python_ok = sys.version_info[:2] == (3, 11)
    transformers_present = packages["transformers"]["present"]
    imports_ok = all(row["ok"] for row in imports)

    blockers: list[str] = []
    if not python_ok:
        blockers.append(
            f"Python {sys.version_info.major}.{sys.version_info.minor} != preregistered 3.11.x"
        )
    if not transformers_present:
        blockers.append("transformers is absent; exact commit imports cannot be tested")
    elif not imports_ok:
        blockers.append("one or more candidate-internal Transformers imports failed")

    result: dict[str, Any] = {
        "schema": "D003-env-probe-v1",
        "contract": {
            "python": "3.11.x",
            "torch_min": "2.4",
            "transformers_commit": TRANSFORMERS_COMMIT,
            "candidate_commit": CANDIDATE_COMMIT,
            "candidate_model_blob_sha": CANDIDATE_MODEL_BLOB_SHA,
            "semantic_patch_limit": 0,
            "compatibility_patch_limit": 1,
        },
        "environment": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "packages": packages,
            "pip_freeze": run_text([sys.executable, "-m", "pip", "freeze"]),
        },
        "import_probe": imports,
        "decision": {
            "stage": "dependency/import gate",
            "status": "PASS" if not blockers else "BLOCKED_ENV",
            "python_ok": python_ok,
            "torch_observed": packages["torch"].get("version"),
            "transformers_present": transformers_present,
            "all_required_imports_ok": imports_ok,
            "blockers": blockers,
            "training_authorized": False,
            "note": "Environment classification only; no Block AttnRes quality inference.",
        },
    }

    raw = json.dumps(result, indent=2, sort_keys=True).encode()
    result_path = out / "D003_environment_probe.json"
    result_path.write_bytes(raw)
    (out / "D003_environment_probe.sha256").write_text(
        f"{sha256_bytes(raw)}  {result_path.name}\n", encoding="utf-8"
    )
    print(json.dumps(result["decision"], indent=2, ensure_ascii=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
