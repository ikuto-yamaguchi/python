from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Hashable, Mapping, Sequence


State = Hashable
Symbol = Hashable
Output = Hashable


@dataclass(frozen=True)
class DeterministicPredictor:
    """Finite deterministic Moore predictor used only as a lower-bound instrument.

    This is deliberately substrate-neutral: states may represent neural activations,
    symbolic configurations, program counters, or any other deterministic predictive
    state.  Partition refinement finds the observationally minimal quotient machine.
    """

    states: tuple[State, ...]
    alphabet: tuple[Symbol, ...]
    transitions: Mapping[tuple[State, Symbol], State]
    outputs: Mapping[State, Output]

    def validate(self) -> None:
        state_set = set(self.states)
        if not self.states:
            raise ValueError("at least one state is required")
        if len(state_set) != len(self.states):
            raise ValueError("states must be unique")
        if set(self.outputs) != state_set:
            raise ValueError("every state needs exactly one output")
        for state in self.states:
            for symbol in self.alphabet:
                target = self.transitions.get((state, symbol))
                if target not in state_set:
                    raise ValueError("transition function must be total and closed")


@dataclass(frozen=True)
class PredictiveQuotient:
    blocks: tuple[tuple[State, ...], ...]
    refinement_rounds: int
    transition_reads: int

    @property
    def state_count(self) -> int:
        return len(self.blocks)

    @property
    def minimum_persistent_state_bits(self) -> int:
        """Information-theoretic lower bound for naming one quotient state."""
        return 0 if self.state_count <= 1 else ceil(log2(self.state_count))

    def block_of(self, state: State) -> int:
        for index, block in enumerate(self.blocks):
            if state in block:
                return index
        raise KeyError(state)


def minimal_predictive_quotient(machine: DeterministicPredictor) -> PredictiveQuotient:
    """Return the coarsest output- and transition-consistent state partition.

    For a deterministic finite predictor, this is the standard observational quotient.
    Its block count is a rigorous lower bound on the number of distinguishable finite
    predictive states; it is not a claim about unrestricted intelligence.
    """

    machine.validate()
    by_output: dict[Output, list[State]] = {}
    for state in machine.states:
        by_output.setdefault(machine.outputs[state], []).append(state)
    blocks = tuple(
        tuple(sorted(group, key=repr))
        for _output, group in sorted(by_output.items(), key=lambda row: repr(row[0]))
    )

    rounds = 0
    transition_reads = 0
    while True:
        block_index = {
            state: index for index, block in enumerate(blocks) for state in block
        }
        refined: list[tuple[State, ...]] = []
        changed = False
        for block in blocks:
            signatures: dict[tuple[int, ...], list[State]] = {}
            for state in block:
                signature = []
                for symbol in machine.alphabet:
                    transition_reads += 1
                    signature.append(block_index[machine.transitions[(state, symbol)]])
                signatures.setdefault(tuple(signature), []).append(state)
            pieces = [
                tuple(sorted(group, key=repr))
                for _signature, group in sorted(signatures.items(), key=lambda row: row[0])
            ]
            refined.extend(pieces)
            changed |= len(pieces) > 1
        rounds += 1
        blocks = tuple(refined)
        if not changed:
            break

    return PredictiveQuotient(blocks, rounds, transition_reads)


def lifetime_resource_objective(
    *,
    executable_bits: int,
    persistent_state_bits: int,
    training_operations: int,
    inference_operations: int,
    peak_working_bits: int,
    prediction_loss_bits: float,
    weights: Sequence[float] = (1.0, 1.0, 1e-6, 1e-6, 1.0, 1.0),
) -> float:
    """Substrate-neutral lifetime resource score.

    The coefficients are explicit rather than hidden in an architecture.  Research
    comparisons must report the unweighted terms as well as any weighted aggregate.
    """

    terms = (
        executable_bits,
        persistent_state_bits,
        training_operations,
        inference_operations,
        peak_working_bits,
        prediction_loss_bits,
    )
    if len(weights) != len(terms):
        raise ValueError("six resource weights are required")
    if any(value < 0 for value in terms) or any(weight < 0 for weight in weights):
        raise ValueError("resource terms and weights must be non-negative")
    return sum(float(weight) * float(value) for weight, value in zip(weights, terms))
