from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2, prod
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ResourcePoint:
    executable_bits: int
    inference_operations: int
    peak_working_entries: int

    def __post_init__(self) -> None:
        if min(
            self.executable_bits,
            self.inference_operations,
            self.peak_working_entries,
        ) < 0:
            raise ValueError("resources must be non-negative")


@dataclass(frozen=True)
class MacroReplacement:
    repetitions: int
    original_bits_per_copy: int
    macro_definition_bits: int
    call_bits_per_use: int
    original_operations_per_copy: int
    macro_operations_per_use: int
    lookup_operations_per_use: int = 0

    @property
    def saved_bits(self) -> int:
        return (
            self.repetitions * self.original_bits_per_copy
            - self.macro_definition_bits
            - self.repetitions * self.call_bits_per_use
        )

    @property
    def saved_operations(self) -> int:
        return self.repetitions * (
            self.original_operations_per_copy
            - self.macro_operations_per_use
            - self.lookup_operations_per_use
        )


def flat_boolean_factor_entries(variable_count: int) -> int:
    """Entries needed by one unrestricted Boolean truth-table factor."""
    if variable_count < 0:
        raise ValueError("variable_count must be non-negative")
    return 1 << variable_count


def fixed_length_program_count(generator_count: int, depth: int) -> int:
    """Number of words of exactly ``depth`` over ``generator_count`` symbols."""
    if generator_count < 1 or depth < 0:
        raise ValueError("invalid generator language")
    return generator_count**depth


def program_code_bits(generator_count: int, depth: int) -> int:
    """Fixed-width code length for one generator word of fixed depth."""
    if generator_count < 1 or depth < 0:
        raise ValueError("invalid generator language")
    bits_per_symbol = 0 if generator_count == 1 else ceil(log2(generator_count))
    return depth * bits_per_symbol


def affine_word_value(word: Sequence[int], generator_count: int) -> int:
    """Injective fixed-length probe for affine generators g_i(x)=m*x+i."""
    if generator_count < 1:
        raise ValueError("generator_count must be positive")
    value = 0
    for symbol in word:
        if symbol < 0 or symbol >= generator_count:
            raise ValueError("generator symbol outside alphabet")
        value = generator_count * value + symbol
    return value


def downstream_error_bound(
    local_errors: Iterable[float],
    downstream_lipschitz_products: Iterable[float],
) -> float:
    """Triangle-inequality bound for several non-overlapping macro replacements.

    For replacement j, ``local_errors[j]`` is a uniform local approximation error,
    and ``downstream_lipschitz_products[j]`` is the product of Lipschitz constants of
    all transformations after that replacement.
    """
    errors = tuple(float(value) for value in local_errors)
    products = tuple(float(value) for value in downstream_lipschitz_products)
    if len(errors) != len(products):
        raise ValueError("each local error needs one downstream product")
    if any(value < 0 for value in errors + products):
        raise ValueError("error bounds and Lipschitz products must be non-negative")
    return sum(error * multiplier for error, multiplier in zip(errors, products))


def suffix_lipschitz_products(lipschitz_constants: Sequence[float]) -> tuple[float, ...]:
    """Return products of all constants strictly after each position."""
    constants = tuple(float(value) for value in lipschitz_constants)
    if any(value < 0 for value in constants):
        raise ValueError("Lipschitz constants must be non-negative")
    return tuple(prod(constants[index + 1 :]) for index in range(len(constants)))


def resource_objective_delta(
    replacement: MacroReplacement,
    *,
    predictive_extra_bits: float,
    bit_weight: float = 1.0,
    operation_weight: float = 0.0,
) -> float:
    """New objective minus old objective; negative means the macro is admitted."""
    if predictive_extra_bits < 0 or bit_weight < 0 or operation_weight < 0:
        raise ValueError("objective terms must be non-negative")
    return (
        predictive_extra_bits
        - bit_weight * replacement.saved_bits
        - operation_weight * replacement.saved_operations
    )


def resource_frontier_dominates(left: ResourcePoint, right: ResourcePoint) -> bool:
    """True iff left is no worse in every resource and better in at least one."""
    left_values = (
        left.executable_bits,
        left.inference_operations,
        left.peak_working_entries,
    )
    right_values = (
        right.executable_bits,
        right.inference_operations,
        right.peak_working_entries,
    )
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )
