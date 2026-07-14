from __future__ import annotations

from typing import Sequence

from .cap_gen_004_btq_core import Program, SynthesisTask

Grid = tuple[tuple[int, ...], ...]


def grid_programs() -> tuple[Program, ...]:
    programs: list[Program] = []
    def add(name: str, tokens: Sequence[str], runner) -> None:
        programs.append(Program("grid", name, tuple(tokens), runner))

    add("identity", ("GRID_ID",), lambda grid: (grid, ("EMIT_INPUT",)))
    add("reverse_rows", ("GRID_FLIP_VERTICAL",), lambda grid: (tuple(reversed(grid)), tuple(["READ_BACK", "WRITE"] * len(grid))))
    add("reverse_each_row", ("GRID_MAP_ROWS", "ROW_REVERSE"), lambda grid: (tuple(tuple(reversed(row)) for row in grid), tuple(["READ", "APPLY", "WRITE"] * len(grid))))
    add("sort_each_row", ("GRID_MAP_ROWS", "ROW_SORT"), lambda grid: (tuple(tuple(sorted(row)) for row in grid), tuple(["READ", "APPLY", "WRITE"] * len(grid))))
    add("rotate_each_row_left", ("GRID_MAP_ROWS", "ROW_ROT_L"), lambda grid: (tuple(row[1:] + row[:1] if row else row for row in grid), tuple(["READ", "APPLY", "WRITE"] * len(grid))))
    add("rotate_each_row_right", ("GRID_MAP_ROWS", "ROW_ROT_R"), lambda grid: (tuple(row[-1:] + row[:-1] if row else row for row in grid), tuple(["READ", "APPLY", "WRITE"] * len(grid))))

    for color in range(10):
        def crop_runner(grid: Grid, color: int = color):
            index = next((row_index for row_index, row in enumerate(grid) if color in row), None)
            if index is None:
                return (), tuple(["TEST_FALSE", "ADVANCE"] * len(grid) + ["HALT_EMPTY"])
            return tuple(grid[index:]), tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "EMIT_REMAINDER"])

        def after_runner(grid: Grid, color: int = color):
            index = next((row_index for row_index, row in enumerate(grid) if color in row), None)
            if index is None:
                return (), tuple(["TEST_FALSE", "ADVANCE"] * len(grid) + ["HALT_EMPTY"])
            return tuple(grid[index + 1 :]), tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "ADVANCE", "EMIT_REMAINDER"])

        def filter_runner(grid: Grid, color: int = color):
            return tuple(row for row in grid if color in row), tuple(["READ", "TEST", "MAYBE_WRITE"] * len(grid))

        add(f"crop_from_row_containing_{color}", ("GRID_FIRST_ROW_CONTAINING", str(color), "GRID_CROP_FROM"), crop_runner)
        add(f"crop_after_row_containing_{color}", ("GRID_FIRST_ROW_CONTAINING", str(color), "GRID_CROP_AFTER"), after_runner)
        add(f"filter_rows_containing_{color}", ("GRID_FILTER_ROWS", str(color)), filter_runner)

    for threshold in (0, 1, 2, 3, 4, 5, 9, 10, 15, 20):
        def sum_crop_runner(grid: Grid, threshold: int = threshold):
            index = next((row_index for row_index, row in enumerate(grid) if sum(row) >= threshold), None)
            if index is None:
                return (), tuple(["TEST_FALSE", "ADVANCE"] * len(grid) + ["HALT_EMPTY"])
            return tuple(grid[index:]), tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "EMIT_REMAINDER"])
        add(f"crop_from_sum_ge_{threshold}", ("GRID_FIRST_ROW_SUM_GE", str(threshold), "GRID_CROP_FROM"), sum_crop_runner)

    for amount in range(1, 8):
        add(f"take_rows_{amount}", ("GRID_TAKE_ROWS", str(amount)), lambda grid, amount=amount: (tuple(grid[:amount]), tuple(["READ", "WRITE"] * min(amount, len(grid)) + ["HALT"])))
        add(f"drop_rows_{amount}", ("GRID_DROP_ROWS", str(amount)), lambda grid, amount=amount: (tuple(grid[amount:]), tuple(["ADVANCE"] * min(amount, len(grid)) + ["EMIT_REMAINDER"])))
        add(f"rotate_rows_left_{amount}", ("GRID_ROT_ROWS_L", str(amount)), lambda grid, amount=amount: (tuple(grid[amount:] + grid[:amount]) if grid else grid, ("ROTATE", "EMIT")))

    def transpose(grid: Grid):
        if not grid:
            return (), ("HALT_EMPTY",)
        if len({len(row) for row in grid}) > 1:
            return (), ("INVALID",)
        return tuple(tuple(row[column] for row in grid) for column in range(len(grid[0]))), ("TRANSPOSE", "EMIT")

    add("transpose", ("GRID_TRANSPOSE",), transpose)
    add("first_row_only", ("GRID_FIRST_ROW",), lambda grid: (tuple(grid[:1]), ("READ", "WRITE", "HALT")))
    add("last_row_only", ("GRID_LAST_ROW",), lambda grid: (tuple(grid[-1:]), ("READ_BACK", "WRITE", "HALT")))
    return tuple(programs)


