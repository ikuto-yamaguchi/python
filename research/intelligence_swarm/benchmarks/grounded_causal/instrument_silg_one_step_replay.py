#!/usr/bin/env python3
"""Instrument pinned SILG for an exact, audit-only learner-step replay.

The public checkpoint omits actor RNG/queue state, so an asynchronous process
restart cannot identify the exact next rollout. This instrumentation does not
change the model, loss, optimizer, scheduler, or sampling defaults. It captures
one real learner update while SILG's existing learner lock is held:

* the exact batch and initial recurrent state consumed by the update;
* model/optimizer/scheduler and Python/NumPy/Torch RNG state before it;
* clipped parameter gradients, model/optimizer/scheduler state, statistics and
  the scheduler-derived frame boundary after it.

The target pre-update frame boundary is supplied by the workflow. This prevents
an apparently successful replay of the first learner update from satisfying the
registered 3,840 -> 5,760 frame qualification.
"""

from __future__ import annotations

import argparse
from pathlib import Path


IMPORT_ANCHOR = "import random\nimport exp_utils\n"
IMPORT_REPLACEMENT = "import random\nfrom pathlib import Path\nimport exp_utils\n"

LEARN_ANCHOR = '''    with lock:\n        learner_outputs, unused_state = model(batch, initial_agent_state)\n'''

LEARN_REPLACEMENT = '''    with lock:\n        capture_prefix = os.environ.get('SILG_ONE_STEP_REPLAY_PREFIX')\n        target_pre_frames_text = os.environ.get('SILG_ONE_STEP_CAPTURE_PRE_FRAMES')\n        frames_per_update = int(flags.batch_size) * int(flags.unroll_length)\n        scheduler_last_epoch = int(scheduler.state_dict().get('last_epoch', 0))\n        derived_pre_frames = scheduler_last_epoch * frames_per_update\n        capture_candidate = (\n            bool(capture_prefix)\n            and target_pre_frames_text is not None\n            and derived_pre_frames == int(target_pre_frames_text)\n        )\n        capture_owner = False\n        capture_pre_path = None\n        capture_post_path = None\n        if capture_candidate:\n            capture_pre_path = Path(capture_prefix + '.pre.pt')\n            capture_post_path = Path(capture_prefix + '.post.pt')\n            marker = Path(capture_prefix + '.claim')\n            marker.parent.mkdir(parents=True, exist_ok=True)\n            try:\n                fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY)\n                os.close(fd)\n                capture_owner = True\n            except FileExistsError:\n                capture_owner = False\n\n        if capture_owner:\n            def _cpu_clone(value):\n                if torch.is_tensor(value):\n                    return value.detach().cpu().clone()\n                if isinstance(value, dict):\n                    return {k: _cpu_clone(v) for k, v in value.items()}\n                if isinstance(value, (list, tuple)):\n                    return type(value)(_cpu_clone(v) for v in value)\n                return copy.deepcopy(value)\n\n            torch.save({\n                'format_version': 2,\n                'classification': 'resume_equivalence_instrumentation_only',\n                'capability_progress_claimed': False,\n                'batch': _cpu_clone(batch),\n                'initial_agent_state': _cpu_clone(tuple(initial_agent_state)),\n                'model_state_dict': _cpu_clone(model.state_dict()),\n                'optimizer_state_dict': _cpu_clone(optimizer.state_dict()),\n                'scheduler_state_dict': _cpu_clone(scheduler.state_dict()),\n                'python_random_state': random.getstate(),\n                'numpy_random_state': np.random.get_state(),\n                'torch_rng_state': torch.get_rng_state().cpu().clone(),\n                'flags': copy.deepcopy(vars(flags)),\n                'frames_per_update': frames_per_update,\n                'derived_frames': derived_pre_frames,\n                'scheduler_last_epoch': scheduler_last_epoch,\n            }, capture_pre_path)\n\n        learner_outputs, unused_state = model(batch, initial_agent_state)\n'''

RETURN_ANCHOR = '''        actor_model.load_state_dict(model.state_dict())\n        return stats\n'''

RETURN_REPLACEMENT = '''        actor_model.load_state_dict(model.state_dict())\n        if capture_owner:\n            gradient_state_dict = {\n                name: (None if parameter.grad is None else parameter.grad.detach().cpu().clone())\n                for name, parameter in model.named_parameters()\n            }\n            post_scheduler_last_epoch = int(scheduler.state_dict().get('last_epoch', 0))\n            derived_post_frames = post_scheduler_last_epoch * frames_per_update\n            torch.save({\n                'format_version': 2,\n                'classification': 'resume_equivalence_instrumentation_only',\n                'capability_progress_claimed': False,\n                'model_state_dict': _cpu_clone(model.state_dict()),\n                'actor_model_state_dict': _cpu_clone(actor_model.state_dict()),\n                'optimizer_state_dict': _cpu_clone(optimizer.state_dict()),\n                'scheduler_state_dict': _cpu_clone(scheduler.state_dict()),\n                'gradient_state_dict': gradient_state_dict,\n                'python_random_state': random.getstate(),\n                'numpy_random_state': np.random.get_state(),\n                'torch_rng_state': torch.get_rng_state().cpu().clone(),\n                'stats': copy.deepcopy(stats),\n                'frames_per_update': frames_per_update,\n                'derived_frames': derived_post_frames,\n                'scheduler_last_epoch': post_scheduler_last_epoch,\n            }, capture_post_path)\n        return stats\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("silg_root", type=Path)
    args = parser.parse_args()

    target = args.silg_root / "run_exp.py"
    original = target.read_text()
    patched = replace_once(original, IMPORT_ANCHOR, IMPORT_REPLACEMENT, "imports")
    patched = replace_once(patched, LEARN_ANCHOR, LEARN_REPLACEMENT, "learn-entry")
    patched = replace_once(patched, RETURN_ANCHOR, RETURN_REPLACEMENT, "learn-exit")
    target.write_text(patched)

    compile(target.read_text(), str(target), "exec")
    print(f"instrumented={target}")
    print("capture_scope=registered_frame_boundary_inside_existing_learner_lock")
    print("captures=exact_batch,recurrent_state,rng,gradients,derived_frames")
    print("model_loss_optimizer_scheduler_sampling_changed=false")


if __name__ == "__main__":
    main()
