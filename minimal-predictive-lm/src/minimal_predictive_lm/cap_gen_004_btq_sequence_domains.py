from __future__ import annotations

from .cap_gen_004_btq_core import Program, SynthesisTask


def string_programs() -> tuple[Program, ...]:
    programs: list[Program] = [
        Program("string", "identity", ("STR_ID",), lambda value: (value, ("EMIT_INPUT",))),
        Program("string", "reverse", ("STR_REVERSE",), lambda value: (value[::-1], tuple(["READ_BACK", "WRITE"] * len(value)))),
    ]
    for marker in ("#", "|", "@", "0"):
        def crop_runner(value: str, marker: str = marker):
            index = value.find(marker)
            if index < 0:
                return "", tuple(["TEST_FALSE", "ADVANCE"] * len(value) + ["HALT_EMPTY"])
            return value[index:], tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "EMIT_REMAINDER"])

        def after_runner(value: str, marker: str = marker):
            index = value.find(marker)
            if index < 0:
                return "", tuple(["TEST_FALSE", "ADVANCE"] * len(value) + ["HALT_EMPTY"])
            return value[index + 1 :], tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "ADVANCE", "EMIT_REMAINDER"])

        programs.extend([
            Program("string", f"slice_from_{marker}", ("STR_FIND", repr(marker), "STR_SLICE_FROM"), crop_runner),
            Program("string", f"slice_after_{marker}", ("STR_FIND", repr(marker), "STR_SLICE_AFTER"), after_runner),
        ])
    transforms = {"upper": str.upper, "lower": str.lower, "swapcase": str.swapcase}
    for name, transform in transforms.items():
        def map_runner(value: str, transform=transform):
            return "".join(transform(character) for character in value), tuple(["READ", "APPLY", "WRITE"] * len(value))
        programs.append(Program("string", f"map_{name}", ("STR_MAP", f"CHAR_{name.upper()}"), map_runner))
    for amount in (1, 2, 3):
        programs.extend([
            Program("string", f"take_{amount}", ("STR_TAKE", str(amount)), lambda value, amount=amount: (value[:amount], tuple(["READ", "WRITE"] * min(amount, len(value)) + ["HALT"]))),
            Program("string", f"drop_{amount}", ("STR_DROP", str(amount)), lambda value, amount=amount: (value[amount:], tuple(["ADVANCE"] * min(amount, len(value)) + ["EMIT_REMAINDER"]))),
        ])
    return tuple(programs)


def list_programs() -> tuple[Program, ...]:
    programs: list[Program] = [
        Program("list", "identity", ("LIST_ID",), lambda values: (values, ("EMIT_INPUT",))),
        Program("list", "reverse", ("LIST_REV",), lambda values: (tuple(reversed(values)), tuple(["READ_BACK", "WRITE"] * len(values)))),
    ]
    for marker in (-1, 0, 1, 2, 9):
        def crop_runner(values: tuple[int, ...], marker: int = marker):
            try:
                index = values.index(marker)
            except ValueError:
                return (), tuple(["TEST_FALSE", "ADVANCE"] * len(values) + ["HALT_EMPTY"])
            return values[index:], tuple(["TEST_FALSE", "ADVANCE"] * index + ["TEST_TRUE", "EMIT_REMAINDER"])

        def filter_runner(values: tuple[int, ...], marker: int = marker):
            return tuple(value for value in values if value == marker), tuple(["READ", "TEST", "MAYBE_WRITE"] * len(values))

        programs.extend([
            Program("list", f"dropwhile_ne_{marker}", ("LIST_DROPWHILE", f"NEQ_{marker}"), crop_runner),
            Program("list", f"filter_eq_{marker}", ("LIST_FILTER", f"EQ_{marker}"), filter_runner),
        ])
    transforms = {"add1": lambda value: value + 1, "sub1": lambda value: value - 1, "neg": lambda value: -value, "abs": abs}
    for name, transform in transforms.items():
        def map_runner(values: tuple[int, ...], transform=transform):
            return tuple(transform(value) for value in values), tuple(["READ", "APPLY", "WRITE"] * len(values))
        programs.append(Program("list", f"map_{name}", ("LIST_COMPREHENSION", f"NUM_{name.upper()}"), map_runner))
    for amount in (1, 2, 3):
        programs.extend([
            Program("list", f"take_{amount}", ("LIST_PREFIX", str(amount)), lambda values, amount=amount: (tuple(values[:amount]), tuple(["READ", "WRITE"] * min(amount, len(values)) + ["HALT"]))),
            Program("list", f"drop_{amount}", ("LIST_SUFFIX", str(amount)), lambda values, amount=amount: (tuple(values[amount:]), tuple(["ADVANCE"] * min(amount, len(values)) + ["EMIT_REMAINDER"]))),
        ])
    return tuple(programs)


def training_tasks() -> tuple[SynthesisTask, ...]:
    return (
        SynthesisTask("string_drop", "string", (("ab#cd", "#cd"), ("x#yz", "#yz"), ("12#3", "#3"))),
        SynthesisTask("string_reverse", "string", (("abcd", "dcba"), ("xy", "yx"), ("hello", "olleh"))),
        SynthesisTask("string_map", "string", (("abC", "ABC"), ("xy", "XY"), ("mN", "MN"))),
        SynthesisTask("list_drop", "list", (((3, 2, 0, 5), (0, 5)), ((8, 0, 1), (0, 1)), ((4, 4, 0), (0,)))),
        SynthesisTask("list_reverse", "list", (((1, 2, 3), (3, 2, 1)), ((4, 5), (5, 4)), ((9, 8, 7, 6), (6, 7, 8, 9)))),
        SynthesisTask("list_map", "list", (((1, 2), (2, 3)), ((0, 5), (1, 6)), ((-1, 3), (0, 4)))),
    )
