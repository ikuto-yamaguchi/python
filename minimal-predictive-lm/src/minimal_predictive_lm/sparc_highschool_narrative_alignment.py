from __future__ import annotations

from dataclasses import dataclass

from .sparc_highschool_counterfactual import CounterfactualNarrativeLearner, CounterfactualResult
from .sparc_highschool_general import World


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
    """Jointly align observations, events and alternatives in one narrative.

    No task name, relation name, intervention index or pre-separated action list is
    supplied.  All sentence decisions share the same latent program bank and world
    executor.  Instead of greedily accepting each locally executable sentence, a
    sparse sequence lattice keeps only complete paths whose accumulated transition
    exactly explains a later observation.  The same lattice then constrains the
    alternative event and immutable counterfactual branch.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.narratives_aligned = 0
        self.narrative_abstentions = 0
        self.narrative_sentences_read = 0
        self.narrative_sentences_ignored = 0
        self.embedded_clauses_recovered = 0
        self.sequence_states_expanded = 0
        self.sequence_paths_pruned = 0

    @staticmethod
    def _single_number(world: World):
        values = world.number_map()
        if world.facts or len(values) != 1:
            return None
        return next(iter(values.items()))

    def _program_identity(self, sentence: str) -> str | None:
        rows = self._rank(sentence)
        if not rows or rows[0][0] < self.threshold or not rows[0][2]:
            return None
        if len(rows) > 1 and rows[0][0] - rows[1][0] < self.margin and rows[0][1].program_id != rows[1][1].program_id:
            return None
        return rows[0][1].program_id

    def _executable_candidates(self, sentence: str, world: World) -> tuple[tuple[str, str, World], ...]:
        """Return semantically distinct executable suffixes for one sentence.

        Discourse framing is not recognized by a phrase table.  Every suffix is
        proposed by the shared program ranker and validated by the shared executor.
        Candidates producing the same program and successor world are equivalent;
        the longest surface realization is retained.
        """
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

    def _aligned_paths(
        self,
        sentences: tuple[str, ...],
        start_world: World,
        end_world: World,
        *,
        max_paths_per_world: int = 2,
    ) -> tuple[_Path, ...]:
        """Solve sentence selection and state evolution as one sparse lattice."""
        frontier: dict[World, list[_Path]] = {start_world: [_Path(start_world, (), (), 0)]}
        for sentence in sentences:
            next_frontier: dict[World, list[_Path]] = {}
            for paths in frontier.values():
                for path in paths:
                    self.sequence_states_expanded += 1
                    choices = [_Path(path.world, path.actions, path.programs, path.ignored + 1)]
                    for clause, pid, successor in self._executable_candidates(sentence, path.world):
                        choices.append(
                            _Path(
                                successor,
                                path.actions + (clause,),
                                path.programs + (pid,),
                                path.ignored,
                            )
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

                paths = self._aligned_paths(sentences[start_i + 1 : end_i], start_world, end_world)
                semantic_paths = {
                    (path.programs, path.world): path
                    for path in paths
                    if path.actions and path.world == end_world
                }
                if len(semantic_paths) != 1:
                    continue
                path = next(iter(semantic_paths.values()))

                replacements: dict[tuple[int, str, World], tuple[str, str, World]] = {}
                for sentence in sentences[end_i + 1 :]:
                    for position, factual_pid in enumerate(path.programs):
                        prefix_world = start_world
                        for action in path.actions[:position]:
                            prefix_result = self.apply(action, prefix_world)
                            if not prefix_result.accepted:
                                break
                            prefix_world = prefix_result.world
                        else:
                            for clause, replacement_pid, successor in self._executable_candidates(sentence, prefix_world):
                                if replacement_pid != factual_pid:
                                    continue
                                replacements[(position, replacement_pid, successor)] = (clause, replacement_pid, successor)

                for (position, _pid, _successor), (clause, _replacement_pid, _world) in replacements.items():
                    comparison = self.compare_intervention(
                        start_world,
                        path.actions,
                        intervention_at=position,
                        replacement_actions=(clause,),
                    )
                    if not comparison.accepted or comparison.factual.world != end_world:
                        continue
                    if comparison.counterfactual.world == comparison.factual.world:
                        continue
                    candidates.append(
                        NarrativeAlignmentResult(
                            True,
                            start_world,
                            end_world,
                            path.actions,
                            (clause,),
                            position,
                            comparison,
                            path.ignored,
                            "shared-sequence-world-alignment",
                        )
                    )

        unique = {
            (
                row.initial_world,
                row.observed_world,
                row.comparison.factual.world if row.comparison else World(),
                row.comparison.counterfactual.world if row.comparison else World(),
                row.intervention_at,
            ): row
            for row in candidates
        }
        if len(unique) != 1:
            self.narrative_abstentions += 1
            return NarrativeAlignmentResult(False, World(), World(), (), (), None, None, len(sentences), "abstain-ambiguous-narrative")
        result = next(iter(unique.values()))
        self.narratives_aligned += 1
        self.narrative_sentences_ignored += result.ignored_sentences
        self.embedded_clauses_recovered += sum(
            int(action not in sentences) for action in result.factual_actions + result.replacement_actions
        )
        return result

    def report(self):
        result = super().report()
        result.update(
            {
                "unlabeled_narrative_alignment": True,
                "intervention_index_supplied": False,
                "preseparated_action_lists_supplied": False,
                "phrase_exception_table_used": False,
                "joint_sequence_alignment": True,
                "narratives_aligned": self.narratives_aligned,
                "narrative_abstentions": self.narrative_abstentions,
                "narrative_sentences_read": self.narrative_sentences_read,
                "narrative_sentences_ignored": self.narrative_sentences_ignored,
                "embedded_clauses_recovered": self.embedded_clauses_recovered,
                "sequence_states_expanded": self.sequence_states_expanded,
                "sequence_paths_pruned": self.sequence_paths_pruned,
            }
        )
        return result
