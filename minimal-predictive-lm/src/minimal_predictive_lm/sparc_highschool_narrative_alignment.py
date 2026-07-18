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


class NarrativeAlignedLearner(CounterfactualNarrativeLearner):
    """Align observations, events and alternatives from one unlabeled narrative.

    The learner does not receive a task name, relation name, intervention index or
    pre-separated action list. It reuses the same observation inducer, program
    ranker and world executor to find a factual path that explains two observed
    states. A later executable clause is aligned to the factual event sharing its
    learned latent program, then the existing immutable world brancher is used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.narratives_aligned = 0
        self.narrative_abstentions = 0
        self.narrative_sentences_read = 0
        self.narrative_sentences_ignored = 0
        self.embedded_clauses_recovered = 0

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

    def _executable_clause(self, sentence: str, world: World | None = None) -> tuple[str, str] | None:
        """Recover the longest state-consistent executable suffix.

        Every candidate is scored by the same program bank and, when a world is
        available, must execute against that world. This removes discourse framing
        structurally without storing cue words or benchmark phrases.
        """
        candidates: list[tuple[int, str, str]] = []
        for start in range(len(sentence)):
            clause = sentence[start:]
            pid = self._program_identity(clause)
            if pid is None:
                continue
            if world is not None and not self.apply(clause, world).accepted:
                continue
            candidates.append((start, clause, pid))
        if not candidates:
            return None
        earliest = min(row[0] for row in candidates)
        selected = [row for row in candidates if row[0] == earliest]
        identities = {(clause, pid) for _start, clause, pid in selected}
        if len(identities) != 1:
            return None
        _start, clause, pid = selected[0]
        self.embedded_clauses_recovered += int(earliest > 0)
        return clause, pid

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

                factual: list[str] = []
                factual_programs: list[str] = []
                current = start_world
                ignored = 0
                for sentence in sentences[start_i + 1 : end_i]:
                    executable = self._executable_clause(sentence, current)
                    if executable is None:
                        ignored += 1
                        continue
                    clause, pid = executable
                    result = self.apply(clause, current)
                    if not result.accepted:
                        ignored += 1
                        continue
                    factual.append(clause)
                    factual_programs.append(pid)
                    current = result.world
                if not factual or current != end_world:
                    continue

                for sentence in sentences[end_i + 1 :]:
                    executable = self._executable_clause(sentence, start_world)
                    if executable is None:
                        ignored += 1
                        continue
                    clause, replacement_pid = executable
                    positions = [i for i, pid in enumerate(factual_programs) if pid == replacement_pid]
                    if len(positions) != 1:
                        continue
                    position = positions[0]
                    comparison = self.compare_intervention(
                        start_world,
                        factual,
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
                            tuple(factual),
                            (clause,),
                            position,
                            comparison,
                            ignored,
                            "shared-observation-program-alignment",
                        )
                    )

        unique = {
            (row.initial_world, row.observed_world, row.factual_actions, row.replacement_actions, row.intervention_at): row
            for row in candidates
        }
        if len(unique) != 1:
            self.narrative_abstentions += 1
            return NarrativeAlignmentResult(False, World(), World(), (), (), None, None, len(sentences), "abstain-ambiguous-narrative")
        result = next(iter(unique.values()))
        self.narratives_aligned += 1
        self.narrative_sentences_ignored += result.ignored_sentences
        return result

    def report(self):
        result = super().report()
        result.update(
            {
                "unlabeled_narrative_alignment": True,
                "intervention_index_supplied": False,
                "preseparated_action_lists_supplied": False,
                "phrase_exception_table_used": False,
                "narratives_aligned": self.narratives_aligned,
                "narrative_abstentions": self.narrative_abstentions,
                "narrative_sentences_read": self.narrative_sentences_read,
                "narrative_sentences_ignored": self.narrative_sentences_ignored,
                "embedded_clauses_recovered": self.embedded_clauses_recovered,
            }
        )
        return result
