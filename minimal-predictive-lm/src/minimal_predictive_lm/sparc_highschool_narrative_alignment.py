from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_counterfactual import CounterfactualNarrativeLearner, CounterfactualResult
from .sparc_highschool_general import Edit, Program, World


@dataclass(frozen=True)
class NarrativeAlignmentResult:
    accepted: bool
    initial_world: World
    observed_world: World
    factual_actions: tuple[str, ...]
    replacement_actions: tuple[str, ...]
    intervention_at: int | None
    comparison: CounterfactualResult | None
    ignored_sentences: int
    mechanism: str


@dataclass(frozen=True)
class _Path:
    world: World
    actions: tuple[str, ...]
    programs: tuple[str, ...]
    ignored: int


class NarrativeAlignedLearner(CounterfactualNarrativeLearner):
    """Jointly align observations, events and alternatives in one narrative."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.narratives_aligned = 0
        self.narrative_abstentions = 0
        self.narrative_sentences_read = 0
        self.narrative_sentences_ignored = 0
        self.embedded_clauses_recovered = 0
        self.sequence_states_expanded = 0
        self.sequence_paths_pruned = 0
        self.endpoint_pairs_considered = 0
        self.complete_paths_found = 0
        self.replacement_options_found = 0
        self.branch_validation_rejected = 0
        self.branch_factual_mismatches = 0
        self.branch_unchanged = 0
        self.complete_alignments_found = 0
        self.slot_bound_arithmetic_executions = 0

    @staticmethod
    def _single_number(world: World):
        values = world.number_map()
        if world.facts or len(values) != 1:
            return None
        return next(iter(values.items()))

    @classmethod
    def _derive_edits(cls, before: World, after: World, atoms: tuple[str, ...]) -> tuple[Edit, ...]:
        """Turn visible arithmetic magnitudes into reusable execution slots.

        The inherited inducer identifies whether a transition is additive or
        multiplicative.  The magnitude is not stored as a training-example constant:
        it is bound from the same surface slot at execution time.  This mechanism is
        shared by calculation, planning, causal rollout and narrative alignment.
        """
        inherited = super()._derive_edits(before, after, atoms)
        edits: list[Edit] = []
        for edit in inherited:
            if edit.kind == "add_const" and edit.delta is not None:
                magnitude = str(abs(edit.delta))
                edits.append(
                    Edit(
                        "add_from_slot",
                        edit.relation,
                        edit.subject_slot,
                        object_slot=cls._slot_for(magnitude, atoms),
                        factor=1 if edit.delta >= 0 else -1,
                    )
                )
            elif edit.kind == "mul_const" and edit.factor is not None:
                magnitude = str(abs(edit.factor))
                edits.append(
                    Edit(
                        "mul_from_slot",
                        edit.relation,
                        edit.subject_slot,
                        object_slot=cls._slot_for(magnitude, atoms),
                        factor=1 if edit.factor >= 0 else -1,
                    )
                )
            else:
                edits.append(edit)
        return tuple(edits)

    @classmethod
    def _execute(cls, world: World, program: Program, bindings: tuple[str, ...]) -> World:
        facts = set(world.facts)
        numbers = world.number_map()
        for edit in program.edits:
            subject = cls._binding(bindings, edit.subject_slot)
            if edit.kind in {"add_fact", "remove_fact"}:
                obj = cls._binding(bindings, edit.object_slot)
                fact = (subject, edit.relation, obj)
                facts.add(fact) if edit.kind == "add_fact" else facts.discard(fact)
            elif edit.kind == "delete_number":
                numbers.pop((subject, edit.relation), None)
            elif edit.kind == "set_from_slot":
                numbers[(subject, edit.relation)] = int(cls._binding(bindings, edit.object_slot))
            elif edit.kind in {"add_const", "add_from_slot"}:
                key = (subject, edit.relation)
                if key not in numbers:
                    raise ValueError("missing numeric state")
                delta = int(edit.delta or 0) if edit.kind == "add_const" else int(cls._binding(bindings, edit.object_slot)) * int(edit.factor or 1)
                numbers[key] += delta
            elif edit.kind in {"mul_const", "mul_from_slot"}:
                key = (subject, edit.relation)
                if key not in numbers:
                    raise ValueError("missing numeric state")
                factor = int(edit.factor or 1) if edit.kind == "mul_const" else int(cls._binding(bindings, edit.object_slot)) * int(edit.factor or 1)
                numbers[key] *= factor
            else:
                raise ValueError(f"unknown edit {edit.kind}")
        return World.from_parts(facts, numbers)

    def _program_identity(self, sentence: str) -> str | None:
        rows = self._rank(sentence)
        if not rows or rows[0][0] < self.threshold or not rows[0][2]:
            return None
        if len(rows) > 1 and rows[0][0] - rows[1][0] < self.margin and rows[0][1].program_id != rows[1][1].program_id:
            return None
        return rows[0][1].program_id

    def _executable_candidates(self, sentence: str, world: World) -> tuple[tuple[str, str, World], ...]:
        equivalent: dict[tuple[str, World], tuple[int, str, str, World]] = {}
        for start in range(len(sentence)):
            clause = sentence[start:]
            pid = self._program_identity(clause)
            if pid is None:
                continue
            applied = self.apply(clause, world)
            if not applied.accepted or applied.program_id != pid or applied.world == world:
                continue
            key = (pid, applied.world)
            row = (start, clause, pid, applied.world)
            current = equivalent.get(key)
            if current is None or start < current[0]:
                equivalent[key] = row
        rows = sorted(equivalent.values(), key=lambda row: (row[0], row[2], row[1]))
        return tuple((clause, pid, successor) for _start, clause, pid, successor in rows)

    def _aligned_paths(self, sentences: tuple[str, ...], start_world: World, end_world: World, *, max_paths_per_world: int = 2) -> tuple[_Path, ...]:
        frontier: dict[World, list[_Path]] = {start_world: [_Path(start_world, (), (), 0)]}
        for sentence in sentences:
            next_frontier: dict[World, list[_Path]] = {}
            for paths in frontier.values():
                for path in paths:
                    self.sequence_states_expanded += 1
                    choices = [_Path(path.world, path.actions, path.programs, path.ignored + 1)]
                    choices.extend(
                        _Path(successor, path.actions + (clause,), path.programs + (pid,), path.ignored)
                        for clause, pid, successor in self._executable_candidates(sentence, path.world)
                    )
                    for choice in choices:
                        bucket = next_frontier.setdefault(choice.world, [])
                        signature = (choice.actions, choice.programs)
                        if any((row.actions, row.programs) == signature for row in bucket):
                            self.sequence_paths_pruned += 1
                            continue
                        bucket.append(choice)
                        bucket.sort(key=lambda row: (row.ignored, len(row.actions), row.actions))
                        if len(bucket) > max_paths_per_world:
                            self.sequence_paths_pruned += len(bucket) - max_paths_per_world
                            del bucket[max_paths_per_world:]
            frontier = next_frontier
        return tuple(frontier.get(end_world, ()))

    def infer_counterfactual_narrative(self, text: str) -> NarrativeAlignmentResult:
        sentences = tuple(self._sentences(text))
        self.narrative_sentences_read += len(sentences)
        observations: list[tuple[int, tuple[str, str], int, World]] = []
        for index, sentence in enumerate(sentences):
            observed = self.observe_world([sentence])
            if observed.accepted != 1 or observed.abstained:
                continue
            row = self._single_number(observed.world)
            if row is not None:
                key, value = row
                observations.append((index, key, value, observed.world))

        candidates: list[NarrativeAlignmentResult] = []
        for left_index in range(len(observations)):
            for right_index in range(left_index + 1, len(observations)):
                start_i, key, _start_value, start_world = observations[left_index]
                end_i, end_key, _end_value, end_world = observations[right_index]
                if key != end_key or end_i <= start_i + 1:
                    continue
                self.endpoint_pairs_considered += 1
                paths = self._aligned_paths(sentences[start_i + 1 : end_i], start_world, end_world)
                semantic_paths = {(path.programs, path.world): path for path in paths if path.actions and path.world == end_world}
                self.complete_paths_found += len(semantic_paths)
                if len(semantic_paths) != 1:
                    continue
                path = next(iter(semantic_paths.values()))

                replacements: dict[tuple[int, str, World], tuple[str, str, World]] = {}
                for sentence in sentences[end_i + 1 :]:
                    prefix_world = start_world
                    prefix_worlds = [start_world]
                    valid_prefix = True
                    for action in path.actions:
                        prefix_result = self.apply(action, prefix_world)
                        if not prefix_result.accepted:
                            valid_prefix = False
                            break
                        prefix_world = prefix_result.world
                        prefix_worlds.append(prefix_world)
                    if not valid_prefix:
                        continue
                    for position, factual_pid in enumerate(path.programs):
                        for clause, replacement_pid, successor in self._executable_candidates(sentence, prefix_worlds[position]):
                            if replacement_pid == factual_pid:
                                replacements[(position, replacement_pid, successor)] = (clause, replacement_pid, successor)
                self.replacement_options_found += len(replacements)

                for (position, _pid, _successor), (clause, _replacement_pid, _world) in replacements.items():
                    comparison = self.compare_intervention(start_world, path.actions, intervention_at=position, replacement_actions=(clause,))
                    if not comparison.accepted:
                        self.branch_validation_rejected += 1
                        continue
                    if comparison.factual.world != end_world:
                        self.branch_factual_mismatches += 1
                        continue
                    if comparison.counterfactual.world == comparison.factual.world:
                        self.branch_unchanged += 1
                        continue
                    self.slot_bound_arithmetic_executions += 1
                    candidates.append(NarrativeAlignmentResult(True, start_world, end_world, path.actions, (clause,), position, comparison, path.ignored, "shared-sequence-world-alignment"))

        self.complete_alignments_found += len(candidates)
        unique = {
            (row.initial_world, row.observed_world, row.comparison.factual.world if row.comparison else World(), row.comparison.counterfactual.world if row.comparison else World(), row.intervention_at): row
            for row in candidates
        }
        if len(unique) != 1:
            self.narrative_abstentions += 1
            return NarrativeAlignmentResult(False, World(), World(), (), (), None, None, len(sentences), "abstain-ambiguous-narrative")
        result = next(iter(unique.values()))
        self.narratives_aligned += 1
        self.narrative_sentences_ignored += result.ignored_sentences
        self.embedded_clauses_recovered += sum(int(action not in sentences) for action in result.factual_actions + result.replacement_actions)
        return result

    def report(self):
        result = super().report()
        result.update({
            "unlabeled_narrative_alignment": True,
            "intervention_index_supplied": False,
            "preseparated_action_lists_supplied": False,
            "phrase_exception_table_used": False,
            "joint_sequence_alignment": True,
            "slot_bound_arithmetic": True,
            "slot_bound_arithmetic_executions": self.slot_bound_arithmetic_executions,
            "narratives_aligned": self.narratives_aligned,
            "narrative_abstentions": self.narrative_abstentions,
            "narrative_sentences_read": self.narrative_sentences_read,
            "narrative_sentences_ignored": self.narrative_sentences_ignored,
            "embedded_clauses_recovered": self.embedded_clauses_recovered,
            "sequence_states_expanded": self.sequence_states_expanded,
            "sequence_paths_pruned": self.sequence_paths_pruned,
            "endpoint_pairs_considered": self.endpoint_pairs_considered,
            "complete_paths_found": self.complete_paths_found,
            "replacement_options_found": self.replacement_options_found,
            "branch_validation_rejected": self.branch_validation_rejected,
            "branch_factual_mismatches": self.branch_factual_mismatches,
            "branch_unchanged": self.branch_unchanged,
            "complete_alignments_found": self.complete_alignments_found,
        })
        return result
