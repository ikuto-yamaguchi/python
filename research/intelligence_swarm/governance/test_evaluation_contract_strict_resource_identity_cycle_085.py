#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "research/intelligence_swarm/benchmarks/grounded_causal/evaluation_contract.py"

spec = importlib.util.spec_from_file_location("evaluation_contract", TARGET)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_strict_positive_bytes_accepts_only_positive_ints():
    assert module._strict_positive_bytes(1)
    assert module._strict_positive_bytes(1024)
    for value in (0, -1, True, False, 1.0, 1.5, "1", "１０", None):
        assert not module._strict_positive_bytes(value), value


def test_artifact_seed_uses_strict_seed_identity():
    source = TARGET.read_text(encoding="utf-8")
    assert 'seed = strict_seed(run["seed"])' in source
    assert 'seed = int(run["seed"])' not in source
    assert 'expected, observed = strict_seed(expected), strict_seed(observed)' in source


def test_byte_fields_are_not_float_coerced():
    source = TARGET.read_text(encoding="utf-8")
    assert 'field in {"model_bytes", "peak_rss_bytes"}' in source
    assert 'raw-log {field} must be a positive JSON integer' in source
    assert '"strict_resource_integer_identity_required": True' in source


if __name__ == "__main__":
    test_strict_positive_bytes_accepts_only_positive_ints()
    test_artifact_seed_uses_strict_seed_identity()
    test_byte_fields_are_not_float_coerced()
    print("cycle 085 strict resource identity regression: PASS")