def heldout_grid_tasks() -> tuple[SynthesisTask, ...]:
    return (
        SynthesisTask("grid_crop_color9", "grid", (
            (((1, 1), (2, 2), (9, 0), (3, 3)), ((9, 0), (3, 3))),
            (((4, 4), (9, 1), (2, 2)), ((9, 1), (2, 2))),
            (((0, 0), (5, 5), (9, 9)), ((9, 9),)),
        ), (
            (((2, 2), (1, 9), (3, 3)), ((1, 9), (3, 3))),
            (((9, 5), (4, 4), (3, 3)), ((9, 5), (4, 4), (3, 3))),
        )),
        SynthesisTask("grid_crop_color4", "grid", (
            (((1, 1), (2, 2), (4, 0), (3, 3)), ((4, 0), (3, 3))),
            (((8, 8), (7, 7), (4, 1), (2, 2)), ((4, 1), (2, 2))),
            (((4, 4), (5, 5)), ((4, 4), (5, 5))),
        ), (
            (((8, 8), (4, 2), (1, 1)), ((4, 2), (1, 1))),
            (((4, 9), (0, 0)), ((4, 9), (0, 0))),
        )),
        SynthesisTask("grid_reverse_rows", "grid", (
            (((1, 2), (3, 4), (5, 6)), ((5, 6), (3, 4), (1, 2))),
            (((7, 8), (9, 0)), ((9, 0), (7, 8))),
            (((1,), (2,), (3,), (4,)), ((4,), (3,), (2,), (1,))),
        ), (
            (((1, 2), (3, 4), (5, 6), (7, 8)), ((7, 8), (5, 6), (3, 4), (1, 2))),
            (((9,), (8,), (7,)), ((7,), (8,), (9,))),
        )),
        SynthesisTask("grid_map_reverse_each_row", "grid", (
            (((1, 2, 3), (4, 5, 6)), ((3, 2, 1), (6, 5, 4))),
            (((7, 8), (9, 0), (1, 2)), ((8, 7), (0, 9), (2, 1))),
            (((1,), (2,)), ((1,), (2,))),
        ), (
            (((1, 4, 7), (2, 5, 8)), ((7, 4, 1), (8, 5, 2))),
            (((9, 0), (3, 2)), ((0, 9), (2, 3))),
        )),
        SynthesisTask("grid_map_sort_each_row", "grid", (
            (((3, 1, 2), (6, 4, 5)), ((1, 2, 3), (4, 5, 6))),
            (((8, 7), (0, 9), (2, 1)), ((7, 8), (0, 9), (1, 2))),
            (((1,), (2,)), ((1,), (2,))),
        ), (
            (((7, 1, 4), (9, 2, 5)), ((1, 4, 7), (2, 5, 9))),
            (((3, 2, 1), (8, 6, 7)), ((1, 2, 3), (6, 7, 8))),
        )),
        SynthesisTask("grid_map_rotate_left", "grid", (
            (((1, 2, 3), (4, 5, 6)), ((2, 3, 1), (5, 6, 4))),
            (((7, 8), (9, 0), (1, 2)), ((8, 7), (0, 9), (2, 1))),
            (((1,), (2,)), ((1,), (2,))),
        ), (
            (((1, 4, 7), (2, 5, 8)), ((4, 7, 1), (5, 8, 2))),
            (((9, 0), (3, 2)), ((0, 9), (2, 3))),
        )),
    )


def grid_probe_inputs() -> tuple[Grid, ...]:
    return (
        ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9)),
        ((9, 8), (7, 6), (5, 4), (3, 2), (1, 0), (9, 0)),
    )
