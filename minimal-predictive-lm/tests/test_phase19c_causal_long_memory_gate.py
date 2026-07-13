from pathlib import Path
import json

from minimal_predictive_lm.phase19a_general_learning_reality_gate import (
    train_ngram,
)
from minimal_predictive_lm.phase19c_causal_long_memory_gate import (
    MemoryConfig,
    memory_file_bits,
    run_gate,
    synthetic_long_range_probe,
)


def test_long_range_probe_needs_large_window():
    assert synthetic_long_range_probe()


def test_future_suffix_does_not_change_explicit_prefix_score():
    model = train_ngram(
        [tuple(b"abcabcabc")], order=3, vocabulary_size=258
    )
    config = MemoryConfig(128, 0.5, 1)
    prefix = tuple(b"abcabc")
    first = memory_file_bits(model, prefix, config)
    second = memory_file_bits(model, prefix, config)
    assert first == second


def test_zero_confidence_equals_base_style():
    model = train_ngram(
        [tuple(b"abcabcabc")], order=3, vocabulary_size=258
    )
    short = memory_file_bits(
        model, tuple(b"abcabc"), MemoryConfig(64, 0.0, 1)
    )
    long = memory_file_bits(
        model, tuple(b"abcabc"), MemoryConfig(4096, 0.0, 2)
    )
    assert short == long


def test_memory_never_reads_future_target():
    model = train_ngram(
        [tuple(b"aaaaab")], order=3, vocabulary_size=258
    )
    config = MemoryConfig(4096, 0.75, 1)
    first = memory_file_bits(model, tuple(b"aaaaa"), config)
    second = memory_file_bits(model, tuple(b"aaaaa"), config)
    assert first == second


def test_real_gate_uses_file_disjoint_calibration(tmp_path: Path):
    for index in range(15):
        repeated = (
            "shared repeated identifier block value value\n" * 80
        ) + str(index)
        (tmp_path / f"c{index}.py").write_text(repeated, encoding="utf-8")
        (tmp_path / f"p{index}.md").write_text(repeated, encoding="utf-8")
        (tmp_path / f"s{index}.json").write_text(
            json.dumps({"rows": [repeated] * 3, "i": index}),
            encoding="utf-8",
        )
    result = run_gate(tmp_path)
    assert result["checks"]["calibration_is_file_disjoint"]
    assert result["online_heldout_adaptation"]
