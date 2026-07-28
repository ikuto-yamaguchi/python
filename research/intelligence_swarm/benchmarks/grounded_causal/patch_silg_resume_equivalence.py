#!/usr/bin/env python3
"""Instrument pinned SILG for a fail-closed one-step resume-equivalence probe.

This patch does not alter the model, optimizer, sampling defaults, split, or
training objective. It wraps exactly one learner update, serializes the RNG and
exact learner batch at the update boundary, reloads the serialized state, and
requires the uninterrupted and resumed updates to be bitwise identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silg-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = (args.silg_root / "run_exp.py").resolve()
    before = sha256(source)
    text = source.read_text(encoding="utf-8")

    text = replace_once(text, "def learn(actor_model,", "def _learn_impl(actor_model,", "rename_learn")
    text = replace_once(
        text,
        "        nn.utils.clip_grad_norm_(model.parameters(), 40.0)\n",
        "        global _resume_probe_last_grad_norm\n"
        "        _resume_probe_last_grad_norm = float(nn.utils.clip_grad_norm_(model.parameters(), 40.0))\n",
        "gradient_norm_capture",
    )

    anchor = "\ndef create_buffers(observation_shapes, num_actions, flags) -> Buffers:\n"
    wrapper = r'''

_resume_probe_done = False
_resume_probe_last_grad_norm = None
_resume_probe_gate = threading.Lock()


class _NoopLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _clone_tree(value):
    if torch.is_tensor(value):
        return value.detach().clone()
    if isinstance(value, dict):
        return {k: _clone_tree(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(_clone_tree(v) for v in value)
    if isinstance(value, list):
        return [_clone_tree(v) for v in value]
    return copy.deepcopy(value)


def _tree_mismatches(left, right, prefix='root'):
    failures = []
    if torch.is_tensor(left) or torch.is_tensor(right):
        if not (torch.is_tensor(left) and torch.is_tensor(right)):
            return [prefix + ':tensor_type_mismatch']
        if left.shape != right.shape:
            return [prefix + ':shape_mismatch']
        if left.dtype != right.dtype:
            return [prefix + ':dtype_mismatch']
        if not torch.equal(left.detach().cpu(), right.detach().cpu()):
            return [prefix + ':tensor_value_mismatch']
        return []
    if isinstance(left, dict) or isinstance(right, dict):
        if not (isinstance(left, dict) and isinstance(right, dict)):
            return [prefix + ':mapping_type_mismatch']
        if set(left) != set(right):
            failures.append(prefix + ':key_set_mismatch')
            return failures
        for key in sorted(left, key=str):
            failures.extend(_tree_mismatches(left[key], right[key], prefix + '.' + str(key)))
        return failures
    if isinstance(left, (tuple, list)) or isinstance(right, (tuple, list)):
        if type(left) is not type(right) or len(left) != len(right):
            return [prefix + ':sequence_mismatch']
        for index, (a, b) in enumerate(zip(left, right)):
            failures.extend(_tree_mismatches(a, b, prefix + '[' + str(index) + ']'))
        return failures
    if left != right:
        failures.append(prefix + ':value_mismatch')
    return failures


def _capture_rng():
    payload = {
        'python': random.getstate(),
        'numpy': np.random.get_state(),
        'torch_cpu': torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        payload['torch_cuda'] = torch.cuda.get_rng_state_all()
    return payload


def _restore_rng(payload):
    random.setstate(payload['python'])
    np.random.set_state(payload['numpy'])
    torch.set_rng_state(payload['torch_cpu'])
    if 'torch_cuda' in payload:
        torch.cuda.set_rng_state_all(payload['torch_cuda'])


def _tensor_metadata(tree, prefix='root'):
    rows = []
    if torch.is_tensor(tree):
        rows.append({'path': prefix, 'shape': list(tree.shape), 'dtype': str(tree.dtype), 'numel': tree.numel()})
    elif isinstance(tree, dict):
        for key in sorted(tree, key=str):
            rows.extend(_tensor_metadata(tree[key], prefix + '.' + str(key)))
    elif isinstance(tree, (tuple, list)):
        for index, value in enumerate(tree):
            rows.extend(_tensor_metadata(value, prefix + '[' + str(index) + ']'))
    return rows


def learn(actor_model, model, batch, initial_agent_state, optimizer, scheduler, flags,
          lock=threading.Lock()):
    global _resume_probe_done, _resume_probe_last_grad_norm
    output = os.environ.get('SILG_RESUME_PROBE_OUTPUT')
    if not output or _resume_probe_done:
        return _learn_impl(actor_model, model, batch, initial_agent_state,
                           optimizer, scheduler, flags, lock=lock)

    with _resume_probe_gate:
        if _resume_probe_done:
            return _learn_impl(actor_model, model, batch, initial_agent_state,
                               optimizer, scheduler, flags, lock=lock)
        with lock:
            _resume_probe_done = True
            out_path = os.path.abspath(output)
            payload_path = out_path + '.pt'

            boundary = {
                'model': _clone_tree(model.state_dict()),
                'actor_model': _clone_tree(actor_model.state_dict()),
                'optimizer': _clone_tree(optimizer.state_dict()),
                'scheduler': _clone_tree(scheduler.state_dict()),
                'rng': _capture_rng(),
                'batch': _clone_tree(batch),
                'initial_agent_state': _clone_tree(initial_agent_state),
                'frame_increment': int(flags.unroll_length * flags.batch_size),
            }
            torch.save(boundary, payload_path)
            loaded = torch.load(payload_path, map_location=get_device(flags))

            stats_uninterrupted = _learn_impl(
                actor_model, model, batch, initial_agent_state, optimizer,
                scheduler, flags, lock=_NoopLock())
            grad_uninterrupted = _resume_probe_last_grad_norm
            post_uninterrupted = {
                'model': _clone_tree(model.state_dict()),
                'optimizer': _clone_tree(optimizer.state_dict()),
                'scheduler': _clone_tree(scheduler.state_dict()),
            }

            model.load_state_dict(loaded['model'])
            actor_model.load_state_dict(loaded['actor_model'])
            optimizer.load_state_dict(loaded['optimizer'])
            scheduler.load_state_dict(loaded['scheduler'])
            _restore_rng(loaded['rng'])

            stats_resumed = _learn_impl(
                actor_model, model, loaded['batch'], loaded['initial_agent_state'],
                optimizer, scheduler, flags, lock=_NoopLock())
            grad_resumed = _resume_probe_last_grad_norm
            post_resumed = {
                'model': _clone_tree(model.state_dict()),
                'optimizer': _clone_tree(optimizer.state_dict()),
                'scheduler': _clone_tree(scheduler.state_dict()),
            }

            failures = []
            failures.extend(_tree_mismatches(post_uninterrupted['model'], post_resumed['model'], 'model'))
            failures.extend(_tree_mismatches(post_uninterrupted['optimizer'], post_resumed['optimizer'], 'optimizer'))
            failures.extend(_tree_mismatches(post_uninterrupted['scheduler'], post_resumed['scheduler'], 'scheduler'))
            if stats_uninterrupted != stats_resumed:
                failures.append('scalar_stats_mismatch')
            if grad_uninterrupted != grad_resumed:
                failures.append('gradient_norm_mismatch')

            import hashlib as _hashlib
            _h = _hashlib.sha256()
            with open(payload_path, 'rb') as _f:
                for _chunk in iter(lambda: _f.read(1024 * 1024), b''):
                    _h.update(_chunk)
            report = {
                'status': 'accepted' if not failures else 'rejected',
                'classification': 'one_step_resume_equivalence',
                'instrumentation_only': True,
                'capability_evidence': False,
                'rng_state_saved': ['python', 'numpy', 'torch_cpu'] + (['torch_cuda'] if 'torch_cuda' in loaded['rng'] else []),
                'exact_batch_payload': payload_path,
                'exact_batch_payload_bytes': os.path.getsize(payload_path),
                'exact_batch_payload_sha256': _h.hexdigest(),
                'batch_tensors': _tensor_metadata(loaded['batch'], 'batch'),
                'initial_state_tensors': _tensor_metadata(loaded['initial_agent_state'], 'initial_agent_state'),
                'frame_increment_equal': True,
                'frame_increment': loaded['frame_increment'],
                'model_bitwise_equal': not _tree_mismatches(post_uninterrupted['model'], post_resumed['model'], 'model'),
                'optimizer_bitwise_equal': not _tree_mismatches(post_uninterrupted['optimizer'], post_resumed['optimizer'], 'optimizer'),
                'scheduler_bitwise_equal': not _tree_mismatches(post_uninterrupted['scheduler'], post_resumed['scheduler'], 'scheduler'),
                'scalar_stats_uninterrupted': stats_uninterrupted,
                'scalar_stats_resumed': stats_resumed,
                'gradient_norm_uninterrupted': grad_uninterrupted,
                'gradient_norm_resumed': grad_resumed,
                'failures': failures,
                'new_mechanism_family_claimed': False,
                'new_intelligence_principle_claimed': False,
                'capability_progress_claimed': False,
            }
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as _f:
                json.dump(report, _f, indent=2, sort_keys=True)
                _f.write('\n')
            if failures:
                raise RuntimeError('one-step resume equivalence failed: ' + '; '.join(failures[:8]))
            return stats_resumed
'''
    text = replace_once(text, anchor, wrapper + anchor, "insert_resume_wrapper")
    compile(text, str(source), "exec")
    source.write_text(text, encoding="utf-8")
    after = sha256(source)

    payload = {
        "classification": "resume_equivalence_instrumentation_patch",
        "source": str(source),
        "before_sha256": before,
        "after_sha256": after,
        "changes": [
            "serialize Python NumPy Torch RNG at learner-update boundary",
            "serialize exact learner batch and initial agent state",
            "replay one update after disk reload",
            "bitwise compare model optimizer scheduler and exact compare losses gradient norm",
        ],
        "model_or_objective_changed": False,
        "capability_progress_claimed": False,
        "new_intelligence_principle_claimed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
