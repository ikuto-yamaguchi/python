#!/usr/bin/env python3
"""Apply Cycle 085 fail-closed seed and byte-count identity hardening."""
from pathlib import Path

TARGET = Path("research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match, found {count}: {old[:120]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    marker = '''def _finite_positive(value: Any) -> bool:\n    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0\n'''
    addition = marker + '''\n\ndef _strict_positive_bytes(value: Any) -> bool:\n    """Byte counts must be real positive integers, never bool/float/string aliases."""\n    return type(value) is int and value > 0\n'''
    if "def _strict_positive_bytes" not in text:
        text = replace_once(text, marker, addition)

    text = replace_once(
        text,
        '''        elif field == "seed":\n            try:\n                expected, observed = int(expected), int(observed)\n            except (TypeError, ValueError):\n                errors.append(f"run {index}: seed is not integer-like in manifest or raw log")\n                continue\n        elif field in {"model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"}:\n            if not _finite_positive(expected) or not _finite_positive(observed):\n                errors.append(f"run {index}: raw-log {field} must be finite and positive")\n                continue\n            expected, observed = float(expected), float(observed)\n''',
        '''        elif field == "seed":\n            try:\n                expected, observed = strict_seed(expected), strict_seed(observed)\n            except (TypeError, ValueError):\n                errors.append(f"run {index}: seed must be a JSON integer in manifest and raw log")\n                continue\n        elif field in {"model_bytes", "peak_rss_bytes"}:\n            if not _strict_positive_bytes(expected) or not _strict_positive_bytes(observed):\n                errors.append(f"run {index}: raw-log {field} must be a positive JSON integer")\n                continue\n        elif field in {"training_wall_seconds", "cpu_inference_ms_per_item"}:\n            if not _finite_positive(expected) or not _finite_positive(observed):\n                errors.append(f"run {index}: raw-log {field} must be finite and positive")\n                continue\n            expected, observed = float(expected), float(observed)\n''',
    )

    text = replace_once(text, '            seed = int(run["seed"])\n', '            seed = strict_seed(run["seed"])\n')
    text = replace_once(
        text,
        '''        for key in ("model_bytes", "peak_rss_bytes", "training_wall_seconds", "cpu_inference_ms_per_item"):\n            if not _finite_positive(run.get(key)): errors.append(f"run {index}: {key} must be a finite positive number")\n''',
        '''        for key in ("model_bytes", "peak_rss_bytes"):\n            if not _strict_positive_bytes(run.get(key)): errors.append(f"run {index}: {key} must be a positive JSON integer")\n        for key in ("training_wall_seconds", "cpu_inference_ms_per_item"):\n            if not _finite_positive(run.get(key)): errors.append(f"run {index}: {key} must be a finite positive number")\n''',
    )

    text = replace_once(
        text,
        '"positive_resource_measurements_required": True,',
        '"positive_resource_measurements_required": True, "strict_resource_integer_identity_required": True, "strict_resource_integer_fields": ["model_bytes", "peak_rss_bytes"],',
    )

    TARGET.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
