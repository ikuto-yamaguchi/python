from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_general import Program, World
from .sparc_highschool_intervention_lattice import InterventionLatticeLearner


@dataclass(frozen=True)
class ImplicitWorldResult:
    accepted: bool
    initial_world: World
    final_world: World
    actions: tuple[str, ...]
    inferred_values: tuple[tuple[str, str, int], ...]
    answer: str
    verified: bool
    mechanism: str


class ImplicitWorldLearner(InterventionLatticeLearner):
    """Recover omitted numeric state through one shared reversible world constraint.

    Learned event programs are compiled to sparse affine transitions ``a*x+b``.  The
    same program bank and surface binder used by forward execution are used in reverse
    against later observations.  This is task/domain blind and works for multiple
    subjects without adding subject-specific rules or vocabulary.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.implicit_worlds_inferred = 0
        self.implicit_world_abstentions = 0
        self.reverse_constraints_solved = 0
        self.reverse_constraint_reads = 0
        self.implicit_world_verification_failures = 0

    def _affine_transition(
        self, sentence: str
    ) -> tuple[tuple[str, str], int, int, str] | None:
        rows = self._rank(sentence)
        if not rows or rows[0][0] < self.threshold or not rows[0][2]:
            return None
        if (
            len(rows) > 1
            and rows[0][0] - rows[1][0] < self.margin
            and rows[0][1].program_id != rows[1][1].program_id
        ):
            return None
        _score, program, bindings, _mechanism = rows[0]
        compiled = self._compile_program(program, bindings)
        if compiled is None:
            return None
        key, scale, offset = compiled
        return key, scale, offset, program.program_id

    @classmethod
    def _compile_program(
        cls, program: Program, bindings: tuple[str, ...]
    ) -> tuple[tuple[str, str], int, int] | None:
        if len(program.edits) != 1:
            return None
        edit = program.edits[0]
        subject = cls._binding(bindings, edit.subject_slot)
        key = (subject, edit.relation)
        if edit.kind == "add_const":
            return key, 1, int(edit.delta or 0)
        if edit.kind == "add_from_slot":
            value = int(cls._binding(bindings, edit.object_slot))
            return key, 1, value * int(edit.factor or 1)
        if edit.kind == "mul_const":
            return key, int(edit.factor or 1), 0
        if edit.kind == "mul_from_slot":
            value = int(cls._binding(bindings, edit.object_slot))
            return key, value * int(edit.factor or 1), 0
        return None

    @staticmethod
    def _compose(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
        """Return right(left(x)) for affine pairs (scale, offset)."""
        left_scale, left_offset = left
        right_scale, right_offset = right
        return right_scale * left_scale, right_scale * left_offset + right_offset

    def infer_implicit_world(self, text: str) -> ImplicitWorldResult:
        sentences = tuple(self._sentences(text))
        observations: list[tuple[int, tuple[str, str], int]] = []
        transitions: list[tuple[int, str, tuple[str, str], int, int, str]] = []
        for index, sentence in enumerate(sentences):
            observed = self.observe_world([sentence])
            if observed.accepted == 1 and not observed.abstained:
                row = self._single_number(observed.world)
                if row is not None:
                    key, value = row
                    observations.append((index, key, value))
            transition = self._affine_transition(sentence)
            if transition is not None:
                key, scale, offset, program_id = transition
                transitions.append((index, sentence, key, scale, offset, program_id))
        self.reverse_constraint_reads += len(sentences) + len(transitions)

        inferred: dict[tuple[str, str], int] = {}
        selected_actions: list[tuple[int, str]] = []
        for observation_index, key, observed_value in observations:
            relevant = [row for row in transitions if row[0] < observation_index and row[2] == key]
            if not relevant:
                continue
            affine = (1, 0)
            for _index, _sentence, _key, scale, offset, _pid in relevant:
                affine = self._compose(affine, (scale, offset))
            scale, offset = affine
            numerator = observed_value - offset
            if scale == 0 or numerator % scale:
                self.implicit_world_abstentions += 1
                return ImplicitWorldResult(False, World(), World(), (), (), "", False, "abstain-nonintegral-or-singular-constraint")
            value = numerator // scale
            previous = inferred.get(key)
            if previous is not None and previous != value:
                self.implicit_world_abstentions += 1
                return ImplicitWorldResult(False, World(), World(), (), (), "", False, "abstain-conflicting-world-constraints")
            inferred[key] = value
            selected_actions.extend((row[0], row[1]) for row in relevant)
            self.reverse_constraints_solved += 1

        if not inferred or len(inferred) != len({key for _i, key, _v in observations if any(row[0] < _i and row[2] == key for row in transitions)}):
            self.implicit_world_abstentions += 1
            return ImplicitWorldResult(False, World(), World(), (), (), "", False, "abstain-insufficient-implicit-constraints")

        initial = World.from_parts(numbers=inferred)
        world = initial
        ordered_actions = tuple(sentence for _index, sentence in sorted(set(selected_actions)))
        for action in ordered_actions:
            applied = self.apply(action, world)
            if not applied.accepted:
                self.implicit_world_abstentions += 1
                return ImplicitWorldResult(False, initial, world, ordered_actions, (), "", False, "abstain-forward-verification-failed")
            world = applied.world

        final_numbers = world.number_map()
        verified = all(final_numbers.get(key) == value for _index, key, value in observations if key in inferred)
        if not verified:
            self.implicit_world_verification_failures += 1
            self.implicit_world_abstentions += 1
            return ImplicitWorldResult(False, initial, world, ordered_actions, (), "", False, "abstain-observation-mismatch")

        rows = tuple((subject, relation, value) for (subject, relation), value in sorted(inferred.items()))
        explanation = "、".join(f"{subject}の{relation}の初期値は{value}" for subject, relation, value in rows)
        answer = f"後段の観測と同じ世界遷移を逆向きに照合すると、{explanation}です。順方向に再実行し、全観測と一致することを検算しました。"
        self.implicit_worlds_inferred += 1
        return ImplicitWorldResult(True, initial, world, ordered_actions, rows, answer, True, "shared-reversible-affine-world-constraint")

    def report(self):
        result = super().report()
        result.update({
            "shared_reversible_world_constraints": True,
            "implicit_initial_state_supplied": False,
            "implicit_worlds_inferred": self.implicit_worlds_inferred,
            "implicit_world_abstentions": self.implicit_world_abstentions,
            "reverse_constraints_solved": self.reverse_constraints_solved,
            "reverse_constraint_reads": self.reverse_constraint_reads,
            "implicit_world_verification_failures": self.implicit_world_verification_failures,
        })
        return result
