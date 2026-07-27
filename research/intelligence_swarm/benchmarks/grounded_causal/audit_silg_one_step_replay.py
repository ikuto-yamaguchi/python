#!/usr/bin/env python3
"""Replay one captured SILG learner update and require exact equality."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import random
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch


def tensor_stream_hash(value: Any) -> str:
    h = hashlib.sha256()

    def visit(obj: Any, path: str) -> None:
        h.update(path.encode())
        if torch.is_tensor(obj):
            tensor = obj.detach().cpu().contiguous()
            h.update(str(tensor.dtype).encode())
            h.update(str(tuple(tensor.shape)).encode())
            h.update(tensor.numpy().tobytes())
        elif isinstance(obj, dict):
            for key in sorted(obj, key=str):
                visit(obj[key], f"{path}/{key}")
        elif isinstance(obj, (list, tuple)):
            for index, item in enumerate(obj):
                visit(item, f"{path}/{index}")
        else:
            h.update(repr(obj).encode())

    visit(value, "root")
    return h.hexdigest()


def assert_exact(actual: Any, expected: Any, path: str = "root") -> None:
    if torch.is_tensor(expected):
        if not torch.is_tensor(actual):
            raise AssertionError(f"{path}: expected tensor, got {type(actual).__name__}")
        if actual.dtype != expected.dtype or tuple(actual.shape) != tuple(expected.shape):
            raise AssertionError(
                f"{path}: tensor metadata mismatch "
                f"{actual.dtype}/{tuple(actual.shape)} != {expected.dtype}/{tuple(expected.shape)}"
            )
        if not torch.equal(actual.detach().cpu(), expected.detach().cpu()):
            delta = 0.0
            if actual.is_floating_point() and expected.is_floating_point():
                delta = float((actual.detach().cpu() - expected.detach().cpu()).abs().max())
            raise AssertionError(f"{path}: tensor values differ; max_abs_delta={delta}")
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{path}: mapping keys differ")
        for key in sorted(expected, key=str):
            assert_exact(actual[key], expected[key], f"{path}/{key}")
        return
    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, type(expected)) or len(actual) != len(expected):
            raise AssertionError(f"{path}: sequence type/length differs")
        for index, (left, right) in enumerate(zip(actual, expected)):
            assert_exact(left, right, f"{path}/{index}")
        return
    if isinstance(expected, float) and math.isnan(expected):
        if not isinstance(actual, float) or not math.isnan(actual):
            raise AssertionError(f"{path}: expected NaN")
        return
    if actual != expected:
        raise AssertionError(f"{path}: {actual!r} != {expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--pre", type=Path, required=True)
    parser.add_argument("--post", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-pre-frames", type=int, required=True)
    parser.add_argument("--expected-post-frames", type=int, required=True)
    args = parser.parse_args()

    pre = torch.load(args.pre, map_location="cpu")
    expected_post = torch.load(args.post, map_location="cpu")
    required_pre = {
        "batch", "initial_agent_state", "model_state_dict",
        "optimizer_state_dict", "scheduler_state_dict", "python_random_state",
        "numpy_random_state", "torch_rng_state", "flags", "frames_per_update",
        "derived_frames", "scheduler_last_epoch",
    }
    required_post = {
        "model_state_dict", "actor_model_state_dict", "optimizer_state_dict",
        "scheduler_state_dict", "gradient_state_dict", "python_random_state",
        "numpy_random_state", "torch_rng_state", "stats", "frames_per_update",
        "derived_frames", "scheduler_last_epoch",
    }
    if missing := sorted(required_pre - set(pre)):
        raise SystemExit(f"pre bundle missing: {missing}")
    if missing := sorted(required_post - set(expected_post)):
        raise SystemExit(f"post bundle missing: {missing}")

    if int(pre["derived_frames"]) != args.expected_pre_frames:
        raise SystemExit(
            f"captured wrong pre-update boundary: {pre['derived_frames']} != {args.expected_pre_frames}"
        )
    if int(expected_post["derived_frames"]) != args.expected_post_frames:
        raise SystemExit(
            f"captured wrong post-update boundary: {expected_post['derived_frames']} != {args.expected_post_frames}"
        )
    if int(expected_post["derived_frames"]) - int(pre["derived_frames"]) != int(pre["frames_per_update"]):
        raise SystemExit("captured frame delta is not exactly one learner update")
    if int(pre["frames_per_update"]) != int(expected_post["frames_per_update"]):
        raise SystemExit("frames_per_update changed across captured learner update")

    sys.path.insert(0, str(args.silg_root))
    run_exp = importlib.import_module("run_exp")
    flags_dict = dict(pre["flags"])
    flags_dict["disable_cuda"] = True
    flags = SimpleNamespace(**flags_dict)

    Net = importlib.import_module(f"model.{flags.model}").Model
    env = Net.create_env(flags)
    learner_model = Net.make(flags, env).to(torch.device("cpu"))
    actor_model = Net.make(flags, env).to(torch.device("cpu"))
    learner_model.load_state_dict(pre["model_state_dict"])
    actor_model.load_state_dict(pre["model_state_dict"])

    optimizer = torch.optim.RMSprop(
        learner_model.parameters(),
        lr=flags.learning_rate,
        momentum=flags.momentum,
        eps=flags.epsilon,
        alpha=flags.alpha,
    )
    optimizer.load_state_dict(pre["optimizer_state_dict"])

    def lr_lambda(epoch: int) -> float:
        return 1 - min(epoch * flags.unroll_length * flags.batch_size, flags.total_frames) / flags.total_frames

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    scheduler.load_state_dict(pre["scheduler_state_dict"])

    random.setstate(pre["python_random_state"])
    np.random.set_state(pre["numpy_random_state"])
    torch.set_rng_state(pre["torch_rng_state"])
    os.environ.pop("SILG_ONE_STEP_REPLAY_PREFIX", None)
    os.environ.pop("SILG_ONE_STEP_CAPTURE_PRE_FRAMES", None)

    batch = {key: value.detach().cpu().clone() for key, value in pre["batch"].items()}
    initial_agent_state = tuple(value.detach().cpu().clone() for value in pre["initial_agent_state"])
    observed_stats = run_exp.learn(
        actor_model,
        learner_model,
        batch,
        initial_agent_state,
        optimizer,
        scheduler,
        flags,
    )

    observed_gradients = {
        name: (None if parameter.grad is None else parameter.grad.detach().cpu().clone())
        for name, parameter in learner_model.named_parameters()
    }
    observed_scheduler_last_epoch = int(scheduler.state_dict().get("last_epoch", 0))
    observed_frames = observed_scheduler_last_epoch * int(pre["frames_per_update"])
    observed = {
        "model_state_dict": learner_model.state_dict(),
        "actor_model_state_dict": actor_model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "gradient_state_dict": observed_gradients,
        "python_random_state": random.getstate(),
        "numpy_random_state": np.random.get_state(),
        "torch_rng_state": torch.get_rng_state(),
        "stats": observed_stats,
        "frames_per_update": int(pre["frames_per_update"]),
        "derived_frames": observed_frames,
        "scheduler_last_epoch": observed_scheduler_last_epoch,
    }
    assert_exact(observed, {key: expected_post[key] for key in observed})

    payload = {
        "status": "accepted",
        "classification": "exact_one_step_resume_equivalence",
        "capability_progress_claimed": False,
        "public_baseline_reproduced": False,
        "exact_batch_sha256": tensor_stream_hash(pre["batch"]),
        "exact_initial_agent_state_sha256": tensor_stream_hash(pre["initial_agent_state"]),
        "pre_model_sha256": tensor_stream_hash(pre["model_state_dict"]),
        "post_model_sha256": tensor_stream_hash(expected_post["model_state_dict"]),
        "post_gradient_sha256": tensor_stream_hash(expected_post["gradient_state_dict"]),
        "pre_frames": int(pre["derived_frames"]),
        "post_frames": int(expected_post["derived_frames"]),
        "frames_per_update": int(pre["frames_per_update"]),
        "model_exact": True,
        "actor_model_exact": True,
        "optimizer_exact": True,
        "scheduler_exact": True,
        "gradient_exact": True,
        "frame_exact": True,
        "rng_exact": True,
        "stats_exact": True,
        "scope": "one captured real learner update; asynchronous actor queue continuation is not claimed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.output.read_text())


if __name__ == "__main__":
    main()
