#!/usr/bin/env python3
"""Run the existing R0.2 comparison with the official SILG action dimension.

The underlying comparison previously inferred ``num_actions`` as
``max(observed_action) + 1``.  A finite policy trajectory need not exercise every
public environment action, so that inference can create a smaller output head
than the live RTFM ``valid`` action mask and make online evaluation fail or,
worse, silently change the parameter budget across samples.

This wrapper adds no model mechanism.  It derives the action dimension from the
immutable typed ``valid`` field exported from the pinned SILG environment,
checks every label against that schema, and then invokes the existing matched
comparison with that fixed dimension.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import r02_typed_comparison as comparison


def _data_argument(argv: list[str]) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data", type=Path, required=True)
    args, _ = parser.parse_known_args(argv)
    return args.data


def _official_action_count(rows: list[dict[str, Any]]) -> int:
    schemas = [row.get("state_schema") for row in rows]
    if not schemas or any(not isinstance(schema, list) for schema in schemas):
        raise ValueError("typed rows must contain state_schema")
    canonical = schemas[0]
    if any(schema != canonical for schema in schemas[1:]):
        raise ValueError("state_schema changed across rows")

    valid_specs = [item for item in canonical if item.get("name") == "valid"]
    if len(valid_specs) != 1:
        raise ValueError(f"expected exactly one official valid-action field, found {len(valid_specs)}")
    shape = valid_specs[0].get("shape")
    if not isinstance(shape, list) or not shape or any(int(width) <= 0 for width in shape):
        raise ValueError(f"invalid official action-mask shape: {shape!r}")
    count = math.prod(int(width) for width in shape)

    labels = [int(row["action"]) for row in rows]
    invalid = sorted({label for label in labels if label < 0 or label >= count})
    if invalid:
        raise ValueError(f"action labels exceed official SILG schema ({count}): {invalid}")
    return count


def main() -> None:
    data = _data_argument(sys.argv[1:])
    rows = comparison.load_rows(data)
    comparison.validate_rows(rows)
    official_num_actions = _official_action_count(rows)
    observed_num_actions = max(int(row["action"]) for row in rows) + 1

    original_config = comparison.Config

    def schema_config(*args: Any, **kwargs: Any):
        requested = int(kwargs.get("num_actions", official_num_actions))
        if requested > official_num_actions:
            raise ValueError(
                f"comparison requested {requested} actions but official SILG schema has {official_num_actions}"
            )
        kwargs["num_actions"] = official_num_actions
        return original_config(*args, **kwargs)

    comparison.Config = schema_config
    print(
        json.dumps(
            {
                "status": "official_action_schema_fixed",
                "data": str(data),
                "observed_max_plus_one": observed_num_actions,
                "official_num_actions": official_num_actions,
                "expanded_unobserved_action_outputs": official_num_actions - observed_num_actions,
            },
            sort_keys=True,
        )
    )
    comparison.main()


if __name__ == "__main__":
    main()
