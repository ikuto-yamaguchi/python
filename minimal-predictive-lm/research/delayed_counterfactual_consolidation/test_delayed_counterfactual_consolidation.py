from delayed_counterfactual_consolidation import FastMemory, blind_rename, key_of, make_example
import random


def test_key_is_deterministic_and_fixed_size():
    first = key_of("葵は青。")
    second = key_of("葵は青。")
    assert first == second
    assert len(first) == 64


def test_blind_rename_changes_symbols_without_task_labels():
    rng = random.Random(1)
    changed = blind_rename("Aは赤。Bは青。", rng)
    assert changed != "Aは赤。Bは青。"
    assert "は" in changed


def test_delayed_mode_rejects_some_candidate_writes():
    rng = random.Random(7)
    memory = FastMemory("delayed_counterfactual")
    for _ in range(128):
        text, target, _ = make_example(rng)
        memory.observe(text, target, rng)
    assert memory.candidates == 128
    assert memory.rejected > 0
    assert memory.accepted < memory.candidates


def test_always_mode_accepts_all_writes():
    rng = random.Random(7)
    memory = FastMemory("always")
    for _ in range(64):
        text, target, _ = make_example(rng)
        memory.observe(text, target, rng)
    assert memory.accepted == 64
    assert memory.rejected == 0
