#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("export_rtfm_generator_signatures.py")
spec = importlib.util.spec_from_file_location("export_rtfm_generator_signatures", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class Element:
    def __init__(self, name: str) -> None:
        self.name = name

    def describe(self) -> str:
        return self.name


class Task:
    monsters = ["wolf", "jaguar", "panther"]
    groups = ["star alliance"]
    modifiers = ["blessed", "gleaming"]
    items = ["sword", "axe"]

    def __init__(self) -> None:
        self.group_assignment = [("star alliance", ("wolf", "jaguar", "panther"))]
        self.modifier_assignment = [(Element("fire"), ("blessed", "gleaming"))]
        self.target_group = "star alliance"


class Wrapper:
    def __init__(self) -> None:
        self.rtfm_env = Task()


def test_preoutcome_metadata_and_support() -> None:
    row = module.extract_generator_metadata(Wrapper(), "test", 7, 3)
    assert row["episode_seed"] == 7 * 1_000_003 + 3
    assert row["dynamics_holdout"] is True
    assert row["entity_holdout"] is False
    assert row["language_holdout"] is False
    assert row["holdout_support"] == {
        "entity": False,
        "dynamics": True,
        "language_form": False,
    }
    assert all(value is False for key, value in row["provenance"].items() if key.startswith("uses_"))


def test_signatures_are_deterministic_and_dynamics_sensitive() -> None:
    first = module.extract_generator_metadata(Wrapper(), "train", 1, 0)
    second = module.extract_generator_metadata(Wrapper(), "train", 1, 0)
    assert first["entity_signature"] == second["entity_signature"]
    assert first["dynamics_signature"] == second["dynamics_signature"]

    changed = Wrapper()
    changed.rtfm_env.modifier_assignment = [(Element("cold"), ("blessed", "gleaming"))]
    third = module.extract_generator_metadata(changed, "train", 1, 0)
    assert first["entity_signature"] == third["entity_signature"]
    assert first["dynamics_signature"] != third["dynamics_signature"]


def test_missing_generator_metadata_fails_closed() -> None:
    class Invalid:
        pass

    try:
        module.extract_generator_metadata(Invalid(), "train", 1, 0)
    except RuntimeError as exc:
        assert ".rtfm_env" in str(exc)
    else:
        raise AssertionError("missing generator metadata was accepted")


if __name__ == "__main__":
    test_preoutcome_metadata_and_support()
    test_signatures_are_deterministic_and_dynamics_sensitive()
    test_missing_generator_metadata_fails_closed()
    print("ok")
